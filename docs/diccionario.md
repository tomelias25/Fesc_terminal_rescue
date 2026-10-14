# Diccionario de datos (parcial)

> Documento recuperado de la wiki de Operaciones. Algunas secciones están desactualizadas.

## AFI_MAE — maestro de afiliados

| Columna | Descripción |
|---|---|
| NRO_DOC | Número de documento del afiliado (texto, sin puntos) |
| TIP_DOC | Tipo de documento (`CC`) |
| NOM1, NOM2 | Primer y segundo nombre (el segundo puede venir vacío) |
| APE1, APE2 | Primer y segundo apellido (el segundo puede venir vacío) |
| EST_AFI | Estado: `A` = activo, `I` = inactivo. Cualquier otro valor no es un código válido |
| COD_EMP | Código de la empresa aportante (ver EMPRESA) |
| FEC_AFI | Fecha de afiliación. Formato oficial `YYYY-MM-DD` |

## EMPRESA — empresas aportantes

| Columna | Descripción |
|---|---|
| COD_EMP | Código de la empresa |
| NOM_EMP | Razón social |
| NIT | NIT con dígito de verificación |
| EST_EMP | Estado de la empresa |

## AFI_BEN — beneficiarios

| Columna | Descripción |
|---|---|
| NRO_DOC_BEN | Documento del beneficiario |
| NRO_DOC_AFI | Documento del afiliado del que depende |
| NOM_BEN | Nombre completo |
| PARENTESCO | Parentesco con el afiliado |
| FEC_NAC | Fecha de nacimiento |

## APORTES — aportes mensuales

| Columna | Descripción |
|---|---|
| NRO_DOC | Documento del afiliado |
| PERIODO | Periodo pagado `YYYY-MM` |
| VALOR | Valor del aporte en pesos |
| FEC_PAGO | Fecha de pago |

## extracto_caja_oriente.csv — cruce enviado por Caja Oriente

Caja Oriente nos envía el estado con el que tiene registrados a nuestros afiliados.
Su sistema usa sus propios nombres de columna, separador `;`, documentos de 12 dígitos
rellenados con ceros a la izquierda y fechas `DD/MM/YYYY`. `situacion` es `VIGENTE`
(equivale a nuestro activo) o `RETIRADO` (equivale a nuestro inactivo).

## Reglas del cierre (acordadas con Operaciones y Auditoría)

1. **Universo:** cada documento distinto de AFI_MAE es un afiliado. Si un documento aparece
   más de una vez se conserva la primera aparición y se reporta `DUPLICADO` (una vez por documento).
2. **Estado:** solo `A` e `I` son válidos. Un código distinto se reporta `CODIGO_INVALIDO` y ese
   afiliado no cuenta como activo ni como inactivo.
3. **Empresa:** un afiliado activo cuyo `COD_EMP` está vacío o no existe en EMPRESA se reporta
   `SIN_EMPRESA` y no entra al archivo de activos ni al total de activos.
4. **Beneficiarios:** un beneficiario cuyo afiliado no existe en AFI_MAE se reporta
   `BENEFICIARIO_HUERFANO` (columna `documento` = documento del beneficiario).
5. **Fechas:** `FEC_AFI` en `DD/MM/YYYY` o `YYYYMMDD` se normaliza a `YYYY-MM-DD`. Una fecha que no
   se puede interpretar como fecha real se reporta `FECHA_INVALIDA`. La fecha no excluye al
   afiliado de los totales: nunca se descarta un registro sin reportarlo.
6. **Cruce Caja Oriente:** si un documento del extracto no existe en AFI_MAE, o su situación no
   corresponde a nuestro estado, se reporta `CRUCE_NO_COINCIDE`.
7. **Archivo de activos:** un registro por afiliado activo con empresa válida; `beneficiarios` es
   la cantidad de beneficiarios del afiliado y `ultimo_aporte` el mayor `PERIODO` pagado (vacío si
   no tiene aportes).
8. **Totales:** `total_afiliados` = documentos distintos; `activos` y `inactivos` según las reglas
   anteriores; `excepciones` = líneas de `excepciones.csv` sin contar el encabezado.

## Códigos de error en logs

Los errores de los tres servicios usan códigos `CIE-####`. Los avisos (`W-###`) no son errores.
