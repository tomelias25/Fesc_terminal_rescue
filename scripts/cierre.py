#!/usr/bin/env python3
"""Cierre mensual de afiliados activos (etapa 1).

Lee los CSV de data/ SIN modificarlos y genera en output/:
  - afiliados_activos.csv
  - excepciones.csv
  - totales.txt

Las reglas estan en docs/diccionario.md (seccion "Reglas del cierre").
Es repetible: no mueve ni borra entradas, sobrescribe las salidas y
produce siempre el mismo resultado con los mismos datos.
"""

import csv
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
SALIDA = RAIZ / "output"


def leer_csv(nombre, delimitador=","):
    with open(DATA / nombre, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=delimitador))


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

    # ETAPA 2 (incidente 7): normalizar FEC_AFI y reportar FECHA_INVALIDA.
    # ETAPA 3 (incidente 8): cruce con extracto_caja_oriente.csv.

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