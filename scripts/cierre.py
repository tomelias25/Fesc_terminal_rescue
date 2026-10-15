#!/usr/bin/env python3
"""Cierre mensual de afiliados activos.

Lee los CSV de data/ SIN modificarlos y genera en output/:
  - afiliados_activos.csv
  - excepciones.csv
  - totales.txt

Las reglas estan en docs/diccionario.md (seccion "Reglas del cierre").
Es repetible: no mueve ni borra entradas, sobrescribe las salidas y
produce siempre el mismo resultado con los mismos datos.
"""

import csv
import re
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
SALIDA = RAIZ / "output"


def leer_csv(nombre, delimitador=","):
    with open(DATA / nombre, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=delimitador))


# Regla 6: equivalencia entre la situacion de Caja Oriente y nuestro estado.
SITUACION_A_ESTADO = {"VIGENTE": "A", "RETIRADO": "I"}

# Regla 5: formatos de fecha aceptados (se normalizan a YYYY-MM-DD).
PATRONES_FECHA = (
    (re.compile(r"^\d{4}-\d{2}-\d{2}$"), "%Y-%m-%d"),
    (re.compile(r"^\d{2}/\d{2}/\d{4}$"), "%d/%m/%Y"),
    (re.compile(r"^\d{8}$"), "%Y%m%d"),
)


def normalizar_fecha(texto):
    """Devuelve la fecha como YYYY-MM-DD, o None si no es una fecha real."""
    texto = texto.strip()
    for patron, formato in PATRONES_FECHA:
        if patron.match(texto):
            try:
                return datetime.strptime(texto, formato).strftime("%Y-%m-%d")
            except ValueError:
                return None
    return None


def nombre_completo(fila):
    partes = [fila["NOM1"], fila["NOM2"], fila["APE1"], fila["APE2"]]
    return " ".join(p.strip() for p in partes if p and p.strip())


def main():
    afiliados_raw = leer_csv("AFI_MAE.csv")
    empresas = {e["COD_EMP"].strip(): e["NOM_EMP"].strip() for e in leer_csv("EMPRESA.csv")}
    beneficiarios = leer_csv("AFI_BEN.csv")
    aportes = leer_csv("APORTES.csv")

    excepciones = []  # tuplas (documento, tipo, detalle)

    # Regla 1: cada documento distinto es un afiliado; se conserva la primera
    # aparicion y el duplicado se reporta una sola vez por documento.
    afiliados = {}
    repeticiones = {}
    for fila in afiliados_raw:
        doc = fila["NRO_DOC"].strip()
        if doc in afiliados:
            repeticiones[doc] = repeticiones.get(doc, 1) + 1
        else:
            afiliados[doc] = fila
    for doc, veces in repeticiones.items():
        excepciones.append((doc, "DUPLICADO", "aparece {0} veces; se conserva la primera".format(veces)))

    # Regla 4 y conteo: beneficiarios por afiliado; los huerfanos se reportan.
    conteo_beneficiarios = {}
    for b in beneficiarios:
        doc_afiliado = b["NRO_DOC_AFI"].strip()
        if doc_afiliado in afiliados:
            conteo_beneficiarios[doc_afiliado] = conteo_beneficiarios.get(doc_afiliado, 0) + 1
        else:
            excepciones.append((
                b["NRO_DOC_BEN"].strip(),
                "BENEFICIARIO_HUERFANO",
                "el afiliado {0} no existe en AFI_MAE".format(doc_afiliado),
            ))

    # Regla 7: ultimo aporte = mayor PERIODO pagado (YYYY-MM se ordena como texto).
    ultimo_aporte = {}
    for a in aportes:
        doc = a["NRO_DOC"].strip()
        periodo = a["PERIODO"].strip()
        if periodo and periodo > ultimo_aporte.get(doc, ""):
            ultimo_aporte[doc] = periodo

    # Reglas 2 y 3: estado valido (A / I) y empresa valida para los activos.
    activos = []
    inactivos = 0
    for doc, fila in afiliados.items():
        estado = fila["EST_AFI"].strip()
        if estado == "I":
            inactivos += 1
            continue
        if estado != "A":
            excepciones.append((doc, "CODIGO_INVALIDO", "estado '{0}' no es A ni I".format(estado)))
            continue
        cod_empresa = fila["COD_EMP"].strip()
        if cod_empresa not in empresas:
            detalle = "COD_EMP '{0}' no existe en EMPRESA".format(cod_empresa) if cod_empresa else "COD_EMP vacio"
            excepciones.append((doc, "SIN_EMPRESA", detalle))
            continue
        activos.append([
            doc,
            nombre_completo(fila),
            "ACTIVO",
            cod_empresa,
            empresas[cod_empresa],
            conteo_beneficiarios.get(doc, 0),
            ultimo_aporte.get(doc, ""),
        ])

    # Regla 5: la fecha invalida se reporta, pero el afiliado NO sale de los totales.
    for doc, fila in afiliados.items():
        if normalizar_fecha(fila["FEC_AFI"]) is None:
            excepciones.append((doc, "FECHA_INVALIDA", "FEC_AFI '{0}' no es una fecha valida".format(fila["FEC_AFI"].strip())))

    # Regla 6: cruce con Caja Oriente. Sus documentos vienen con ceros a la izquierda
    # (12 digitos), asi que se comparan sin ceros iniciales.
    estado_por_documento = {doc.lstrip("0"): fila["EST_AFI"].strip() for doc, fila in afiliados.items()}
    for fila in leer_csv("extracto_caja_oriente.csv", ";"):
        doc = fila["id_afiliado"].strip().lstrip("0")
        situacion = fila["situacion"].strip().upper()
        if doc not in estado_por_documento:
            excepciones.append((doc, "CRUCE_NO_COINCIDE", "el documento no existe en AFI_MAE"))
        elif estado_por_documento[doc] != SITUACION_A_ESTADO.get(situacion):
            excepciones.append((doc, "CRUCE_NO_COINCIDE", "Caja Oriente dice {0} y nuestro estado es '{1}'".format(situacion, estado_por_documento[doc])))

    SALIDA.mkdir(exist_ok=True)

    with open(SALIDA / "afiliados_activos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["documento", "nombre", "estado", "cod_empresa", "empresa", "beneficiarios", "ultimo_aporte"])
        w.writerows(activos)

    with open(SALIDA / "excepciones.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["documento", "tipo", "detalle"])
        w.writerows(excepciones)

    with open(SALIDA / "totales.txt", "w", encoding="utf-8") as f:
        f.write("total_afiliados={0}\n".format(len(afiliados)))
        f.write("activos={0}\n".format(len(activos)))
        f.write("inactivos={0}\n".format(inactivos))
        f.write("excepciones={0}\n".format(len(excepciones)))

    print("Cierre terminado: {0} afiliados, {1} activos, {2} inactivos, {3} excepciones".format(
        len(afiliados), len(activos), inactivos, len(excepciones)))


if __name__ == "__main__":
    main()