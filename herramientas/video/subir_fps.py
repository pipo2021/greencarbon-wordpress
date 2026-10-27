"""Sube los fps del recorrido interpolando lo que ya está publicado (los clips de Flow no están en esta Mac).

Uso: python3 subir_fps.py <greencarbon-web> <salida>
  <salida>/recorrido-1080p60.mp4 : computadora, 30 -> 60 fps (minterpolate mci)
  <salida>/pack-v/               : celular, cuadros WebP 24 -> 48 fps, mismos paquetes de grueso a fino,
                                   con "fps" en el manifest para que el JS convierta las anclas (en cuadros de 24/s).
"""
import json, os, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

WEB, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
MI = 'minterpolate=fps={}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1'


def ff(*a):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *a], check=True)


def computadora():
    # Mismos criterios que el MP4 de 30: GOP corto y sin B-frames para que las búsquedas por scroll sean rápidas.
    ff('-i', f'{WEB}/video/recorrido-1080p30.mp4', '-vf', MI.format(60), '-c:v', 'libx264', '-preset', 'slow',
       '-crf', os.environ.get('CRF', '26'), '-g', '15', '-bf', '0', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
       '-an', f'{OUT}/recorrido-1080p60.mp4')


def celular(fps=48, calidad='68'):
    src = f'{WEB}/pack/v/'
    man = json.load(open(src + 'manifest.json'))
    tmp = tempfile.mkdtemp(dir=OUT)
    for p in man['paquetes']:
        buf = open(src + p['f'], 'rb').read()
        for n, off, ln in p['c']:
            open(f'{tmp}/{n:05d}.webp', 'wb').write(buf[off:off + ln])
    inter = f'{tmp}/inter.mkv'
    ff('-framerate', '24', '-i', f'{tmp}/%05d.webp', '-vf', MI.format(fps) + ',format=yuv420p',
       '-c:v', 'libx264', '-crf', '0', '-preset', 'ultrafast', inter)
    salida = f'{OUT}/pack-v'
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'empaquetar.py'),
                    inter, salida, calidad], check=True)
    m = json.load(open(f'{salida}/manifest.json'))
    m['fps'] = fps
    json.dump(m, open(f'{salida}/manifest.json', 'w'), separators=(',', ':'))
    subprocess.run(['rm', '-rf', tmp])


with ThreadPoolExecutor(2) as ex:
    for f in [ex.submit(computadora), ex.submit(celular)]:
        f.result()
print('listo')
