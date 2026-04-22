# Plan de mejoras — Auditoría externa del dashboard

Estado de revisión: actualizado el 2026-04-22. Las tareas del checklist final
figuran como completadas en el código actual; el cuerpo del documento conserva
la descripción original de los problemas para trazabilidad histórica.

Auditoría externa dio score 6.7/10. Atacamos las 7 recomendaciones de mayor impacto en este orden:

**R4 → R6 → R1 → R3 → R2 → R5 → R7**

Cada tarea es independiente. Ejecutar **una a la vez**, verificar en navegador, y avanzar a la siguiente.

---

## TAREA 1 — R4: Truncar labels en "Posición ocupacional"

**Problema:** En `view_ocupados`, el bar chart horizontal de P6430 muestra labels tipo "rabajador sin remuneración..." con la primera letra cortada. Causa: el margen izquierdo del chart es insuficiente para textos largos.

**Archivos:** [app/main.py:1644-1665](../app/main.py#L1644-L1665)

**Cambios:**
1. Antes del `px.bar`, crear columna `P6430_label_corto` que trunque a 38 caracteres con sufijo "…" cuando excede.
2. Pasar `y="P6430_label_corto"` al `px.bar` y añadir `custom_data=["P6430_label"]` con el label completo.
3. En `hovertemplate`, mostrar `%{customdata[0]}` para que el tooltip tenga el texto íntegro.
4. En `fig.update_layout`, agregar `margin=dict(l=200, r=24, t=56, b=40)` y `fig.update_yaxes(automargin=True, tickfont=dict(size=11))`.

**Restricciones:** No tocar otras vistas. No cambiar colores ni el orden de las barras.

**Verificación:** vista Ocupados → ningún label cortado, hover muestra texto completo.

---

## TAREA 2 — R6: Ocultar chips de filtros en estado default

**Problema:** `render_filters_summary` siempre dibuja 3 chips (Año, Nivel territorial, Ubicación) aunque el usuario no haya tocado ningún filtro. Genera ruido visual en la primera carga.

**Archivos:** [app/main.py:1223-1229](../app/main.py#L1223-L1229)

**Cambios:** Reemplazar la función por:

```python
def render_filters_summary(ano_ui, geo_level, geo_sel):
    chips = []
    if ano_ui != "Todos":
        chips.append(f"<span class='pill'>📅 {ano_ui}</span>")
    if geo_level != "Sin filtro":
        chips.append(f"<span class='pill'>🗺 {geo_level}</span>")
    if geo_sel not in ("Todas", "Todos"):
        chips.append(f"<span class='pill'>📍 {geo_sel}</span>")
    if not chips:
        return
    st.markdown(f"<div class='pill-row'>{''.join(chips)}</div>", unsafe_allow_html=True)
```

**Restricciones:** No tocar la invocación en línea 2015 ni el CSS de `.pill`.

**Verificación:** estado limpio → no chips. Cambiar año a "2024" → solo chip de Año.

---

## TAREA 3 — R1: Indicador de informalidad

**Problema original:** Al momento de la auditoría, el dashboard no calculaba tasa de informalidad pese a que las variables ya estaban cargadas (`P6090`, `P6920` en config.py:86). Esta brecha ya fue cerrada en el código actual.

**Definición:** Informal = ocupado con `P6090 == 2` (no afiliado a salud contributiva). Tasa = `informales_exp / ocupados_exp × 100`. Rango esperado nacional: 55-60%.

### 3.a — ETL: agregar `tasa_informalidad`

**Archivos:** [src/indicators.py:37-73](../src/indicators.py#L37-L73)

**Cambios en `_agg_mercado_laboral`:**
1. Hacer `P6090` opcional. Si la columna no está, agregarla como `pl.lit(None).cast(pl.Int8).alias("P6090")` antes del group_by.
2. Dentro del `.agg(...)`, añadir:
   ```python
   (
       pl.when((pl.col("OCI").fill_null(0) == 1) & (pl.col("P6090").cast(pl.Int8) == 2))
         .then(pl.col(FEX))
         .otherwise(0.0)
   ).sum().alias("informales_exp"),
   ```
3. En `.with_columns(...)`, añadir:
   ```python
   (pl.col("informales_exp") / pl.col("ocupados_exp") * 100)
   .alias("tasa_informalidad"),
   ```

**Restricciones:** No modificar `_agg_resumen_poblacional` ni `_agg_ingreso_mediano`.

### 3.b — Regenerar parquet

Ejecutar el script ETL existente (probablemente `python -m scripts.build_indicadores` o similar). Validar:
- Columna `tasa_informalidad` presente en `data/processed/indicadores_mensuales.parquet`.
- Promedio para `dimension == "nacional"` y año 2024 entre 50 y 70.

### 3.c — UI: módulo de informalidad en `view_ocupados`

**Archivos:** [app/main.py:1576-1724](../app/main.py#L1576-L1724)

**Cambios:**
1. **KPI nuevo:** En la fila de KPIs principales, añadir columna "Tasa de informalidad" usando `row.get("tasa_informalidad")` con formato `f"{val:.1f}%"`. Calcular delta vs mes previo igual que los otros KPIs.
2. **Sección nueva** tras "Estructura sectorial" (antes de "Posición ocupacional"):
   - `render_section("Informalidad laboral", "P6090: ocupados sin afiliación contributiva")`
   - Bar chart horizontal de `tasa_informalidad` por `RAMA2D_R4_label` (top 10 con mayor informalidad), promedio del periodo filtrado.
   - Texto interpretativo breve (2 líneas) sobre rango 55-60% nacional y concentración en agro/comercio.

**Restricciones:** No insertar serie temporal de informalidad — eso queda para v2.

**Verificación:** vista Ocupados → KPI nuevo ~58%, sección nueva con bar chart por rama.

---

## TAREA 4 — R3: Doble eje Y para TD vs TO/TGP

**Problema:** En `view_resumen`, el chart de tendencia muestra TD (~10%), TO (~60%) y TGP (~64%) en el mismo eje. TD se ve como línea casi plana porque la escala la aplasta.

**Archivos:** [app/main.py:1374-1402](../app/main.py#L1374-L1402)

**Cambios:**
1. Importar `from plotly.subplots import make_subplots` al inicio del archivo si no está.
2. Reemplazar `fig = go.Figure()` por `fig = make_subplots(specs=[[{"secondary_y": True}]])`.
3. En el loop `for ind in ["TGP", "TO", "TD"]:`, agregar cada `add_trace` con `secondary_y=True` cuando `ind == "TD"`, `False` para los otros dos.
4. Después del loop:
   ```python
   fig.update_yaxes(title_text="TO / TGP (%)", ticksuffix="%", secondary_y=False)
   fig.update_yaxes(title_text="TD (%)", ticksuffix="%", secondary_y=True, showgrid=False)
   ```
5. Mantener `fill="tozeroy"` para TD (queda en su propio eje, ya no aplasta a las otras).

**Restricciones:** No tocar colores ni `hovertemplate`. No tocar otros charts.

**Verificación:** vista Resumen → TD se mueve en su propio rango (8-12% visible con detalle), TO/TGP en eje izquierdo. Eje derecho rotulado "TD (%)".

---

## TAREA 5 — R2: Mapa coroplético reemplaza burbujas

**Problema:** `plot_mapa_departamentos` usa `Scattermapbox` con dos capas de burbujas. Codifica magnitud por color y tamaño (redundante) y deja vacíos visuales entre departamentos. Los dashboards económicos colombianos publicables usan coroplético.

**Archivos:** [app/main.py:190-330](../app/main.py#L190-L330) (función). Invocada en líneas 1460 y 1913.

**Riesgo:** Requiere GeoJSON externo (~1-3 MB). Si no está descargado, hay que descargarlo y guardarlo en `data/reference/`.

**Cambios:**
1. Verificar si existe `data/reference/colombia_departamentos.geojson`. Si no, descargar desde fuente oficial (DANE o https://gist.github.com/john-guerra/43c7656821069d00dcbc) y guardar allí. Confirmar que tiene `properties.DPTO` o `properties.NOMBRE_DPT` con códigos/nombres compatibles con `DPTO_label`.
2. Reescribir `plot_mapa_departamentos` usando `go.Choroplethmapbox`:
   - Cargar GeoJSON con `@st.cache_data` (helper `_load_geojson_dptos()`).
   - Reemplazar ambas capas `Scattermapbox` por una sola `Choroplethmapbox` con `featureidkey` apuntando al campo correcto.
   - `marker_opacity=0.85`, `marker_line_width=0.6`, `marker_line_color=t["bg"]`.
   - `hovertemplate="<b>%{customdata}</b><br>" + indicador + ": %{z:.1f}%<extra></extra>"`.
3. Si los centroides hardcodeados (líneas 150-175) ya no se usan en otra función, eliminarlos.
4. Verificar que las llamadas en líneas 1460 y 1913 siguen funcionando sin cambios en la firma.

**Verificación:** vistas Resumen y Brechas → mapa muestra polígonos de departamentos coloreados, no burbujas. Hover con nombre y valor. Funciona en modo oscuro y claro.

---

## TAREA 6 — R5: Anotaciones de eventos en series temporales

**Problema:** Los charts de tendencia mensual no marcan eventos relevantes (cambio metodológico GEIH 2022, etc.), lo que dificulta lectura de quiebres.

**Archivos:**
- [app/main.py:1374-1402](../app/main.py#L1374-L1402) — TD/TO/TGP en `view_resumen` (después de R3).
- [app/main.py:1844-1858](../app/main.py#L1844-L1858) — Brecha de género en `view_brechas`.

**Cambios:**
1. Crear helper en `app/main.py` (cerca de `fig_base`, antes de las vistas):
   ```python
   def add_eventos_geih(fig, t):
       fig.add_vline(
           x="2022-03-01",
           line_width=1, line_dash="dot", line_color=t["soft_text"],
           annotation_text="Cambio metodológico GEIH",
           annotation_position="top",
           annotation_font_size=10,
           annotation_font_color=t["soft_text"],
       )
       return fig
   ```
2. Llamar `fig = add_eventos_geih(fig, t)` justo antes de cada `st.plotly_chart` en:
   - `view_resumen` chart de tendencia (después de R3).
   - `view_brechas` chart de brecha de género TD.

**Restricciones:** Solo el cambio metodológico por ahora — mantenerlo limpio.

**Verificación:** vistas Resumen y Brechas → línea vertical punteada en marzo 2022 con etiqueta "Cambio metodológico GEIH".

---

## TAREA 7 — R7: Texto interpretativo entre gráficos

**Problema:** El dashboard muestra datos sin guiar la lectura. Para portafolio (audiencia mixta técnica/no técnica) falta narrativa breve que destaque hallazgos.

**Archivos:** múltiples vistas en `app/main.py`.

**Cambios:**
1. Añadir al CSS en `inject_styles` (~línea 137):
   ```css
   .interpretation-block {
       background: var(--secondary-bg);
       border-left: 3px solid var(--accent);
       padding: 0.75rem 1rem;
       margin: 0.5rem 0 1.25rem 0;
       border-radius: 4px;
       font-size: 0.92rem;
       color: var(--soft-text);
       line-height: 1.5;
   }
   ```
   Si las variables CSS no están definidas para ambos temas, usar valores hex directos del dict `t`.
2. Crear helper `def render_interpretation(text: str)` que renderice:
   ```python
   st.markdown(f"<div class='interpretation-block'>{text}</div>", unsafe_allow_html=True)
   ```
3. Insertar llamadas con textos breves (2-4 líneas, datos concretos, sin adjetivos vacíos):

| Vista | Línea aprox | Contenido |
|---|---|---|
| `view_resumen` | ~1370 | TD ronda 10%, por debajo del promedio histórico ~12% |
| `view_resumen` | ~1425 | Patrón territorial: Chocó, Quibdó suelen liderar TD |
| `view_caracterizacion` | ~1502 | Lectura demográfica de la pirámide |
| `view_ocupados` | ~1602 | Estructura del empleo (servicios > industria > agro) |
| `view_desocupados` | ~1768 | Distinción desempleo abierto vs inactividad (FFT) |
| `view_brechas` | ~1837 | Por qué importan las brechas de género/edad |

**Restricciones:** Tono sobrio, datos concretos, sin emojis.

**Verificación:** las 5 vistas tienen 1-2 bloques interpretativos visibles, estilo coherente con tema oscuro y claro.

---

## Lo que NO se hace

Recomendaciones fuera de alcance (sobredimensionadas para portafolio o ya cubiertas):

- R8 NINI, R9 quinquenios en brechas, R10 percentiles ingreso → v2 o post LinkedIn.
- R11 benchmarks mapa, R12 sub-página informalidad ciudades → scope creep.
- R13 selector indicador tendencia → ya hay selectbox de indicador en mapa.
- R14 CI/CD → infraestructura, no producto.
- R15 responsive sidebar → Streamlit limita esto.

---

## Checklist de progreso

- [x] T1 — R4 labels truncadas
- [x] T2 — R6 chips default
- [x] T3a — R1 ETL informalidad
- [x] T3b — R1 regenerar parquet
- [x] T3c — R1 UI informalidad
- [x] T4 — R3 doble eje Y
- [x] T5 — R2 mapa coroplético
- [x] T6 — R5 anotaciones eventos
- [x] T7 — R7 texto interpretativo
