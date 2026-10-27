#!/usr/bin/env python3
"""Exporta el sitio WordPress ya renderizado (español e inglés) a una carpeta estática, para revisión pública.

Uso: python3 exportar_estatico.py <url-del-wordpress> <carpeta-del-tema> <salida>
  ej.: python3 exportar_estatico.py http://localhost:8095 tema/greencarbon /tmp/sitio

Deja <salida>/index.html (ES), <salida>/en/index.html (EN), el tema y los archivos de WordPress que la página
pide (CSS/JS del núcleo y fotos subidas). Las rutas quedan relativas, así funciona en cualquier subcarpeta
(por ejemplo GitHub Pages). No incluye el panel: para editar hace falta el WordPress real.
"""
import re
import shutil
import sys
import urllib.request
from pathlib import Path

BASE, TEMA, OUT = sys.argv[1].rstrip('/'), Path(sys.argv[2]), Path(sys.argv[3])
ESC = BASE.replace('/', '\\/')


def bajar(url):
    with urllib.request.urlopen(url) as r:
        return r.read()


def relativizar(html, raiz):
    # Primero los enlaces de idioma, después cualquier otra URL del sitio (también las escapadas en JSON).
    for viejo, nuevo in ((BASE + '/?lang=en', raiz + 'en/'), (BASE + '/"', (raiz or './') + '"'),
                         (BASE + "/'", (raiz or './') + "'"), (BASE + '/', raiz), (ESC + '\\/', raiz.replace('/', '\\/'))):
        html = html.replace(viejo, nuevo)
    return html


if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
pedidos = set()
for lang, archivo, raiz in (('es', OUT / 'index.html', ''), ('en', OUT / 'en' / 'index.html', '../')):
    html = bajar(BASE + ('/?lang=en' if lang == 'en' else '/')).decode('utf-8')
    assert f'<html lang="{lang}"' in html, f'la página {lang} no salió en {lang}'
    # Recursos del propio sitio fuera del tema (CSS/JS de wp-includes, fotos subidas).
    pedidos |= {m.split('?')[0] for m in re.findall(re.escape(BASE) + r'/(wp-(?:includes|content/uploads)/[^"\'\s)>]+)', html.replace('\\/', '/'))}
    html = re.sub(r'<link rel=["\'](?:https://api\.w\.org/|EditURI|alternate" title="JSON)[^>]*>\n?', '', html)
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(relativizar(html, raiz), encoding='utf-8')

shutil.copytree(TEMA, OUT / 'wp-content/themes' / TEMA.name)
for ruta in sorted(pedidos):
    destino = OUT / ruta
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(bajar(f'{BASE}/{ruta}'))
(OUT / '.nojekyll').write_text('')  # GitHub Pages: servir tal cual, sin Jekyll

for f in (OUT / 'index.html', OUT / 'en' / 'index.html'):
    assert BASE not in f.read_text(encoding='utf-8'), f'quedaron URLs absolutas en {f}'
print(f'Exportado en {OUT}: 2 páginas, {len(pedidos)} recursos de WordPress.')
