# Cómo entregar

1. Descompriman este archivo y entren a la carpeta.
2. Conviértanla en un repositorio Git y hagan el primer commit:

   ```bash
   git init
   git add -A
   git commit -m "Importa el kit"
   ```

3. Creen un repositorio **público** en GitHub, GitLab o Bitbucket (sin README ni licencia) y súbanlo:

   ```bash
   git remote add origin https://github.com/<usuario>/<proyecto>.git
   git branch -M main
   git push -u origin main
   ```

4. Entren a la plataforma del evento (https://hackafesc.ingsoftwarefesc.com), opción **Mi equipo**, cada uno con su correo de inscripción.
   La primera contraseña es su número de documento (sin puntos ni espacios) y la plataforma les pide
   cambiarla. Registren el enlace del repositorio. La plataforma comprueba en ese momento que el
   repositorio sea público y les muestra el resultado. Pueden cambiar el enlace hasta la fecha de cierre.
   En la misma página registren el enlace de Google Drive de su **pitch**: un video de 60 segundos o
   menos que presente su solución, compartido como «Cualquier persona con el enlace». La plataforma
   verifica al momento que sea público y su duración; el comité revisa el contenido.
5. Trabajen con commits frecuentes y hagan `git push` seguido. Al llegar la fecha de cierre la plataforma
   descarga el repositorio y califica **el último commit anterior a esa fecha**. Lo que suban después no cuenta.
6. Cuando el comité verifique su resultado, lo verán en **Mi equipo** con el detalle y el reporte PDF.

Importante:

- Si al llegar la fecha de cierre el repositorio no está registrado o no es público, la pareja **no se califica**.
- `KIT.md` es la guía de los organizadores. `README.md` es la documentación de **su** software: llenen la
  plantilla completa, porque el sistema la contrasta con su `.env.example`, su `docker-compose.yml` y el contrato.
- No suban secretos reales: usen `.env.example` y dejen `.env` fuera del repositorio (ya está en `.gitignore`).
- `./validator` les dice durante el reto cómo va su solución. La calificación oficial la hace la plataforma
  con pruebas más completas que no se publican.
- Sus scripts (`run.sh`, `reset.sh` y los demás) se ejecutan en Linux solo con docker/compose, git, python3,
  curl, jq, psql y las utilidades estándar. Lo que necesite otra herramienta debe correr dentro de un contenedor.
