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
TRADUCCION = Path(__file__).resolve().parent / 'traduccion-en.json'  # {texto en español: texto en inglés}
# Textos que escribe el JS: (literal en main.js, clave en GC.t, texto en español)
TEXTOS_JS = [
    ("'MENÚ'", 'menu', 'MENÚ'), ("'CERRAR'", 'cerrar', 'CERRAR'),
    ('`Cargando el territorio · ${pct}%`', 'cargando', 'Cargando el territorio'),
    ("'Mapa del territorio'", 'iframe_mapa', 'Mapa del territorio'),
    ("'Monitoreo de incendios'", 'iframe_incendios', 'Monitoreo de incendios'),
    ("'Completá nombre, un correo válido y el mensaje.'", 'form_faltan', 'Completá nombre, un correo válido y el mensaje.'),
    ("'Necesitamos tu consentimiento para responderte.'", 'form_consentimiento', 'Necesitamos tu consentimiento para responderte.'),
    ("'Enviando…'", 'form_enviando', 'Enviando…'),
    ("'Hemos recibido tu mensaje.'", 'form_ok', 'Hemos recibido tu mensaje.'),
    ("'No se pudo enviar. Probá de nuevo en unos minutos.'", 'form_error', 'No se pudo enviar. Probá de nuevo en unos minutos.'),
]


def corto(t, n=48):
    return t if len(t) <= n else t[:n - 1].rstrip() + '…'


class Campos:
    def __init__(self):
        self.secciones = []          # [{id, titulo, campos: {clave: {...}}}]
        self.cuenta = {}
        self.imagenes = {}           # src -> clave (el logo se usa dos veces)
        self.ocultos = {}            # (seccion, texto) -> clave, para la marquesina duplicada
        self.trad = json.loads(TRADUCCION.read_text(encoding='utf-8')) if TRADUCCION.exists() else {}
        self.sin_traducir = set()

    def en(self, texto):
        if texto not in self.trad:
            self.sin_traducir.add(texto)
        return self.trad.get(texto, '')

    def seccion(self, sid, titulo):
        self.secciones.append({'id': sid, 'titulo': titulo, 'campos': {}})

    def nuevo(self, tipo, etiqueta, defecto, desc='', clave=None):
        s = self.secciones[-1]
        if clave is None:
            self.cuenta[s['id']] = self.cuenta.get(s['id'], 0) + 1
            clave = f"{s['id']}_{self.cuenta[s['id']]:02d}"
        s['campos'][clave] = {'tipo': tipo, 'etiqueta': etiqueta, 'defecto': defecto, 'desc': desc}
        if tipo in ('texto', 'parrafo'):
            s['campos'][clave]['en'] = self.en(defecto) if defecto else ''
        return clave


def php(fn, *args):
    return '<?php ' + fn + '(' + ', '.join(json.dumps(a, ensure_ascii=False).replace('$', '\\$') for a in args) + '); ?>'


def convertir_cuerpo(cuerpo, c):
    # Avisos y huecos de foto que el admin reemplaza con el dato real (vacío = se ve el aviso).
    cuerpo = re.sub(r'<div class="bio-foto"><span class="pend">([^<]*)</span></div>',
                    lambda m: f'<div class="bio-foto"><gcbiofoto texto="{m[1]}"></div>', cuerpo)
    cuerpo = re.sub(r'<div class="retrato"><svg class="i"><use href="#i-retrato"/></svg></div>',
                    '<gcretrato>', cuerpo)
    for viejo, nuevo in (('  <a href="#contacto" class="btn pri cta-cab">', '  <div class="cab-der"><gcidioma>\n  <a href="#contacto" class="btn pri cta-cab">'),
                         ('</a>\n</header>', '</a></div>\n</header>')):
        assert cuerpo.count(viejo) == 1, viejo
        cuerpo = cuerpo.replace(viejo, nuevo)
    cuerpo = re.sub(r'<span class="(pend|ssot)">([^<]*)</span>',
                    lambda m: f'<gcaviso clase="{m[1]}" texto="{m[2]}">', cuerpo)

    salida, ultimo, svg, oculto = [], 'p', 0, 0
    pila_oculta = []
    c.seccion('cab', 'Cabecera y menú')
    for tok in re.split(r'(<!--.*?-->|<[^>]+>)', cuerpo, flags=re.S):
        if not tok:
            continue
        if tok == '<!-- gc:mapa-img -->':
            img = c.nuevo('imagen', 'Imagen estática del mapa del proyecto', '',
                          'Mapa de ubicación de las TCO exportado de Global Nature Watch (horizontal, mín. 1600 px de ancho). '
                          'Vacío = se muestra el aviso «Falta imagen del mapa».')
            alt = 'Mapa de ubicación de los territorios indígenas Monte Verde y Lomerío'
            salida.append(php('gc_mapa_img', img, c.nuevo('texto', f'Texto alternativo: {corto(alt)}', alt)))
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
        # Textos que después reescribe el JS: arrancan con el mismo campo traducible que usa el JS.
        if texto == 'MENÚ' and 'id="menu-btn"' in ultimo:
            salida.append(php('gc_t', 'js_menu'))
            continue
        if texto.startswith('Cargando el territorio') and 'id="loader-txt"' in ultimo:
            salida.append(php('gc_t', 'js_cargando') + ' · 0%')
            continue
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
    if nombre == 'gcidioma':
        return php('gc_idioma')
    if nombre == 'gcaviso':
        m = re.match(r'<gcaviso clase="(\w+)" texto="([^"]*)">', tok)
        texto = html.unescape(m[2])
        clave = c.nuevo('texto', f'Aviso «{corto(texto, 40)}»', '',
                        'Escribí el dato real para reemplazar el aviso. Vacío = se muestra el aviso.')
        return php('gc_aviso', clave, m[1], texto, c.en(texto))
    if nombre == 'gcbiofoto':
        texto = html.unescape(re.match(r'<gcbiofoto texto="([^"]*)">', tok)[1])
        clave = c.nuevo('imagen', 'Foto de la especie', '', 'Vacío = se muestra el aviso «' + texto + '».')
        return php('gc_foto_o_aviso', clave, texto, c.en(texto))
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
        if a == 'poster':
            return f'{m[1]}poster="{php("gc_u", c.nuevo("imagen", f"Portada del video: {Path(v).name}", v))}"'
        if a == 'src' and nombre == 'video':
            return f'{m[1]}src="{php("gc_u", c.nuevo("video", f"Video: {Path(v).name}", v))}"'
        if a == 'srcset':
            src = re.search(r'\ssrc="([^"]*)"', tok)[1]
            return php('gc_srcset', c.imagenes[src], v)  # el src viene antes que srcset en el HTML
        if a == 'alt' and v:
            return f'{m[1]}alt="{php("gc_a", c.nuevo("texto", f"Texto alternativo: {corto(v)}", v))}"'
        if a == 'aria-label':
            return f'{m[1]}aria-label="{php("gc_a", c.nuevo("texto", f"Lector de pantalla: {corto(v)}", v))}"'
        if a in ('href', 'action') and re.match(r'(https?:|mailto:|tel:)', v):
            etiqueta = 'Destino del formulario' if a == 'action' else f'Enlace: {corto(v)}'
            return f'{m[1]}{a}="{php("gc_u", c.nuevo("url", etiqueta, v))}"'
        return m[0]

    tok = re.sub(r'(\s)(src|srcset|alt|aria-label|href|action|poster)="([^"]*)"', attr, tok)
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
            'Opcional, para más adelante: si se completa, reemplaza la imagen estática del mapa por un iframe. '
            'El sitio enlazado tiene que permitir ser embebido.', clave='enlace_mapas')
    c.nuevo('url', 'Enlace embebible del monitoreo de incendios', '',
            'Opcional, para más adelante: si se completa, reemplaza la imagen estática del Centro de Operaciones de Incendios '
            'por el dashboard en un iframe. Tiene que estar publicado fuera de claude.ai y permitir ser embebido en el dominio.', clave='enlace_incendios')
    c.nuevo('check', 'Mostrar el selector de idioma ES | EN', True,
            'Los textos en inglés vacíos se muestran en español.', clave='mostrar_idioma')
    for k, etiqueta, defecto in (('alfa-hoja', 'Opacidad de las hojas claras', .84), ('alfa-oscuro', 'Opacidad de las hojas verdes', .74),
                                 ('alfa-tarjeta', 'Opacidad de las tarjetas', .72)):
        assert f'--{k}: {str(defecto).lstrip("0")}' in css, k
        c.nuevo('opacidad', etiqueta, defecto, '1 = tapa el video del todo; más bajo = se ve más el video detrás.', clave=k)
    cuerpo_php = convertir_cuerpo(cuerpo, c)
    c.seccion('js', 'Mensajes de la página (menú, carga, formulario)')
    for _, k, es in TEXTOS_JS:
        c.nuevo('texto', es, es, clave='js_' + k)
    c.secciones = [s for s in c.secciones if s['campos']]

    # JS: rutas relativas -> carpeta del tema; ENLACES -> valores del Personalizador.
    reemplazos = [
        (re.compile(r'const ENLACES = \{.*?\n  \};', re.S), 'const ENLACES = window.GC.enlaces;'),
        (re.compile(r"'video/(recorrido-[^']+)'"), r"GC.tema + '/video/\1'"),
        ('`pack/${dir}/`', '`${GC.tema}/pack/${dir}/`'),
    ]
    for viejo, nuevo in reemplazos:
        js, n = (viejo.subn(nuevo, js) if hasattr(viejo, 'subn') else (js.replace(viejo, nuevo), js.count(viejo)))
        assert n == 1, f'reemplazo JS no encontrado una sola vez: {viejo}'
    for literal, k, es in TEXTOS_JS:
        nuevo = '`${GC.t.cargando} · ${pct}%`' if k == 'cargando' else f'GC.t.{k}'
        assert literal in js, literal
        js = js.replace(literal, nuevo)

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
             '.retrato > img { width: 100%; height: 100%; object-fit: cover; }\n'
             '\n/* Selector de idioma */\n'
             '.cab-der { display: flex; align-items: center; gap: 10px; }\n'
             '.idioma { display: inline-flex; gap: 2px; padding: 4px; border-radius: 999px; background: var(--glass); border: 1px solid var(--glass-borde);\n'
             '  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); }\n'
             '.idioma a { font: 500 11px/1 var(--f-mono); letter-spacing: .12em; padding: 8px 10px; border-radius: 999px; color: var(--mist-2); text-decoration: none; }\n'
             '.idioma a:hover { color: var(--mist); }\n'
             '.idioma a[aria-current] { background: var(--lichen); color: var(--night); }\n'
             '@media (max-width: 1060px) { .cab-der { margin-left: auto; } .menu-btn { margin-left: 10px; order: 3; } }\n'
             '/* Celular: el logo no se encoge y el selector muestra solo el otro idioma */\n'
             '.marca { flex-shrink: 0; }\n'
             '@media (max-width: 520px) { .idioma a[aria-current] { display: none; } }\n'
             '@media (max-width: 359px) { .marca-pais { display: none; } }\n')
    (TEMA / 'style.css').write_text(
        '/*\nTheme Name: Green Carbon Bolivia\nDescription: Sitio de una página con recorrido en video. '
        'Todo el contenido se edita en Apariencia → Personalizar → Contenido de la web.\nVersion: 1.2.2\n'
        'Requires PHP: 8.1\nText Domain: greencarbon\n*/\n' + css + extra, encoding='utf-8')
    (TEMA / 'js' / 'main.js').write_text(js, encoding='utf-8')
    (TEMA / 'inc' / 'campos.json').write_text(json.dumps(c.secciones, ensure_ascii=False, indent=1), encoding='utf-8')
    (TEMA / 'index.php').write_text(
        '<?php /* Generado por herramientas/convertir.py desde greencarbon-web/index.html: no editar a mano. */ ?>\n'
        '<!doctype html>\n<html lang="<?php echo esc_attr( gc_lang() ); ?>">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        f'<title>{php("gc_t", "gen_titulo")}</title>\n'
        f'<meta name="description" content="{php("gc_a", "gen_descripcion")}">\n'
        f'<?php gc_hreflang(); ?>\n{fuentes}\n<?php wp_head(); ?>\n</head>\n<body>\n<?php wp_body_open(); ?>\n'
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
    faltan = Path(__file__).resolve().parent / 'sin-traducir.json'
    faltan.unlink(missing_ok=True)
    if c.sin_traducir:
        faltan.write_text(json.dumps(sorted(c.sin_traducir), ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'{len(c.sin_traducir)} textos sin traducción al inglés: {faltan}')
    print(f'Tema generado en {TEMA}: {len(c.secciones)} secciones, {total} campos editables.')


if __name__ == '__main__':
    main()
