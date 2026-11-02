#!/usr/bin/env python3
"""Convert an EPUB (reflowable, XHTML spine) to a print-style PDF using WeasyPrint.

usage: epub_to_pdf.py book.epub out.pdf [workdir]
"""
import os, sys, re, zipfile, tempfile, posixpath, shutil
from urllib.parse import unquote, urlparse
from lxml import etree, html as lhtml
import weasyprint
from weasyprint import HTML, CSS

NS = {"c": "urn:oasis:names:tc:opendocument:xmlns:container",
      "o": "http://www.idpf.org/2007/opf",
      "dc": "http://purl.org/dc/elements/1.1/",
      "x": "http://www.w3.org/1999/xhtml"}
XLINK = "http://www.w3.org/1999/xlink"

PRINT_CSS = """
@page { size: 6in 9in; margin: 0.8in 0.75in 0.85in 0.75in;
  @bottom-center { content: counter(page); font-family: "EB Garamond", Georgia, serif;
                   font-size: 9pt; color: #7A776E; } }
@page cover { margin: 0; @bottom-center { content: none; } }
@page front { @bottom-center { content: none; } }
html { font-size: 11pt; }
html, body { height: auto !important; min-height: 0 !important; }
body { margin: 0 !important; padding: 0 !important; background: none !important;
       font-size: 11pt; line-height: 1.5; }
.spine-doc { break-before: page; }
.spine-doc.first { break-before: auto; }
.spine-doc.is-cover { page: cover; width: 6in; height: 9in; break-after: page; overflow: hidden; }
.spine-doc.is-cover img, .spine-doc.is-cover svg { display:block; width: 6in; height: 9in; }
img { max-width: 100%; }
a { color: inherit; }
"""


def local(tag):
    return tag.split('}')[-1] if isinstance(tag, str) else ''


def main(epub, out, work=None):
    work = work or tempfile.mkdtemp(prefix="e2p-")
    root = os.path.join(work, "x")
    shutil.rmtree(root, ignore_errors=True)
    with zipfile.ZipFile(epub) as z:
        z.extractall(root)
    cont = etree.parse(os.path.join(root, "META-INF/container.xml"))
    opf_rel = cont.find(".//c:rootfile", NS).get("full-path")
    opf_path = os.path.join(root, opf_rel)
    opf_dir = os.path.dirname(opf_path)
    opf = etree.parse(opf_path)
    title = (opf.findtext(".//dc:title", namespaces=NS) or "").strip()
    author = (opf.findtext(".//dc:creator", namespaces=NS) or "").strip()
    lang = (opf.findtext(".//dc:language", namespaces=NS) or "en").strip()
    manifest = {i.get("id"): i for i in opf.findall(".//o:manifest/o:item", NS)}
    spine = [manifest[r.get("idref")] for r in opf.findall(".//o:spine/o:itemref", NS)
             if r.get("idref") in manifest]
    # cover image href from metadata, if present
    cover_img = None
    cm = opf.find(".//o:meta[@name='cover']", NS)
    if cm is not None and cm.get("content") in manifest:
        cover_img = manifest[cm.get("content")].get("href")
    for it in manifest.values():
        if "cover-image" in (it.get("properties") or ""):
            cover_img = it.get("href")

    doc_ids = {}
    for n, it in enumerate(spine):
        doc_ids[posixpath.normpath(it.get("href"))] = f"sd{n}"

    css_links = []
    parts = []
    for n, it in enumerate(spine):
        href = it.get("href")
        if it.get("media-type") != "application/xhtml+xml":
            continue
        p = os.path.join(opf_dir, unquote(href))
        tree = etree.parse(p, etree.XMLParser(resolve_entities=False, recover=True))
        r = tree.getroot()
        head = r.find("{*}head")
        body = r.find("{*}body")
        if body is None:
            continue
        ddir = posixpath.dirname(href)
        # stylesheets, rebased to the opf dir
        if head is not None:
            for l in head.iter("{*}link"):
                if "stylesheet" in (l.get("rel") or ""):
                    h = posixpath.normpath(posixpath.join(ddir, l.get("href")))
                    if h not in css_links:
                        css_links.append(h)
        is_cover = ("cover" in (it.get("id") or "").lower() and n == 0) or \
                   (body.get("id") == "cover") or ("coverbody" in (body.get("class") or "")) or \
                   (body.get("{http://www.idpf.org/2007/ops}type") == "cover")
        # rebase urls
        for el in body.iter():
            if not isinstance(el.tag, str):
                continue
            for att in ("src", "href", "{%s}href" % XLINK):
                v = el.get(att)
                if not v:
                    continue
                u = urlparse(v)
                if u.scheme or v.startswith("data:"):
                    continue
                if v.startswith("#"):
                    continue
                path = posixpath.normpath(posixpath.join(ddir, unquote(u.path))) if u.path else ""
                if el.tag.endswith("}a") and path in doc_ids:
                    el.set(att, "#" + doc_ids[path] + ("" if not u.fragment else ""))
                elif path:
                    el.set(att, path + (("#" + u.fragment) if u.fragment else ""))
        # strip any ids that would collide across docs? keep, WeasyPrint tolerates dups
        inner = etree.tostring(body, encoding="unicode", method="xml")
        inner = re.sub(r"^<body[^>]*>", "", inner)
        inner = re.sub(r"</body>$", "", inner)
        # HTML parsers ignore the self-closing slash on non-void tags: expand them
        void = "area|base|br|col|embed|hr|img|input|link|meta|source|track|wbr"
        inner = re.sub(r"<(?!(?:%s)\b)([A-Za-z][\w:-]*)([^<>]*?)\s*/>" % void,
                       r"<\1\2></\1>", inner)
        inner = inner.replace(' xmlns="http://www.w3.org/1999/xhtml"', "")
        cls = "spine-doc" + (" first" if not parts else "") + (" is-cover" if is_cover else "")
        bcls = body.get("class") or ""
        if is_cover:
            # SVG-wrapped cover images don't paginate well; use a plain <img>
            m = re.search(r'(?:xlink:href|href|src)="([^"]+\.(?:jpe?g|png))"', inner)
            img = m.group(1) if m else cover_img
            inner = f'<img src="{img}" alt="Cover"/>' if img else inner
        parts.append(f'<div id="{doc_ids[posixpath.normpath(href)]}" class="{cls} {bcls}">{inner}</div>')

    links = "\n".join(f'<link rel="stylesheet" href="{h}"/>' for h in css_links)
    doc = (f'<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml" lang="{lang}"><head>'
           f'<meta charset="utf-8"/><title>{etree.CDATA(title) if False else title}</title>'
           f'<meta name="author" content="{author}"/>{links}</head><body>\n' + "\n".join(parts) + "</body></html>")
    combined = os.path.join(opf_dir, "_combined.xhtml")
    with open(combined, "w", encoding="utf-8") as f:
        f.write(doc)
    HTML(filename=combined, base_url=combined).write_pdf(
        out, stylesheets=[CSS(string=PRINT_CSS)], pdf_variant=None, optimize_images=True)
    print("OK", os.path.basename(epub), "->", out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
