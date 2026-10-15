# Uso de inteligencia artificial

## Uso 1
    - Herramienta: Claude (Anthropic), en el chat de claude.ai.

    - Para qué se usó: Configurar el entorno de trabajo (WSL2, Docker Desktop, Ubuntu, VS Code, Git y GitHub) y entender cómo estaba armado el kit del reto.
    
    - Prompt principal (resumido): "Ayúdame a configurar el entorno de Visual Studio Code para poder empezar a resolver el reto", adjuntando el zip del kit y capturas de los errores que fueron saliendo.

    - Qué produjo: Una guía paso a paso para instalar WSL2 y Docker con integración a Ubuntu, la creación del repositorio, el flujo de commits y la lectura inicial de los archivos del kit.

    - Qué modificó o corrigió el equipo: Los comandos asumían nombres y rutas que no coincidían con nuestros equipos, así que los adaptamos: usamos git remote set-url con el nombre real del repositorio, borramos y recreamos el repositorio cuando el historial local y el de GitHub no coincidían, y quitar el error de permisos.

## Uso 2
    - Herramienta: Claude (Anthropic), en el chat de claude.ai.

    - Para qué se usó: Diagnosticar los incidentes 1, 2, 3, 4 y 6 a partir de los logs y de los errores del validador.

    - Prompt principal (resumido): Pegamos capturas de docker compose ps, de los logs de cierre-worker y cierre-api y de la salida de ./validator check --quick, y preguntamos qué fallaba y cómo comprobarlo.
    
    - Qué produjo: Las causas probables (WORKER_INTERVAL_SECONDS con la letra s, DATABASE_HOST con un nombre de servicio inexistente, la ruta de entrada del cierre y el error de nombres vacíos en app.py), junto con los comandos para verificarlas y la forma de contar el error más frecuente en los tres logs.

    - Qué modificó o corrigió el equipo: Verificamos cada causa nosotros mismos con los logs y con curl antes de aceptarla. En el incidente 6 la primera edición de app.py quedó con una llave sin cerrar y sin la clave empresa; lo detectamos con el SyntaxError del log y leyendo la respuesta JSON, y lo corregimos. También reconstruimos la imagen de la API, porque el contenedor seguía con el código viejo.

## Uso 3
    - Herramienta: Claude (Anthropic), en el chat de claude.ai.

    - Para qué se usó: Reescribir el cierre mensual en Python (scripts/cierre.py) con las reglas del diccionario de datos: duplicados, estados inválidos, empresas, beneficiarios huérfanos, fechas y cruce con Caja Oriente.

    - Prompt principal (resumido): Le pedimos ayuda para resolver los incidentes 5, 7, 8, 9 y 10 de forma repetible, pasándole la salida del validador y los formatos de los archivos CSV.

    - Qué produjo: El script cierre.py por etapas, el script top_error.sh y los comandos para guardar la evidencia, comparar con la hoja de control y probar la repetibilidad con md5sum.

    - Qué modificó o corrigió el equipo: Ejecutamos el script y comparamos sus totales con control/hoja_control.csv y con el validador antes de aceptarlo. Corregimos los permisos de ejecución de los scripts con chmod, reemplazamos el cierre.sh heredado por una llamada a cierre.py, rehicimos la evidencia del incidente 10 cuando quedó mezclada y reescribimos comandos que perdían los asteriscos al copiarlos.

## Uso 4
    - Herramienta: Claude (Anthropic), en el chat de claude.ai.

    - Para qué se usó: Preparar un borrador del informe de incidentes, del README y de este documento a partir de lo que ya habíamos hecho.

    - Prompt principal (resumido): Le pedimos que armara incident-report.md, README.md y AI_USAGE.md siguiendo la rúbrica, con las evidencias reales de cada incidente.

    - Qué produjo: Borradores de los tres documentos con la estructura exigida por el validador de entregables.
    
    - Qué modificó o corrigió el equipo: Revisamos cada incidente contra lo que ejecutó cada uno, completamos los nombres e integrantes, ajustamos los textos con nuestras palabras y comprobamos el resultado con ./validator entregables antes de subirlos.