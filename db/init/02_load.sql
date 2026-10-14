-- Carga inicial desde los CSV del kit (montados en /data).
\copy empresa FROM '/data/EMPRESA.csv' WITH (FORMAT csv, HEADER true)
\copy afi_mae FROM '/data/AFI_MAE.csv' WITH (FORMAT csv, HEADER true)
\copy afi_ben FROM '/data/AFI_BEN.csv' WITH (FORMAT csv, HEADER true)
\copy aportes FROM '/data/APORTES.csv' WITH (FORMAT csv, HEADER true)
