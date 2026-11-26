(function () {
  // Enlaces que da Green Carbon Bolivia. Al completarlos, el mapa y el centro de monitoreo cargan la fuente real.
  const ENLACES = window.GC.enlaces;
  function embeber(id, url, titulo) {
    if (!url) return;
    const caja = document.getElementById(id);
    caja.querySelectorAll('.mapa-vacio, .vista, .mapa-img, .mapa-fuente, .panel-abrir, .mapa-gnw, .mapa-vivo').forEach(el => el.remove());
    const f = document.createElement('iframe');
    f.src = url; f.title = titulo; f.loading = 'lazy';
    caja.appendChild(f);
  }
  embeber('mapa-territorio', ENLACES.mapas, GC.t.iframe_mapa);
  embeber('mapa-monitoreo', ENLACES.incendios, GC.t.iframe_incendios);

  // Mapa del territorio: satélite + contornos de Monte Verde y Lomerío (datos de Global Nature Watch), sin herramientas.
  // Leaflet y los contornos se bajan recién cuando la sección se acerca a la pantalla.
  // Las pestañas Monte Verde / Lomerío mueven el mapa y cambian el enlace del botón a GNW.
  (function () {
    const caja = document.getElementById('mapa-vivo');
    const pestanas = document.querySelectorAll('[data-territorio]');
    const boton = document.querySelector('#mapa-territorio .mapa-gnw');
    const enlaceGnw = { 'Monte Verde': boton && boton.href, 'Lomerío': boton && (boton.dataset.lomerio || boton.href) };
    let elegido = 'Monte Verde', mostrar = null;
    pestanas.forEach(b => b.addEventListener('click', () => {
      elegido = b.dataset.territorio;
      if (boton && enlaceGnw[elegido]) boton.href = enlaceGnw[elegido];
      if (mostrar) mostrar(true);
    }));
    if (!caja || !('IntersectionObserver' in window)) return;
    const base = GC.tema + '/';
    const cargar = (tag, attrs) => new Promise((ok, mal) => {
      const el = Object.assign(document.createElement(tag), attrs);
      el.onload = ok; el.onerror = mal; document.head.appendChild(el);
    });
    const bajar = n => fetch(base + 'datos/' + n + '.geojson?v=' + GC.v).then(r => { if (!r.ok) throw r.status; return r.json(); });
    function armar(geos) {
      const tactil = matchMedia('(pointer: coarse)').matches;
      const L = window.L;
      const mapa = L.map(caja, {
        zoomSnap: .25, scrollWheelZoom: false, dragging: !tactil, touchZoom: !tactil,
        doubleClickZoom: !tactil, boxZoom: false, keyboard: false, zoomControl: !tactil, attributionControl: true
      });
      if (mapa.zoomControl) mapa.zoomControl.setPosition('topright');
      mapa.attributionControl.setPrefix(false);
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 17, attribution: 'Esri, Maxar · Global Nature Watch'
      }).addTo(mapa);
      const capas = {};
      for (const n in geos) capas[n] = L.geoJSON(geos[n], { interactive: false }).addTo(mapa);
      const margen = { paddingTopLeft: [20, 60], paddingBottomRight: [20, tactil ? 110 : 30] };
      mostrar = animar => {
        for (const n in capas) {
          const si = n === elegido;
          capas[n].setStyle(si
            ? { color: '#b8d48f', weight: 2, opacity: 1, dashArray: null, fillColor: '#b8d48f', fillOpacity: .14 }
            : { color: '#eef3ef', weight: 1, opacity: .45, dashArray: '4 4', fillOpacity: 0 });
          if (si) capas[n].bringToFront();
        }
        // Algunos retazos sueltos quedan dibujados pero no cuentan para el encuadre ("encuadre": false).
        const lim = L.latLngBounds([]);
        capas[elegido].eachLayer(l => { if (l.feature.properties.encuadre !== false) lim.extend(l.getBounds()); });
        if (animar && !matchMedia('(prefers-reduced-motion: reduce)').matches) mapa.flyToBounds(lim, Object.assign({ duration: .9 }, margen));
        else mapa.fitBounds(lim, margen);
      };
      mostrar(false);
      mapa.setMinZoom(Math.max(5, mapa.getZoom() - 2.5));
      new ResizeObserver(() => { mapa.invalidateSize(); }).observe(caja);
      document.getElementById('mapa-territorio').classList.add('con-mapa');
    }
    const io = new IntersectionObserver(es => {
      if (!es.some(e => e.isIntersecting)) return;
      io.disconnect();
      cargar('link', { rel: 'stylesheet', href: base + 'js/leaflet/leaflet.css?v=1.9.4' });
      Promise.all([
        window.L ? 0 : cargar('script', { src: base + 'js/leaflet/leaflet.js?v=1.9.4' }),
        bajar('monte-verde'), bajar('lomerio')
      ]).then(([, mv, lo]) => armar({ 'Monte Verde': mv, 'Lomerío': lo })).catch(() => caja.remove());
    }, { rootMargin: '800px 0px' });
    io.observe(caja);
  })();

  // Voces del territorio: «Ver historia» abre el video en un reproductor sobre la página (sin dialog, abre el MP4).
  (function () {
    const botones = document.querySelectorAll('.voz-video');
    if (!botones.length || typeof HTMLDialogElement !== 'function') return;
    const dlg = document.createElement('dialog');
    dlg.className = 'reproductor';
    dlg.innerHTML = '<button type="button" class="reproductor-cerrar" aria-label="' + (GC.t.cerrar || 'Cerrar') + '">×</button><video controls playsinline preload="none"></video>';
    document.body.appendChild(dlg);
    const video = dlg.querySelector('video');
    const cerrar = () => dlg.close();
    dlg.querySelector('button').addEventListener('click', cerrar);
    dlg.addEventListener('click', e => { if (e.target === dlg) cerrar(); });
    dlg.addEventListener('close', () => { video.pause(); video.removeAttribute('src'); video.load(); });
    botones.forEach(b => b.addEventListener('click', e => {
      e.preventDefault();
      dlg.setAttribute('aria-label', b.dataset.titulo || '');
      video.src = b.href;
      dlg.showModal();
      video.play().catch(() => {});
    }));
  })();

  const raiz = document.documentElement;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Cabecera: transparente sobre la portada, sólida al bajar. Menú en celular.
  const cab = document.getElementById('cab'), menuBtn = document.getElementById('menu-btn');
  menuBtn.addEventListener('click', () => {
    const abierto = cab.classList.toggle('menu');
    menuBtn.setAttribute('aria-expanded', String(abierto));
    menuBtn.textContent = abierto ? GC.t.cerrar : GC.t.menu;
  });
  document.querySelectorAll('.nav a').forEach(a => a.addEventListener('click', () => {
    cab.classList.remove('menu'); menuBtn.setAttribute('aria-expanded', 'false'); menuBtn.textContent = GC.t.menu;
  }));

  // Títulos que entran palabra por palabra: cada palabra va en una máscara (.w) que la deja subir.
  function partir(el) {
    let k = 0;
    const recorrer = nodo => [...nodo.childNodes].forEach(n => {
      if (n.nodeType === 1) return recorrer(n);
      if (n.nodeType !== 3 || !n.textContent.trim()) return;
      const frag = document.createDocumentFragment();
      n.textContent.split(/(\s+)/).forEach(parte => {
        if (!parte) return;
        if (/^\s+$/.test(parte)) return frag.appendChild(document.createTextNode(parte));
        const w = document.createElement('span'), s = document.createElement('span');
        w.className = 'w'; s.textContent = parte; s.style.setProperty('--w', k++); w.appendChild(s); frag.appendChild(w);
      });
      n.replaceWith(frag);
    });
    recorrer(el);
  }
  document.querySelectorAll('.reveal h2, .hero h1').forEach(partir);

  // Animaciones de entrada por bloque.
  const reveals = [...document.querySelectorAll('.reveal')];
  reveals.forEach(r => {
    // Los hijos directos sin marca también entran en cascada, en el orden del DOM.
    [...r.children].forEach(c => { if (!c.querySelector('.item')) c.classList.add('item'); });
    r.querySelectorAll('.item').forEach((el, i) => el.style.setProperty('--i', Math.min(i, 12)));
  });
  document.querySelectorAll('.hero .cont > *').forEach((el, i) => { el.classList.add('item'); el.style.setProperty('--i', i); });
  if (!reduce && 'IntersectionObserver' in window) {
    raiz.classList.add('anim');
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) e.target.classList.add('in');
      else if (e.boundingClientRect.top > 0) e.target.classList.remove('in');
    }), { threshold: .12 });
    reveals.forEach(r => io.observe(r));
  }

  // Selector de idioma: el otro idioma se abre en la misma sección que se está leyendo.
  document.querySelectorAll('.idioma a').forEach(a => a.addEventListener('click', () => {
    let id = '';
    document.querySelectorAll('main > section[id]').forEach(s => {
      if (s.getClientRects().length && s.getBoundingClientRect().top < innerHeight * .4) id = s.id;
    });
    const u = new URL(a.href);
    u.hash = id;
    a.href = u.href;
  }));

  // Mapa: pestañas Monte Verde / Lomerío.
  document.querySelectorAll('[data-territorio]').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('[data-territorio]').forEach(o => o.setAttribute('aria-selected', String(o === b)));
    document.getElementById('t-nombre').textContent = 'TIOC ' + b.dataset.territorio;
    document.getElementById('migas-territorio').textContent = b.dataset.territorio;
    document.querySelectorAll('.ficha [data-t]').forEach(d => { d.hidden = d.dataset.t !== b.dataset.territorio; });
  }));

  // Voces: flechas del carrusel.
  const carrusel = document.getElementById('carrusel');
  document.querySelectorAll('[data-mover]').forEach(b => b.addEventListener('click', () => {
    const paso = carrusel.querySelector('.voz').offsetWidth + 16;
    carrusel.scrollBy({ left: paso * Number(b.dataset.mover), behavior: reduce ? 'auto' : 'smooth' });
  }));

  // Impacto: pestañas con teclado (flechas).
  const tabs = [...document.querySelectorAll('.tabs [role="tab"]')];
  function elegir(t) {
    tabs.forEach(o => { const sel = o === t; o.setAttribute('aria-selected', String(sel)); o.tabIndex = sel ? 0 : -1; document.getElementById(o.getAttribute('aria-controls')).hidden = !sel; });
  }
  tabs.forEach((t, i) => {
    t.addEventListener('click', () => elegir(t));
    t.addEventListener('keydown', e => {
      const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
      if (!d) return;
      const n = tabs[(i + d + tabs.length) % tabs.length]; elegir(n); n.focus();
    });
  });

  // En acción: filtro por categoría; el video corre solo mientras se ve.
  document.querySelectorAll('.cats button').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.cats button').forEach(o => o.setAttribute('aria-pressed', String(o === b)));
    document.querySelectorAll('.pieza').forEach(p => p.classList.toggle('oculta', b.dataset.cat !== 'todo' && !p.dataset.cat.split(' ').includes(b.dataset.cat)));
  }));
  const video = document.querySelector('.pieza video');
  if ('IntersectionObserver' in window && !reduce) {
    new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) video.play().catch(() => {}); else video.pause(); }), { threshold: .3 }).observe(video);
  }

  // Formulario: lo envía WordPress por correo (gc/v1/contacto), o un servicio externo si se cargó en el Personalizador.
  const form = document.getElementById('contacto-form'), estado = document.getElementById('form-estado');
  form.addEventListener('submit', async ev => {
    ev.preventDefault();
    const datos = Object.fromEntries(new FormData(form));
    const decir = (t, cls) => { estado.textContent = t; estado.className = 'form-estado ' + (cls || ''); };
    if (!datos.nombre.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(datos.correo.trim()) || !datos.mensaje.trim()) return decir(GC.t.form_faltan, 'error');
    if (!datos.consentimiento) return decir(GC.t.form_consentimiento, 'error');
    const boton = form.querySelector('button'); boton.disabled = true; decir(GC.t.form_enviando);
    try {
      const r = await fetch(form.action, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify({ ...datos, origen: 'web Green Carbon Bolivia' }) });
      if (!r.ok) throw new Error(r.status);
      form.reset(); decir(GC.t.form_ok, 'ok');
    } catch (e) { decir(GC.t.form_error, 'error'); }
    boton.disabled = false;
  });

  // ---------- Recorrido de video atado al scroll ----------
  // Un solo plano continuo (9 escenas de Google Flow unidas con fundidos). Las anclas están en cuadros de 24/s.
  // Computadora: video MP4 1920x1080 a 30 cuadros/s (interpolado) que el scroll adelanta y retrocede.
  // Celular vertical: cuadros WebP 540x960 en paquetes de lo grueso a lo fino (en Safari de iPhone mover
  // currentTime de un video deja la imagen en negro). Si el MP4 falla, la computadora usa los paquetes 1440x810.
  let N = 1294;
  const FPS_ANCLAS = 24;
  let ESC = 1;  // cuadros del paquete por cuadro de ancla: el manifest trae sus fps (48 en celular)
  const VERSION = '?v=' + GC.v;  // GC_RECORRIDO_V en functions.php: subirlo con cada recorrido nuevo (el navegador cachea los archivos)
  const dir = matchMedia('(max-aspect-ratio: 1/1)').matches ? 'v' : 'h';
  let usarVideo = dir === 'h';
  let peli = document.createElement('video');
  const canvas = document.getElementById('film');
  const ctx = canvas.getContext('2d');
  const blobs = [];
  let cargados = 0, paraMostrar = N;
  // La página se muestra con los primeros cuadros del primer paquete (~150 KB), sin esperar el paquete entero.
  const MIN_CUADROS = 4;
  // Antes de que la persona se mueva se bajan solo los primeros cuadros del primer paquete (~0,9 MB de 6,9 MB).
  const CUADROS_ANTES = 24;
  // Ahorro de datos o red 2G: se baja menos recorrido (más saltado, pero mucho más liviano).
  const con = navigator.connection;
  const ahorro = !!(con && (con.saveData || /(^|-)2g$/.test(con.effectiveType || '')));
  // El resto del recorrido (decenas de MB) se baja recién cuando la persona empieza a moverse por la página.
  const alInteractuar = new Promise(ok => {
    const evs = ['scroll', 'wheel', 'touchstart', 'pointerdown', 'keydown'];
    // Sin captura: solo cuenta el desplazamiento de la página, no el de un carrusel o una cinta.
    const listo = () => { evs.forEach(e => removeEventListener(e, listo)); ok(); };
    evs.forEach(e => addEventListener(e, listo, { passive: true }));
  });

  raiz.classList.add('cargando');
  scrollTo(0, 0);
  const barra = document.getElementById('loader-barra'), txt = document.getElementById('loader-txt');
  let mostrada = false, saltar = false;
  function progreso() {
    const pct = Math.min(100, Math.floor(cargados / paraMostrar * 100));
    barra.style.width = pct + '%';
    txt.textContent = `${GC.t.cargando} · ${pct}%`;
    if (cargados >= paraMostrar) esperarInicio();
  }
  function esperarInicio() {
    if (mostrada) return;
    if (!bitmaps.has(0)) return setTimeout(esperarInicio, 100);
    mostrar();
  }
  function mostrar() {
    if (mostrada) return;
    mostrada = true;
    raiz.classList.remove('cargando');
    requestAnimationFrame(() => raiz.classList.add('listo'));
    document.getElementById('loader').classList.add('fuera');
    medir();
    irAlAncla();
  }
  // Con #seccion en la dirección (al cambiar de idioma o desde un enlace externo) se abre en esa sección,
  // no en la portada. Se hace al sacar la pantalla de carga, cuando la página ya se puede desplazar.
  function irAlAncla() {
    let el = null;
    try { el = location.hash.length > 1 && document.getElementById(decodeURIComponent(location.hash.slice(1))); } catch (e) {}
    if (!el || !el.getClientRects().length) return;
    const st = raiz.style.scrollBehavior;
    raiz.style.scrollBehavior = 'auto';  // salto directo (el CSS tiene desplazamiento suave)
    el.scrollIntoView(true);
    raiz.style.scrollBehavior = st;
    saltar = true;  // el recorrido va directo a ese punto, sin recorrer todo el video desde el principio
  }
  setTimeout(mostrar, 15000);  // red muy lenta: se muestra igual con lo que haya

  // Computadora: el navegador baja el MP4 de a partes (preload auto) y el scroll mueve currentTime.
  if (usarVideo) {
    peli.muted = true; peli.playsInline = true; peli.preload = 'auto';
    peli.setAttribute('playsinline', ''); peli.setAttribute('aria-hidden', 'true');
    peli.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block';
    canvas.style.display = 'none';
    document.querySelector('.film').appendChild(peli);
    const avance = () => {
      if (!peli.duration || !peli.buffered.length) return;
      const pct = Math.min(100, Math.round(peli.buffered.end(peli.buffered.length - 1) / Math.min(8, peli.duration) * 100));
      barra.style.width = pct + '%'; txt.textContent = `${GC.t.cargando} · ${pct}%`;
    };
    peli.addEventListener('progress', avance);
    peli.addEventListener('loadeddata', () => { avance(); mostrar(); }, { once: true });
    peli.addEventListener('error', e => {  // sin MP4: vuelve a los cuadros
      if (e.target !== peli) return;  // el video viejo que se descarta al pasar a la copia local
      usarVideo = false; peli.remove(); canvas.style.display = ''; cargarPaquetes();
    }, { once: true });
    const SRC_VIDEO = GC.tema + '/video/recorrido-1080p60.mp4' + VERSION;
    peli.src = SRC_VIDEO;
    // El navegador baja el MP4 de a partes y una búsqueda hacia una parte que no llegó puede quedar colgada.
    // Se baja el archivo entero en segundo plano y, al terminar, se cambia a una copia local (búsquedas
    // instantáneas). El cambio usa un segundo <video> que se muestra recién cuando ya tiene el cuadro actual.
    // Esa copia completa pesa decenas de MB: se pide al primer gesto y no con ahorro de datos.
    if (!ahorro) alInteractuar.then(async () => {
      try {
        const r = await fetch(SRC_VIDEO);
        if (!r.ok) return;
        const url = URL.createObjectURL(new Blob([await r.blob()], { type: 'video/mp4' }));
        const local = peli.cloneNode(false);
        local.removeAttribute('src');
        local.muted = true; local.playsInline = true; local.preload = 'auto';
        local.style.opacity = '0';
        local.src = url;
        local.addEventListener('loadedmetadata', () => { local.currentTime = peli.currentTime; }, { once: true });
        local.addEventListener('seeked', () => {
          local.style.opacity = '';
          const viejo = peli; peli = local;
          viejo.remove(); viejo.removeAttribute('src'); viejo.load();
        }, { once: true });
        peli.after(local);
      } catch (e) {}  // sin copia local se sigue con la descarga de a partes
    });
  }

  // Cada paquete (o un tramo de cuadros de él) se lee a medida que llega: los cuadros quedan disponibles uno
  // por uno, en el orden del manifest, que es el de los bytes. Un tramo se pide con Range; si el servidor
  // no lo acepta y manda el archivo entero, se corta la descarga al llegar al último cuadro del tramo.
  async function bajarPaquete(base, p, desde = 0, hasta = p.c.length, intentos = 3) {
    const cs = p.c.slice(desde, hasta);
    if (!cs.length) return;
    const ini = cs[0][1], fin = cs[cs.length - 1][1] + cs[cs.length - 1][2];
    const tramo = desde > 0 || hasta < p.c.length;
    for (let i = 0; i < intentos; i++) {
      try {
        const r = await fetch(base + p.f + VERSION, tramo ? { headers: { Range: `bytes=${ini}-${fin - 1}` } } : undefined);
        if (!r.ok) throw new Error(r.status);
        const off0 = r.status === 206 ? ini : 0;  // 200: llegó el archivo desde el byte 0
        const total = fin - off0;
        const buf = new Uint8Array(total);
        let llego = 0, hechos = 0;
        const separar = () => {
          let nuevos = 0;
          while (hechos < cs.length) {
            const [n, off, len] = cs[hechos];
            if (off - off0 + len > llego) break;
            if (!blobs[n]) { blobs[n] = new Blob([buf.subarray(off - off0, off - off0 + len)], { type: 'image/webp' }); cargados++; nuevos++; }
            hechos++;
          }
          if (nuevos) progreso();
        };
        const lector = r.body && r.body.getReader && r.body.getReader();
        if (lector) {
          while (llego < total) {
            const { done, value } = await lector.read();
            if (done) break;
            const n = Math.min(value.length, total - llego);
            buf.set(n === value.length ? value : value.subarray(0, n), llego); llego += n;
            separar();
          }
          if (llego >= total) lector.cancel().catch(() => {});  // lo que sobre (archivo entero) no se baja
        } else {
          const todo = new Uint8Array(await r.arrayBuffer());
          const n = Math.min(total, todo.length);
          buf.set(todo.subarray(0, n)); llego = n; separar();
        }
        if (hechos < cs.length) throw new Error('incompleto');
        return;
      } catch (e) { await new Promise(r => setTimeout(r, 800 * (i + 1))); }
    }
    cargados += cs.filter(([n]) => !blobs[n]).length; progreso();  // sin esos cuadros: que no trabe la carga
  }
  async function cargarPaquetes() {
    const base = `${GC.tema}/pack/${dir}/`;
    let man;
    try { man = await (await fetch(base + 'manifest.json' + VERSION)).json(); } catch (e) { return mostrar(); }
    N = man.n;
    ESC = (man.fps || FPS_ANCLAS) / FPS_ANCLAS;
    medir();
    const [primero, ...resto] = man.paquetes;
    paraMostrar = Math.min(MIN_CUADROS, primero.c.length);
    const antes = Math.min(CUADROS_ANTES, primero.c.length);
    // Al primer gesto: el resto del primer paquete y después los demás (con ahorro de datos, solo uno más).
    const cola = [{ p: primero, desde: antes }, ...(ahorro ? resto.slice(0, 1) : resto).map(p => ({ p, desde: 0 }))];
    const trabajador = async () => { while (cola.length) { const t = cola.shift(); await bajarPaquete(base, t.p, t.desde); } };
    alInteractuar.then(() => Promise.all([trabajador(), trabajador()]));
    await bajarPaquete(base, primero, 0, antes);
  }
  if (!usarVideo) cargarPaquetes();

  // Decodificación por adelantado (ImageBitmap) solo en una ventana alrededor de la cámara.
  const bitmaps = new Map(), decodificando = new Set();
  const ATRAS = 16, ADELANTE = 36;
  function mantenerVentana(a, sentido) {
    const desde = a - (sentido > 0 ? ATRAS / 2 : ADELANTE), hasta = a + (sentido > 0 ? ADELANTE : ATRAS / 2);
    for (const [n, bm] of bitmaps) if (n < desde - 8 || n > hasta + 8) { bm.close && bm.close(); bitmaps.delete(n); }
    for (let d = 0; d <= Math.max(ADELANTE, ATRAS) && decodificando.size < 6; d++) {
      for (const n of [a + d * sentido, a - d * sentido]) {
        if (n < desde || n > hasta || n < 0 || n >= N) continue;
        if (!blobs[n] || bitmaps.has(n) || decodificando.has(n)) continue;
        decodificando.add(n);
        createImageBitmap(blobs[n]).then(bm => bitmaps.set(n, bm), () => {}).finally(() => decodificando.delete(n));
        if (decodificando.size >= 6) break;
      }
    }
  }

  // Anclas: cada [data-cuadro] fija el cuadro que se ve cuando su borde superior llega arriba de la pantalla.
  // Entre dos anclas el recorrido avanza parejo; dos anclas con el mismo cuadro = el video se queda quieto.
  let anclas = [];
  function medir() {
    anclas = [...document.querySelectorAll('[data-cuadro]')].filter(el => el.getClientRects().length)
      .map(el => [el.getBoundingClientRect().top + scrollY, Math.min((N - 1) / ESC, Number(el.dataset.cuadro))])
      .sort((a, b) => a[0] - b[0]);
  }
  function cuadroPara(y) {
    if (!anclas.length) return 0;
    if (y <= anclas[0][0]) return anclas[0][1];
    for (let i = 1; i < anclas.length; i++) {
      const [y1, c1] = anclas[i];
      if (y < y1) { const [y0, c0] = anclas[i - 1]; return c0 + (c1 - c0) * ((y - y0) / Math.max(1, y1 - y0)); }
    }
    return anclas[anclas.length - 1][1];
  }
  addEventListener('resize', medir);
  addEventListener('load', medir);
  if ('ResizeObserver' in window) new ResizeObserver(medir).observe(document.body);
  medir();

  let ultimo = -1;
  function ajustar() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(innerWidth * dpr);
    canvas.height = Math.round(innerHeight * dpr);
    ultimo = -1;
  }
  addEventListener('resize', ajustar);
  ajustar();

  function pintar(im, alpha) {
    const cw = canvas.width, ch = canvas.height;
    const esc = Math.max(cw / im.width, ch / im.height);
    const w = im.width * esc, h = im.height * esc;
    ctx.globalAlpha = alpha;
    ctx.drawImage(im, (cw - w) / 2, (ch - h) / 2, w, h);
  }

  // Pasos de monitoreo: se encienden al pasar por el centro; la línea crece con el avance.
  const pasos = [...document.querySelectorAll('.paso')], listaPasos = document.getElementById('pasos');
  const sepImg = document.getElementById('sep-img');
  // Cápsula de navegación: marca la sección del menú en la que se está; barra de progreso arriba.
  const MENU = [['#quienes', ['quienes']], ['#trabajo', ['trabajo']],
    ['#proyecto', ['proyecto', 'mapa', 'territorio', 'gobernanza', 'voces', 'biodiversidad', 'clima']],
    ['#centro', ['centro']], ['#impacto', ['impacto']], ['#contacto', ['accion', 'contacto']]];
  const enlacesMenu = MENU.map(([h]) => document.querySelector(`.nav > li > a[href="${h}"]`));
  const seccionesMenu = MENU.flatMap(([, ids], i) => ids.map(id => [document.getElementById(id), i]))
    .sort((x, y) => x[0].compareDocumentPosition(y[0]) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1);  // orden de la página
  const barraProg = document.getElementById('progreso');
  let menuActivo = -2;
  function espiar() {
    let act = -1;
    for (const [el, i] of seccionesMenu) if (el.getBoundingClientRect().top < innerHeight * .4) act = i;
    if (act !== menuActivo) { menuActivo = act; enlacesMenu.forEach((a, i) => a.classList.toggle('activa', i === act)); }
    const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    barraProg.style.transform = `scaleX(${(scrollY / max).toFixed(4)})`;
  }

  let pos = 0, sentido = 1, inicioBusqueda = 0;
  function frame() {
    const meta = cuadroPara(scrollY);
    if (saltar) { pos = meta; saltar = false; }
    if (Math.abs(meta - pos) > .5) sentido = meta > pos ? 1 : -1;
    pos = reduce ? meta : pos + (meta - pos) * .1;
    const pc = usarVideo ? pos : pos * ESC;  // posición en cuadros del paquete
    const a = Math.floor(pc);
    if (usarVideo) {
      // Un salto por vez: mientras el video busca no se le pide otro, así no se encolan búsquedas.
      const t = pos / FPS_ANCLAS;
      const ahora = performance.now();
      // Búsqueda trabada (parte del video que no llegó): se vuelve a pedir en vez de esperar para siempre.
      if (peli.seeking && ahora - inicioBusqueda > 1500) inicioBusqueda = 0;
      if (peli.readyState >= 1 && (!peli.seeking || !inicioBusqueda) && Math.abs(peli.currentTime - t) > .02) {
        peli.currentTime = Math.min(t, (peli.duration || t) - .05);
        inicioBusqueda = ahora;
      }
    } else mantenerVentana(a, sentido);
    if (!usarVideo && Math.abs(pc - ultimo) > .001) {
      let lo = -1, hi = -1;
      for (let d = 0; d <= 16 && (lo < 0 || hi < 0); d++) {
        if (lo < 0 && bitmaps.has(a - d)) lo = a - d;
        if (hi < 0 && d > 0 && bitmaps.has(a + d)) hi = a + d;
      }
      if (lo >= 0) {
        pintar(bitmaps.get(lo), 1);
        if (hi > lo) { const f = (pc - lo) / (hi - lo); if (f > .01) pintar(bitmaps.get(hi), Math.min(1, f)); }
        ctx.globalAlpha = 1;
        ultimo = pc;
      } else if (hi >= 0) { pintar(bitmaps.get(hi), 1); ctx.globalAlpha = 1; }
    }
    cab.classList.toggle('solida', scrollY > innerHeight * .6);
    espiar();
    const h = innerHeight;
    for (const p of pasos) { const b = p.getBoundingClientRect(); p.classList.toggle('activo', b.top < h * .6); }
    const bl = listaPasos.getBoundingClientRect();
    listaPasos.style.setProperty('--avance', Math.min(1, Math.max(0, (h * .6 - bl.top) / bl.height)).toFixed(3));
    if (!reduce) { const bs = sepImg.parentElement.getBoundingClientRect(); if (bs.bottom > 0 && bs.top < h) sepImg.style.setProperty('--sc', (1.12 - .1 * Math.min(1, Math.max(0, (h - bs.top) / (h + bs.height)))).toFixed(4)); }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
