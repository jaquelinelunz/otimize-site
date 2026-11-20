from pathlib import Path
import html, re, shutil, datetime, xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent
out=root/'dist';out.mkdir(exist_ok=True)
base=(root/'site'/'index.html').read_text(encoding='utf-8')
posts=[]
for p in sorted((root/'content'/'artigos').glob('*.md'),reverse=True):
    raw=p.read_text(encoding='utf-8')
    match=re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$',raw,re.S)
    if not match:continue
    meta={}
    for line in match.group(1).splitlines():
        if ':' in line:
            k,v=line.split(':',1);meta[k.strip()]=v.strip().strip('"\'')
    if meta.get('publicado','false').lower()!='true':continue
    slug=re.sub(r'[^a-z0-9-]','',p.stem.lower())
    title=meta.get('titulo',slug);desc=meta.get('resumo','');date=meta.get('data','')
    body=[];paragraph=[]
    def flush():
        if paragraph:body.append('<p>'+html.escape(' '.join(paragraph))+'</p>');paragraph.clear()
    for line in match.group(2).splitlines():
        s=line.strip()
        if not s:flush();continue
        if s.startswith('## '):flush();body.append('<h2>'+html.escape(s[3:])+'</h2>')
        elif s.startswith('# '):flush();body.append('<h2>'+html.escape(s[2:])+'</h2>')
        elif s.startswith('- '):flush();body.append('<p>• '+html.escape(s[2:])+'</p>')
        else:paragraph.append(s)
    flush()
    target=out/'artigos'/slug;target.mkdir(parents=True,exist_ok=True)
    page='''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} | Otimize</title><meta name="description" content="{desc}"><link rel="canonical" href="https://otimizesuasaude.com.br/artigos/{slug}/"><style>body{{font:17px/1.75 system-ui,sans-serif;color:#29243a;margin:0}}header{{background:#573d88;padding:18px 7%;color:white}}header a{{color:white}}main{{max-width:780px;margin:55px auto;padding:0 24px}}h1,h2{{line-height:1.25}}h1{{color:#573d88}}footer{{background:#f3eff9;padding:24px;text-align:center}}.meta{{color:#666}}a{{color:#573d88}}</style></head><body><header><a href="/">← Otimize — Medicina e Cuidados de Saúde</a></header><main><p class="meta">{date} · Conteúdo educativo</p><h1>{title}</h1><p>{desc}</p>{body}<p><small>Informações educativas. Não substituem avaliação individualizada por profissional de saúde.</small></p></main><footer><a href="/">Voltar ao site da Otimize</a></footer></body></html>'''.format(title=html.escape(title),desc=html.escape(desc,quote=True),slug=slug,date=html.escape(date),body='\n'.join(body))
    (target/'index.html').write_text(page,encoding='utf-8')
    posts.append((slug,title,desc,date))
if posts:
    cards=''.join(f'<article style="padding:18px;border:1px solid #ddd;border-radius:14px"><small>{html.escape(d)}</small><h3><a href="/artigos/{s}/">{html.escape(t)}</a></h3><p>{html.escape(x)}</p></article>' for s,t,x,d in posts)
    section=f'<section id="artigos" style="max-width:1100px;margin:45px auto;padding:24px"><h2>Artigos e orientações de saúde</h2><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px">{cards}</div></section>'
    base=base.replace('</body>',section+'</body>')
(out/'index.html').write_text(base,encoding='utf-8')
shutil.copytree(root/'admin',out/'admin',dirs_exist_ok=True)
if (root/'static').exists():shutil.copytree(root/'static',out/'static',dirs_exist_ok=True)
(out/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: https://otimizesuasaude.com.br/sitemap.xml\n',encoding='utf-8')
urls=['https://otimizesuasaude.com.br/']+[f'https://otimizesuasaude.com.br/artigos/{s}/' for s,*_ in posts]
(out/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'<url><loc>{u}</loc></url>\n' for u in urls)+'</urlset>\n',encoding='utf-8')
print(f'Site preparado: {len(posts)} artigos publicados; saída: dist/')
