-- Esquema heredado del cierre de afiliados (copia operativa de Informix).
-- Todas las columnas son texto: así llegaron los datos del sistema origen.

CREATE TABLE empresa (
    cod_emp  TEXT,
    nom_emp  TEXT,
    nit      TEXT,
    est_emp  TEXT
);

CREATE TABLE afi_mae (
    nro_doc  TEXT,
    tip_doc  TEXT,
    nom1     TEXT,
    nom2     TEXT,
    ape1     TEXT,
    ape2     TEXT,
    est_afi  TEXT,
    cod_emp  TEXT,
    fec_afi  TEXT
);

CREATE TABLE afi_ben (
    nro_doc_ben TEXT,
    nro_doc_afi TEXT,
    nom_ben     TEXT,
    parentesco  TEXT,
    fec_nac     TEXT
);

CREATE TABLE aportes (
    nro_doc  TEXT,
    periodo  TEXT,
    valor    TEXT,
    fec_pago TEXT
);

CREATE INDEX idx_afi_mae_doc ON afi_mae (nro_doc);
CREATE INDEX idx_afi_ben_afi ON afi_ben (nro_doc_afi);
CREATE INDEX idx_aportes_doc ON aportes (nro_doc);
