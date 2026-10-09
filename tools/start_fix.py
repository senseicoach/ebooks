#!/usr/bin/env python3
"""Make an EPUB open on its first page, with that page centred in two-page view.
Changes only the package file (.opf) and the navigation landmarks; page content is untouched.
  - removes "start reading here" markers (landmark bodymatter / guide text) that skip the first page
  - puts the cover page first in reading order if it exists but was left out
  - marks the first page rendition:page-spread-center (reflowable books only)
Usage: python3 tools/start_fix.py in.epub out.epub
"""
import re, sys, zipfile, posixpath

def main(src, dst):
    z = zipfile.ZipFile(src)
    opf_path = re.search(r'full-path="([^"]+)"', z.read('META-INF/container.xml').decode()).group(1)
    base = posixpath.dirname(opf_path)
    opf = z.read(opf_path).decode('utf-8')
    notes = []
    fixed_layout = re.search(r'rendition:layout"\s*>\s*pre-paginated', opf) is not None

    items = {}
    for m in re.finditer(r'<item\b[^>]*>', opf):
        t = m.group(0)
        i, h = re.search(r'\bid="([^"]+)"', t), re.search(r'\bhref="([^"]+)"', t)
        if i and h: items[i.group(1)] = h.group(1)
    spine_ids = re.findall(r'<itemref\b[^>]*\bidref="([^"]+)"', opf)

    # 1. cover page present in the manifest but missing from the reading order
    cover_id = next((i for i, h in items.items() if posixpath.basename(h) == 'cover.xhtml'), None)
    if cover_id and cover_id not in spine_ids:
        opf = re.sub(r'(<spine\b[^>]*>)', r'\1\n    <itemref idref="%s"/>' % cover_id, opf, count=1)
        spine_ids.insert(0, cover_id); notes.append('cover added as first page')
    first_href = items[spine_ids[0]]

    # 2. remove guide "text" references that skip the first page
    def guide(m):
        if re.search(r'type="text"', m.group(0)) and first_href not in m.group(0):
            notes.append('guide start marker removed'); return ''
        return m.group(0)
    opf = re.sub(r'\s*<reference\b[^>]*/>', guide, opf)

    # 3. centre the first page in two-page view (reflowable books)
    if not fixed_layout:
        def first_itemref(m):
            t = m.group(0)
            if 'page-spread-center' in t: return t
            if 'properties="' in t: return t.replace('properties="', 'properties="rendition:page-spread-center ', 1)
            return t.replace('<itemref', '<itemref properties="rendition:page-spread-center"', 1)
        new = re.sub(r'<itemref\b[^>]*>', first_itemref, opf, count=1)
        if new != opf: notes.append('first page centred')
        opf = new
        if 'xmlns:rendition' not in opf and 'prefix=' not in re.search(r'<package\b[^>]*>', opf).group(0):
            pass  # "rendition:" is a reserved prefix in EPUB 3; no declaration needed

    with zipfile.ZipFile(dst, 'w') as out:
        for info in z.infolist():
            data = z.read(info.filename)
            if info.filename == opf_path:
                data = opf.encode('utf-8')
            elif info.filename.endswith(('.xhtml', '.html')) and b'landmarks' in data:
                t = data.decode('utf-8')
                def lm(nav):
                    def li(m):
                        if 'bodymatter' in m.group(0) and posixpath.basename(first_href) not in m.group(0):
                            notes.append('landmark start marker removed'); return ''
                        return m.group(0)
                    return re.sub(r'\s*<li\b[^>]*>\s*<a\b[^>]*>.*?</a>\s*</li>', li, nav.group(0), flags=re.S)
                t = re.sub(r'<nav\b[^>]*landmarks.*?</nav>', lm, t, flags=re.S)
                data = t.encode('utf-8')
            out.writestr(info, data, compress_type=zipfile.ZIP_STORED if info.filename == 'mimetype' else zipfile.ZIP_DEFLATED)
    print(f'{dst.split("/")[-1]}: {", ".join(notes) or "already fine"}')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
