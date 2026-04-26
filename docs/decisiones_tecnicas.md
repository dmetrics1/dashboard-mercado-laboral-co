# Log de decisiones tecnicas

Ultima revision: 2026-04-26 (tercera actualizacion).

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
