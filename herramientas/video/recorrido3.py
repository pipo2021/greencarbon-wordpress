"""Arma el recorrido continuo (scroll = video) de la web de Green Carbon.

Uso: python3 recorrido.py {h|v} salida.mp4
  h: 1280x720 (computadora) · v: 540x960 recortado por plano (celular)
Imprime en stderr el segundo donde arranca cada plano (para anclar secciones).
"""
import os, subprocess, sys

F = os.path.expanduser('~/greencarbon-media/1080p/')
P = os.path.expanduser('~/greencarbon-media/propios/videos/A117_0101')
FPS, XF = 24, 0.7
N = os.path.expanduser('~/greencarbon-media/flow-escenas/')

# (clave, archivo, desde s, duración s, centro x del recorte vertical 0..1, real)
PLANOS = [
    ('aerea',     F + '0-apertura-1080p.mp4', 0,   6.5, .50, False),
    ('rio',       F + '1-portada-1080p.mp4',  0,   6,   .55, False),
    ('equipo',    N + 'v2-equipo.mp4',        0,   7,   .50, False),
    ('camino',    N + 'v1-dron-camino.mp4',   0,   7,   .50, False),
    ('selva',     F + '2b-selva-1080p.mp4',   1,   5.5, .50, False),
    ('trampa',    N + 'v3-camara-trampa.mp4', 0,   7,   .55, False),
    ('dron',      N + 'v4-dron-despega.mp4',  0,   7.5, .50, False),
    ('dosel',     F + '2-dosel-1080p.mp4',    0,   6,   .50, False),
    ('cielo',     F + '4-cielo-1080p.mp4',    0,   7,   .50, False),
]

modo, salida = sys.argv[1], sys.argv[2]
W, H = (1440, 810) if modo == 'h' else (540, 960)

args, filtros = ['ffmpeg', '-v', 'error', '-y'], []
for i, (_, f, ss, d, cx, real) in enumerate(PLANOS):
    args += ['-ss', str(ss), '-t', str(d), '-i', f]
    if modo == 'h':
        geo = f'scale={W}:{H}'
    else:
        # Recorte vertical 9:16 de un cuadro 1920x1080: 608 de ancho, centrado en cx.
        cw = 608
        x = max(0, min(1920 - cw, round(1920 * cx - cw / 2)))
        geo = f'scale=1920:1080,crop={cw}:1080:{x}:0,scale={W}:{H}'
    # Las tomas reales vienen planas: un poco de contraste y color para que casen con las aéreas.
    color = ',eq=contrast=1.07:saturation=1.18:gamma=0.97' if real else ''
    filtros.append(f'[{i}:v]setpts=PTS-STARTPTS,{geo}{color},setsar=1,format=yuv420p,fps={FPS}[c{i}]')

prev, t, inicios = 'c0', 0.0, [0.0]
for i in range(1, len(PLANOS)):
    t += PLANOS[i - 1][3] - XF
    inicios.append(t)
    out = f'x{i}'
    filtros.append(f'[{prev}][c{i}]xfade=transition=fade:duration={XF}:offset={t:.3f}[{out}]')
    prev = out

args += ['-filter_complex', ';'.join(filtros), '-map', f'[{prev}]',
         '-c:v', 'libx264', '-crf', '12', '-preset', 'slow', '-pix_fmt', 'yuv420p', salida]
subprocess.run(args, check=True)
total = inicios[-1] + PLANOS[-1][3]
for (k, *_), s in zip(PLANOS, inicios):
    # Inicio del plano = mitad del fundido de entrada, en cuadros.
    print(k, round((s + (XF / 2 if s else 0)) * FPS), file=sys.stderr)
print('total_s', round(total, 2), 'cuadros', round(total * FPS), file=sys.stderr)
