#!/usr/bin/env bash
# Devuelve el entorno al estado inicial: borra contenedores, volúmenes (la base se
# recarga desde data/) y la carpeta output/. No modifica tu código ni tu .env.
set -euo pipefail
cd "$(dirname "$0")"

echo ">> Deteniendo servicios y borrando volúmenes"
docker compose down -v --remove-orphans

echo ">> Restaurando datos originales y limpiando output/"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git checkout -- data 2>/dev/null || true
fi
rm -rf output

if [ ! -f .env ]; then
    cp .env.example .env
fi

echo ">> Levantando servicios"
docker compose up -d --build
docker compose ps
