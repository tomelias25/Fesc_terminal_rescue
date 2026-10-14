# FESC Legacy Challenge 2026 — Lo esperado y rúbrica de calificación

Este documento complementa `RETO.md`. Define qué se espera de cada reto, cómo se califica y cómo se calcula la nota final.

**Principio:** toda la nota es verificable. La única parte que decide una persona es la mitad del pitch (5 puntos), donde el comité revisa el contenido del video:

- El **sistema de calificación** ejecuta las pruebas del validador, revisa los entregables con reglas fijas y detecta las penalizaciones.
- El **comité** verifica cada resultado antes de publicarlo, revisa el contenido del pitch (válido o no válido) y registra la copia entre equipos si la confirma.
- El **jurado** consulta en la plataforma el resultado de cada pareja en lenguaje sencillo. No asigna puntos ni necesita leer código.

Los identificadores (`T01`, `GE03`, `PE02`…) son los mismos que aparecen en los reportes. Cada equipo puede revisar su avance con `./validator check` (pruebas) y `./validator entregables` (documentos), que usan las mismas reglas del calificador oficial.

---

## 1. Fórmula general

Nota final sobre 100 puntos:

| Componente | Técnico | Tecnólogo | Profesional | Quién lo califica |
|---|---:|---:|---:|---|
| Validador automático | 80 | 70 | 70 | Sistema: pruebas sobre el entorno entregado |
| Entregables verificables | 20 | 30 | 30 | Sistema: revisa documentos, código y Git con las reglas de esta rúbrica. Pitch: mitad el sistema (duración) y mitad el comité (contenido) |

```text
nota_validador = (puntos_obtenidos / puntos_posibles) × peso_validador
nota_final     = nota_validador + entregables − penalizaciones      (entre 0 y 100)
```

- Las pruebas y entregables con resultado parcial otorgan puntos proporcionales. Por ejemplo, 7 de 10 incidentes completos dan el 70 % de los puntos de TE01.
- Los puntos de los entregables están directamente en la escala de la nota final: TE01 vale 8 puntos de los 100.
- Los documentos se revisan solo en **Markdown (`.md`)** con la ruta exacta del reto (`openapi.yaml` y `config/cajas.yaml` en YAML). Un documento entregado en Word, PDF u otro formato cuenta como no entregado (el reporte dice qué archivo se encontró). La evidencia del nivel Técnico acepta además `.txt`, `.log`, `.csv`, `.json`, `.pdf`, `.png` y `.jpg`. Los archivos de texto de más de 1 MB no se revisan.

---

## 2. Alcance por nivel (plan de estudios FESC)

Lo que se pide en cada reto corresponde a lo que el estudiante ya cursó en su ciclo propedéutico ([plan de estudios](https://www.ingsoftwarefesc.com/)). Nada de lo exigido requiere materias de un ciclo posterior.

| Nivel | Semestres | Materias en las que se apoya | Se exige | No se exige |
|---|---|---|---|---|
| Técnico | I a III | Sistemas Operativos, Virtualización, Docker, Base de Datos Relacionales, Programación Estructurada y Orientada a Objetos, Modelos y Documentación del Software | Diagnosticar desde la terminal, reparar Docker Compose, consultas SQL, scripts en Bash o Python, documentar incidentes con evidencia, usar Git | Diseñar arquitectura, construir APIs nuevas, seguridad, pruebas automatizadas |
| Tecnólogo | IV a VI | Arquitectura y Diseño del Software, Desarrollo Básico y Avanzado de Aplicaciones en Red, Arquitectura Cliente-Servidor, Codificación y Pruebas del Software, Seguridad Informática | Construir una API REST con adapter, autenticación por token, pruebas automatizadas, contrato OpenAPI, plan de migración con rollback | ADR formales, modelo de amenazas, pruebas de carga, sistemas distribuidos |
| Profesional | VII a IX | Gestión de Proyectos de Software, Calidad y Seguridad del Software, Tecnologías Emergentes, Prototipado y Validación (y todo lo anterior) | Integración de sistemas heterogéneos, tolerancia a fallas, protección de datos (Ley 1581), ADR, modelo de amenazas demostrado con pruebas, prueba de carga, versionado y extensión por configuración | — |

---

## 3. Nivel Técnico — Terminal Rescue

### Lo que se espera

Un entorno Docker reparado en el que el cierre de afiliados corre de forma repetible y produce archivos correctos, con un informe que demuestre cómo se diagnosticó cada falla desde la terminal.

### Validador (625 puntos → 80)

| ID | Prueba | Cómo se verifica | Pts |
|---|---|---|---:|
| T01 | Servicios arriba | `cierre-db`, `cierre-api`, `cierre-worker` en `running` y sin reinicios en 60 s | 25 |
| T02 | API conectada a la base | La API responde una consulta conocida (no error de conexión) | 25 |
| T03 | Entrada del cierre legible | `./run.sh` termina con código 0 y genera los 4 archivos de `output/` | 25 |
| T04 | Error más frecuente | `top_error.txt` coincide con el código y el conteo esperados | 50 |
| T05 | Calidad de datos | `excepciones.csv` contiene los `DUPLICADO`, `SIN_EMPRESA`, `BENEFICIARIO_HUERFANO` y `CODIGO_INVALIDO` esperados (puntaje proporcional al acierto; falsos positivos restan) | 75 |
| T06 | Consulta de afiliado | `GET /afiliados/{doc}` responde 200 con datos correctos para una muestra oculta, y 404 para inexistentes | 75 |
| T07 | Fechas | Las fechas mal formadas aparecen como `FECHA_INVALIDA` o normalizadas; ningún registro desaparece sin reporte | 50 |
| T08 | Cruce Caja Oriente | `CRUCE_NO_COINCIDE` contiene los casos esperados y `afiliados_activos.csv` conserva sus columnas | 100 |
| T09 | Totales | `totales.txt` coincide con la hoja de control (oficial y oculta) | 100 |
| T10 | Repetibilidad | `./run.sh` dos veces seguidas produce salidas idénticas; también tras `./reset.sh` + arreglos documentados | 100 |

### Entregables verificables (20 puntos)

Los formatos obligatorios están en `RETO.md` §4.

| ID | Entregable | Qué revisa el sistema | Pts |
|---|---|---|---:|
| TE01 | Informe de incidentes | `incident-report.md` tiene una sección `## Incidente N` por cada incidente del 1 al 10, con los campos Síntoma, Diagnóstico, Comandos, Solución y Evidencia llenos. Cada campo vale 1/5 del incidente | 5 |
| TE02 | Evidencia por incidente | El campo Evidencia apunta a un archivo de `evidence/` que existe y no está vacío | 2 |
| TE03 | Diagnóstico desde terminal | En Comandos y Diagnóstico aparecen al menos 6 herramientas distintas de: docker, psql, grep, awk, sed, sort, uniq, wc, find, chmod | 1 |
| TE04 | Scripts verificables | `run.sh` y los scripts de `scripts/` tienen permiso de ejecución, primera línea `#!` y no tienen errores de sintaxis | 1 |
| TE05 | Historial Git | Entre el inicio y la hora límite: al menos 10 commits, los dos integrantes con al menos 3 commits cada uno y el 80 % de los mensajes descriptivos (3 palabras o más; no "update", "fix", "wip"…) | 2 |
| TE06 | Uso de IA documentado | `AI_USAGE.md` tiene al menos 3 secciones `## Uso N` con los cinco campos llenos y la corrección del equipo explicada en 8 palabras o más | 2 |
| TE07 | Pitch de 1 minuto | En **Mi equipo** está registrado el enlace público de Google Drive de un video de **60 segundos o menos** que presenta la solución. Mitad automática: el sistema consulta en Drive que el archivo sea un video público, su duración y que no se haya modificado después de la hora límite. Mitad del comité: contenido válido. Si el comité lo marca **no válido**, el entregable vale 0 | 5 |
| TE08 | README: documentación del software | `README.md` documenta el software con once secciones `##` de igual peso: Descripción (≥ 30 palabras), Integrantes (una viñeta por integrante), Requisitos, Instalación y ejecución (≥ 15 palabras y los comandos `docker compose … up` y `./run.sh`), Configuración (**cada variable de `.env.example`**), Arquitectura (≥ 30 palabras y **cada servicio de `docker-compose.yml`**), Uso (`/afiliados/{documento}` y los 4 archivos de `output/`), Pruebas (≥ 15 palabras sobre cómo verificar), Documentación (enlaces a `incident-report.md`, `evidence/` y `AI_USAGE.md`), Qué resolvimos (≥ 30 palabras) y Limitaciones y pendientes (≥ 10 palabras). Las secciones con listas se cuentan en proporción | 2 |

---

## 6. Penalizaciones

Todas se detectan automáticamente, salvo la copia. El reporte de cada equipo muestra la evidencia de cada penalización.

| Situación | Efecto | Cómo se detecta |
|---|---|---|
| Repositorio no registrado o no público | No se califica | Al llegar la hora límite, la plataforma intenta descargar el repositorio registrado sin usuario ni contraseña. Si no hay enlace registrado o la descarga falla, el equipo queda NO CALIFICADO. La plataforma ya avisa al registrar el enlace si no es público |
| Entrega tardía | Ver regla | Se califica el **último commit anterior a la hora límite**; lo posterior se ignora. Si no hay ningún commit antes de la hora límite, el equipo queda NO CALIFICADO |
| Sin `AI_USAGE.md` o sin usos | −5 puntos | No existe `AI_USAGE.md` en la raíz del repositorio, o no tiene ninguna sección `## Uso N` completa (la plantilla vacía del kit no cuenta) |
| Secretos versionados | −5 puntos | `.env` está o estuvo en el historial de Git, o el valor de un token, clave o contraseña de `.env`/`.env.example` aparece escrito en otro archivo del equipo (se ignoran los valores de ejemplo como `cambiar-...`) |
| Acceso directo a la base (Tecnólogo) o a los datos internos de otra caja (Profesional) | −10 puntos y 0 en GE01 / PE05 | Tecnólogo: un servicio nuevo que no se llama `gateway…`, `adapter…` ni `tests` se conecta a `legacy-db` (registro de conexiones de PostgreSQL) o depende de ella en `docker-compose.yml`. Profesional: un servicio del equipo monta la carpeta `mocks/` o su código lee los archivos de datos de las cajas simuladas |
| El entorno no levanta desde cero | El validador corre con lo que levante; las pruebas que fallen valen 0 | `docker compose up -d --build` termina con error, o `docker-compose.yml` usa opciones que dan acceso al servidor (`privileged`, `cap_add`, `devices`, red o procesos del host, montajes fuera del repositorio) y por eso no se levanta (se anota en el reporte) |
| Copia entre equipos | Descalificación de los equipos involucrados | El reporte de similitud marca dos entregas del mismo nivel con 60 % o más de líneas de código propias en común (sin contar el código del kit). El comité revisa el caso y la registra en la plataforma |

Si una detección automática resulta ser un falso positivo, el comité la anula en la plataforma con el motivo. La anulación queda visible en los reportes.

## 7. Desempate

1. Mayor puntaje del validador.
2. Mayor puntaje en entregables.
3. Último commit más temprano.

## 8. Premios

| Premio | Regla |
|---|---|
| Technical Builder | Mayor nota final del nivel Técnico |
| Product Builder | Mayor nota final del nivel Tecnólogo |
| Engineering Award | Mayor nota final del nivel Profesional |
| AI Engineering Award | Entre los equipos calificados **sin penalizaciones**, el de mayor puntaje en el entregable de uso de IA (TE06 / GE09 / PE09). Desempate por nota final |
| FESC Productization | Entre los tres primeros de cada nivel, los que están **listos para producción**: sin penalizaciones, validador ≥ 80 % y entregables ≥ 80 %. Gana la mayor nota final; desempate por porcentaje del validador |

Si ningún equipo cumple la regla, el premio se declara desierto.

## 9. Calificación automatizada

Todo el proceso corre en la plataforma del evento. Las personas solo verifican y consultan:

1. **Material:** cada nivel descarga su kit (ZIP con el kit, el reto y la rúbrica de su ciclo).
2. **Registro:** cada pareja registra el enlace público de su repositorio en **Mi equipo** (cada integrante entra con su correo; la primera contraseña es su número de documento y la plataforma obliga a cambiarla); la plataforma comprueba en ese momento que se pueda descargar. En el mismo lugar registra el enlace de Drive del **pitch**, y la plataforma verifica al momento que sea un video público de 60 segundos o menos.
3. **Cierre:** al llegar la hora límite, la plataforma descarga cada repositorio, lo deja en el último commit anterior a la hora límite, levanta el entorno desde cero en un servidor aislado, ejecuta el validador oficial (con casos ocultos), revisa los entregables, ejecuta las pruebas del equipo y el rollback, y detecta las penalizaciones. Los equipos se califican uno por uno.
4. **Verificación:** el comité mira cada pitch y lo marca válido o no válido, y luego revisa cada resultado (no se puede verificar un resultado con el pitch pendiente). Solo entonces la pareja lo ve en **Mi equipo** y el jurado lo consulta en una ficha sencilla: nota, puesto en el nivel y cómo le fue en cada parte.
5. **Veredicto:** la plataforma combina todo y produce:
   - **Matriz Excel:** ranking por nivel con fórmulas, detalle de cada prueba y entregable con su evidencia, penalizaciones (origen y estado), rúbrica y calculadora de la fórmula.
   - **PDF:** reporte por equipo (cada prueba, cada entregable y penalizaciones con su evidencia, nota final) y consolidado con ranking y premios.
   - **Reporte de similitud** entre equipos del mismo nivel, para que el comité revise posibles copias.
6. **Publicación:** el comité publica la tabla de resultados cuando termina la verificación.
