#!/bin/bash
# Prepara e instala WordPress ANTES de arrancar Apache: así nadie puede adelantarse en /wp-admin/install.php.
set -e
# El entrypoint oficial solo copia WordPress y escribe wp-config.php si el comando empieza con "apache2";
# gc-preparar es un comando vacío con ese prefijo para correr solo esa parte.
docker-entrypoint.sh apache2-gc-preparar
gc-instalar
exec docker-entrypoint.sh "$@"
