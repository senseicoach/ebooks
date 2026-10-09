#!/usr/bin/env python3
"""Stop readers (Apple Books in a window, etc.) from adding near-blank pages.
Appends one commented block to each stylesheet; nothing else is changed.
  1. Nothing after the last line of a document has space beneath it
     (bottom margins -> 0; bottom padding -> 0, except boxes that paint a
     background or border keep a hairline so the tint isn't flush with text).
  2. Large percentage top margins (which follow page WIDTH, so a wide, short
     window pushes the content off the bottom) are capped at 30vh; readers that
     don't understand min() keep the original value.
Usage: python3 tools/blankpage_fix.py in.epub out.epub
"""
import re, sys, zipfile

MARK = '/* --- Added to prevent blank pages in windowed readers --- */'

def block_for(css):
    clean = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    painted, caps = set(), []
    for sel, body in re.findall(r'([^{}]+)\{([^{}]*)\}', clean):
        sels = [s.strip() for s in sel.split(',')]
        if re.search(r'background(-color)?\s*:\s*(?!none|transparent)[^;]+|border(-bottom|-left)?\s*:\s*(?!0|none)[^;]*\d', body):
            for s in sels:
                if re.fullmatch(r'[\w-]*\.[\w-]+', s): painted.add(s)
        m = re.search(r'margin-top\s*:\s*(\d+(?:\.\d+)?)%', body) or re.search(r'(?<![-\w])margin\s*:\s*(\d+(?:\.\d+)?)%', body)
        if m and float(m.group(1)) >= 15 and all(not s.startswith('@') for s in sels):
            caps.append((sel.strip(), m.group(1)))
    chain = ['body > :last-child'] + ['body > :last-child' + ' > :last-child' * i for i in range(1, 7)]
    out = ['', MARK,
           ',\n'.join(chain) + ' { margin-bottom: 0 !important; padding-bottom: 0 !important; }']
    if painted:
        pc = sorted(painted)
        out.append(',\n'.join(f'body > {p}:last-child, body > :last-child > {p}:last-child' for p in pc)
                   + ' { padding-bottom: 0.15em !important; }')
    for sel, pct in caps:
        out.append(f'{sel} {{ margin-top: {pct}%; margin-top: min({pct}%, 30vh); }}')
    return '\n'.join(out) + '\n'

def main(src, dst):
    z = zipfile.ZipFile(src)
    with zipfile.ZipFile(dst, 'w') as o:
        for i in z.infolist():
            d = z.read(i.filename)
            if i.filename.endswith('.css'):
                t = d.decode('utf-8')
                if MARK not in t: t += block_for(t)
                d = t.encode('utf-8')
            o.writestr(i, d, compress_type=zipfile.ZIP_STORED if i.filename == 'mimetype' else zipfile.ZIP_DEFLATED)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
