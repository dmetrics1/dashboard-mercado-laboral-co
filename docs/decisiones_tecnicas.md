# Log de decisiones tecnicas

Ultima revision: 2026-05-09 (quinta actualizacion).

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

**Decision:** la app incorpora bloques narrativos con `render_interpretation()`, marcas temporales en graficos y mapas coropleticos departamentales con GeoJSON. En abril de 2026 se refino la interfaz para compactar espacios, reforzar contenedores en modo claro/oscuro y mejorar la legibilidad de ejes/valores.

**Razon:** el dashboard no solo presenta indicadores; tambien guia lectura economica para usuarios academicos y tomadores de decision. Los mapas coropleticos sustituyen burbujas o dispersiones porque representan mejor la comparacion territorial por departamento.

**Implicaciones de implementacion:**

- `app/main.py -> plot_mapa_departamentos()` usa `go.Choroplethmapbox` y `data/reference/colombia_departamentos.geojson`.
- El mapa mantiene contexto territorial con base cartografica, zoom medio-cercano, leyenda interna y una perspectiva ligera (`pitch` bajo) para evitar distorsion.
- Los graficos Plotly se renderizan sobre contenedores con fondo, borde y sombra suave para que los valores sean legibles en modo claro y oscuro.
- La dimension `departamento` se genera en `src/etl.py` con `DPTO_label`.
- La vista `Instrucciones` queda separada de las vistas filtrables y sirve como guia de uso para facultades y programas.

## DT-010 - Rediseno visual editorial (2026-04-25)

**Decision:** refactorizacion completa del sistema visual de `app/main.py` siguiendo principios de la skill `frontend-design` (anthropics/skills): direccion estetica comprometida, tipografia distintiva, paleta coherente, sin estetica generica de IA.

**Razon:** auditoria de diseno detecto inconsistencias entre el acento de UI (morado) y la paleta de graficos (azul-teal), falta de contenedores visibles para graficos en modo claro, mini-cards redundantes que triplicaban la misma informacion, e interpretaciones incorrectas que citaban graficos inexistentes en la vista activa.

**Implicaciones de implementacion:**

- **Tipografia dual:** `Fraunces` (serif editorial) para KPIs/titulos + `Manrope` (humanista sans) para body. Se eliminan Inter, Roboto y fuentes genericas.
- **Paleta unificada:** acento morado (`#7C3AED`) eliminado. Todo el sistema UI usa la escala BLUE_TEAL_DISCRETE. Modo claro en familia cromatica calida arena/lino (`#F4EFE6` base).
- **Contenedores de graficos:** `[data-testid="stPlotlyChart"]` recupera borde, padding y sombra. Sidebar y tarjeta de filtros usan el mismo `panel_bg` que las KPI cards para coherencia total.
- **KPI cards:** stripe horizontal 3px en degradado BT_NAVY→BT_TEAL al tope de cada card.
- **Eliminacion de redundancias:** mini-cards laterales de `view_resumen` eliminadas (duplicaban KPIs y extremos del mapa). Comparativo departamental cambiado a "mayor TD" en lugar de "menor TD". "Pulso nacional" de `view_instrucciones` eliminado (repetia KPIs del Resumen).
- **Vistas Instrucciones y Metodologia:** reescritas completamente. Instrucciones incluye glosario de 6 indicadores, 4 rutas de lectura por perfil (Ingenieria, Ciencias Sociales, Decanaturas, Periodismo) y 5 reglas de interpretacion. Metodologia incluye tabla de trazabilidad indicador→variable→calculo.
- **Interpretaciones corregidas:** cada `render_interpretation()` corresponde exactamente a los graficos visibles en su vista. Eliminado texto sobre "piramide poblacional" en vista Brechas y "esta zona" en Ocupados.
- **Codigo muerto:** `BAR_COLORS_DARK` y `BAR_COLORS_LIGHT` (identicos, sin uso) eliminados.

---

## DT-011 - Eliminacion de indentacion en st.markdown

**Decision:** remover toda indentación (espacios iniciales) dentro de las f-strings multilínea pasadas a `st.markdown` en los componentes UI (`render_section`, `render_interpretation`, `render_kpi`, etc.).

**Razon:** el procesador de Markdown de Streamlit interpreta líneas con 4 o más espacios iniciales como bloques de código. Esto causaba que el HTML inyectado se renderizara como texto literal (ej. el tag `</div>` huérfano) dentro de cajas con fondo oscuro, rompiendo la interfaz. Al limpiar la indentación, el motor de Markdown procesa el contenido correctamente como HTML puro.

---

## DT-012 - Implementación de "Limpiar Filtros" con callbacks

**Decision:** añadir un botón de reseteo de filtros que utiliza `on_click` para limpiar las variables de `st.session_state` asociadas a los widgets de filtrado.

**Razon:** intentar modificar el estado de un widget directamente en el cuerpo del script (después de su definición) provoca una `StreamlitAPIException`. El uso de un callback asegura que el cambio de estado ocurra antes del re-renderizado de los widgets en el siguiente ciclo.

---

## DT-013 - Refuerzo de contraste en selectores (Modo Claro)

**Decision:** aplicar selectores CSS más agresivos (`[data-baseweb="list-item"]`) y colores sólidos para el resaltado de opciones en los menús desplegables.

**Razon:** los estilos por defecto de Streamlit/BaseWeb en modo claro aplicaban un fondo oscuro con texto oscuro al seleccionar/hover, haciendo las opciones ilegibles. Se forzó un color de fondo gris claro sólido y se aseguró que todos los elementos hijos hereden el color de texto oscuro.

---

## DT-014 - Cruces geo x demografico para vista Poblacion

**Decision:** agregar 10 dimensiones geo x demografico al ETL (`dpto_sexo_edad`, `dpto_educacion`, `dpto_estado_civil`, `dpto_sexo`, `dpto_clase` y sus equivalentes `ciudad_*`) para que la vista Poblacion responda a los filtros de departamento y ciudad.

**Razon:** el parquet original solo calculaba indicadores demograficos a nivel nacional, dejando los filtros territoriales sin efecto en la vista Poblacion. La solicion correcta es generar los cruces en el ETL (no en el dashboard) para mantener la separacion entre capa de datos y capa de presentacion.

**Implementacion:**

- `src/etl.py -> DIMENSIONES`: 10 entradas nuevas con columnas de corte combinadas (p. ej. `["DPTO_label", "P3271_label", "grupo_edad"]`). El ETL reutiliza `calcular_dimension()` sin modificaciones; el `pl.concat(..., how="diagonal_relaxed")` maneja las columnas extras con nulls.
- `app/main.py`: helper `_dem(base_dim)` definido en el cuerpo del script antes de los filtros demograficos. Cuando `geo_level == "Departamento"` y hay departamento seleccionado, `_dem` elige la dimension `dpto_<base_dim>`; si esta vacia (departamento sin datos), cae al agregado nacional. Mismo patron para ciudades.
- El aviso informativo de `view_caracterizacion` ("filtro territorial aun no modifica vistas demograficas") fue eliminado.

**Impacto en parquet:** 6.160 filas -> 106.061 filas. Tamanio en disco sigue siendo manejable para uso local de Streamlit.

**Vistas beneficiadas:** Poblacion (piramide, educacion, estado civil, clase, sexo), Ocupados (piramide de ocupados, educacion e ingresos) y Desocupados (piramide de desocupados, educacion). Todos usan `df_sx_age`, `df_edu`, `df_civil`, `df_sexo` o `df_clase` que ahora pasan por `_dem()`.

---

## DT-015 - Correcciones de KPIs en vista Poblacion y mejoras de mapas

**Decision:** conjunto de correcciones de datos y UI aplicadas a la vista Poblacion y a los mapas de Resumen, Ocupados y Desocupados.

**Correcciones de datos:**

- **KPI Poblacion total:** usaba `df_sx_age` (dimension `sexo_edad`) que excluye menores de 15 porque `asignar_grupo_edad` les asigna `grupo_edad=null`. Resultado incorrecto: 40.9 M en lugar de 52.3 M. Corregido usando `df_sexo` (suma Hombre + Mujer incluye todos los rangos de edad).
- **KPI Poblacion urbana:** el label real en el parquet es `"Urbano"` (no `"Urbana"`). El filtro `== "Urbana"` retornaba 0 filas y mostraba 0.0%.
- **Delta en Mujeres y Urbana:** los KPIs solo mostraban el valor del ultimo periodo. Se agrego calculo del penultimo periodo para mostrar `delta vs periodo anterior` consistente con el resto de vistas.

**Correcciones de UI:**

- **Altura de KPI cards:** `min-height: 116px` cambiado a `height: 148px` fijo para que todas las cards de todas las vistas tengan la misma dimension, independientemente del contenido.
- **`.kpi-value-sm`:** nueva clase CSS (1.45rem / weight 600) para valores de texto largo (p.ej. "Basica primaria"). Evita que el texto se corte o desborde la card.
- **Nivel educativo:** valor truncado antes del parentesis (`"Basica primaria (1o - 5o)"` -> `"Basica primaria"`) para caber en la card estandar.

**Correcciones de mapa de ciudades (`plot_mapa_ciudades`):**

- Matching fragil reemplazado por lookup via `_geo_key()` + strip de sufijos `" AM"` y `" DC"`. Clave `"Bogota D.C."` corregida a `"Bogota"` en `CITY_COORDS`.
- `mode="markers+text"` cambiado a `mode="markers"`: las etiquetas de texto superponian 23 ciudades; el hover muestra el dato completo.
- Panel de control del mapa de ciudades equiparado al departamental: container con titulo, subtitulo y extremos Mayor/Menor.
- Mapa de ciudades movido fuera del bloque `if not df_dep.empty` para que sea independiente del mapa departamental.

**Renombrados en vista Desocupados:**

- KPI `"Fuera de fuerza de trabajo (FFT)"` -> `"Inactivos"`.
- Seccion `"Fuera de fuerza de trabajo (FFT)"` -> `"Poblacion inactiva"`.
- Titulo del grafico de barras -> `"Poblacion inactiva (FFT)"`.
- Warnings obsoletos de geo eliminados en Ocupados y Desocupados (ya cubiertos por DT-014).

---

## DT-016 - Reduccion de KPIs en vista Poblacion y mejoras visuales de mapas (2026-04-26)

**Decision:** eliminacion del KPI "Educacion predominante" en vista Poblacion; aumento de pitch en mapa departamental; tamano proporcional al valor en burbujas del mapa de ciudades.

**KPI Educacion predominante eliminado:**

- Vista Poblacion pasa de 4 KPIs a 3: Poblacion total, Mujeres y Poblacion urbana.
- `st.columns(4)` cambiado a `st.columns(3)`. Todo el codigo del bloque KPI 4 (calculo de nivel modal, card con `kpi-value-sm`) eliminado.
- Razon: el dato (nivel educativo modal) es menos relevante que los tres demograficos y repetia informacion ya visible en el grafico de barras de la seccion inferior.

**Mapa departamental — efecto perspectiva:**

- `mapbox pitch` aumentado de 10 a 40 grados en `plot_mapa_departamentos()`.
- `marker_opacity` subido a 1.0, `marker_line_width` a 1.0 y `marker_line_color` cambiado a blanco 75% de opacidad.
- Resultado: los departamentos del sur/centro aparecen en primer plano y los del norte se alejan en perspectiva, replicando el efecto visual 3D de un mapa isometrico.

**Mapa de ciudades — burbujas proporcionales:**

- `marker.size` cambia de valor fijo `20` a escala lineal: `18 + (v - vmin) / (vmax - vmin) * 26` (rango 18–44 px).
- `sizemode="diameter"` asegura que el diametro sea el valor mapeado.
- Ciudades con mayor TD/informalidad quedan visualmente mas prominentes; ciudades con valor minimo mantienen un tamano base legible.

---

## DT-017 - Filtro de mes, marcador de tendencia, KPI compacto y resaltado geografico (2026-05-09)

**Decision:** conjunto de mejoras de UX e interactividad aplicadas a controles, KPIs, grafico de tendencia y mapas.

**Filtro de mes en controles:**

- `render_controls()` agrega un selectbox de mes despues del selector de ano. Devuelve `(ano_ui, anos_sel, mes_ui, meses_sel, geo_level, geo_sel)`.
- `filtrar()` recibe el nuevo parametro `meses_sel` y aplica el filtro de mes ademas del de ano.
- La funcion de resumen de filtros (`render_filters_summary`) muestra un chip adicional con el mes activo.

**Grafico de tendencia con marcador mensual:**

- Cuando el usuario selecciona un ano especifico, el grafico muestra solo los 12 meses de ese ano (dtick `M1`). Cuando es "Todos" muestra la serie completa (dtick `M3`).
- `df_tendencia` se calcula sin filtro de mes para conservar la linea de fondo completa.
- Cuando se selecciona un mes, se agrega un marcador scatter sobre la linea de tendencia en el punto del mes elegido, sin ocultar los demas.

**KPI cards rediseñadas:**

- Eliminados bloque delta (`±N vs periodo ant.`) y pie (`Expandida · personas`).
- Titulo y valor centrados horizontalmente con `text-align: center`.
- Altura cambiada de `height:148px` fijo a `height:auto` con flex vertical, lo que hace las cards mas compactas.

**Leyenda del grafico de lineas bajada:**

- `legend.y` cambiado de `1.06` a `-0.18`; `yanchor` de `"bottom"` a `"top"`.
- Margen inferior del layout subido de 36 a 56 px para acomodar la leyenda sin recorte.

**Resaltado geografico en mapas (sin ocultar otras entidades):**

- `plot_mapa_departamentos`: cuando hay departamento seleccionado se agrega una segunda traza `Choroplethmapbox` sobre el mismo poligono con relleno naranja semitransparente (rgba 20%) y borde naranja 3 px (`#E05A2A`). El resto de departamentos permanece visible.
- `plot_mapa_ciudades`: cuando hay ciudad seleccionada se agrega una traza `Scattermapbox` con circulo naranja (`#E05A2A`) de diametro `base_size + 14` detras de la burbuja principal, mas una traza de texto encima. Todas las demas ciudades permanecen visibles.
- `df_city_mapa` creado sin filtro geografico (analogo a `df_dep_mapa`) para que el mapa de ciudades siempre muestre todas las ciudades independientemente del filtro de departamento o ciudad activo.
- Color naranja `#E05A2A` elegido por contraste optico con el colorscale azul-teal: elimina confusion visual entre el anillo de seleccion y las burbujas normales.

**Correccion de titulo del mapa departamental:**

- Cuando `title_prefix` esta vacio, el subtitulo encima del mapa mostraba `": TO"`. Corregido: si `title_prefix` es vacio se muestra el nombre completo del indicador (`meta['label']`); si tiene valor se usa el formato `"Prefijo: SIGLA"` como antes.

---

## DT-018 - Graficos de tendencia y mapas de ciudades en vistas Ocupados y Desocupados (2026-05-09)

**Decision:** agregar graficos de lineas interactivos y mapas de ciudades a las vistas Ocupados y Desocupados; corregir ejes en graficos de barras horizontales; bajar leyendas al pie de los graficos.

**Grafico de tendencia en Ocupados:**

- Doble eje: TO (%) en eje izquierdo azul + tasa de informalidad (%) en eje derecho teal con relleno.
- Responde al filtro de ano (dtick M1) y mes (marcador puntual con valor encima de cada linea).
- `df_tendencia` como serie de fondo; `df_context` como fallback si la tendencia no esta disponible.
- Parametros `df_tendencia`, `ano_ui`, `mes_ui` agregados a la firma de `view_ocupados`.

**Grafico de tendencia en Desocupados:**

- Doble eje: Inactivos FFT en millones (eje izquierdo teal) + TD (%) en eje derecho navy con relleno.
- No se usa tasa_inactividad (requiere PET_exp que no esta en df_tendencia); se usa FFT_exp / 1e6 directamente.
- Mismo patron de marcador mensual y dtick adaptativo que en Ocupados y Resumen.
- Parametros `df_tendencia`, `ano_ui`, `mes_ui`, `df_city_mapa` agregados a la firma de `view_desocupados`.
- Grafico de barras "Poblacion inactiva (FFT)" eliminado (redundante con la nueva linea de tendencia).

**Mapa de ciudades en Ocupados:**

- Indicadores: TO e Informalidad. Panel Mayor/Menor. Resaltado naranja al seleccionar ciudad.
- Usa `df_city_mapa` (sin filtro geo) para mostrar siempre todas las areas metropolitanas.

**Mapa de ciudades en Desocupados:**

- Indicadores: TD e Inactivos (FFT_exp). `FFT_exp` agregado a MAP_INDICATORS con `kind="count"`.
- Desocupados expandidos (`desocupados_exp`) eliminado del selector: indicadores mas relevantes son TD e Inactivos.

**Mapa departamental en Poblacion:**

- `render_map_module` reemplazado por `plot_mapa_departamentos` directo con `poblacion_total_exp`.
- Sin panel de selector; mapa a ancho completo mostrando la distribucion poblacional por departamento.

**Correccion de graficos de barras horizontales (todas las vistas):**

- Titulos de ejes Y eliminados (las categorias son autoexplicativas).
- Titulos de ejes X cambiados a nombres descriptivos: "Personas ocupadas", "Tasa de informalidad (%)", "Ingreso mediano (COP)", "Diferencia (pp)", etc.
- Subtitulos de `fig_base_h` sin referencias a variables internas (P3042, P6430, RAMA2D_R4).
- Margen derecho subido a 90 px en todos los graficos horizontales para evitar recorte del texto de valor en barras largas.
- Leyenda de piramide poblacional bajada de `y=1.08` a `y=-0.12` para evitar solapamiento con titulos vecinos.

---

## DT-019 - Rediseno visual con identidad de marca "Premium Dark Tech" (2026-08-02)

**Decision:** alinear todo el sistema visual del dashboard con la marca personal de Daniel Molina, tomando como referencia `personal_landing/colores_paleta.md` (paleta oficial) y `shiny-app/www/brand.css` + `shiny-app/R/plot_theme.R` (implementacion de la misma identidad en el dashboard R/Shiny).

**Tokens adoptados (modo oscuro, espejo de la landing):**

- Canvas `#0A0E1A` - escala de superficies `#0F1729` / `#131C31` / `#18233C` / `#202D4E`.
- Gradiente de marca `linear-gradient(135deg, #1E40AF 0%, #2563EB 50%, #06B6D4 100%)` (constante `BRAND_GRAD`): borde superior de tarjetas, item activo del nav y acentos.
- Textos `#F9FAFB` / `#E5E7EB` / `#9CA3AF`; bordes `rgba(255,255,255,0.06)`; radio 14px.
- KPIs con valor en cian `#06B6D4` (token `kpi` del tema), como los `.kpi-value` del brand.css.

**Modo claro derivado:** la landing es dark-only, por lo que el modo claro se derivo de la misma paleta con superficies frias azul-blanco (`#F3F6FB` / `#FFFFFF`), mismos acentos azul/cian oscurecidos para contraste WCAG (`#1D4ED8`, `#0891B2`).

**Graficos Plotly:**

- `BLUE_TEAL_30` regenerada como rampa de marca cian claro -> cian -> azul primario -> azul oscuro (`#EAFBFF` -> `#06B6D4` -> `#2563EB` -> `#1E40AF`).
- `BLUE_TEAL_DISCRETE` = tonos de la misma rampa; `SEX_COLORS` espejo de `COLOR_SEXO` del plot_theme.R (Hombre `#2563EB`, Mujer `#06B6D4`).
- Resaltado geografico cambiado de naranja `#E05A2A` a ambar de acento del tema (`accent_3`).

**Tipografia:** Inter (unica familia, como la marca) reemplaza a Fraunces + Manrope en CSS, graficos y documentos HTML.

**Tintas por tema (`THEMES[...]["ink"]`):** los documentos Guia y Metodologia usaban colores de la paleta de graficos como color de texto; sobre fondo oscuro quedaban ilegibles. Cada tema define ahora 6 tintas (`navy/deep/blue/teal/mint/pale`) legibles sobre su fondo, y las vistas de documento las usan sombreando localmente las constantes `BT_*`.

---

## DT-020 - Layout global con cuadricula de 8px (2026-08-02)

**Decision:** unificar el sistema de layout y espaciado de toda la aplicacion en una cuadricula de multiplos de 8px (0.5rem), de modo que las 7 vistas compartan exactamente el mismo eje de inicio y no existan saltos visuales al cambiar de modulo.

**Sistema adoptado (definido en `inject_styles`):**

- Gutter de pagina = 1rem (16px): sidebar en `top/left: 1rem`, `block-container` con `padding: 1rem 1rem 1.5rem` y `margin-left = sidebar_gap + sidebar_width` (16.5rem).
- Padding interno de cards = 1rem; padding de tarjetas de grafico = 0.5rem; mini-cards 0.5rem 1rem.
- Separadores: `.section-gap` 0.5rem, `.section-gap-lg` 1rem, `.section-header` margin 0.5rem + padding-top 0.5rem; bloques de interpretacion margin 1rem 0 1.5rem.
- Mobile y breakpoint <=1200px con el mismo gutter de 1rem.

**Correccion clave:** los `st.markdown` que inyectan elementos `position:fixed` (sidebar, tabbar) y el bloque `<style>` ocupaban slots del flex vertical de Streamlit (el `gap` de 1rem los cuenta aunque midan 0px), desplazando el contenido ~48px hacia abajo. Se sacan del flujo con `position:absolute` via `:has(.fixed-sidebar)`, `:has(.mobile-tabbar)` y un marcador `.dm-style-marker` en el markdown de estilos.

**Alineacion de documentos:** las vistas Guia y Metodologia dejan de centrar su contenido (`margin: 0 auto` -> `margin: 0`); conservan `max-width: 960px` solo por legibilidad, arrancando en el mismo eje izquierdo que las tarjetas del resto de vistas.

**Verificacion:** medicion programatica (Playwright) del primer elemento de cada vista: las 7 vistas inician en el mismo punto `[x=280, y=16]` con sidebar en `[16, 16]` a 1600px de viewport.

---

## DT-021 - Experiencia movil mobile-first (2026-08-02)

**Decision:** redisenar la capa responsive como experiencia mobile-first, con diagnostico y auditoria medidos programaticamente (Playwright a 360/390/768/1440 px).

**Diagnostico inicial (390px):** el bloque de filtros media 543px y el primer KPI empezaba en y=591 (primera pantalla sin datos); la vista Metodologia tenia 18 elementos con desbordamiento horizontal; objetivos tactiles < 44px; sin focus-visible ni prefers-reduced-motion.

**Cambios:**

- **Tipografia fluida:** escala con `clamp()` en tokens (`--fs-topbar`, `--fs-section`, `--fs-kpi`, `--fs-kpi-sm`) en lugar de overrides por breakpoint.
- **Content first en movil:** filtros en cuadricula 2x2 (selects a 2 por fila via `:has(stSelectbox)`), spacer del boton oculto (clase `.filter-btn-spacer`), boton Limpiar con altura tactil. Resultado: bloque de filtros 543px -> 348px y KPIs visibles en la primera pantalla.
- **Densidad de KPIs:** columnas con `.card` (sin grafico) a 2 por fila via `:has()`; graficos y mapas siempre a ancho completo.
- **Flujo de mapas:** el panel de indicador se ordena ANTES del mapa en movil (`order:-1` sobre la columna con `.map-control-title`): primero eliges, luego ves.
- **Grids de documentos:** clases `.dm-grid/.dm-grid-4/.dm-grid-2` reemplazan los selectores `[style*=...]` (Streamlit normaliza los atributos style y los volvia inertes — causa raiz del desborde en Metodologia). Tablas HTML con scroll interno (`stMarkdownContainer table { display:block; overflow-x:auto }`).
- **Tacto y accesibilidad (WCAG 2.2 AA):** token `--touch: 44px` aplicado a nav, botones y tab bar; `aria-label` en todos los enlaces de icono; tab bar como `<nav aria-label>`; `:focus-visible` con anillo cian en nav/botones/selects; `prefers-reduced-motion` respetado; safe-area (`env(safe-area-inset-bottom)`) en tab bar y padding inferior.
- **Microinteracciones:** `:active` scale 0.97 en elementos tactiles, hover lift de tarjetas solo en `@media (hover:hover)`.
- **Nota tecnica:** el testid de columnas en Streamlit 1.56 es `stColumn` (no `column`); el apilado previo funcionaba solo por el CSS nativo de Streamlit.

**Auditoria final:** 390px sin desbordamiento (0 elementos), Metodologia 18 -> 0 desbordes, KPIs en 2x2, desktop sin regresiones (4 KPIs en fila, hero 179px, sidebar intacta), 25 tests y ruff en verde.

---

## DT-022 - Bottom sheet de filtros y experiencia movil nativa (2026-08-02)

**Decision:** en movil los filtros salen del flujo del documento hacia un bottom sheet accionado por un FAB, siguiendo el principio "informacion antes que controles" (Stripe Dashboard / Material 3 / HIG).

**Como funciona:**

- `render_controls` emite un `<button class="dm-fab">` (icono embudo/X) y un `.dm-sheet-scrim`, solo en las vistas con filtros; ambos son `display:none` en escritorio.
- El JS de `components.html` (el mismo iframe del notranslate) registra UN listener delegado en `document` con guard `doc.__dmSheetHooked`: click en `.dm-fab` togglea la clase `dm-filters-open` en `<html>`, click en el scrim o tecla Escape la quitan. El listener y la clase sobreviven a los reruns de Streamlit (se reconstruye el body, no el html).
- CSS movil: el `stHorizontalBlock` de filtros se vuelve `position:fixed` inferior con `translateY(110%)` cerrado / `translateY(0)` abierto, scrim con opacidad, popovers de selects con z-index sobre el sheet, cabecera "FILTROS" via `::before`.
- El sheet queda abierto tras cambiar un filtro (rerun): permite ajustar varios antes de cerrar.

**Efecto medido (390x844):** el primer KPI pasa de y=591 (inicio del dia) a y=142; la primera pantalla muestra titulo, 4 KPIs y el inicio de la tendencia.

**Otros cambios de la iteracion:**

- Encabezados de seccion sticky en movil (orientacion en scroll largo).
- Ticks del eje X responsivos: se elimina `dtick="M3"` fijo en las series; Plotly densifica segun el ancho real (en movil ~1 tick por anio, en desktop semestral). `dtick="M1"` se conserva solo con un anio especifico seleccionado.
- Fix a11y critico: la regla de `prefers-reduced-motion` anulaba `transform` y habria dejado el sheet siempre visible; ahora solo neutraliza duraciones.
- Sin hueco residual en la tarjeta de titulo (gap 0 del bloque en movil).

---

## DT-023 - Drawer de navegacion movil y aire entre KPIs (2026-08-02)

**Decision:** en movil la sidebar (ya existente, con marca y pildora activa) se convierte en drawer deslizante desde la izquierda, accionado por una hamburguesa flotante — mismo patron visual del Observatorio GEIH en Shiny, para coherencia entre productos DM.

- Hamburguesa fija arriba-izquierda (48px, panel_solid) + scrim propio (.dm-nav-scrim); el contenido movil recibe padding-top 4.5rem para despejarla.
- El drawer reutiliza `.fixed-sidebar` con `translateX(-110%)` cerrado / `translateX(0)` abierto (clase `dm-nav-open` en <html>), radio 0 22px 22px 0, `100dvh` y safe-area-inset-top.
- Mismo mecanismo robusto del bottom sheet (DT-022): listener delegado unico en document, cierre por scrim y Escape; navegar recarga la pagina y el drawer se cierra solo (el <html> se recrea).
- Coexiste con la tab bar inferior: tab bar = cambio rapido de vista con un toque; drawer = menu completo etiquetado + marca + LinkedIn/GitHub/tema.
- KPIs en movil con mas respiracion: gap del flex 1rem (cuadricula 8px) y margen inferior de tarjeta, como la referencia del Observatorio.

Verificado con Playwright (390px): abre en left:0 con 304px de ancho, navega a otra vista y queda cerrado; desktop sin cambios.

---

## DT-024 - Eliminacion de la tab bar inferior en movil (2026-08-02)

**Decision:** con el drawer de navegacion (DT-023) operativo, la tab bar inferior se elimina: dos sistemas de navegacion paralelos duplicaban la misma jerarquia (7 vistas) y anadian carga cognitiva. El drawer queda como navegacion unica (hamburguesa flotante siempre visible), el FAB de filtros baja a la esquina inferior derecha (bottom 1.25rem + safe-area) y el padding inferior del contenido se ajusta a 6rem. El toggle de tema sigue disponible en el pie del drawer. Se retiran el markup de la tab bar, sus reglas CSS y sus selectores auxiliares.

---

## DT-025 - Alineacion tipografica al sistema de diseno formal (2026-08-02)

**Decision:** adoptar la tipografia del sistema `dm-design-system` (tokens.json > typography): titulos en **Space Grotesk 600/700** (puente gratuito hacia Aeonik), cuerpo en **Inter 400/500**, y numeros de KPI / tablas / codigos de variable en **JetBrains Mono** con `font-variant-numeric: tabular-nums`.

**Aplicacion:**

- Tokens CSS `--font-heading` y `--font-mono`; import de Google Fonts ampliado.
- Heading: `.topbar-title`, `.section-header-title`, `.interpretation-title`, `.display-serif`, encabezados h2 y titulos de los documentos Guia/Metodologia, y titulos de graficos Plotly (family en `fig_base`).
- Mono: `.kpi-value`, `.kpi-value-sm`, `.mini-value`, `.map-extreme-value`, valores de `param_card`, codigos de indicador (`TD`, `PET`...) en Guia/Metodologia, pills de formula y columna de variables de la tabla de trazabilidad (antes `monospace` generico).
- `render_kpi` agrega la clase `kpi-value--long` cuando el valor supera 8 caracteres; en movil baja un paso de la escala fluida — evita que `$1.500.000` (mas ancho en mono) se parta dentro de la tarjeta.

Verificado en dark/light y 390/1440 px; 25 tests y ruff en verde. Pendiente del sistema formal: consumir `dist/tokens.py` en lugar del dict `THEMES` hardcodeado.
