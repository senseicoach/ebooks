#!/usr/bin/env python3
"""Make an EPUB read well on older Kindles (and other basic e-ink readers).

Older Kindles ignore background colours but keep text colours, so light text
on a dark box turns into faint grey text on a white page. They also squeeze
wide tables onto a small screen. This script:
  1. Rewrites CSS so every coloured box uses dark text on a light tint.
  2. Turns tables with 4+ columns into stacked "label: value" blocks.
  3. Makes the remaining tables a little more compact.

Usage: python3 tools/kindle_fix.py in.epub out.epub
"""
import re, sys, zipfile

def hex2rgb(h):
    h = h.lstrip('#')
    if len(h) == 3: h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

def lum(h):
    r, g, b = hex2rgb(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

DARK_TEXT, GOLD_TEXT, LIGHT_BG = '#1B2A4A', '#7A5A12', '#F4EFE3'

def fix_css(css):
    def rule(m):
        sel, body = m.group(1), m.group(2)
        def bg(mm):
            col = mm.group(2)
            return mm.group(1) + (LIGHT_BG if lum(col) < 0.35 else col)
        body = re.sub(r'(background(?:-color)?\s*:\s*)(#[0-9a-fA-F]{3,6})', bg, body)
        def fg(mm):
            col = mm.group(2)
            if lum(col) < 0.6: return mm.group(0)
            r, g, b = hex2rgb(col)
            warm = r > b + 0.12          # gold / amber labels stay gold, just darker
            return mm.group(1) + (GOLD_TEXT if warm else DARK_TEXT)
        body = re.sub(r'((?<![-\w])color\s*:\s*)(#[0-9a-fA-F]{3,6})', fg, body)
        return sel + '{' + body + '}'
    css = re.sub(r'([^{}]+)\{([^{}]*)\}', rule, css)
    css += """
/* --- Added for older Kindles and small e-ink screens --- */
table { font-size: 0.82em; }
th { border-bottom: 2px solid #1B2A4A; }
td, th { overflow-wrap: break-word; word-wrap: break-word; }
.rowcards { margin: 0.4em 0 1em 0; }
.rowcard { border-left: 3px solid #C9A24D; padding: 0.25em 0 0.25em 0.8em; margin: 0 0 0.8em 0; }
.rowcard p { margin: 0 0 0.2em 0; text-indent: 0; }
.rc-title { font-weight: bold; color: #1B2A4A; }
.rc-k { font-weight: bold; color: #1B2A4A; }
"""
    return css

def cell_html(c):
    c = c.strip()
    c = re.sub(r'^<p[^>]*>(.*)</p>$', r'\1', c, flags=re.S)
    c = re.sub(r'</p>\s*<p[^>]*>', '<br/>', c)
    return c.strip()

def stack_table(m):
    tb = m.group(0)
    head = re.search(r'<thead>(.*?)</thead>', tb, re.S)
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
    hdr = [cell_html(h) for h in hdr]
    out = ['<div class="rowcards">']
    for r in body_rows:
        cells = [cell_html(c) for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.S)]
        cells += [''] * (ncol - len(cells))
        title = cells[0] or '__________'
        out.append('<div class="rowcard">')
        out.append(f'<p class="rc-title"><span class="rc-k">{hdr[0]}:</span> {title}</p>'
                   if not cells[0] or re.fullmatch(r'#|\d+', re.sub(r'<[^>]+>', '', hdr[0]).strip()) else
                   f'<p class="rc-title">{title}</p>')
        for h, c in zip(hdr[1:], cells[1:]):
            label = re.sub(r'<[^>]+>', '', h).strip()
            sep = '' if label.endswith(('…', ':', '?')) else ':'
            out.append(f'<p><span class="rc-k">{h}{sep}</span> {c or "__________"}</p>')
        out.append('</div>')
    out.append('</div>')
    return '\n'.join(out)

def main(src, dst):
    zin = zipfile.ZipFile(src)
    stacked = 0
    with zipfile.ZipFile(dst, 'w') as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename.endswith('.css'):
                data = fix_css(data.decode('utf-8')).encode('utf-8')
            elif info.filename.endswith(('.xhtml', '.html')):
                t = data.decode('utf-8')
                n0 = t.count('<table')
                t = re.sub(r'<table\b.*?</table>', stack_table, t, flags=re.S)
                stacked += n0 - t.count('<table')
                data = t.encode('utf-8')
            zout.writestr(info, data, compress_type=zipfile.ZIP_STORED if info.filename == 'mimetype' else zipfile.ZIP_DEFLATED)
    print(f'{dst}: {stacked} wide tables stacked')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
