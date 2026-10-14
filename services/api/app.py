"""cierre-api: consulta de afiliados para Subsidios.

GET /afiliados/{documento} -> {"documento", "nombre", "estado", "empresa"}
"""

import json
import logging
import os
import re
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import psycopg2

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(levelname)s [cierre-api] %(message)s")
log = logging.getLogger("cierre-api")

ESTADOS = {"A": "ACTIVO", "I": "INACTIVO"}
ROUTE = re.compile(r"^/afiliados/([0-9]+)$")

QUERY = """
SELECT a.nro_doc, a.nom1, a.nom2, a.ape1, a.ape2, a.est_afi, e.nom_emp
FROM afi_mae a
JOIN empresa e ON e.cod_emp = a.cod_emp
WHERE a.nro_doc = %s
LIMIT 1
"""


def connect():
    return psycopg2.connect(
        host=os.environ.get("DATABASE_HOST", "localhost"),
        port=int(os.environ.get("DATABASE_PORT", "5432")),
        dbname=os.environ.get("DATABASE_NAME", "cierre"),
        user=os.environ.get("DATABASE_USER", "cierre"),
        password=os.environ.get("DATABASE_PASSWORD", ""),
        connect_timeout=3,
    )


def find_member(documento):
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(QUERY, (documento,))
            row = cur.fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    nro_doc, nom1, nom2, ape1, ape2, est_afi, nom_emp = row
    nombre = nom1 + " " + nom2 + " " + ape1 + " " + ape2
    return {"documento": nro_doc, "nombre": nombre.strip(), "estado": ESTADOS[est_afi], "empresa": nom_emp}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"status": "UP"})
        match = ROUTE.match(self.path)
        if not match:
            return self._send(404, {"error": "ruta no encontrada"})
        documento = match.group(1)
        try:
            member = find_member(documento)
        except psycopg2.OperationalError as exc:
            log.error("CIE-2210 No hay conexión con la base de datos: %s", str(exc).strip())
            return self._send(503, {"error": "base de datos no disponible"})
        except Exception:
            log.error("CIE-5003 Error interno consultando afiliado documento=%s\n%s", documento, traceback.format_exc())
            return self._send(500, {"error": "error interno"})
        if member is None:
            return self._send(404, {"error": "afiliado no encontrado"})
        log.info("GET /afiliados/%s 200", documento)
        return self._send(200, member)

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    port = int(os.environ.get("API_INTERNAL_PORT", "8081"))
    log.info("cierre-api escuchando en el puerto %s (base: %s)", port, os.environ.get("DATABASE_HOST"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
