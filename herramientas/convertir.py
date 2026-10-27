#!/usr/bin/env python3
"""Convierte greencarbon-web/index.html en el tema WordPress `greencarbon`.

Cada texto, imagen, enlace externo y aviso (.pend/.ssot) del HTML pasa a ser un campo
del Personalizador con el valor actual como predeterminado: el sitio se ve idéntico
hasta que el administrador cambia algo. Volver a correrlo regenera el tema entero.

Uso: python3 convertir.py <greencarbon-web> <carpeta-del-tema>
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

ORIGEN = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / 'greencarbon-web'
TEMA = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parents[1] / 'tema' / 'greencarbon'

ETIQUETAS = {'h1': 'Título', 'h2': 'Título', 'h3': 'Subtítulo', 'h4': 'Subtítulo', 'em': 'Resaltado',
             'a': 'Botón o enlace', 'button': 'Botón', 'b': 'Destacado', 'li': 'Ítem', 'p': 'Párrafo',
             'label': 'Etiqueta del formulario', 'option': 'Opción del formulario', 'q': 'Cita',
             'figcaption': 'Pie de foto', 'dt': 'Rótulo', 'dd': 'Dato', 'small': 'Texto chico'}
SALTAR_IDS = ('id="loader-txt"', 'id="menu-btn"', 'id="form-estado"')  # textos que reescribe el JS


def corto(t, n=48):
    return t if len(t) <= n else t[:n - 1].rstrip() + '…'


class Campos:
    def __init__(self):
        self.secciones = []          # [{id, titulo, campos: {clave: {...}}}]
        self.cuenta = {}
        self.imagenes = {}           # src -> clave (el logo se usa dos veces)
        self.ocultos = {}            # (seccion, texto) -> clave, para la marquesina duplicada

    def seccion(self, sid, titulo):
        self.secciones.append({'id': sid, 'titulo': titulo, 'campos': {}})

    def nuevo(self, tipo, etiqueta, defecto, desc='', clave=None):
        s = self.secciones[-1]
        if clave is None:
            self.cuenta[s['id']] = self.cuenta.get(s['id'], 0) + 1
            clave = f"{s['id']}_{self.cuenta[s['id']]:02d}"
        s['campos'][clave] = {'tipo': tipo, 'etiqueta': etiqueta, 'defecto': defecto, 'desc': desc}
        return clave


def php(fn, *args):
    return '<?php ' + fn + '(' + ', '.join(json.dumps(a, ensure_ascii=False).replace('$', '\\$') for a in args) + '); ?>'


def convertir_cuerpo(cuerpo, c):
    # Avisos y huecos de foto que el admin reemplaza con el dato real (vacío = se ve el aviso).
    cuerpo = re.sub(r'<div class="bio-foto"><span class="pend">([^<]*)</span></div>',
                    lambda m: f'<div class="bio-foto"><gcbiofoto texto="{m[1]}"></div>', cuerpo)
    cuerpo = re.sub(r'<div class="retrato"><svg class="i"><use href="#i-retrato"/></svg></div>',
                    '<gcretrato>', cuerpo)
    cuerpo = re.sub(r'<span class="(pend|ssot)">([^<]*)</span>',
                    lambda m: f'<gcaviso clase="{m[1]}" texto="{m[2]}">', cuerpo)

    salida, ultimo, svg, oculto = [], 'p', 0, 0
    pila_oculta = []
    c.seccion('cab', 'Cabecera y menú')
    for tok in re.split(r'(<!--.*?-->|<[^>]+>)', cuerpo, flags=re.S):
        if not tok:
            continue
        if tok.startswith('<!--'):
            m = re.match(r'<!-- (\d+) · (.+?) -->', tok)
            if m:
                c.seccion(f's{int(m[1]):02d}', f'{m[1]} · {m[2]}')
            salida.append(tok)
            continue
        if tok.startswith('<'):
            nombre = re.match(r'</?([a-zA-Z0-9]+)', tok)
            nombre = nombre[1].lower() if nombre else ''
            if nombre == 'svg':
                svg += -1 if tok.startswith('</') else (0 if tok.endswith('/>') else 1)
            if nombre == 'footer' and not tok.startswith('</'):
                c.seccion('pie', 'Pie de página')
            if not tok.startswith('</') and 'aria-hidden="true"' in tok and not tok.endswith('/>'):
                oculto += 1; pila_oculta.append(nombre)
            elif tok.startswith('</') and pila_oculta and pila_oculta[-1] == nombre:
                oculto -= 1; pila_oculta.pop()
            salida.append(convertir_tag(tok, nombre, c))
            if not tok.startswith('</') and nombre not in ('br', 'img', 'input', 'use', 'svg', 'path', 'circle', 'rect'):
                ultimo = tok
            continue
        texto = tok.strip()
        if svg or not texto or not re.search(r'\w', texto) or any(i in ultimo for i in SALTAR_IDS):
            salida.append(tok)
            continue
        valor = html.unescape(texto)
        tag = re.match(r'<([a-zA-Z0-9]+)', ultimo)[1].lower()
        if oculto and (c.secciones[-1]['id'], valor) in c.ocultos:
            clave = c.ocultos[(c.secciones[-1]['id'], valor)]
        else:
            tipo = 'parrafo' if len(valor) > 70 else 'texto'
            clave = c.nuevo(tipo, f"{ETIQUETAS.get(tag, 'Texto')}: {corto(valor)}", valor)
            if oculto:
                c.ocultos[(c.secciones[-1]['id'], valor)] = clave
        izq, der = tok[:len(tok) - len(tok.lstrip())], tok[len(tok.rstrip()):]
        salida.append(izq + php('gc_t', clave) + der)
    return ''.join(salida)


def convertir_tag(tok, nombre, c):
    if nombre == 'gcaviso':
        m = re.match(r'<gcaviso clase="(\w+)" texto="([^"]*)">', tok)
        texto = html.unescape(m[2])
        clave = c.nuevo('texto', f'Aviso «{corto(texto, 40)}»', '',
                        'Escribí el dato real para reemplazar el aviso. Vacío = se muestra el aviso.')
        return php('gc_aviso', clave, m[1], texto)
    if nombre == 'gcbiofoto':
        texto = html.unescape(re.match(r'<gcbiofoto texto="([^"]*)">', tok)[1])
        clave = c.nuevo('imagen', 'Foto de la especie', '', 'Vacío = se muestra el aviso «' + texto + '».')
        return php('gc_foto_o_aviso', clave, texto)
    if nombre == 'gcretrato':
        clave = c.nuevo('imagen', 'Retrato', '', 'Vacío = se muestra la silueta.')
        return php('gc_retrato', clave)
    if tok.startswith('</') or nombre in ('svg', 'use', 'path', 'symbol', 'circle', 'rect'):
        return tok

    def attr(m):
        a, v = m[2], html.unescape(m[3])
        if a == 'src' and nombre == 'img':
            clave = c.imagenes.get(v) or c.nuevo('imagen', f'Imagen: {Path(v).name}', v)
            c.imagenes[v] = clave
            return f'{m[1]}src="{php("gc_u", clave)}"'
        if a == 'src' and nombre == 'video':
            return f'{m[1]}src="{php("gc_u", c.nuevo("video", f"Video: {Path(v).name}", v))}"'
        if a == 'srcset':
            src = re.search(r'\ssrc="([^"]*)"', tok)[1]
            return php('gc_srcset', c.imagenes[src], v)  # el src viene antes que srcset en el HTML
        if a == 'alt' and v:
            return f'{m[1]}alt="{php("gc_a", c.nuevo("texto", f"Texto alternativo: {corto(v)}", v))}"'
        if a in ('href', 'action') and re.match(r'(https?:|mailto:|tel:)', v):
            etiqueta = 'Destino del formulario' if a == 'action' else f'Enlace: {corto(v)}'
            return f'{m[1]}{a}="{php("gc_u", c.nuevo("url", etiqueta, v))}"'
        return m[0]

    tok = re.sub(r'(\s)(src|srcset|alt|href|action)="([^"]*)"', attr, tok)
    if 'id="monitoreo"' in tok:
        clave = c.nuevo('check', 'Mostrar «Del bosque a los datos»', False,
                        'Oculto hasta la certificación (aprox. marzo 2027). Al mostrarlo hay que rehacer las '
                        'anclas data-cuadro de #monitoreo a #impacto para que el video siga fluido.', clave='mostrar_monitoreo')
        tok = tok.replace(' hidden>', php('gc_oculto', clave) + '>')
    return tok


def main():
    src = (ORIGEN / 'index.html').read_text(encoding='utf-8')
    css = re.search(r'<style>\n(.*?)</style>', src, re.S)[1]
    js = re.search(r'<script>\n(.*?)</script>\s*</body>', src, re.S)[1]
    cuerpo = re.search(r'<body>\n(.*?)<script>', src, re.S)[1]
    titulo = re.search(r'<title>(.*?)</title>', src)[1]
    descripcion = re.search(r'<meta name="description" content="([^"]*)"', src)[1]
    fuentes = re.search(r'(<link rel="preconnect".*?display=swap">)', src, re.S)[1]

    c = Campos()
    c.seccion('general', 'General')
    c.nuevo('texto', 'Título de la pestaña del navegador', html.unescape(titulo), clave='gen_titulo')
    c.nuevo('parrafo', 'Descripción para buscadores', html.unescape(descripcion), clave='gen_descripcion')
    c.nuevo('url', 'Enlace de los mapas interactivos', '',
            'Se muestra en un iframe en «Explora el territorio». Vacío = aviso «Falta enlace de mapas».', clave='enlace_mapas')
    c.nuevo('url', 'Enlace embebible del monitoreo de incendios', '',
            'Se muestra en un iframe en «Centro de monitoreo». Vacío = vista previa que abre el dashboard en otra pestaña. '
            'claude.ai no deja embeberse: hace falta hospedarlo en un sitio que lo permita.', clave='enlace_incendios')
    cuerpo_php = convertir_cuerpo(cuerpo, c)
    c.secciones = [s for s in c.secciones if s['campos']]

    # JS: rutas relativas -> carpeta del tema; ENLACES -> valores del Personalizador.
    reemplazos = [
        (re.compile(r'const ENLACES = \{.*?\n  \};', re.S), 'const ENLACES = window.GC.enlaces;'),
        ("'video/recorrido-1080p30.mp4'", "GC.tema + '/video/recorrido-1080p30.mp4'"),
        ('`pack/${dir}/`', '`${GC.tema}/pack/${dir}/`'),
    ]
    for viejo, nuevo in reemplazos:
        js, n = (viejo.subn(nuevo, js) if hasattr(viejo, 'subn') else (js.replace(viejo, nuevo), js.count(viejo)))
        assert n == 1, f'reemplazo JS no encontrado una sola vez: {viejo}'

    if TEMA.exists():
        shutil.rmtree(TEMA)
    (TEMA / 'inc').mkdir(parents=True)
    (TEMA / 'js').mkdir()
    for d in ('assets', 'video', 'pack'):
        shutil.copytree(ORIGEN / d, TEMA / d)
    plantillas = Path(__file__).resolve().parent / 'plantillas'
    for f in plantillas.iterdir():
        shutil.copy(f, TEMA / f.name)

    extra = ('\n/* Fotos que carga el administrador en huecos que eran avisos */\n'
             '.bio-foto > img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }\n'
             '.bio-foto { overflow: hidden; }\n'
             '.retrato > img { width: 100%; height: 100%; object-fit: cover; }\n')
    (TEMA / 'style.css').write_text(
        '/*\nTheme Name: Green Carbon Bolivia\nDescription: Sitio de una página con recorrido en video. '
        'Todo el contenido se edita en Apariencia → Personalizar → Contenido de la web.\nVersion: 1.0.0\n'
        'Requires PHP: 8.1\nText Domain: greencarbon\n*/\n' + css + extra, encoding='utf-8')
    (TEMA / 'js' / 'main.js').write_text(js, encoding='utf-8')
    (TEMA / 'inc' / 'campos.json').write_text(json.dumps(c.secciones, ensure_ascii=False, indent=1), encoding='utf-8')
    (TEMA / 'index.php').write_text(
        '<?php /* Generado por herramientas/convertir.py desde greencarbon-web/index.html: no editar a mano. */ ?>\n'
        '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        f'<title>{php("gc_t", "gen_titulo")}</title>\n'
        f'<meta name="description" content="{php("gc_a", "gen_descripcion")}">\n'
        f'{fuentes}\n<?php wp_head(); ?>\n</head>\n<body>\n<?php wp_body_open(); ?>\n'
        f'{cuerpo_php}<?php wp_footer(); ?>\n</body>\n</html>\n', encoding='utf-8')

    # Auto-chequeo: con los valores predeterminados, el texto visible debe ser el mismo que el original.
    def texto_visible(h):
        h = re.sub(r'<!--.*?-->|<[^>]+>', ' ', h, flags=re.S)
        return ' '.join(html.unescape(h).split())
    indice = {k: v for s in c.secciones for k, v in s['campos'].items()}
    def render(m):
        fn, args = m[1], json.loads('[' + m[2].replace('\\$', '$') + ']')
        if fn == 'gc_t':
            return html.escape(indice[args[0]]['defecto'])
        if fn == 'gc_aviso':
            return args[2]
        if fn == 'gc_foto_o_aviso':
            return args[1]
        return ''
    simulado = re.sub(r'<\?php (gc_\w+)\((.*?)\); \?>', render, cuerpo_php)
    assert texto_visible(simulado) == texto_visible(cuerpo), 'el texto renderizado no coincide con el original'
    total = sum(len(s['campos']) for s in c.secciones)
    print(f'Tema generado en {TEMA}: {len(c.secciones)} secciones, {total} campos editables.')


if __name__ == '__main__':
    main()
