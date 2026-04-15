# Log de decisiones tecnicas

---

## DT-001 - Variable de sexo: `P3271`, no `P6020`

**Decision:** usar `P3271` para sexo al nacer en todas las bases 2022-2025.

**Razon:** la GEIH fue redisenada a partir del ano 2022. En el diseno anterior la variable era `P6020`; en el rediseno paso a `P3271`. Este proyecto cubre exclusivamente la encuesta redisenada, por lo que `P6020` no aplica.

---

## DT-002 - Mapeos complementarios en `config.py`

**Decision:** variables con metadata en el diccionario pero sin codigos explicitos se mapean en `src/config.py -> MAPEOS_COMPLEMENTARIOS`.

**Razon:** `P3271` aparece en el diccionario con metadata pero sin filas de `codigo_categoria`. Los valores `1=Hombre, 2=Mujer` estan documentados en el Manual Metodologico GEIH 2025 (DANE DIMPE, version 55). `RAMA2D_R4` tambien aparece solo con metadata; por eso su agrupacion sectorial se resuelve en `MAPEOS_COMPLEMENTARIOS` usando la regla documentada en `portafolio/bases_datos/geih/protocolo_diccionario_geih.md`. Centralizar estos mapeos en `config.py` garantiza trazabilidad y evita hardcodeo disperso.

---

## DT-003 - `AREA` y `DPTO` siempre como `string`

**Decision:** cargar `AREA` y `DPTO` con `dtype="string"` en todo el pipeline.

**Razon:** los codigos de area metropolitana y departamento tienen ceros a la izquierda significativos (`05` = Medellin AM, `08` = Barranquilla AM, `11` = Bogota DC). Convertirlos a entero destruye esa informacion y rompe los joins con el diccionario.

---

## DT-004 - Duplicados `(variable, codigo)` en diccionario: conservar primero, warning

**Decision:** cuando el diccionario tiene la misma `(nombre_variable, codigo_categoria)` con categorias distintas, se conserva la primera ocurrencia y se emite `warnings.warn`.

**Razon:** el diccionario real contiene 43 de estos casos. La mayoria son variaciones tipograficas o de acentuacion. Conservar el primero es reproducible; el warning garantiza visibilidad del problema sin detener el pipeline.

---

## DT-005 - Recodificacion Opcion 1: conservar original + `_label`

**Decision:** al aplicar el diccionario, conservar la columna original y agregar `<col>_label` con la etiqueta.

**Razon:** la columna original es necesaria para filtros, joins y comparabilidad entre anos. La columna `_label` es la que se muestra en el dashboard. Reemplazar la original romperia el pipeline aguas abajo.

**Implementacion tecnica en Python (`pandas`):**
La implementacion real (ejecutada en `src/dictionary.py -> aplicar_labels`) ilustra como aplicar esto dinamicamente preservando los ceros a la izquierda, basandose en la estructura `{variable: {codigo: categoria}}`:

```python
def aplicar_labels(df: pd.DataFrame, mapeos: dict[str, dict[str, str]], variables: list[str]) -> pd.DataFrame:
    df = df.copy()
    for var in variables:
        if var in df.columns and var in mapeos:
            # .astype(str) es vital para no perder ceros a la izquierda (DT-003)
            df[f"{var}_label"] = df[var].astype(str).map(mapeos[var])
    return df
```

---

## DT-006 - Parquet para tabular, JSON solo para mapeos

**Decision:** los archivos procesados tabulares se guardan en Parquet; los mapeos `{variable: {codigo: categoria}}` se guardan en JSON.

**Razon:** Parquet es mas eficiente en lectura y preserva tipos. JSON es legible por humanos y facil de inspeccionar para los mapeos, que son estructuras de diccionario pequenas.

---

## DT-007 - Dashboard con tema dual y sidebar fija sin colapso

**Decision:** la app `app/main.py` soporta dos temas visuales (`Dark` y `Light`) y oculta el control nativo de colapso del sidebar.

**Razon:** el dashboard se usa principalmente en escritorio analitico. Mantener la barra lateral fija evita cambios bruscos de layout, mejora la legibilidad de filtros y conserva visible la identidad visual del proyecto. El tema dual permite trabajar tanto en modo oscuro como en modo claro sin duplicar componentes.

**Implicaciones de implementacion:**
- la paleta visual se centraliza en `THEMES`;
- el isotipo del sidebar se renderiza inline para adaptarse al color del tema activo;
- las tarjetas KPI usan reticula 3 + 3 en la hoja principal para evitar quiebres de texto y valores apiñados.
