# Log de decisiones tecnicas

Ultima revision: 2026-04-22.

---

## DT-001 - Variable de sexo: `P3271`, no `P6020`

**Decision:** usar `P3271` para sexo al nacer en todas las bases 2022-2025.

**Razon:** la GEIH fue redisenada a partir de 2022. En el diseno anterior la variable era `P6020`; en el rediseno paso a `P3271`. Este proyecto cubre exclusivamente la encuesta redisenada.

---

## DT-002 - Mapeos complementarios en `config.py`

**Decision:** variables con metadata en el diccionario pero sin codigos explicitos se mapean en `src/config.py -> MAPEOS_COMPLEMENTARIOS`.

**Razon:** `P3271`, `CLASE`, `P3042` y `RAMA2D_R4` requieren una capa semantica estable para el dashboard. Centralizar estos mapeos evita hardcodeo disperso y conserva trazabilidad metodologica.

---

## DT-003 - `AREA` y `DPTO` siempre como `string`

**Decision:** cargar `AREA` y `DPTO` con tipo texto en todo el pipeline.

**Razon:** los codigos territoriales tienen ceros a la izquierda significativos (`05`, `08`, `11`). Convertirlos a entero destruye informacion y rompe joins con diccionario o GeoJSON.

---

## DT-004 - Duplicados `(variable, codigo)` en diccionario: conservar primero, warning

**Decision:** cuando el diccionario tiene la misma pareja `(nombre_variable, codigo_categoria)` con categorias distintas, se conserva la primera ocurrencia y se emite `warnings.warn`.

**Razon:** el diccionario real contiene conflictos tipograficos y de acentuacion. Conservar el primero es reproducible; el warning mantiene visible el problema sin detener el pipeline.

---

## DT-005 - Recodificacion opcion 1: conservar original + `_label`

**Decision:** al aplicar el diccionario, conservar la columna original y agregar `<col>_label`.

**Razon:** la columna original se usa para filtros, joins y comparabilidad entre anos. La columna `_label` es la capa de presentacion del dashboard.

---

## DT-006 - Parquet para tabular, JSON solo para mapeos

**Decision:** los archivos procesados tabulares se guardan en Parquet; los mapeos `{variable: {codigo: categoria}}` se guardan en JSON.

**Razon:** Parquet preserva tipos y acelera lectura. JSON es mas facil de inspeccionar para estructuras pequenas de mapeo.

---

## DT-007 - Dashboard con tema dual y sidebar fija sin colapso

**Decision:** `app/main.py` soporta dos temas visuales (`Dark` y `Light`) y oculta el control nativo de colapso del sidebar.

**Razon:** el dashboard esta pensado para lectura analitica de escritorio. La barra lateral fija mejora continuidad de filtros e identidad visual; el tema dual permite trabajar en entornos claros u oscuros sin duplicar componentes.

---

## DT-008 - Calculo de informalidad laboral con metodologia DANE

**Decision:** la tasa de informalidad usa la regla DANE implementada en `src/indicators.py -> _calcular_formalidad_dane()` cuando el dataset contiene todas las columnas requeridas.

**Razon:** la informalidad laboral no depende de una unica variable. La regla combina posicion ocupacional, salud, pension, registro mercantil, tamano del establecimiento, oficio y rama de actividad. El resultado se agrega como `informales_exp` y `tasa_informalidad`.

**Variables clave:** `P6430`, `P6100`, `P6110`, `P6450`, `P6920`, `P6930`, `P6940`, `RAMA2D_R4`, `P3045S1`, `P3046`, `P3069`, `P6765`, `P3065`, `P3066`, `P3067`, `P3067S1`, `P3067S2`, `P6775`, `P3068`, `OFICIO_C8`.

**Fallback:** si faltan esas columnas en datasets minimos de prueba, el calculo degrada a una regla simple basada en `P6090` para no romper TD/TO/TGP.

---

## DT-009 - Storytelling UI y refinamiento geo-espacial

**Decision:** la app incorpora bloques narrativos con `render_interpretation()`, marcas temporales en graficos y mapas coropleticos departamentales con GeoJSON.

**Razon:** el dashboard no solo presenta indicadores; tambien guia lectura economica para usuarios academicos y tomadores de decision. Los mapas coropleticos sustituyen burbujas o dispersiones porque representan mejor la comparacion territorial por departamento.

**Implicaciones de implementacion:**

- `app/main.py -> plot_mapa_departamentos()` usa `go.Choroplethmapbox` y `data/reference/colombia_departamentos.geojson`.
- La dimension `departamento` se genera en `src/etl.py` con `DPTO_label`.
- La vista `Instrucciones` queda separada de las vistas filtrables y sirve como guia de uso para facultades y programas.
