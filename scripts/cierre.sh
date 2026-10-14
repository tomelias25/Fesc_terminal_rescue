#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Cierre mensual de afiliados activos (script heredado de Operaciones).
# Autor original: equipo de sistemas 2019. Última modificación: "temporal".
# ---------------------------------------------------------------------------
set -e

ENTRADA=/opt/cierre/entrada
SALIDA=output

mkdir $SALIDA

echo "Leyendo afiliados desde $ENTRADA/AFI_MAE.csv"

# Archivo de activos para Subsidios
echo "documento,nombre,estado,cod_empresa,empresa,beneficiarios,ultimo_aporte" > $SALIDA/afiliados_activos.csv
awk -F',' 'NR > 1 && $7 == "A" { print $1 "," $3 " " $4 " " $5 " " $6 ",ACTIVO," $8 ",,0," }' \
    $ENTRADA/AFI_MAE.csv >> $SALIDA/afiliados_activos.csv

# TODO: nombre de la empresa desde EMPRESA.csv
# TODO: contar beneficiarios desde AFI_BEN.csv
# TODO: último aporte desde APORTES.csv (YYYY-MM)
# TODO: excepciones (lo pidió Auditoría, nunca se terminó)
# TODO: cruce con el extracto de Caja Oriente

TOTAL=$(tail -n +2 $ENTRADA/AFI_MAE.csv | wc -l)
ACTIVOS=$(tail -n +2 $SALIDA/afiliados_activos.csv | wc -l)
echo "total_afiliados=$TOTAL" >> $SALIDA/totales.txt
echo "activos=$ACTIVOS" >> $SALIDA/totales.txt

# El archivo de entrada ya fue procesado
mkdir -p $ENTRADA/procesados
mv $ENTRADA/AFI_MAE.csv $ENTRADA/procesados/

echo "Cierre terminado"
