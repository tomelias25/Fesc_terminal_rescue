#!/usr/bin/env bash
# Cierre mensual: delega en cierre.py (repetible, no modifica data/)
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/cierre.py