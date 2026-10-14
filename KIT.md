# Terminal Rescue — el cierre de afiliados

Cada mes Operaciones ejecuta en el servidor el proceso que genera el archivo de afiliados
activos que usa Subsidios. Este mes el proceso no corre, la API de consulta falla, los
totales no cuadran con la hoja de control y los logs están llenos de errores. El equipo
original ya no está. Ustedes son el nuevo equipo.

> Esta es la guía del kit. La documentación de **su** software va en `README.md`, que trae la plantilla con el formato obligatorio (entregable «README: documentación del software»).

## Inicio

```bash
cp .env.example .env
docker compose up -d
docker compose ps
./validator check
```

## Qué hay en el kit

| Ruta | Contenido |
|---|---|
| `docker-compose.yml` | `cierre-db` (PostgreSQL), `cierre-api` (puerto 8081), `cierre-worker` |
| `data/` | CSV del sistema origen y extracto de Caja Oriente |
| `control/hoja_control.csv` | Totales esperados por Operaciones |
| `logs/` | Logs de la última noche (`api.log`, `worker.log`, `database.log`) |
| `scripts/` | Script de cierre heredado |
| `run.sh` | Punto de entrada del cierre |
| `docs/diccionario.md` | Diccionario de datos y reglas del cierre |
| `validator` | Validador del equipo (`./validator check` y `./validator entregables`) |
| `reset.sh` | Vuelve el entorno al estado inicial (contenedores, base y `output/`) |
| `incident-report.md`, `AI_USAGE.md` | Plantillas de los entregables con el formato obligatorio (vacías no suman) |
| `evidence/` | Un archivo por incidente con la salida de terminal que lo demuestra |

## Contrato

- `docker compose ps` muestra `cierre-db`, `cierre-api` y `cierre-worker` en `running`.
- `GET http://localhost:8081/afiliados/{documento}` →
  `{ "documento", "nombre", "estado", "empresa" }`; documento inexistente → `404`.
- `./run.sh` genera en `output/`: `afiliados_activos.csv`, `excepciones.csv`, `totales.txt` y
  `top_error.txt` con los formatos de `retos.md`. Debe poder ejecutarse varias veces seguidas
  y también después de `./reset.sh`.

## Herramientas sugeridas

`docker compose logs`, `docker compose exec cierre-db psql -U cierre -d cierre`, `grep`, `awk`,
`sed`, `sort`, `uniq`, `wc`, `find`, `chmod`.

## Validador

`./validator check` ejecuta la parte pública de las pruebas (requiere Python 3.8+ y Docker).
El validador oficial ejecuta además casos ocultos y otorga puntajes parciales.
`./validator check --quick` omite la espera de estabilidad de 60 s.

`./validator entregables` revisa `incident-report.md`, `evidence/`, los scripts, el historial Git,
`AI_USAGE.md` y `README.md` con las mismas reglas y puntos del calificador oficial (no necesita Docker). Agreguen
`--desde AAAA-MM-DDTHH:MM` (inicio del evento) para contar solo los commits del evento.

Las correcciones deben vivir en el repositorio (código, `run.sh`, `scripts/`, `docker-compose.yml`,
`.env.example`): el calificador parte de una copia limpia del último commit anterior a la hora límite
y ejecuta `./reset.sh` para comprobar que el cierre es repetible.
