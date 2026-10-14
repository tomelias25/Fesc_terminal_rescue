#!/usr/bin/env bash
# Punto de entrada del cierre mensual. El validador ejecuta este archivo.
set -euo pipefail
cd "$(dirname "$0")"
./scripts/top_error.sh
./scripts/cierre.sh
