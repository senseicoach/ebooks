#!/usr/bin/env python3
"""Make an EPUB read well on older Kindles (and other basic e-ink readers).

Older Kindles ignore background colours but keep text colours, so light text
on a dark box turns into faint text on a white page. They also squeeze wide
tables onto a small screen. This script changes only what is affected:
  1. Any box with a dark background becomes a light tint, and light text that
     actually sits on a dark background becomes dark. Light text elsewhere
     (e.g. decorative numbers on a white page) is left exactly as it is.
  2. Tables with 4+ columns become stacked "label: value" blocks.
  3. Remaining tables get slightly smaller text so they fit.
The words of the book are not changed.

Usage: python3 tools/kindle_fix.py in.epub out.epub
"""
import re, sys, zipfile
from lxml import etree
from cssselect import GenericTranslator, SelectorError

HEX = r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b'

def hex2rgb(h):
    h = h.lstrip('#')
    if len(h) == 3: h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

def lum(h):
    r, g, b = hex2rgb(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

DARK_TEXT, GOLD_TEXT, LIGHT_BG = '#1B2A4A', '#7A5A12', '#F4EFE3'
RULE = re.compile(r'([^{}]+)\{([^{}]*)\}')

def css_vars(css):
    return dict(re.findall(r'(--[\w-]+)\s*:\s*(' + HEX + r')', css))

def bg_colours(body, vars_):
    out = []
    for val in re.findall(r'background(?:-color)?\s*:\s*([^;]+)', body):
        out += re.findall(HEX, val)
        out += [vars_[v] for v in re.findall(r'var\((--[\w-]+)\)', val) if v in vars_]
    return out

def has_dark_bg(body, vars_):
    return any(lum(c) < 0.35 for c in bg_colours(body, vars_))

def light_text(body):
    return any(lum(c) >= 0.6 for c in re.findall(r'(?<![-\w])color\s*:\s*(' + HEX + ')', body))

def to_xpath(sel):
    sel = re.sub(r'::?[\w-]+(\([^)]*\))?', '', sel).strip()   # drop pseudo-classes/elements
    if not sel: return None
    try: return GenericTranslator().css_to_xpath(sel)
    except SelectorError: return None

def strip_ns(tree):
    for el in tree.iter():
        if isinstance(el.tag, str) and '}' in el.tag: el.tag = el.tag.split('}', 1)[1]
    return tree

def fix_css(css, docs):
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    clean = css
    vars_ = css_vars(clean)
    dark_sels = [s.strip() for sel, body in RULE.findall(clean) if has_dark_bg(body, vars_) for s in sel.split(',')]
    dark_xp = [x for x in (to_xpath(s) for s in dark_sels) if x]
    dark_els = set()   # keep the element objects themselves (stable identity)
    for d in docs:
        for xp in dark_xp:
            for el in d.xpath(xp): dark_els.add(el)
    def in_dark(sel):
        for s in sel.split(','):
            xp = to_xpath(s)
            if not xp: continue
            for d in docs:
                for el in d.xpath(xp):
                    if any(a in dark_els for a in [el, *el.iterancestors()]): return True
        return False
    def has_text(sel):
        for s_ in sel.split(','):
            xp = to_xpath(s_)
            if not xp: return True          # can't tell: be safe and treat as text
            for d in docs:
                for el in d.xpath(xp):
                    if ''.join(el.itertext()).strip(): return True
        return False
    dark_classes = set(re.findall(r'\.([\w-]+)', ' '.join(dark_sels)))
    def mentions_dark(sel):
        return bool(set(re.findall(r'\.([\w-]+)', sel)) & dark_classes)
    changed = []
    def rule(m):
        sel, body = m.group(1), m.group(2)
        dark = has_dark_bg(body, vars_)
        if dark and not light_text(body) and not has_text(sel):
            return m.group(0)                 # a decorative line/bar with no text: keep it dark
        if not dark and not (light_text(body) and (in_dark(sel) or mentions_dark(sel))): return m.group(0)
        def bg(mm):
            val = mm.group(2)
            cols = re.findall(HEX, val) + [vars_[v] for v in re.findall(r'var\((--[\w-]+)\)', val) if v in vars_]
            return mm.group(1) + (LIGHT_BG if any(lum(c) < 0.35 for c in cols) else val)
        body = re.sub(r'(background(?:-color)?\s*:\s*)([^;}]+)', bg, body)
        def fg(mm):
            col = mm.group(2)
            if lum(col) < 0.6: return mm.group(0)
            r, g, b = hex2rgb(col)
            return mm.group(1) + (GOLD_TEXT if r > b + 0.12 else DARK_TEXT)
        body = re.sub(r'((?<![-\w])color\s*:\s*)(' + HEX + ')', fg, body)
        changed.append(sel.strip()[:40])
        return sel + '{' + body + '}'
    css = RULE.sub(rule, css)
    css += """
/* --- Added for older Kindles and small e-ink screens --- */
table { font-size: 0.82em; }
td, th { overflow-wrap: break-word; word-wrap: break-word; }
.rowcards { margin: 0.4em 0 1em 0; }
.rowcard { border-left: 3px solid #C9A24D; padding: 0.25em 0 0.25em 0.8em; margin: 0 0 0.8em 0; }
.rowcard p { margin: 0 0 0.2em 0; text-indent: 0; }
.rc-title { font-weight: bold; color: #1B2A4A; }
.rc-k { font-weight: bold; color: #1B2A4A; }
"""
    return css, changed

def cell_html(c):
    c = c.strip()
    c = re.sub(r'^<p[^>]*>(.*)</p>$', r'\1', c, flags=re.S)
    c = re.sub(r'</p>\s*<p[^>]*>', '<br/>', c)
    return c.strip()

def stack_table(m):
    tb = m.group(0)
    head = re.search(r'<thead[^>]*>(.*?)</thead>', tb, re.S)
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tb, re.S)
    if not rows: return tb
    if head:
        hdr = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', head.group(1), re.S)
        body_rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tb[head.end():], re.S)
    else:
        hdr = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', rows[0], re.S)
        body_rows = rows[1:]
    ncol = max(len(re.findall(r'<t[hd]\b', r)) for r in rows)
    if ncol < 4 or len(hdr) != ncol: return tb
    if any(re.search(r'(row|col)span', r) for r in rows): return tb
    hdr = [cell_html(h) for h in hdr]
    out = ['<div class="rowcards">']
    for r in body_rows:
        cells = [cell_html(c) for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.S)]
        cells += [''] * (ncol - len(cells))
        title = cells[0] or '__________'
        num_head = re.fullmatch(r'#|\d+', re.sub(r'<[^>]+>', '', hdr[0]).strip())
        out.append('<div class="rowcard">')
        lab0 = re.sub(r'<[^>]+>', '', hdr[0]).strip()
        sep0 = '' if lab0.endswith(('…', ':', '?')) else ':'
        out.append(f'<p class="rc-title"><span class="rc-k">{hdr[0]}{sep0}</span> {title}</p>' if lab0
                   else f'<p class="rc-title">{title}</p>')
        for h, c in zip(hdr[1:], cells[1:]):
            label = re.sub(r'<[^>]+>', '', h).strip()
            sep = '' if label.endswith(('…', ':', '?')) else ':'
            out.append(f'<p><span class="rc-k">{h}{sep}</span> {c or "__________"}</p>')
        out.append('</div>')
    out.append('</div>')
    return '\n'.join(out)

def main(src, dst):
    zin = zipfile.ZipFile(src)
    docs = []
    for n in zin.namelist():
        if n.endswith(('.xhtml', '.html')):
            try: docs.append(strip_ns(etree.fromstring(zin.read(n), etree.XMLParser(recover=True))))
            except Exception: pass
    stacked, changed = 0, []
    with zipfile.ZipFile(dst, 'w') as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename.endswith('.css'):
                css, ch = fix_css(data.decode('utf-8'), docs); changed += ch
                data = css.encode('utf-8')
            elif info.filename.endswith(('.xhtml', '.html')):
                t = data.decode('utf-8'); n0 = t.count('<table')
                t = re.sub(r'<table\b.*?</table>', stack_table, t, flags=re.S)
                stacked += n0 - t.count('<table'); data = t.encode('utf-8')
            zout.writestr(info, data, compress_type=zipfile.ZIP_STORED if info.filename == 'mimetype' else zipfile.ZIP_DEFLATED)
    print(f'{dst}: {len(changed)} style rules fixed {changed}; {stacked} wide tables stacked')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
