#!/usr/bin/env python3
"""Generate one page per book (e.g. wise-up/index.html) from the BOOKS list in index.html.
Run from the repository root:  python3 tools/build_book_pages.py"""
import re, html, os, hashlib

SITE = "https://senseicoach.github.io/ebooks"
src = open("index.html", encoding="utf-8").read()
block = re.search(r"const BOOKS = \[(.*?)\n\];", src, re.S).group(1)
books = []
for m in re.finditer(r"\{(.*?)\}", block, re.S):
    body = m.group(1)
    get = lambda k: re.search(rf'{k}:"((?:[^"\\]|\\.)*)"', body).group(1)
    books.append(dict(id=get("id"), title=get("title"), lang=get("lang"), desc=get("desc"),
                      kb=int(re.search(r"kb:(\d+)", body).group(1))))

# Cache-busting version: a short hash of all cover images.
h = hashlib.sha1()
for f in sorted(os.listdir("covers")): h.update(open(os.path.join("covers", f), "rb").read())
V = h.hexdigest()[:8]
src = re.sub(r'const V = "[^"]*";', f'const V = "{V}";', src)
open("index.html", "w", encoding="utf-8").write(src)

LABEL = {"en": "English", "pt": "Português"}
HELP = {
 "en": ("How to open your book", [
   ("iPhone or iPad", "Tap <em>Download</em>, then tap <em>Open in Books</em>. If you don't see that, tap the Share button and choose <em>Books</em>."),
   ("Mac", "Download the file, then double-click it in your Downloads folder. It opens in Apple Books."),
   ("Android or Windows", "Install a free EPUB reader such as Google Play Books (Android) or Thorium Reader (Windows), then open the downloaded file with it."),
   ("Kindle", "Go to amazon.com/sendtokindle, sign in and upload the .epub file. It appears on your Kindle in a few minutes.")],
   "Download the ebook", "More books by Ron Taylor"),
 "pt": ("Como abrir o seu livro", [
   ("iPhone ou iPad", "Toque em <em>Baixar</em> e depois em <em>Abrir no Livros</em>. Se não aparecer, toque no botão Compartilhar e escolha <em>Livros</em>."),
   ("Mac", "Baixe o arquivo e clique duas vezes nele na pasta Downloads. Ele abre no Apple Books."),
   ("Android ou Windows", "Instale um leitor de EPUB gratuito, como o Google Play Livros (Android) ou o Thorium Reader (Windows), e abra o arquivo baixado."),
   ("Kindle", "Acesse amazon.com/sendtokindle, entre na sua conta e envie o arquivo .epub. Ele aparece no seu Kindle em poucos minutos.")],
   "Baixar o ebook", "Mais livros de Ron Taylor"),
}

TPL = """<!doctype html>
<html lang="{htmllang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · executiveclass.ca</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="book">
<meta property="og:site_name" content="executiveclass.ca">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{site}/covers/{coverfile}">
<meta property="og:url" content="{site}/{id}/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--bg:#f6f3ec;--paper:#fffdf8;--ink:#16202e;--muted:#5d6675;--line:#e3ddcf;--navy:#14213a;--gold:#c9a24a;--gold-ink:#8a6a1f;--gold-title:#a8822c;--focus:#2b5bd7}}
@media (prefers-color-scheme: dark){{:root{{--bg:#0f1520;--paper:#161e2c;--ink:#ece7dc;--muted:#a3abb8;--line:#273145;--navy:#0b111b;--gold:#d8b45e;--gold-ink:#e3c477;--gold-title:#d8b45e;--focus:#7aa2ff}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 Inter,system-ui,-apple-system,sans-serif;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:960px;margin:0 auto;padding:0 20px}}
header{{border-bottom:1px solid var(--line)}}
header .wrap{{display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:4px 16px;padding:22px 20px 18px}}
header a{{color:var(--gold-title);text-decoration:none;font-family:Fraunces,Georgia,serif;font-weight:600;font-size:26px}}header a:hover{{text-decoration:underline}}
header span{{color:var(--gold-ink);font-size:14px;font-weight:500}}
.book{{display:grid;grid-template-columns:minmax(0,320px) 1fr;gap:48px;align-items:start;padding:56px 0 40px}}
.cover{{width:100%;aspect-ratio:2/3;border-radius:8px;overflow:hidden;box-shadow:0 2px 0 rgba(0,0,0,.05),0 24px 48px -20px rgba(0,0,0,.55)}}
.cover img{{width:100%;height:100%;object-fit:cover;display:block}}
.lang{{font-size:12px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--gold-ink)}}
h1{{font-family:Fraunces,Georgia,serif;font-weight:600;font-size:clamp(30px,5vw,46px);line-height:1.08;margin:10px 0 6px;letter-spacing:-.01em}}
.by{{color:var(--muted);margin:0 0 22px}}
.desc{{font-size:18px;margin:0 0 30px;max-width:52ch}}
.btn{{display:inline-flex;align-items:center;gap:10px;text-decoration:none;border-radius:10px;padding:14px 26px;font:600 16px Inter,sans-serif;background:var(--navy);color:#f3eee3}}
@media (prefers-color-scheme: dark){{.btn{{background:var(--gold);color:#14213a}}}}
.btn:focus-visible{{outline:2px solid var(--focus);outline-offset:3px}}
.meta{{display:block;margin-top:10px;color:var(--muted);font-size:13px}}
section{{border-top:1px solid var(--line);padding:36px 0 40px}}
h2{{font-family:Fraunces,Georgia,serif;font-size:24px;margin:0 0 16px}}
.steps{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px}}
.step{{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:16px}}
.step b{{display:block;margin-bottom:4px}}
.step p{{margin:0;color:var(--muted);font-size:14px}}
footer{{color:var(--muted);font-size:13px;padding:0 0 40px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}}
footer a{{color:inherit}}

.book.wide{{grid-template-columns:1fr;gap:28px;padding-top:40px}}
.book.wide .cover{{aspect-ratio:16/9;background:#000;max-width:none}}
@media (max-width:640px){{.book{{grid-template-columns:1fr;gap:28px;padding:32px 0 28px}}.cover{{max-width:240px;margin:0 auto}}.btn{{width:100%;justify-content:center}}}}
</style>
</head>
<body>
<header><div class="wrap"><a href="https://executiveclass.ca">executiveclass.ca</a><span>Course materials for professionals investing in their success.</span></div></header>
<main class="wrap">
  <article class="book{wideclass}">
    <div class="cover"><img src="../covers/{coverfile}?v={v}" alt="Cover of {title}"></div>
    <div>
      <span class="lang">{langlabel}</span>
      <h1>{title}</h1>
      <p class="by">Ron Taylor</p>
      <p class="desc">{desc}</p>
      <a class="btn" href="../books/{id}.epub" download>{dl}</a>
      <span class="meta">EPUB · {size}</span>
    </div>
  </article>
  <section>
    <h2>{helptitle}</h2>
    <div class="steps">{steps}</div>
  </section>
  <footer><span>© Ron Taylor · <a href="https://executiveclass.ca">executiveclass.ca</a></span><a href="../">{more}</a></footer>
</main>
</body>
</html>
"""

for b in books:
    ht, steps, dl, more = HELP[b["lang"]]
    e = lambda s: html.escape(s, quote=True)
    size = f'{b["kb"]/1024:.1f} MB' if b["kb"] >= 1000 else f'{b["kb"]} KB'
    wide = os.path.exists(f"covers/{b['id']}-wide.jpg")
    page = TPL.format(v=V, site=SITE, id=b["id"], wideclass=" wide" if wide else "",
        coverfile=f"{b['id']}-wide.jpg" if wide else f"{b['id']}.jpg", title=e(b["title"]), desc=e(b["desc"]),
        htmllang="pt-BR" if b["lang"] == "pt" else "en", langlabel=LABEL[b["lang"]],
        dl=dl, size=size, helptitle=ht, more=more,
        steps="".join(f'<div class="step"><b>{t}</b><p>{p}</p></div>' for t, p in steps))
    os.makedirs(b["id"], exist_ok=True)
    open(os.path.join(b["id"], "index.html"), "w", encoding="utf-8").write(page)
    print("built", b["id"] + "/")
