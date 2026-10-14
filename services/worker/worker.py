"""cierre-worker: concilia periódicamente el conteo de afiliados del cierre."""

import os
import sys
import time
from datetime import datetime, timezone

import psycopg2


def log(level, message):
    stamp = datetime.now(timezone.utc).strftime("[%Y-%m-%dT%H:%M:%SZ]")
    print("{0} [{1}] {2}".format(stamp, level, message), flush=True)


def load_interval():
    raw = os.environ.get("WORKER_INTERVAL_SECONDS", "")
    try:
        return int(raw)
    except ValueError:
        log("ERROR", "codigo=CIE-1107 WORKER_INTERVAL_SECONDS debe ser un entero de segundos; valor recibido: '{0}'".format(raw))
        sys.exit(1)


def reconcile():
    conn = psycopg2.connect(
        host=os.environ.get("DATABASE_HOST", "localhost"),
        port=int(os.environ.get("DATABASE_PORT", "5432")),
        dbname=os.environ.get("DATABASE_NAME", "cierre"),
        user=os.environ.get("DATABASE_USER", "cierre"),
        password=os.environ.get("DATABASE_PASSWORD", ""),
        connect_timeout=3,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*), count(DISTINCT nro_doc) FROM afi_mae")
            total, distinct = cur.fetchone()
    finally:
        conn.close()
    log("INFO", "conciliacion registros={0} documentos_distintos={1}".format(total, distinct))


def main():
    interval = load_interval()
    log("INFO", "cierre-worker iniciado; intervalo={0}s".format(interval))
    while True:
        try:
            reconcile()
        except psycopg2.OperationalError as exc:
            log("ERROR", "codigo=CIE-2210 sin conexión a la base: {0}".format(str(exc).strip().splitlines()[0]))
        time.sleep(interval)


if __name__ == "__main__":
    main()
