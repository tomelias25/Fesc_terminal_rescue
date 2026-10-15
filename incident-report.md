# Informe de incidentes — Terminal Rescue

Pareja: Andres Leonardo Ortega Diaz y Pedro Daniel. Repositorio: https://github.com/tomelias25/Fesc_terminal_rescue

## Incidente 1
- **Síntoma:** El servicio cierre-worker no se mantenía arriba: `docker compose ps -a` lo mostraba en estado Exited (1) mientras cierre-db y cierre-api seguían corriendo.
- **Diagnóstico:** El log del contenedor mostraba el error CIE-1107: WORKER_INTERVAL_SECONDS debe ser un entero de segundos y el valor recibido era '30s'. La variable estaba mal escrita en `.env.example`, y el worker la convierte a número al arrancar y se cae.
- **Comandos:** `docker compose ps -a`, `docker compose logs cierre-worker | tail -5`, `sed -i 's/^WORKER_INTERVAL_SECONDS=.*/WORKER_INTERVAL_SECONDS=30/' .env.example`, `cp .env.example .env`, `docker compose up -d --force-recreate cierre-worker`
- **Solución:** Se cambió el valor a 30 (entero, sin la letra s) en `.env.example`, se copió a `.env` y se recreó el contenedor. El worker quedó en Up y el log muestra "cierre-worker iniciado; intervalo=30s".
- **Evidencia:** evidence/01-worker.txt

## Incidente 2
- **Síntoma:** La API respondía HTTP 503 con el mensaje "base de datos no disponible" a cualquier consulta de afiliado.
- **Diagnóstico:** El log de cierre-api repetía el error CIE-2210: could not translate host name "cierre-database". El servicio de base de datos en `docker-compose.yml` se llama cierre-db, pero DATABASE_HOST apuntaba a un nombre que no existe en la red de Docker.
- **Comandos:** `curl -i localhost:8081/afiliados/3756530718`, `docker compose logs cierre-api --tail 5`, `sed -i 's/^DATABASE_HOST=.*/DATABASE_HOST=cierre-db/' .env.example`, `cp .env.example .env`, `docker compose up -d --force-recreate`
- **Solución:** Se corrigió DATABASE_HOST a cierre-db en `.env.example` y se recrearon los contenedores. La API dejó de responder 503 y conectó con PostgreSQL; esto dejó a la vista el error 500 del incidente 6.
- **Evidencia:** evidence/02-api.txt

## Incidente 3
- **Síntoma:** `./run.sh` terminaba con código de salida 2 y no generaba los archivos de `output/`.
- **Diagnóstico:** El script heredado `scripts/cierre.sh` fallaba con "awk: fatal: cannot open file `/opt/cierre/entrada/AFI_MAE.csv'". La variable ENTRADA apuntaba a una ruta que no existe en este entorno, mientras que los archivos de entrada están en la carpeta `data/` del repositorio.
- **Comandos:** `./run.sh`, `./validator check --quick`, `ls data/`, `git diff scripts/cierre.sh`, `chmod +x run.sh reset.sh scripts/cierre.sh validator`
- **Solución:** Se cambió ENTRADA a `data`, de modo que el cierre lee los CSV del repositorio. Después el cierre se reescribió en Python (`scripts/cierre.py`), que calcula la ruta a `data/` desde la raíz del repositorio y no depende de rutas del servidor.
- **Evidencia:** evidence/03-entrada.txt

## Incidente 4
- **Síntoma:** No existía `output/top_error.txt`: nadie sabía cuál era el error más frecuente de los logs.
- **Diagnóstico:** Hay tres logs con formatos distintos (api.log, worker.log y database.log, 11515 líneas en total). Por separado el error más repetido cambia de un archivo a otro, así que se contaron los códigos CIE-#### sobre los tres juntos. El código más frecuente es CIE-4012 con 1424 ocurrencias, seguido de CIE-5003 con 700. Se verificó que ninguna línea con CIE-4012 deja de ser de nivel ERROR y que los avisos W-### no se cuentan.
- **Comandos:** `wc -l logs/*.log`, `grep 'CIE-' logs/database.log | head -3`, `cat logs/api.log logs/worker.log logs/database.log | grep -o 'CIE-[0-9][0-9][0-9][0-9]' | sort | uniq -c | sort -rn | head -5`, `grep -c 'CIE-4012'`, `chmod +x scripts/top_error.sh`
- **Solución:** Se creó `scripts/top_error.sh`, que cuenta los errores de los tres logs con grep, sort, uniq y awk y escribe codigo_error y ocurrencias en `output/top_error.txt`. `run.sh` lo ejecuta antes del cierre, así que el resultado se recalcula en cada corrida.
- **Evidencia:** evidence/04-top-error.txt

## Incidente 5
- **Síntoma:** No existía `output/excepciones.csv` y los datos de calidad no se reportaban: duplicados, estados inválidos, afiliados sin empresa y beneficiarios sin afiliado.
- **Diagnóstico:** Las reglas del diccionario de datos indican que cada documento distinto es un afiliado (AFI_MAE trae filas repetidas), que solo A e I son estados válidos, que un activo necesita una empresa existente en EMPRESA y que un beneficiario debe tener un afiliado en AFI_MAE. El script heredado no aplicaba ninguna de estas reglas.
- **Comandos:** `python3 scripts/cierre.py`, `tail -n +2 output/excepciones.csv | cut -d, -f2 | sort | uniq -c`, `./validator check --quick`
- **Solución:** `scripts/cierre.py` conserva la primera aparición de cada documento y reporta DUPLICADO (20), CODIGO_INVALIDO (14), SIN_EMPRESA (18) y BENEFICIARIO_HUERFANO (15) en `output/excepciones.csv`, sin contarlos indebidamente como activos o inactivos.
- **Evidencia:** evidence/05-calidad-datos.txt

## Incidente 6
- **Síntoma:** Una vez que la API conectó a la base, `GET /afiliados/3756530718` respondía HTTP 500 con "error interno".
- **Diagnóstico:** El log de cierre-api mostraba un traceback con "TypeError: can only concatenate str (not NoneType) to str" en la función find_member de `app.py`. Una consulta con `psql` a la tabla afi_mae mostró que ese afiliado no tiene segundo nombre (nom2 vacío, NULL en la base), y el código sumaba los cuatro campos de nombre sin controlar los valores nulos.
- **Comandos:** `curl -i localhost:8081/afiliados/3756530718`, `docker compose logs cierre-api --tail 30`, `docker compose exec cierre-db psql -U cierre -d cierre -c "SELECT * FROM afi_mae WHERE nro_doc='3756530718';"`, `docker compose up -d --build cierre-api`
- **Solución:** En `services/api/app.py` el nombre se arma con un join de las partes no vacías, y el estado usa ESTADOS.get con un valor por defecto para no fallar con códigos desconocidos, manteniendo la clave empresa de la respuesta. Se verificó con tres documentos reales (HTTP 200) y uno inexistente (HTTP 404).
- **Evidencia:** evidence/06-consulta.txt

## Incidente 7
- **Síntoma:** Algunas fechas de afiliación tenían formatos raros o eran imposibles y no se reportaban; el resultado de las fechas no coincidía con lo esperado.
- **Diagnóstico:** La columna FEC_AFI de AFI_MAE mezcla formatos YYYY-MM-DD, DD/MM/YYYY y YYYYMMDD, y además trae valores que no son fechas reales, como 2025-02-30, 31/13/2024, 00000000, SIN FECHA y N/A. Según el diccionario, una fecha que no se puede interpretar se reporta como FECHA_INVALIDA sin sacar al afiliado de los totales.
- **Comandos:** `python3 scripts/cierre.py`, `grep FECHA_INVALIDA output/excepciones.csv`, `./validator check --quick`
- **Solución:** Se agregó la función normalizar_fecha en `scripts/cierre.py`, que valida cada fecha con expresiones regulares y la biblioteca datetime. Los 12 afiliados con fecha inválida quedan en excepciones.csv como FECHA_INVALIDA y siguen contando en los totales.
- **Evidencia:** evidence/07-fechas.txt

## Incidente 8
- **Síntoma:** El cruce con el extracto de Caja Oriente no producía casos CRUCE_NO_COINCIDE y el validador marcaba la prueba como parcial.
- **Diagnóstico:** El extracto de Caja Oriente usa otro formato: separador punto y coma, columnas con otros nombres (id_afiliado, situacion), documentos de 12 dígitos rellenados con ceros a la izquierda y la situación VIGENTE o RETIRADO en lugar de A o I. Sin normalizar el documento ninguno coincidía con AFI_MAE.
- **Comandos:** `head -5 data/extracto_caja_oriente.csv`, `grep CRUCE_NO_COINCIDE output/excepciones.csv`, `wc -l evidence/08-cruce-caja-oriente.txt`
- **Solución:** `scripts/cierre.py` compara los documentos sin ceros iniciales y equipara VIGENTE con A y RETIRADO con I. Reporta CRUCE_NO_COINCIDE (25 casos) cuando el documento no existe en AFI_MAE o la situación no corresponde con nuestro estado.
- **Evidencia:** evidence/08-cruce-caja-oriente.txt

## Incidente 9
- **Síntoma:** Los totales del cierre no cuadraban con la hoja de control de Operaciones.
- **Diagnóstico:** La hoja de control espera 1500 afiliados, 1194 activos y 274 inactivos. Los totales solo coinciden si se cuentan documentos distintos, se excluyen del total de activos los estados inválidos y los activos sin empresa, y no se cuentan los duplicados.
- **Comandos:** `cat output/totales.txt`, `cat control/hoja_control.csv`, `./validator check --quick`
- **Solución:** `scripts/cierre.py` escribe `output/totales.txt` con total_afiliados=1500, activos=1194, inactivos=274 y excepciones=104, que coincide con la hoja de control y con el validador (T09 en PASS).
- **Evidencia:** evidence/09-totales.txt

## Incidente 10
- **Síntoma:** Ejecutar `./run.sh` dos veces seguidas fallaba: la segunda corrida terminaba con "mkdir: output: File exists" y código de salida 1.
- **Diagnóstico:** El script heredado creaba la carpeta de salida sin tolerar que ya existiera y además movía el archivo de entrada a `data/procesados/` al terminar, por lo que la segunda corrida ya no encontraba AFI_MAE.csv. Las salidas dependían de si la corrida era la primera.
- **Comandos:** `./run.sh`, `ls data data/procesados`, `md5sum output/afiliados_activos.csv output/excepciones.csv output/totales.txt output/top_error.txt`, `diff /tmp/a.txt /tmp/b.txt`, `./reset.sh`
- **Solución:** `scripts/cierre.py` no mueve ni modifica las entradas, crea `output/` con exist_ok y sobrescribe los archivos en cada corrida. Se comprobó con md5sum que dos corridas seguidas producen salidas idénticas y que `./reset.sh` seguido de `./run.sh` deja el validador en 625 de 625 puntos.
- **Evidencia:** evidence/10-repetibilidad.txt