# Protocolo del diccionario de variables GEIH

## Archivo fuente

`data/reference/diccionario.xlsx` - hoja `Hoja1`

Columnas: `nombre_variable`, `etiqueta_variable`, `descripcion`, `pregunta_literal`, `tipo_variable`, `codigo_categoria`, `categoria`

Contenido real: 3.096 filas, 676 variables unicas, 188 con mapeos codigo->categoria, 488 solo metadata.

---

## Reglas no negociables

1. **`codigo_categoria` siempre como string.** `dtype=str` al abrir el Excel. `05` jamas puede volverse `5`.
2. **Ceros a la izquierda se preservan.** Aplica especialmente a `AREA` y `DPTO`.
3. **Regla central:** `nombre_variable + codigo_categoria -> categoria`.
4. **Recodificacion Opcion 1 (DT-005):** conservar columna original y agregar `<col>_label`.
   - `AREA` se conserva -> `AREA_label` recibe el nombre de la ciudad.
   - El dashboard siempre muestra `_label`; filtros y joins usan el codigo original.
5. **Duplicados `(variable, codigo)` con categorias distintas (DT-004):** conservar primero, emitir `warnings.warn`. Detectados 43 en el diccionario real.

---

## Validaciones obligatorias

- **Cobertura:** que variables de la base tienen mapeo en el diccionario.
- **Codigos sin mapeo:** reportar explicitamente.
- **Duplicados:** warning con conteo.
- **Variables en base no documentadas:** reportar.

---

## Productos generados por `src/dictionary.py`

| Archivo | Contenido |
|---|---|
| `data/processed/diccionario_limpio.parquet` | Tabla maestra limpia |
| `data/processed/mapeos_variables.json` | `{variable: {codigo: categoria}}` |
| `data/processed/metadata_variables.parquet` | Una fila por variable |
| `data/processed/reporte_cobertura_diccionario.md` | Reporte de cobertura |

---

## Mapeos complementarios

Variables con metadata en el diccionario pero sin codigos explicitos se resuelven en `src/config.py -> MAPEOS_COMPLEMENTARIOS`, con trazabilidad al Manual GEIH DANE y al protocolo del portafolio.

Casos documentados:
- `P3271` (sexo al nacer). Ver DT-002.
- `RAMA2D_R4` (division CIIU Rev. 4): se agrupa en sectores amplios siguiendo `portafolio/bases_datos/geih/protocolo_diccionario_geih.md`.
