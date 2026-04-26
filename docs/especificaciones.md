# Especificaciones de Diseño: Dashboard de Mercado Laboral (GEIH)

Última revisión: 2026-04-26 (segunda actualización).

Este documento refleja el estado actual del código y del parquet procesado
`data/processed/indicadores_mensuales.parquet`: 106.061 filas, 25 columnas y 22
dimensiones analíticas.

## 1. Filtros globales

- **Año:** selector múltiple sobre 2022, 2023, 2024 y 2025.
- **Nivel territorial:** Nacional, Departamento o Ciudad.
- **Ubicación:** departamentos o 23 áreas metropolitanas, según el nivel elegido.
- **Tema:** modo Dark/Light por query param.

Pendiente: granularidad trimestral/anual explícita. El parquet actual está en
frecuencia mensual.

## 2. Vistas del dashboard

| vista | estado | contenido actual |
|---|---|---|
| Resumen | listo | KPIs de población, PEA, ocupados, desocupados, TD, TO, TGP, ingreso mediano, tendencia, mapa departamental y mapa de ciudades (23 áreas metropolitanas). |
| Población | listo | 4 KPIs (población total, % mujeres, % urbana, nivel educativo) con delta; pirámide, nivel educativo, estado civil, sexo y clase urbano/rural. Responde a filtros territoriales. |
| Ocupados | listo | KPIs laborales, rama de actividad, informalidad, posición ocupacional, ciudad, educación e ingresos. Mapa departamental filtrable por TO e Informalidad. |
| Desocupados | parcial | KPIs (incluye Inactivos), pirámide, ciudad y educación. Gráfico FFT como barras. Mapa departamental filtrable por TD e Inactividad. Tiempo de búsqueda pendiente. |
| Brechas | listo | Brecha de género, brecha etaria 15-28 vs 29+, comparativo regional y mapa. |
| Instrucciones | listo | Guía de lectura para facultades y programas. No usa filtros. |
| Metodología | listo | Ficha técnica, glosario y trazabilidad de variables. No usa filtros. |

### Criterios visuales vigentes (2026-04-26)

**Tipografía dual:**
- Display: `Fraunces` (serif editorial, opsz 9–144) para KPIs, títulos de vista y mini-values.
- Body: `Manrope` (humanista sans) para todo el texto de soporte, etiquetas, pies y navegación.
- Se prohíbe explícitamente el uso de Inter, Roboto y Space Grotesk (clichés de AI-generados).

**Paleta unificada azul-teal (BLUE_TEAL_DISCRETE):**
- `#1E2D55` (BT_NAVY), `#27638A` (BT_DEEP), `#338CA1` (BT_BLUE), `#51A6AE` (BT_TEAL),
  `#7BBDBF` (BT_MINT), `#A2D0D2` (BT_PALE), `#D5EAEB` (BT_ICE).
- Los acentos de UI (sidebar activo, stripe de card, borde de interpretation-block) usan
  esta misma escala. No hay morado ni color externo al sistema.

**Modo claro — familia cromática cálida (arena/lino):**
- Fondo de app: `#F4EFE6`.
- Panel/card bg: `#FBF8F1` — usado uniformemente en KPI cards, contenedores de gráfico,
  sidebar y tarjeta de filtros (todos en el mismo tono para coherencia).
- Bordes y sombras en tono café cálido (`rgba(139,110,75,...)`) en lugar de azul-negro.
- Dropdowns y selects: fondo `#F5F0E6`, borde cálido.

**Modo oscuro:**
- Fondo de app: gradiente profundo `#080c1a → #04060f`.
- Panel bg: `rgba(15,21,40,0.96)`, borde `rgba(255,255,255,0.10)`.
- Estructura idéntica al claro; solo cambian los valores de color.

**Contenedores de gráficos:**
- `[data-testid="stPlotlyChart"]` lleva `border`, `border-radius: 10px`, `padding` y
  `box-shadow` — cumple el criterio de "gráficos dentro de contenedores propios".

**KPI cards:**
- Stripe horizontal de 3 px en degradado BT_NAVY → BT_TEAL al tope de cada `.card`.
- Altura fija `height: 148px` uniforme en todas las vistas; `overflow: hidden` evita desbordamiento.
- KPI value en Fraunces 700, 2.15rem. Valores de texto largo usan `.kpi-value-sm` (1.45rem/600).
- Todas las cards muestran delta `↑/↓ vs periodo ant.` cuando el valor es numérico.

**Section headers:**
- Usan `border-top` separador + `padding-top` generoso (0.85rem) entre secciones.
- Título en Fraunces 600, 1.32rem.

**Interpretation blocks:**
- Borde izquierdo de 4 px en BT_DEEP.
- Título con prefijo `—` generado por CSS `::before`.
- Tono sobrio, datos concretos, sin emojis.

**Reglas de no-redundancia:**
- `view_resumen`: tendencia a ancho completo; mini-cards laterales eliminadas (duplicaban KPIs).
- Comparativo departamental: muestra los de **mayor** TD/menor TO (relevante para política).
- `view_instrucciones`: sin gráfico "Pulso nacional" (repetía KPIs del Resumen).
- Todas las `render_interpretation()` reescritas para corresponder exactamente a los gráficos
  visibles en cada vista.

**Mapas:**
- **Departamental** (Resumen, Ocupados, Desocupados, Brechas): coroplético `go.Choroplethmapbox`,
  escala BLUE_TEAL_30, panel lateral con selectbox de indicador y extremos Mayor/Menor.
  - Resumen: indicadores TD, TO, TGP, Informalidad, Ocupados, Desocupados, Población, Ingreso.
  - Ocupados: solo TO e Informalidad.
  - Desocupados: solo TD e Inactividad (`tasa_inactividad = FFT_exp / PET_exp × 100`).
- **Ciudades** (Resumen): `go.Scattermapbox` con 23 áreas metropolitanas. Coordenadas en
  `CITY_COORDS`. Matching por `_geo_key()` + strip de sufijos `" AM"` / `" DC"`.
  Panel lateral con selectbox (TD, TO, Informalidad) y extremos Mayor/Menor.

## 3. Salida analítica actual

### Columnas principales

`_año`, `MES`, `dimension`, `poblacion_total_exp`, `PEA_exp`, `FFT_exp`,
`ocupados_exp`, `desocupados_exp`, `informales_exp`, `PET_exp`, `TD`, `TO`,
`TGP`, `tasa_informalidad`, `ingreso_mediano`.

### Dimensiones disponibles

| dimensión | columna de corte | filas actuales |
|---|---:|---:|
| nacional | sin corte adicional | 48 |
| departamento | `DPTO_label` | 1.152 |
| ciudad | `AREA_label` | 1.104 |
| sexo | `P3271_label` | 96 |
| edad | `grupo_edad` | 528 |
| sexo_edad | `P3271_label`, `grupo_edad` | 1.056 |
| edad_brecha | `grupo_edad_brecha` | 96 |
| sector | `RAMA2D_R4_label` | 659 |
| clase | `CLASE_label` | 96 |
| estado_civil | `P6070_label` | 288 |
| educacion | `P3042_label` | 653 |
| posicion_ocupacional | `P6430_label` | 384 |
| dpto_sexo_edad | `DPTO_label`, `P3271_label`, `grupo_edad` | 25.344 |
| dpto_educacion | `DPTO_label`, `P3042_label` | 14.759 |
| dpto_estado_civil | `DPTO_label`, `P6070_label` | 6.912 |
| dpto_sexo | `DPTO_label`, `P3271_label` | 2.304 |
| dpto_clase | `DPTO_label`, `CLASE_label` | 2.304 |
| ciudad_sexo_edad | `AREA_label`, `P3271_label`, `grupo_edad` | 24.288 |
| ciudad_educacion | `AREA_label`, `P3042_label` | 14.054 |
| ciudad_estado_civil | `AREA_label`, `P6070_label` | 6.624 |
| ciudad_sexo | `AREA_label`, `P3271_label` | 2.208 |
| ciudad_clase | `AREA_label`, `CLASE_label` | 1.104 |

## 4. Matriz de variables requeridas

| hoja | elemento | variables | estado actual | observaciones |
|---|---|---|---|---|
| Resumen | Población total | `PT`, `FEX_C18` | listo | Sale como `poblacion_total_exp`. |
| Resumen | Fuerza de trabajo | `FT`, `FEX_C18` | listo | Sale como `PEA_exp`. |
| Resumen | Ocupados | `OCI`, `FEX_C18` | listo | Sale como `ocupados_exp`. |
| Resumen | Desocupados | `DSI`, `FEX_C18` | listo | Sale como `desocupados_exp`. |
| Resumen | TD, TO, TGP | `OCI`, `DSI`, `P6040`, `FEX_C18` | listo | Calculadas en `src/indicators.py`. |
| Resumen | Mapa departamental | `DPTO`, `DPTO_label`, GeoJSON | listo | Usa `data/reference/colombia_departamentos.geojson`. |
| Población | Pirámide | `P3271`, `P6040`, `FEX_C18` | listo | Grupos quinquenales. |
| Población | Nivel educativo | `P3042` | listo | Homologado en `MAPEOS_COMPLEMENTARIOS`. |
| Población | Estado civil | `P6070` | listo | Etiquetas vía diccionario. |
| Población | Clase urbano/rural | `CLASE` | listo | Mapeo complementario `Urbana`/`Rural`. |
| Ocupados | Rama de actividad | `RAMA2D_R4` | listo | Agrupación CIIU Rev. 4. |
| Ocupados | Posición ocupacional | `P6430` | listo | Dimensión `posicion_ocupacional`. |
| Ocupados | Informalidad | variables DANE de formalidad | listo | `tasa_informalidad` usa regla DANE cuando están las columnas completas. |
| Ocupados | Educación e ingresos | `P3042`, `P6500` | listo | Ingreso mediano ponderado, no promedio. |
| Desocupados | Tiempo de búsqueda | `P6240`, `DSI`, `FEX_C18` | pendiente | Variable cargada, pero falta agregar métrica al parquet. |
| Brechas | Género | `P3271`, `OCI`, `DSI` | listo | Dimensión `sexo`. |
| Brechas | Edad 15-28 vs 29+ | `P6040` | listo | Dimensión `edad_brecha`. |
| Brechas | Comparativo regional | `DPTO_label`, `TD` | listo | Dimensión `departamento`. |

## 5. Pendientes reales

- Agregar tiempo promedio de búsqueda de empleo con `P6240`.
- Definir y documentar hogares/viviendas si se quieren como KPIs finales.
- Añadir granularidad trimestral móvil y anual si el dashboard la va a exponer.
- ~~Generar cruces geo-demográficos~~ — implementado: 10 dimensiones `dpto_*` y `ciudad_*` en el parquet.
- Validar TD contra cifras oficiales DANE en notebook dedicado.

## 6. Decisiones metodológicas vigentes

- El factor de expansión oficial es `FEX_C18`.
- La edad laboral se calcula con `P6040 >= 15`.
- Nivel educativo usa `P3042`, no `P6210`, porque `P6210` no está en el
  encabezado real de `geih_2025.csv`.
- Ingreso mostrado es mediana ponderada de `P6500` entre ocupados.
- La informalidad usa la regla DANE implementada en
  `src/indicators.py -> _calcular_formalidad_dane()`. Si faltan columnas en un
  dataset mínimo de pruebas, el cálculo degrada a una regla simple basada en
  `P6090`.
