# FESC Legacy Challenge 2026

Hackathon del programa de Ingeniería de Software · Técnico · Tecnólogo · Profesional

---

## 1. Información general

| | |
|---|---|
| Duración | La anuncian los organizadores. La **hora límite** se publica en la plataforma del evento |
| Equipos | Parejas (2 estudiantes del mismo nivel) |
| Organización del tiempo | Libre. No hay hitos ni orden obligatorio. Todo el material está disponible desde el inicio |
| Inteligencia artificial | Permitida durante todo el reto (ver sección 3) |
| Entorno | Cada nivel descarga su propio kit (ZIP) desde la plataforma del evento. Ningún nivel depende del trabajo de otro |
| Calificación | Validador automático + entregables verificados por el sistema (ver `rubrica.md`). La única excepción es la mitad del pitch: el comité revisa el contenido del video |

### El escenario común

Una Caja de Compensación Familiar lleva años operando sobre un sistema legacy (IBM Informix / Genero) cuya base de datos se convirtió en el punto de integración de todo: afiliaciones, subsidios, educación, reportes. Cambiar una columna rompe varias aplicaciones, y validar afiliaciones con otras cajas sigue siendo manual.

Cada nivel resuelve una parte distinta del problema:

| Nivel | Reto | Pregunta |
|---|---|---|
| Técnico | **Terminal Rescue** | ¿Puedes diagnosticar y reparar un proceso crítico averiado desde la terminal? |
| Tecnólogo | **Legacy Escape** | ¿Puedes modernizar el sistema sin apagarlo ni romper las aplicaciones que dependen de él? |
| Profesional | **Caja Link** | ¿Puedes integrar varias cajas entre sí con seguridad, privacidad y tolerancia a fallas? |

---

## 2. Reglas comunes

1. **Entrega:** cada pareja descarga el kit de su nivel, lo sube a **su propio repositorio Git público** (GitHub, GitLab o Bitbucket) y registra el enlace en la plataforma del evento (**Mi equipo**) (cada integrante entra con su correo; la primera contraseña es su número de documento y la plataforma obliga a cambiarla). El enlace se puede cambiar hasta la fecha de cierre.
2. **Repositorio público:** la plataforma comprueba al registrar que el repositorio se pueda descargar sin usuario ni contraseña. Si al llegar la hora límite el repositorio no está registrado o no es público, el equipo **no se califica**.
3. **Hora límite:** se califica automáticamente el **último commit con fecha anterior a la hora límite**. Lo que se suba después se ignora. Si no hay ningún commit antes de la hora límite, el equipo no se califica.
4. **Commits:** los dos integrantes hacen commits con su propio nombre y correo. El sistema revisa que haya al menos 10 commits durante el evento, al menos 3 de cada integrante y mensajes que describan el cambio ("corrige host de la base en cierre-api", no "update").
5. El entorno debe quedar **levantable desde cero** con `docker compose up -d --build` (o con el `run.sh` que indique cada reto). La calificación es automática y corre en un servidor Linux: los scripts del equipo (`run.sh`, `reset.sh`, `rollback.sh`) se ejecutan con `bash` y solo pueden contar con `docker` / `docker compose`, `git`, `python3`, `curl`, `jq`, `psql` y las utilidades estándar (`grep`, `awk`, `sed`, `sort`…). Cualquier otra herramienta debe correr dentro de un contenedor (`docker compose exec` o `docker compose run`). Por seguridad del servidor, `docker-compose.yml` no puede usar `privileged`, `cap_add`, `devices`, `network_mode: host`, `pid: host` ni montar carpetas fuera del repositorio (por ejemplo, `/var/run/docker.sock`): si lo hace, el entorno no se levanta y las pruebas valen 0.
6. Los secretos van en `.env` (no se versiona). Se entrega `.env.example`. Ningún archivo del repositorio puede tener escrito el valor de un token, clave o contraseña: el código los lee de variables de entorno.
7. Se permite cualquier lenguaje y framework, salvo que el reto indique lo contrario. Los nombres de endpoints, archivos, carpetas, servicios y puertos de este documento son **obligatorios**: el sistema de calificación los usa.
8. Cada kit incluye:
   - `./validator check`: ejecuta las pruebas públicas del contrato. El validador oficial ejecuta además casos ocultos.
   - `./validator entregables`: revisa los documentos y el repositorio con **las mismas reglas y puntos** del calificador oficial.
   - `./reset.sh`: devuelve el kit al estado inicial si el equipo rompe el entorno.
9. Los documentos entregables tienen un **formato obligatorio** (títulos, campos y tablas) indicado en cada reto. El sistema los revisa de forma automática: si el formato no se respeta, el entregable no suma. Cada kit trae estos archivos como **plantillas** con los títulos, campos y tablas listos para llenar; una plantilla sin llenar no suma puntos.
10. **Formato de los documentos:** todos los documentos que se califican van en **Markdown (`.md`)** con el nombre y la ruta exactos que pide el reto (`openapi.yaml` y `config/cajas.yaml` van en YAML). No se aceptan Word (`.docx`), PDF ni otros formatos en su lugar: si el sistema encuentra, por ejemplo, `AI_USAGE.docx` en vez de `AI_USAGE.md`, el entregable vale 0 y el reporte lo indica. La única excepción es la carpeta `evidence/` del nivel Técnico, que acepta `.txt`, `.log`, `.md`, `.csv`, `.json`, `.pdf`, `.png`, `.jpg` y `.jpeg`. Ningún archivo de texto puede pesar más de 1 MB: los que lo superen no se revisan.

11. **Pitch de 1 minuto:** cada pareja graba un video de **60 segundos o menos** que presente su solución (el problema, qué construyeron y qué resultado lograron), lo sube a **Google Drive**, lo comparte como «Cualquier persona con el enlace» y registra ese enlace en **Mi equipo** antes de la hora límite. Vale 5 puntos de los entregables: la mitad la da el sistema si Drive confirma que es un video público de 60 segundos o menos, y la otra mitad el comité si el contenido es válido. Si el comité lo marca como **no válido**, el pitch vale 0. No modifiquen el archivo después de la hora límite: el sistema lo detecta y pierde la mitad automática.

12. **README: documentación del software (2 puntos):** el `README.md` del repositorio es la documentación del software de la pareja (la guía de los organizadores viene aparte, en `KIT.md`). Cada kit lo trae como plantilla con once secciones obligatorias: `## Descripción`, `## Integrantes`, `## Requisitos`, `## Instalación y ejecución`, `## Configuración`, `## Arquitectura`, `## Uso`, `## Pruebas`, `## Documentación`, `## Qué resolvimos` y `## Limitaciones y pendientes`. El sistema no solo revisa que estén llenas: las contrasta con el repositorio. Configuración debe explicar **cada variable de `.env.example`**; Arquitectura, nombrar **cada servicio de `docker-compose.yml`**; Uso, incluir las rutas del contrato (en el Técnico, la API y los archivos de `output/`); Documentación, enlazar los demás entregables del nivel; e Instalación y ejecución, los comandos para levantarlo. El detalle está en la rúbrica (TE08 / GE11 / PE11).

---

## 3. Uso de inteligencia artificial

Se permite usar cualquier herramienta durante el reto (ChatGPT, Claude, Gemini, Copilot, Cursor, agentes, modelos locales).

> Puedes usar IA para construir cualquier parte de la solución, pero ambos integrantes deben poder entender, ejecutar, depurar y modificar todo lo entregado. Documentar con honestidad cómo usaron la IA y qué corrigieron también suma puntos (`AI_USAGE.md`).

Cada equipo entrega `AI_USAGE.md` en la raíz con **al menos 3 usos relevantes**, cada uno con este formato exacto:

```markdown
## Uso 1
- Herramienta: ChatGPT
- Para qué se usó: diagnosticar el error de conexión de la API
- Prompt principal (resumido): "connection refused contra cierre-db en docker compose"
- Qué produjo: sugirió cambiar el host a localhost
- Qué modificó o corrigió el equipo: localhost no sirve entre contenedores; usamos el nombre del servicio cierre-db
```

Los cinco campos deben estar llenos y "Qué modificó o corrigió el equipo" debe explicar la corrección en **8 palabras o más**. Si `AI_USAGE.md` no existe o no tiene ningún uso completo, se aplica la penalización de −5 puntos.

---

## 4. Nivel Técnico — Terminal Rescue: el cierre de afiliados

### Contexto

Cada mes, Operaciones ejecuta un proceso en el servidor que genera el archivo de afiliados activos que usa Subsidios. Este mes el proceso no corre, la API de consulta falla, los totales no cuadran con la hoja de control y los logs están llenos de errores. El equipo original ya no está.

### Kit entregado

```text
tecnico/
├── docker-compose.yml       cierre-db, cierre-api, cierre-worker
├── .env.example
├── data/
│   ├── AFI_MAE.csv          afiliados
│   ├── AFI_BEN.csv          beneficiarios
│   ├── EMPRESA.csv          empresas
│   ├── APORTES.csv          aportes
│   └── extracto_caja_oriente.csv   cruce de otra caja (otras columnas, otro formato de fecha)
├── control/
│   └── hoja_control.csv     totales esperados por Operaciones
├── logs/                    api.log, worker.log, database.log
├── scripts/                 script de cierre heredado (incompleto)
├── docs/diccionario.md      diccionario de datos parcial
├── validator                validador del equipo
└── reset.sh
```

Inicio:

```bash
cp .env.example .env
docker compose up -d
docker compose ps
./validator check
```

La guía del kit (`KIT.md`) no dice dónde están las fallas. Encontrarlas es parte del reto.

### Incidentes a resolver

| # | Síntoma | Debe quedar | Pts |
|---|---|---|---:|
| 1 | `cierre-worker` en `Exited (1)` | Servicio arriba y estable | 25 |
| 2 | La API no conecta a la base | Configuración corregida | 25 |
| 3 | El script de cierre no lee su archivo de entrada | Permisos o rutas corregidos | 25 |
| 4 | Miles de líneas de log | Error más frecuente identificado y contado | 50 |
| 5 | Duplicados, afiliados sin empresa, beneficiarios huérfanos, códigos inválidos | Corregidos en la base; lo irreparable reportado en excepciones | 75 |
| 6 | La consulta del afiliado responde 500 | Responde 200 con los datos correctos | 75 |
| 7 | Fechas en formatos que el cierre no entiende | Se procesan o se reportan; nunca se descartan en silencio | 50 |
| 8 | Extracto de Caja Oriente con otras columnas | Cruces que no coinciden reportados en excepciones; el archivo de activos conserva su formato | 100 |
| 9 | Totales que no cuadran | `totales.txt` coincide con la hoja de control | 100 |
| 10 | El cierre solo funciona una vez | `./run.sh` es repetible: corre dos veces seguidas y después de un `./reset.sh` + arreglos | 100 |
| | | **Total verificable** | **625** |

### Contrato obligatorio (lo que revisa el validador)

**Servicios:** `docker compose ps` muestra `cierre-db`, `cierre-api` y `cierre-worker` en estado `running`.

**API:** `GET http://localhost:8081/afiliados/{documento}`

```json
{ "documento": "1098765432", "nombre": "JUAN CARLOS PEREZ GOMEZ", "estado": "ACTIVO", "empresa": "EMPRESA ABC" }
```

Documento inexistente → `404`.

**`./run.sh`** en la raíz del repositorio genera:

| Archivo | Contenido |
|---|---|
| `output/afiliados_activos.csv` | `documento,nombre,estado,cod_empresa,empresa,beneficiarios,ultimo_aporte` (fecha `YYYY-MM`) |
| `output/excepciones.csv` | `documento,tipo,detalle` con `tipo` ∈ `DUPLICADO`, `SIN_EMPRESA`, `BENEFICIARIO_HUERFANO`, `CODIGO_INVALIDO`, `FECHA_INVALIDA`, `CRUCE_NO_COINCIDE` |
| `output/totales.txt` | Líneas `clave=valor`: `total_afiliados`, `activos`, `inactivos`, `excepciones` |
| `output/top_error.txt` | `codigo_error=<código>` y `ocurrencias=<n>` |

### Requisitos técnicos

- Diagnóstico desde terminal: `docker`, `docker compose logs`, `psql`, `grep`, `awk`, `sed`, `sort`, `uniq`, `wc`, `find`, `chmod`.
- Scripting en Bash o Python. Todo script de `scripts/` y `run.sh` empieza con `#!`, tiene permiso de ejecución y no tiene errores de sintaxis.

### Entregables

```text
README.md              documentación del software (regla 12)
incident-report.md     formato obligatorio (abajo)
AI_USAGE.md            sección 3
run.sh
scripts/
evidence/              un archivo por incidente con la salida de terminal que lo demuestra
output/                generado por run.sh
```

**Formato obligatorio de `incident-report.md`:** una sección por cada incidente del 1 al 10, con estos cinco campos.

```markdown
## Incidente 1
- **Síntoma:** `docker compose ps` muestra `cierre-worker  Exited (1)`.
- **Diagnóstico:** el log del worker dice que WORKER_INTERVAL_SECONDS no es un entero.
- **Comandos:** `docker compose ps`, `docker compose logs cierre-worker | tail -5`
- **Solución:** WORKER_INTERVAL_SECONDS=30 en `.env` y reinicio del worker.
- **Evidencia:** evidence/01-worker.txt
```

- Síntoma, Diagnóstico y Solución: al menos 3 palabras.
- Comandos: al menos un comando entre comillas invertidas.
- Evidencia: la ruta de un archivo de `evidence/` que exista, no esté vacío y sea `.txt`, `.log`, `.md`, `.csv`, `.json`, `.pdf`, `.png`, `.jpg` o `.jpeg` (se recomienda `.txt` con la salida de terminal; Word no se acepta).
- Entre todos los incidentes deben aparecer al menos 6 herramientas distintas de la lista de requisitos técnicos.

---

## 7. Premios

| Premio | Para |
|---|---|
| Technical Builder | Mayor nota final del nivel Técnico |
| Product Builder | Mayor nota final del nivel Tecnólogo |
| Engineering Award | Mayor nota final del nivel Profesional |
| AI Engineering Award | Entre los equipos calificados sin penalizaciones, el mejor `AI_USAGE.md` según el sistema |
| FESC Productization | Entre los tres primeros de cada nivel, la mayor nota de los que están listos para producción: sin penalizaciones, validador ≥ 80 % y entregables ≥ 80 % |

La calificación detallada está en `rubrica.md`.
