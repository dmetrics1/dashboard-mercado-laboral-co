# Especificaciones de Diseño: Dashboard de Mercado Laboral (GEIH)

Última revisión: 2026-04-25.

Este documento refleja el estado actual del código y del parquet procesado
`data/processed/indicadores_mensuales.parquet`: 6.160 filas, 25 columnas y 12
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
| Resumen | listo | KPIs de población, PEA, ocupados, desocupados, TD, TO, TGP, ingreso mediano, tendencia y mapa departamental. |
| Población | listo | Pirámide por sexo y edad, nivel educativo, estado civil, sexo y clase urbano/rural. |
| Ocupados | listo | KPIs laborales, rama de actividad, informalidad, posición ocupacional, ciudad, educación e ingresos. |
| Desocupados | parcial | KPIs, pirámide, ciudad y educación. Tiempo de búsqueda sigue pendiente. |
| Brechas | listo | Brecha de género, brecha etaria 15-28 vs 29+, comparativo regional y mapa. |
| Instrucciones | listo | Guía de lectura para facultades y programas. No usa filtros. |
| Metodología | listo | Ficha técnica, glosario y trazabilidad de variables. No usa filtros. |

### Criterios visuales vigentes (2026-04-25)

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
- KPI value en Fraunces 700, 2.15rem; mini-value en Fraunces 700, 1.55rem.

**Section headers:**
- Usan `border-top` separador + `padding-top` generoso (0.85rem) entre secciones.
- Título en Fraunces 600, 1.32rem.

**Interpretation blocks:**
- Borde izquierdo de 4 px en BT_DEEP.
- Título con prefijo `—` generado por CSS `::before`.
- Tono sobrio, datos concretos, sin emojis.

**Reglas de no-redundancia:**
- `view_resumen`: tendencia a ancho completo; mini-cards laterales eliminadas (duplicaban KPIs).
- Comparativo departamental: muestra los de **mayor** TD/menor TO (relevante para política),
  no los de menor TD.
- `view_instrucciones`: sin gráfico "Pulso nacional" (repetía KPIs del Resumen).
- Todas las `render_interpretation()` reescritas para corresponder exactamente a los gráficos
  visibles en cada vista.

**Mapa departamental:**
- Coroplético con escala BLUE_TEAL_30, `carto-positron` en claro / `carto-darkmatter` en oscuro.
- Panel de control lateral con extremos Mayor/Menor calculados en tiempo real.

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
- Generar cruces geo-demográficos adicionales si se requiere que todos los
  gráficos demográficos cambien simultáneamente por departamento/ciudad.
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
