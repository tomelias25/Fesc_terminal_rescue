#!/usr/bin/env bash
# Punto de entrada del cierre mensual. El validador ejecuta este archivo.
cd "$(dirname "$0")"
./scripts/cierre.sh
