FROM wordpress:6.8.3-php8.3-apache

COPY --from=wordpress:cli-2.12.0-php8.3 /usr/local/bin/wp /usr/local/bin/wp
RUN printf 'upload_max_filesize=64M\npost_max_size=64M\nmemory_limit=256M\n' > /usr/local/etc/php/conf.d/subidas.ini

# El tema va en la imagen (no en un volumen): actualizar el tema = reconstruir la imagen.
COPY tema/greencarbon /usr/src/wordpress/wp-content/themes/greencarbon
COPY docker/instalar.sh /usr/local/bin/gc-instalar
COPY docker/entrypoint.sh /usr/local/bin/gc-entrypoint
RUN printf '#!/bin/sh\nexit 0\n' > /usr/local/bin/apache2-gc-preparar \
 && chmod +x /usr/local/bin/gc-instalar /usr/local/bin/gc-entrypoint /usr/local/bin/apache2-gc-preparar

ENTRYPOINT ["gc-entrypoint"]
CMD ["apache2-foreground"]
