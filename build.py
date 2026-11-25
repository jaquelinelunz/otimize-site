
from pathlib import Path
import html
import re
import shutil
import xml.etree.ElementTree as ET
from datetime import date, datetime

import yaml
import markdown

root = Path(__file__).resolve().parent
out = root / "dist"
domain = "https://otimizesuasaude.com.br"

if out.exists():
    shutil.rmtree(out)

out.mkdir()
base = (root / "index.html").read_text(encoding="utf-8")
posts = []

def esc(value):
    return html.escape(str(value or ""), quote=True)

def format_date(value):
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")
    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        ).strftime("%d/%m/%Y")
    except ValueError:
        return str(value or "")

# Preservar arquivos e painel administrativo
for folder in ["admin", "static", "assets", "imagens"]:
    source = root / folder
    if source.exists():
        shutil.copytree(source, out / folder, dirs_exist_ok=True)

if (root / "site" / "imagens").exists():
    shutil.copytree(
        root / "site" / "imagens",
        out / "imagens",
        dirs_exist_ok=True
    )

# Identidade visual das paginas do blog
style = """
*{box-sizing:border-box}
body{margin:0;font:17px/1.75 system-ui,sans-serif;
color:#29243a;background:#faf9fc}
header{background:#573D88;padding:22px 7%;color:white}
header a{color:white;text-decoration:none;font-weight:600}
main{max-width:1100px;margin:45px auto;padding:0 24px}
h1,h2,h3{color:#573D88;line-height:1.3}
h1{font-size:clamp(28px,4vw,42px)}
a{color:#573D88}
.meta{color:#626270;font-size:14px}
.category{color:#287d85;font-weight:700;font-size:14px}
.grid{display:grid;gap:24px;
grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.card{background:white;border:1px solid #e5dfed;
border-radius:18px;overflow:hidden}
.card-content{padding:24px}
.card img{width:100%;height:210px;object-fit:cover}
.article{max-width:800px;margin:auto}
.article img{max-width:100%;height:auto;border-radius:14px}
.cover{width:100%;max-height:450px;object-fit:cover}
.button{display:inline-block;background:#573D88;color:white;
padding:12px 22px;border-radius:30px;text-decoration:none}
footer{background:#f0edf6;text-align:center;padding:30px}
"""

def page(title, description, path, content, image=""):
    social_image = ""
    if image:
        image_url = image if image.startswith("https://") else domain + image
        social_image = f'<meta property="og:image" content="{esc(image_url)}">'

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | Otimize</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{domain}{path}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{domain}{path}">
{social_image}
<style>{style}</style>
</head>
<body>
<header>
<a href="/">Otimize — Medicina e Cuidados de Saúde</a>
&nbsp; | &nbsp; <a href="/blog/">Blog</a>
</header>
<main>{content}</main>
<footer>
<strong>Otimize — Medicina e Cuidados de Saúde</strong>
<p>Cachoeiro de Itapemirim — ES</p>
<a href="/">Voltar ao site</a>
</footer>
</body>
</html>"""

# Ler artigos cadastrados pelo painel
for p in sorted((root / "content" / "blog").glob("*.md"), reverse=True):
    raw = p.read_text(encoding="utf-8-sig")
    match = re.match(
        r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n(.*)$",
        raw,
        re.S
    )

    if not match:
        print(f"Artigo sem metadados: {p.name}")
        continue

    meta = yaml.safe_load(match.group(1)) or {}

    if str(meta.get("published", False)).lower() != "true":
        continue

    slug = re.sub(r"[^a-z0-9-]", "", p.stem.lower())
    if not slug:
        continue

    title = meta.get("title", slug)
    description = meta.get("description", "")
    category = meta.get("category", "")
    published_date = format_date(meta.get("date", ""))
    image = str(meta.get("image") or "")

    if image.startswith("site/imagens/"):
        image = "/" + image.removeprefix("site/")
    elif image.startswith("imagens/"):
        image = "/" + image

    if image and not image.startswith(("/imagens/", "https://")):
        image = ""

    body = markdown.markdown(
        match.group(2),
        extensions=["extra", "sane_lists"]
    )

    path = f"/blog/{slug}/"
    cover = (
        f'<img class="cover" src="{esc(image)}" '
        f'alt="{esc(title)}">'
        if image else ""
    )

    content = f"""
    <article class="article">
    <a href="/blog/">Voltar ao blog</a>
    <p class="category">{esc(category)}</p>
    <h1>{esc(title)}</h1>
    <p class="meta">{esc(published_date)}</p>
    {cover}
    <p><strong>{esc(description)}</strong></p>
    {body}
    <hr>
    <p class="meta">Conteúdo educativo. Não substitui
    avaliação individualizada por profissional de saúde.</p>
    <a class="button" href="/#contato">Conheça a Otimize</a>
    </article>
    """

    target = out / "blog" / slug
    target.mkdir(parents=True, exist_ok=True)

    (target / "index.html").write_text(
        page(title, description, path, content, image),
        encoding="utf-8"
    )

    posts.append({
        "title": title,
        "description": description,
        "category": category,
        "date": published_date,
        "image": image,
        "path": path
    })

# Criar pagina principal do blog
cards = []

for post in posts:
    cover = (
        f'<img src="{esc(post["image"])}" '
        f'alt="{esc(post["title"])}" loading="lazy">'
        if post["image"] else ""
    )

    cards.append(f"""
    <article class="card">
    <a href="{post["path"]}">{cover}</a>
    <div class="card-content">
    <p class="category">{esc(post["category"])}</p>
    <p class="meta">{esc(post["date"])}</p>
    <h2><a href="{post["path"]}">{esc(post["title"])}</a></h2>
    <p>{esc(post["description"])}</p>
    <a href="{post["path"]}">Leia mais</a>
    </div>
    </article>
    """)

listing = "".join(cards) or "<p>Em breve, novos conteúdos.</p>"

blog_content = f"""
<p class="category">CIÊNCIA • PREVENÇÃO • SAÚDE</p>
<h1>Blog Otimize</h1>
<p>Informações sobre vacinação, saúde respiratória,
prevenção e qualidade de vida.</p>
<div class="grid">{listing}</div>
"""

blog = out / "blog"
blog.mkdir(exist_ok=True)

(blog / "index.html").write_text(
    page(
        "Blog de saúde e vacinação",
        "Artigos e orientações de saúde da Otimize em Cachoeiro de Itapemirim.",
        "/blog/",
        blog_content
    ),
    encoding="utf-8"
)

# Integrar blog ao menu sem substituir o site original
if not re.search(r'href=["\']/blog/?["\']', base):
    base, count = re.subn(
        r"</nav\s*>",
        '<a href="/blog/">Blog</a></nav>',
        base,
        flags=re.I
    )
    if count == 0:
        base = re.sub(
            r"</body\s*>",
            '<p style="text-align:center"><a href="/blog/">'
            'Conheça o Blog Otimize</a></p></body>',
            base,
            count=1,
            flags=re.I
        )

(out / "index.html").write_text(base, encoding="utf-8")

# Atualizar robots.txt
(out / "robots.txt").write_text(
    "User-agent: *\n"
    "Allow: /\n"
    "Disallow: /admin/\n"
    f"Sitemap: {domain}/sitemap.xml\n",
    encoding="utf-8"
)

# Gerar sitemap com paginas publicadas
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
urlset = ET.Element(ns + "urlset")

urls = [domain + "/", domain + "/blog/"]
urls.extend(domain + post["path"] for post in posts)

for address in urls:
    entry = ET.SubElement(urlset, ns + "url")
    ET.SubElement(entry, ns + "loc").text = address

ET.ElementTree(urlset).write(
    out / "sitemap.xml",
    encoding="utf-8",
    xml_declaration=True
)

print(f"Site preparado: {len(posts)} artigos publicados.")
print("Blog, robots.txt e sitemap.xml gerados.")
