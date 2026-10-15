# Terminal Rescue — Leonardo y Pedro

## Descripción

Este proyecto repara el proceso de cierre mensual de afiliados de una caja de compensación. El cierre lee los archivos de afiliados, beneficiarios, empresas y aportes, genera el archivo de afiliados activos que usa Subsidios, reporta las excepciones de calidad de datos y calcula los totales. También incluye una API de consulta de afiliados y un worker, todos corriendo en Docker Compose.

## Integrantes

- Andres Leonardo Ortega Diaz
- Pedro Daniel Puentes Cuervo

## Requisitos

- Docker Desktop con Docker Compose v2 (comando `docker compose`).
- Git y Python 3 (solo para el validador del reto).
- Sistema operativo Linux, o Windows con WSL2 y Ubuntu.
- curl y jq para consultar la API desde la terminal.

## Instalación y ejecución

Desde una copia limpia del repositorio, estos son los comandos en orden:

```bash
git clone https://github.com/tomelias25/Fesc_terminal_rescue.git
cd Fesc_terminal_rescue
cp .env.example .env
docker compose up -d --build
./run.sh
```

El primer comando descarga el código, el tercero crea la configuración local, `docker compose up -d --build` construye y levanta los tres servicios, y `./run.sh` ejecuta el cierre y deja los resultados en la carpeta `output/`. Para volver al estado inicial se usa `./reset.sh`.

## Configuración

Las variables están en `.env.example`; al copiarlo a `.env` se pueden cambiar sin tocar el código.

- `POSTGRES_DB`: nombre de la base de datos que crea PostgreSQL. Ejemplo: `cierre`.
- `POSTGRES_USER`: usuario administrador de la base. Ejemplo: `cierre`.
- `POSTGRES_PASSWORD`: contraseña de ese usuario. Ejemplo: `cambiar-esta-clave`.
- `DATABASE_HOST`: nombre del servicio de base de datos en la red de Docker, que debe ser `cierre-db`.
- `DATABASE_PORT`: puerto de PostgreSQL. Ejemplo: `5432`.
- `DATABASE_NAME`: base a la que se conectan la API y el worker. Ejemplo: `cierre`.
- `DATABASE_USER`: usuario con el que se conectan la API y el worker. Ejemplo: `cierre`.
- `DATABASE_PASSWORD`: contraseña de ese usuario. Ejemplo: `cambiar-esta-clave`.
- `API_PORT`: puerto donde escucha la API de consulta. Ejemplo: `8081`.
- `WORKER_INTERVAL_SECONDS`: cada cuántos segundos trabaja el worker; debe ser un número entero. Ejemplo: `30`.

## Arquitectura

La solución tiene tres servicios definidos en `docker-compose.yml`. El servicio `cierre-db` es la base de datos PostgreSQL, que se carga con los datos de `data/` al iniciar. El servicio `cierre-api` es una API en Python que consulta esa base y responde por el puerto 8081. El servicio `cierre-worker` es un proceso en Python que se conecta a la misma base y corre cada cierto número de segundos. Los tres comparten la red de Docker y se encuentran por su nombre de servicio. El cierre mensual corre aparte, con `./run.sh`: ejecuta `scripts/top_error.sh` y `scripts/cierre.py`, que leen los CSV de `data/` y los logs de `logs/`.

## Uso

Para consultar un afiliado se usa la ruta `/afiliados/{documento}` de la API:

```bash
curl -i localhost:8081/afiliados/3756530718
```

Responde 200 con un JSON como este y 404 si el documento no existe:

```json
{"documento": "3756530718", "nombre": "CAROLINA CASTRO CASTELLANOS", "estado": "ACTIVO", "empresa": "CONSTRUCTORA SAN LUIS S EN C"}
```

Al ejecutar `./run.sh` se generan cuatro archivos en `output/`:

- `afiliados_activos.csv`: un registro por afiliado activo con empresa válida, con su cantidad de beneficiarios y su último aporte.
- `excepciones.csv`: los casos que se reportan (duplicados, estados inválidos, sin empresa, beneficiarios huérfanos, fechas inválidas y cruce con Caja Oriente).
- `totales.txt`: total de afiliados, activos, inactivos y excepciones.
- `top_error.txt`: el código de error más frecuente de los logs y cuántas veces aparece.

## Pruebas

Para comprobar que todo funciona se ejecuta el validador del reto, que prueba los servicios, la API y los archivos generados, y debe terminar con todas las pruebas en PASS:

```bash
./validator check --quick
./validator entregables
```

También se puede ejecutar `./run.sh` dos veces seguidas y comparar las salidas de `output/` con `md5sum`: deben ser idénticas. El comando `./reset.sh` devuelve el entorno al inicio y después `./run.sh` debe dar el mismo resultado.

## Documentación

- [Informe de incidentes](incident-report.md): síntoma, diagnóstico, comandos y solución de cada uno de los diez incidentes.
- [Evidencias](evidence/): archivos con la salida de terminal de cada incidente.
- [Uso de IA](AI_USAGE.md): cómo se usó la inteligencia artificial y qué corrigió el equipo.

## Qué resolvimos

Corregimos los fallos del entorno: el worker caía por un valor mal escrito y la API no encontraba la base de datos por un nombre de servicio equivocado. Reparamos la consulta de afiliados, que fallaba con nombres vacíos. Reescribimos el cierre en Python para que lea los datos del repositorio, detecte duplicados, estados inválidos, empresas faltantes, fechas inválidas y diferencias con Caja Oriente, calcule los totales de la hoja de control y produzca siempre las mismas salidas. Además, identificamos el error más frecuente en los logs.

## Limitaciones y pendientes

El cierre se probó con los datos del kit; el calificador oficial usa casos ocultos que no conocemos. Los documentos del cruce con Caja Oriente se reportan sin ceros iniciales. La API usa el servidor básico de Python, que no está pensado para producción.