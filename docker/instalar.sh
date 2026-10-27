#!/bin/bash
# Corre en cada arranque, antes de Apache. Instala WordPress la primera vez y deja el tema y las opciones al día.
set -e
cd /var/www/html
wp() { command wp --allow-root "$@"; }

for i in $(seq 90); do
  php -r '
    [$h, $p] = array_pad(explode(":", getenv("WORDPRESS_DB_HOST")), 2, 3306);
    exit(@new mysqli($h, getenv("WORDPRESS_DB_USER"), getenv("WORDPRESS_DB_PASSWORD"), getenv("WORDPRESS_DB_NAME"), (int) $p) ? 0 : 1);' 2>/dev/null && break
  [ "$i" = 90 ] && { echo "[gc-instalar] la base de datos no responde" >&2; exit 1; }
  sleep 2
done

# /var/www/html es un volumen de la imagen oficial: sin esto, una imagen nueva seguiría sirviendo el tema viejo.
rm -rf wp-content/themes/greencarbon
cp -a /usr/src/wordpress/wp-content/themes/greencarbon wp-content/themes/
chown -R www-data:www-data wp-content/themes/greencarbon

if ! wp core is-installed 2>/dev/null; then
  wp core install --url="$GC_URL" --title="Green Carbon Bolivia" \
    --admin_user="$GC_ADMIN_USER" --admin_password="$GC_ADMIN_PASSWORD" --admin_email="$GC_ADMIN_EMAIL" --skip-email
  wp language core install es_ES --activate || echo "[gc-instalar] sin internet: el admin queda en inglés"
  wp option update timezone_string America/La_Paz
  wp theme activate greencarbon
  wp theme delete --all || true                    # deja solo el tema activo
  wp plugin delete --all || true
  chown -R www-data:www-data wp-content
fi

# Idempotente: se reaplica en cada arranque por si un arranque anterior quedó a medias.
wp theme activate greencarbon
wp option update blog_public "${GC_INDEXAR:-0}"     # 0 = noindex, igual que el sitio actual
wp rewrite structure '/%postname%/' >/dev/null
echo "[gc-instalar] Listo: $GC_URL/wp-admin (usuario $GC_ADMIN_USER)."
