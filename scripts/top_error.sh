#!/usr/bin/env bash
# Incidente 4: identifica el codigo CIE mas frecuente en los logs
mkdir -p output
cat logs/api.log logs/worker.log logs/database.log | grep 'ERROR' | grep -o 'CIE-[0-9][0-9][0-9][0-9]' | sort | uniq -c | sort -rn | head -1 | awk '{print "codigo_error=" $2; print "ocurrencias=" $1}' > output/top_error.txt