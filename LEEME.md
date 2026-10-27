# Green Carbon Bolivia — versión WordPress

**Guía completa (instalación, acceso, qué se edita, qué falta completar): [`docs/Guia-Green-Carbon-WordPress.pdf`](docs/Guia-Green-Carbon-WordPress.pdf).**

Sitio de una sola página, en **español e inglés**, con el recorrido en video que avanza con el scroll, convertido en un tema de WordPress. **Todo el contenido** (textos, fotos, enlaces, datos de contacto, avisos pendientes) se edita desde un único administrador, en **Apariencia → Personalizar → Contenido de la web**, con vista previa en vivo.

## Levantarlo en local (Docker)

Requisitos: Docker con Compose v2.

```bash
cp .env.ejemplo .env      # cambiar las contraseñas (si vino un .env, ya tiene unas generadas)
docker compose up -d --build
```

- Sitio: http://localhost:8080 (puerto `GC_PUERTO` en `.env`)
- Administrador: http://localhost:8080/wp-admin, con el usuario y la contraseña de `GC_ADMIN_USER` / `GC_ADMIN_PASSWORD` en `.env`

La primera vez, antes de arrancar Apache, el contenedor instala WordPress en español, activa el tema, crea el único administrador y borra los temas y plugins de ejemplo (`docker/instalar.sh`). En los arranques siguientes solo reaplica el tema y las opciones, sin tocar el contenido.

`GC_URL` se guarda en la base en la primera instalación. Para cambiar de dominio después: `docker compose exec wordpress wp --allow-root search-replace 'http://viejo' 'https://nuevo'`.

Con la imagen ya construida (`greencarbon-wordpress-1.2.2-amd64.tar.gz`, para servidores x86) no hace falta reconstruir:

```bash
docker load -i greencarbon-wordpress-1.2.2-amd64.tar.gz
docker tag greencarbon-wordpress:1.2.2-amd64 greencarbon-wordpress:1.2.2
docker compose up -d --no-build
```

## Qué edita el administrador

21 secciones, en el mismo orden que la página, con 354 campos. Cada texto tiene dos campos, **ES** y **EN** (debajo):

| Sección | Qué se edita |
|---|---|
| General | Título de la pestaña, descripción para buscadores, **enlace de los mapas** e **enlace del monitoreo de incendios** (si se completan, se muestran en un iframe) |
| Cabecera y menú → Pie de página | Cada título, párrafo, botón, ítem del menú, foto (y su texto alternativo), enlace externo, redes sociales y destino del formulario |
| Avisos «Falta» / «SSOT» | Cada aviso tiene un campo. Si se escribe el dato real, el aviso desaparece y se muestra el dato. Si se deja vacío, vuelve el aviso. |
| Retratos y foto de especie | Huecos de imagen. Mientras estén vacíos se ve la silueta o el aviso. |
| General → idioma | Casilla para mostrar el selector **ES \| EN** de la cabecera. El inglés se ve en `?lang=en`. Un texto en inglés vacío se muestra en español. |
| General → opacidades | Deslizadores para la opacidad de las hojas claras, las hojas verdes y las tarjetas (1 = tapa el video; más bajo = se ve más el video). |
| Mensajes de la página | Textos que escribe el JavaScript: MENÚ/CERRAR, «Cargando el territorio» y los mensajes del formulario. |
| 9 · Monitoreo territorial | Casilla para mostrar «Del bosque a los datos», que está oculta hasta la certificación (aprox. marzo de 2027). Al activarla hay que rehacer las anclas `data-cuadro` (ver más abajo). |

**El inglés es un borrador** (`herramientas/traduccion-en.json`): el cliente tiene que aprobarlo. Se corrige desde el panel o en ese archivo, y después se vuelve a correr `convertir.py`.

En los textos se permiten `<em>`, `<strong>`, `<b>`, `<br>` y `<a>`.

## Qué NO se edita desde el panel (está fijo en el tema)

- **El recorrido en video**: `video/recorrido-1080p60.mp4` (60 fps) en computadora y los cuadros WebP `pack/v` a 48 fps en celular. `pack/h` (24 fps) solo es un respaldo si falla el MP4. Los fps altos se interpolaron (minterpolate) desde los de 30 y 24 fps con `herramientas/video/subir_fps.py` (los clips originales de Flow no están en el repo; `recorrido3.py` y `empaquetar.py` son el pipeline original). El manifest de cada paquete trae sus `fps` y el JS convierte las anclas, que siguen en cuadros de 24/s. Se generan con los scripts de Python del recorrido. Si cambia, hay que reemplazar los archivos y subir `VERSION` en `js/main.js`, porque el navegador los cachea.
- **Las anclas `data-cuadro`** de cada sección, que sincronizan el scroll con el video.
- **El diseño**: `style.css`, los íconos SVG y la estructura de secciones.

## Cómo está hecho

```
herramientas/convertir.py     index.html original → tema (regenera tema/greencarbon entero)
herramientas/plantillas/      functions.php (Personalizador y funciones de salida)
tema/greencarbon/             tema generado: index.php, style.css, js/main.js, inc/campos.json, assets, video, pack
docker/                       entrypoint e instalación inicial
Dockerfile, docker-compose.yml
```

- `inc/campos.json` define cada campo (tipo, etiqueta y valor predeterminado = contenido actual del sitio). Mientras el admin no cambie nada, el sitio es idéntico al HTML original. `convertir.py` lo verifica al generar el tema.
- Los cambios de diseño conviene hacerlos en el `index.html` original y volver a correr `python3 herramientas/convertir.py <greencarbon-web> tema/greencarbon`. Las claves de los campos (`s05_03`, etc.) son posicionales, así que agregar o quitar textos en una sección corre las claves siguientes de esa sección. Después de un cambio de estructura, revisar los valores ya cargados.
- El tema no usa plugins. La barra de administración está oculta en el frente porque tapa la cabecera fija.
- `/var/www/html` es un volumen de la imagen oficial: al arrancar, `docker/instalar.sh` vuelve a copiar el tema de la imagen para que una imagen nueva no siga sirviendo el tema viejo.

## Para producción

- Usar el `.env` con contraseñas propias, `GC_URL` con el dominio real y `GC_INDEXAR=1` cuando el cliente apruebe publicar (hoy está en `noindex`, igual que el sitio actual).
- Poner HTTPS delante (proxy inverso o el panel del hosting) y publicar el puerto solo en `127.0.0.1`. El editor de archivos del admin está desactivado (`DISALLOW_FILE_EDIT`).
- Las contraseñas de `.env` quedan visibles con `docker inspect`: en producción conviene usar secretos del orquestador.
- Si se despliega en un hosting WordPress sin Docker: subir solo `tema/greencarbon` a `wp-content/themes/` y activarlo. Pesa unos 245 MB por el video y los cuadros.
- Respaldo: volúmenes `db` (base de datos) y `uploads` (fotos que suba el admin).

## Pendientes del cliente (se cargan desde el panel cuando lleguen)

Enlaces de mapas y de monitoreo de incendios (el dashboard actual vive en claude.ai, que no deja embeberse), foto de Lomerío, retratos y testimonios con consentimiento, especie de biodiversidad, cifras de impacto, dirección, correo y teléfono, destino del Canal de Integridad, texto de privacidad y confirmar si los datos del centro de monitoreo son en vivo. La traducción al inglés no está incluida: el sitio es solo en español.
