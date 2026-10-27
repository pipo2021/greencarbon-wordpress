"""Pasa el recorrido a cuadros WebP y los junta en paquetes de lo grueso a lo fino.

Uso: python3 empaquetar.py recorrido.mp4 carpeta_salida calidad
Escribe p*.bin + manifest.json {n, paquetes:[{f, c:[[cuadro, offset, largo], ...]}]}.
"""
import glob, json, os, subprocess, sys, tempfile

src, out, q = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
tmp = tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(__file__)))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-c:v', 'libwebp', '-quality', q,
                '-compression_level', '5', f'{tmp}/%05d.webp'], check=True)
cuadros = sorted(glob.glob(f'{tmp}/*.webp'))
n = len(cuadros)

# Niveles: 1 de cada 16, los 8 del medio, después 4, 2 y por último los impares en 4 tramos.
niveles = [[i for i in range(0, n, 16)], [i for i in range(8, n, 16)],
           [i for i in range(4, n, 8)], [i for i in range(2, n, 4)]]
impares = list(range(1, n, 2))
k = (len(impares) + 3) // 4
niveles += [impares[j:j + k] for j in range(0, len(impares), k)]

paquetes = []
for p, idx in enumerate(niveles):
    nombre, off, c = f'p{p}.bin', 0, []
    with open(f'{out}/{nombre}', 'wb') as fh:
        for i in idx:
            datos = open(cuadros[i], 'rb').read()
            fh.write(datos)
            c.append([i, off, len(datos)])
            off += len(datos)
    paquetes.append({'f': nombre, 'c': c})
    print(nombre, len(idx), 'cuadros', round(off / 1e6, 1), 'MB')
json.dump({'n': n, 'paquetes': paquetes}, open(f'{out}/manifest.json', 'w'), separators=(',', ':'))
for f in cuadros:
    os.remove(f)
os.rmdir(tmp)
print('total', n)
