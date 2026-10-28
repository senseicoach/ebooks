#!/usr/bin/env python3
"""Generate one page per book (e.g. wise-up/index.html) from the BOOKS list in index.html.
Run from the repository root:  python3 tools/build_book_pages.py"""
import re, html, os, hashlib

SITE = "https://executiveclass.ca/ebooks"
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

# Every page shows Portuguese by default, with a PT | EN switch (the choice is shared with the library page).
LABEL = {"pt": {"en": "Livro em inglês", "pt": "Livro em português"}, "en": {"en": "Book in English", "pt": "Book in Portuguese"}}
TAGLINE = {"pt": "Invista no seu sucesso", "en": "Invest in your success"}
HELP = {
 "en": ("Need help opening the book?", [
   ("iPhone or iPad", "Tap <em>Download</em>, then tap <em>Open in Books</em>. If you don't see that, tap the Share button and choose <em>Books</em>."),
   ("Mac", "Download the file, then double-click it in your Downloads folder. It opens in Apple Books."),
   ("Android or Windows", "Install a free EPUB reader such as Google Play Books (Android) or Thorium Reader (Windows), then open the downloaded file with it."),
   ("Kindle", "Go to amazon.com/sendtokindle, sign in and upload the .epub file. It appears on your Kindle in a few minutes.")],
   "Download the ebook", "More free resources"),
 "pt": ("Precisa de ajuda para abrir o livro?", [
   ("iPhone ou iPad", "Toque em <em>Baixar</em> e depois em <em>Abrir no Livros</em>. Se não aparecer, toque no botão Compartilhar e escolha <em>Livros</em>."),
   ("Mac", "Baixe o arquivo e clique duas vezes nele na pasta Downloads. Ele abre no Apple Books."),
   ("Android ou Windows", "Instale um leitor de EPUB gratuito, como o Google Play Livros (Android) ou o Thorium Reader (Windows), e abra o arquivo baixado."),
   ("Kindle", "Acesse amazon.com/sendtokindle, entre na sua conta e envie o arquivo .epub. Ele aparece no seu Kindle em poucos minutos.")],
   "Baixar o ebook", "Mais recursos gratuitos"),
}

# Call to action shown under the download button.
# OPENING is the first sentence, written for each book. CTA_REST is shared by every book in that language.
CTA_URL = "https://executiveclass.ca/#cursos"
CTA_REST = {
 "en": ("If you want to take your English further, explore Executive Class, Ron Taylor's private English consulting practice for Brazilian professionals.",
        "Explore Executive Class →"),
 "pt": ("Se você quer levar o seu inglês mais longe, conheça a Executive Class, a consultoria privada de inglês de Ron Taylor para profissionais brasileiros.",
        "Conheça a Executive Class →"),
}
# The OPENING sentence in the other language (shown when the reader switches PT/EN).
OPENING_ALT = {
 "evolving": "Você é mais do que o rótulo com que chegou. Descubra quem você pode se tornar e surfe a onda da mudança com confiança.",
 "the-brazilian-edge": "Você já conquistou muita coisa. Agora, aprenda a reconhecer os pontos fortes, a experiência e a perspectiva que você traz para o Canadá, e a comunicá-los com confiança.",
 "the-first-90-days": "Os seus três primeiros meses definem o tom da sua carreira no Canadá. Aprenda as regras não escritas e use-as com confiança.",
 "the-canadian-networking-code": "Your experience already has value. Now, learn to turn it into opportunities in Canada—and to talk about it with confidence.",
 "the-brazucan-pathway": "Building a new life takes courage, and you have already taken the first step. Now, move forward with clarity and confidence.",
 "comece-com-tudo": "You are already preparing for a big step. Now, arrive at university ready to take part with confidence in English.",
 "52-hours-to-a-winning-interview": "Toda entrevista é uma chance de mostrar quem você é. Aprenda a contar a sua história com clareza e a dar respostas que as pessoas lembram.",
 "why-you-the-art-of-the-interview": "Toda entrevista faz a mesma pergunta: por que você? Aprenda a conhecer o seu valor, a comprová-lo e a comunicá-lo com confiança.",
 "blue-ocean": "As melhores estratégias não lutam contra a concorrência: elas a tornam irrelevante. Aprenda a pensar assim e a discutir essas ideias com confiança em inglês.",
 "remarkable-canadians": "As pessoas destas páginas ajudaram a construir o país que agora é a sua casa. Conheça as histórias delas e fale sobre o Canadá com confiança.",
 "first-principles": "Grandes ideias nascem quando alguém questiona o que todos os outros aceitam. Aprenda a pensar diferente e a expressar o seu raciocínio com confiança.",
 "wise-up": "Todo grande fracasso traz uma lição para quem está disposto a aprendê-la. Aprenda com as decisões mais difíceis da história e discuta-as com confiança.",
 "natures-business-model": "A natureza resolve problemas difíceis há milhões de anos. Aprenda os princípios dela e leve-os para o seu trabalho com confiança.",
 "the-intimacies-of-ritual": "Toda cultura responde às mesmas perguntas humanas do seu próprio jeito. Aprenda a ver o mundo por meio de outros costumes e a falar sobre eles com confiança.",
 "crisis-management": "Toda crise é também um ponto de virada. Aprenda como pessoas e organizações transformaram colapso em avanço, e discuta isso com confiança.",
 "shadows-in-the-cave": "Os grandes pensadores nos deixaram ferramentas para enxergar com clareza. Aprenda a usá-las no seu trabalho e a explicar o seu raciocínio com confiança.",
 "humanities-business-school": "A filosofia e a literatura ainda têm muito a ensinar a uma carreira. Aprenda essas lições e leve-as para o seu trabalho com confiança.",
 "masterclass": "Um inglês forte se constrói uma palavra, um som e um exercício de cada vez. Continue construindo e fale com confiança.",
}
# Book descriptions in the other language come from the DESC table in index.html.
DESC_ALT = {}
_dm = re.search(r"const DESC = \{(.*?)\n\};", src, re.S)
if _dm:
    for _lang, _body in re.findall(r'(pt|en): \{(.*?)\n  \}', _dm.group(1), re.S):
        for _id, _t in re.findall(r'"([^"]+)": "((?:[^"\\]|\\.)*)"', _body):
            DESC_ALT[(_id, _lang)] = _t

OPENING = {
 "evolving": "You are more than the label you arrived with. Discover who you could become—and ride the wave of change with confidence.",
 "the-brazilian-edge": "You have already achieved a great deal. Now, learn to recognize the strengths, experience and perspective you bring to Canada—and communicate them with confidence.",
 "the-first-90-days": "Your first three months set the tone for your career in Canada. Learn the unwritten rules—and use them with confidence.",
 "the-canadian-networking-code": "A sua experiência já tem valor. Agora, aprenda a transformá-la em oportunidades no Canadá—e a falar sobre ela com confiança.",
 "the-brazucan-pathway": "Construir uma nova vida exige coragem, e você já deu o primeiro passo. Agora, siga em frente com clareza e confiança.",
 "comece-com-tudo": "Você já está se preparando para um grande passo. Agora, chegue à universidade pronto para participar com confiança em inglês.",
 "52-hours-to-a-winning-interview": "Every interview is a chance to show who you are. Learn to tell your story clearly—and give answers people remember.",
 "why-you-the-art-of-the-interview": "Every interview asks the same question: why you? Learn to know your value, prove it, and communicate it with confidence.",
 "blue-ocean": "The best strategies don't fight the competition—they make it irrelevant. Learn to think this way, and to discuss these ideas with confidence in English.",
 "remarkable-canadians": "The people in these pages helped shape the country you now call home. Learn their stories, and talk about Canada with confidence.",
 "first-principles": "Great ideas begin when someone questions what everyone else accepts. Learn to think differently—and express your thinking with confidence.",
 "wise-up": "Every great failure carries a lesson for those willing to learn it. Learn from history's hardest decisions, and discuss them with confidence.",
 "natures-business-model": "Nature has been solving hard problems for millions of years. Learn its principles, and bring them into your work with confidence.",
 "the-intimacies-of-ritual": "Every culture answers the same human questions in its own way. Learn to see the world through other customs, and talk about them with confidence.",
 "crisis-management": "Every crisis is also a turning point. Learn how people and organizations turned breakdown into breakthrough—and discuss it with confidence.",
 "shadows-in-the-cave": "The great thinkers left us tools for seeing clearly. Learn to use them in your work, and to explain your thinking with confidence.",
 "humanities-business-school": "Philosophy and literature still have much to teach a working career. Learn their lessons, and bring them to your work with confidence.",
 "masterclass": "Strong English is built one word, one sound and one exercise at a time. Keep building—and speak with confidence.",
}

# Optional link-preview text (what WhatsApp, LinkedIn etc. show when the page is shared).
# wide_preview: use covers/<id>-wide.jpg only for the preview; the page itself keeps the normal cover.
SOCIAL = {
 "the-brazilian-edge": dict(
   title="The Brazilian Edge · Livro gratuito de Ron Taylor",
   desc="The Brazilian Edge é um material gratuito para profissionais brasileiros que se preparam para construir o seu futuro no Canadá. A Executive Class oferece consultoria privada de inglês para um número limitado de profissionais que querem se comunicar com mais confiança e impacto.",
   locale="pt_BR", alt="The Brazilian Edge, livro gratuito de Ron Taylor", wide_preview=True),
}

TPL = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · executiveclass.ca</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="book">
<meta property="og:site_name" content="executiveclass.ca">
<meta property="og:title" content="{ogtitle}">
<meta property="og:description" content="{ogdesc}">
{ogextra}<meta property="og:image" content="{site}/covers/{ogimage}">
{ogimgextra}<meta property="og:url" content="{site}/{id}/">
<link rel="icon" type="image/png" href="../favicon.png">
<link rel="apple-touch-icon" href="../apple-touch-icon.png">
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
header .wrap{{display:grid;grid-template-columns:minmax(0,320px) 1fr;gap:12px 48px;align-items:center;padding:22px 20px 18px}}header .wrap>a{{justify-self:center;text-align:center}}header .hright{{display:flex;justify-content:flex-end;align-items:center}}header .hright>.tag{{grid-column:2;text-align:center}}header .hright>.lang-toggle{{grid-column:3;justify-self:end}}@media (max-width:640px){{header .wrap{{grid-template-columns:1fr auto;gap:12px}}header .wrap>a{{justify-self:start}}}}
header a{{color:var(--gold-title);text-decoration:none;font-family:Fraunces,Georgia,serif;font-weight:600;font-size:26px}}header a:hover{{text-decoration:underline}}
header span{{color:var(--gold-ink);font-size:12px;font-weight:600;letter-spacing:.22em;text-transform:uppercase}}
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
.cta{{margin:32px 0 0;padding:22px 24px;background:var(--paper);border:1px solid var(--line);border-left:3px solid var(--gold);border-radius:12px;max-width:56ch}}.cta p{{margin:0 0 12px;font-size:16px}}.cta p.lead{{font-family:Fraunces,Georgia,serif;font-size:19px;line-height:1.4}}.cta p.sub{{color:var(--muted);font-size:15px;margin-bottom:16px}}.cta a{{display:inline-flex;align-items:center;text-decoration:none;border-radius:10px;padding:11px 20px;font:600 15px Inter,sans-serif;color:var(--gold-title);border:1px solid var(--gold)}}.cta a:hover{{background:var(--gold);color:#14213a}}.cta a:focus-visible{{outline:2px solid var(--focus);outline-offset:3px}}@media (max-width:640px){{.cta{{padding:18px}}.cta a{{width:100%;justify-content:center}}}}
section.help{{border-top:1px solid var(--line);padding:20px 0 8px}}
section.help summary{{cursor:pointer;color:var(--muted);font-size:15px;padding:8px 0;list-style:none;display:inline-flex;align-items:center;gap:8px}}section.help summary::-webkit-details-marker{{display:none}}section.help summary::before{{content:"+";display:inline-grid;place-items:center;width:20px;height:20px;border:1px solid var(--line);border-radius:50%;font-size:14px;line-height:1}}section.help details[open] summary::before{{content:"−"}}section.help summary:hover{{color:var(--ink)}}section.help summary:focus-visible{{outline:2px solid var(--focus);outline-offset:3px;border-radius:4px}}section.help .steps{{margin:14px 0 16px}}
.steps{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px}}
.step{{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:16px}}
.step b{{display:block;margin-bottom:4px}}
.step p{{margin:0;color:var(--muted);font-size:14px}}
html:not(.en) [data-l="en"],html.en [data-l="pt"]{{display:none !important}}
.lang-toggle{{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;background:var(--paper);align-self:center}}
.lang-toggle button{{border:0;background:none;color:var(--muted);font:600 12px/1 Inter,sans-serif;letter-spacing:.12em;padding:9px 14px;min-width:44px;min-height:36px;cursor:pointer}}
.lang-toggle button[aria-pressed="true"]{{background:var(--ink);color:var(--bg)}}
.lang-toggle button:focus-visible{{outline:2px solid var(--focus);outline-offset:-2px}}
.seal{{text-align:center;padding:56px 0 26px}}.seal a{{display:inline-block;border-radius:50%;box-shadow:0 10px 24px -14px rgba(0,0,0,.6)}}.seal img{{display:block;width:110px;height:110px}}.seal .sitelink{{display:block;margin-top:12px;font-family:Fraunces,Georgia,serif;font-weight:600;font-size:18px;color:var(--gold-title);text-decoration:none;box-shadow:none;border-radius:0}}
footer{{color:var(--muted);font-size:11px;padding:0 0 40px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}}
footer a{{color:inherit}}

.book.wide{{grid-template-columns:1fr;gap:28px;padding-top:40px}}
.book.wide .cover{{aspect-ratio:16/9;background:#000;max-width:none}}
@media (max-width:640px){{.book{{grid-template-columns:1fr;gap:28px;padding:32px 0 28px}}.cover{{max-width:240px;margin:0 auto}}.btn{{width:100%;justify-content:center}}}}
</style>
<script>try{{var q=new URLSearchParams(location.search).get("lang");var l=(q==="en"||q==="pt")?q:localStorage.getItem("lib:lang");if(l==="en"){{document.documentElement.classList.add("en");document.documentElement.lang="en";}}}}catch(e){{}}</script>
</head>
<body>
<header><div class="wrap"><a href="https://executiveclass.ca">executiveclass.ca</a><div class="hright"><div class="lang-toggle" role="group" aria-label="Idioma / Language"><button type="button" data-lang="pt" aria-pressed="true">PT</button><button type="button" data-lang="en" aria-pressed="false">EN</button></div></div></div></header>
<main class="wrap">
  <article class="book{wideclass}">
    <div class="cover"><img src="../covers/{coverfile}?v={v}" alt="Cover of {title}"></div>
    <div>
      <h1>{title}</h1>
      <p class="by">Ron Taylor</p>
      <p class="desc">{descbody}</p>
      <a class="btn" href="../books/{id}.epub" download>{dl}</a>
      <span class="meta">EPUB · {size}</span>
{cta}    </div>
  </article>
  <section class="help"><details>
    <summary>{helptitle}</summary>
    <div class="steps">{steps}</div>
  </details></section>
  <div class="seal"><a href="https://executiveclass.ca" aria-label="Executive Class: executiveclass.ca"><img src="../covers/executiveclass-logo.png?v={v}" alt="Executive Class logo" width="110" height="110"></a><a class="sitelink" href="https://executiveclass.ca">executiveclass.ca</a></div>
  <footer><span>© Ron Taylor</span><a href="../">{more}</a></footer>
</main>
<script>
(function(){{var h=document.documentElement,bs=document.querySelectorAll(".lang-toggle button");
function set(l){{h.classList.toggle("en",l==="en");h.lang=l==="en"?"en":"pt-BR";bs.forEach(function(b){{b.setAttribute("aria-pressed",String(b.dataset.lang===l));}});}}
set(h.classList.contains("en")?"en":"pt");
bs.forEach(function(b){{b.addEventListener("click",function(){{set(b.dataset.lang);try{{localStorage.setItem("lib:lang",b.dataset.lang);}}catch(e){{}}}});}});}})();
</script>
<script data-goatcounter="https://executiveclass.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</body>
</html>
"""

for b in books:
    e = lambda s: html.escape(s, quote=True)
    both = lambda pt, en: f'<span data-l="pt">{pt}</span><span data-l="en">{en}</span>'
    other = "en" if b["lang"] == "pt" else "pt"
    def by_lang(native, alt):   # (pt, en) pair from the book's own text and its translation
        return (native, alt) if b["lang"] == "pt" else (alt, native)
    size = f'{b["kb"]/1024:.1f} MB' if b["kb"] >= 1000 else f'{b["kb"]} KB'
    soc = SOCIAL.get(b["id"], {})
    has_wide = os.path.exists(f"covers/{b['id']}-wide.jpg")
    wide = has_wide and not soc.get("wide_preview")          # wide cover on the page itself
    coverfile = f"{b['id']}-wide.jpg" if wide else f"{b['id']}.jpg"
    ogimage = f"{b['id']}-wide.jpg" if has_wide and soc.get("wide_preview") else coverfile
    ogextra = f'<meta property="og:locale" content="{soc["locale"]}">\n' if soc.get("locale") else ""
    ogimgextra = ""
    if soc.get("wide_preview"):
        ogimgextra = ('<meta property="og:image:type" content="image/jpeg">\n<meta property="og:image:width" content="1200">\n'
                      '<meta property="og:image:height" content="630">\n'
                      + (f'<meta property="og:image:alt" content="{e(soc["alt"])}">\n' if soc.get("alt") else "")
                      + '<meta name="twitter:card" content="summary_large_image">\n')
    cta = ""
    if b["id"] in OPENING:
        op_pt, op_en = by_lang(OPENING[b["id"]], OPENING_ALT.get(b["id"], OPENING[b["id"]]))
        cta = (f'      <aside class="cta">\n        <p class="lead">{both(e(op_pt), e(op_en))}</p>\n'
               f'        <p class="sub">{both(e(CTA_REST["pt"][0]), e(CTA_REST["en"][0]))}</p>\n'
               f'        <a href="{CTA_URL}">{both(CTA_REST["pt"][1], CTA_REST["en"][1])}</a>\n      </aside>\n')
    d_pt, d_en = by_lang(b["desc"], DESC_ALT.get((b["id"], other), b["desc"]))
    stepsof = lambda L: "".join(f'<div class="step"><b>{t}</b><p>{p}</p></div>' for t, p in HELP[L][1])
    page = TPL.format(v=V, site=SITE, id=b["id"], wideclass=" wide" if wide else "",
        coverfile=coverfile, ogimage=ogimage, ogextra=ogextra, ogimgextra=ogimgextra, cta=cta,
        ogtitle=e(soc.get("title", b["title"])), ogdesc=e(soc.get("desc", b["desc"])),
        title=e(b["title"]), desc=e(b["desc"]),
        langlabel=both(LABEL["pt"][b["lang"]], LABEL["en"][b["lang"]]), tagline=both(TAGLINE["pt"], TAGLINE["en"]),
        descbody=both(e(d_pt), e(d_en)),
        dl=both(HELP["pt"][2], HELP["en"][2]), size=size, helptitle=both(HELP["pt"][0], HELP["en"][0]),
        more=both(HELP["pt"][3], HELP["en"][3]),
        steps=f'<div data-l="pt" style="display:contents">{stepsof("pt")}</div><div data-l="en" style="display:contents">{stepsof("en")}</div>')
    os.makedirs(b["id"], exist_ok=True)
    open(os.path.join(b["id"], "index.html"), "w", encoding="utf-8").write(page)
    print("built", b["id"] + "/")
