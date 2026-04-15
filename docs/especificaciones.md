# Especificaciones de Diseño: Dashboard de Mercado Laboral (GEIH)

## 1. Configuración Global de Filtros (Sidebar)
*Estos filtros afectan a todas las hojas del dashboard de manera persistente.*

- **Temporalidad:**
  - **Selector de Año:** [2022, 2023, 2024, 2025].
  - **Granularidad:** Toggle para elegir entre [Mensual, Trimestral, Anual].
  - **Periodo Específico:** Dropdown dinámico según la granularidad (ej: "Enero", "Trimestre Móvil Ene-Mar").
- **Geografía:**
  - **Nivel Territorial:** Selector entre [Nacional, Departamental, Ciudades Capitales].
  - **Ubicación:** Listado de los 32 departamentos o las 23 ciudades principales.

---

## 2. Estructura de Menús y Hojas

### Hoja 1: Resumen Ejecutivo
**Objetivo:** Vista macro y rápida de la situación laboral.
- **KPI Cards (Top):**
    - Población Total.
    - Fuerza de Trabajo (PEA).
    - Ocupados.
    - Desocupados.
    - Tasas: TGP, TO y TD (con indicador de variación vs. periodo anterior).
- **Gráfica Principal:** Mapa de coropletas (Colombia por departamentos) y que permita seleccionar tres estados o tres indicadores a mostrar: Población;Desempleados, Ocupados, coloreado.
- **Gráfica de Tendencia:** Serie de tiempo (líneas) con la evolución de la TD, TO y TGP en el rango seleccionado.

### Hoja 2: Caracterización Poblacional
**Objetivo:** Entender quién es la población  la poblacions de colombia.
- **KPI Cards:** Poblacions total, Hogares Totales, Viviendas Totales.
- **Visualizaciones:**
    - **Pirámide Poblacional:** Distribución por sexo y rangos de edad (Características Generales).
    - **Nivel Educativo:** Gráfico de barras horizontales (Sin nivel, Primaria, Secundaria, Media, Superior).
    - **Estado Civil:** Gráfico de barras horizontales.
    - **Población por sexo:** Gráfico de  de torta.
    - **Población por clase:** Gráfico de torta, para mirar la poblacions que vive en los urbano y en lo rural.


### Hoja 3: Mercado de Ocupados
**Objetivo:** Análisis detallado de la calidad y estructura del empleo.
- **KPI Cards:** Total Ocupados, Tasa de empleo, Promedio de ingresos (si aplica)
- **Visualizaciones:**
    - **Rama de Actividad (CIIU):** Treemap o Barras horizontales (Comercio, Industria, Agricultura, etc.).
    - **Pirámide Ocupados:** Distribución por sexo y rangos de edad .
    - **Posición Ocupados:** Gráfico de barras (Empleado particular, Cuenta propia, Gobierno).
    - **Ocupados por sexo:** Gráfico de torta.
    - **Informalidad:** Gráfico de velocímetro o barra apilada (Formal vs. Informal basado en Seguridad Social).
    - **Grafico de Ocupados por ciudades:** Distribución por ciudades capitales (Volumen absoluto).
    - **Grafico de Ocupados por Nivel educativo:** Gráfico de barras horizontales (Sin nivel, Primaria, Secundaria, Media, Superior).
    - **Grafico de ingresos por nivel educativo:** Gráfico de barras horizontales (Sin nivel, Primaria, Secundaria, Media, Superior).

### Hoja 4: Dinámica de Desocupados
**Objetivo:** Analizar el perfil de las personas que buscan empleo.
- **KPI Cards:** Total Desocupados, Tasa de desempleo, Tiempo promedio de búsqueda (semanas).
- **Visualizaciones:**
    - **Pirámide Desocupados:** Distribución por sexo y rangos de edad .
    - **Ocupacional por sexo:** Gráfico de torta.
    - **Grafico de Desocupados por ciudades:** Distribución por ciudades capitales (Volumen absoluto).
    - **Grafico de Desocupados por Nivel educativo:** Gráfico de barras horizontales (Sin nivel, Primaria, Secundaria, Media, Superior).

### Hoja 5: Brechas y Comparaciones
**Objetivo:** Cruces de variables para análisis de equidad.
- **Visualizaciones:**
    - **Brecha de Género:** Comparativa de TD Mujer vs. Hombre en el tiempo.
    - **Brecha por Edad:** TD en Jóvenes (15-28) vs. Resto de la población.
    - **Comparativa Regional:** Gráfico de barras comparando el departamento seleccionado vs. el Promedio Nacional.

### Hoja 6: Metodología y Glosario
**Objetivo:** Documentación técnica y transparencia.
- **Ficha Técnica:** Fuente (DANE - GEIH), periodos cubiertos, fecha de última actualización.
- **Conceptos:** Definiciones de TGP, TO, TD, PFT (según conceptos OIT/DANE).
- **Notas Técnicas:** Breve explicación sobre el factor de expansión y cambios metodológicos.

---

## 7. Matriz de variables requeridas

Esta matriz cruza cada calculo o visual solicitado contra tres capas de disponibilidad:

- existe en microdato GEIH 2022-2025;
- ya se carga en el ETL actual (`src/config.py -> VARS_DASHBOARD`);
- ya sale al parquet analitico (`data/processed/indicadores_mensuales.parquet`).

### Convenciones de estado

- `listo`: ya existe en microdato, ETL y salida analitica con una logica utilizable.
- `parcial`: hay parte de la logica o de los datos, pero falta completar agregacion, dimension o presentacion.
- `falta_etl`: la variable existe en microdato, pero hoy no se carga o no se agrega en el pipeline.
- `falta_recodificacion`: la variable existe y puede cargarse, pero falta mapeo o capa semantica para mostrarla.
- `falta_definicion_metodologica`: hay datos, pero falta definir una regla analitica formal antes de implementarlo.

| hoja | elemento | calculo_o_visual | variables_requeridas | variables_actuales_en_microdato | variables_actuales_en_etl | recodificacion_requerida | nivel_de_agregacion | estado | observaciones |
|---|---|---|---|---|---|---|---|---|---|
| Hoja 1 | KPI | Poblacion total | `PT`, `FEX_C18`, `MES`, `PER` | `PT` y `FEX_C18` existen | `PT` no se carga; `FEX_C18` si | no necesariamente; depende de definicion final del KPI | persona, nacional, mensual/anual | falta_etl | La spec pide poblacion total pero el ETL actual no carga `PT`. |
| Hoja 1 | KPI | Fuerza de trabajo (PEA) | `FT`, `OCI`, `DSI`, `FEX_C18`, `MES` | `FT`, `OCI`, `DSI`, `FEX_C18` existen | `FT` no se carga; `OCI`, `DSI`, `FEX_C18` si | no | persona, nacional, mensual/anual | parcial | Puede derivarse como `ocupados_exp + desocupados_exp`, pero no sale hoy como metrica explicita ni para todas las granularidades de la spec. |
| Hoja 1 | KPI | Ocupados | `OCI`, `FEX_C18`, `MES` | si | si | no | persona, nacional/ciudad, mensual | listo | Ya sale como `ocupados_exp` en parquet. |
| Hoja 1 | KPI | Desocupados | `DSI`, `FEX_C18`, `MES` | si | si | no | persona, nacional/ciudad, mensual | listo | Ya sale como `desocupados_exp` en parquet. |
| Hoja 1 | KPI | TGP, TO y TD con variacion | `OCI`, `DSI`, `P6040`, `FEX_C18`, `MES` | si | si | no | persona, nacional/ciudad/sexo/edad/sector, mensual | listo | Ya calculadas en `src/indicators.py`. La variacion se puede construir en app sobre la serie. |
| Hoja 1 | Mapa | Coropleta por departamentos | `DPTO`, `FEX_C18`, `OCI`, `DSI`, `PT` | si | `DPTO` si, `PT` no | si; falta `DPTO_label` y capa geografica para mapa | departamento, mensual/trimestral/anual | falta_etl | El ETL actual no produce dimension `departamento` y el parquet no tiene agregacion departamental. |
| Hoja 1 | Tendencia | Serie TD, TO, TGP | `OCI`, `DSI`, `P6040`, `FEX_C18`, `MES`, `ano` | si | si | no | nacional/ciudad/sexo/edad/sector, mensual | listo | Falta solo soportar granularidad trimestral y anual de forma explicita. |
| Filtros globales | Temporalidad | Granularidad mensual/trimestral/anual | `MES`, `ano` | si | si | no | mensual, trimestral, anual | falta_definicion_metodologica | Mensual existe; trimestral movil y anual requieren regla formal de agregacion. |
| Filtros globales | Geografia | Nivel territorial departamental | `DPTO` | si | `DPTO` si | si; falta etiqueta departamental reusable | departamento | falta_etl | Hoy solo existen dimensiones `nacional`, `ciudad`, `sexo`, `edad`, `sector`. |
| Filtros globales | Geografia | Ciudades capitales | `AREA` | si | `AREA` si | `AREA_label` ya sale del diccionario | ciudad | parcial | El ETL actual usa ciudad, pero no distingue una capa separada de "ciudades capitales" en la spec. |
| Hoja 2 | KPI | Poblacion total | `PT`, `FEX_C18` | si | `PT` no | no | persona, nacional/departamento/ciudad | falta_etl | Misma brecha de Hoja 1. |
| Hoja 2 | KPI | Hogares totales | `DIRECTORIO`, `HOGAR`, `FEX_C18` | `DIRECTORIO`, `HOGAR`, `FEX_C18` existen | si | no | hogar, nacional/departamento/ciudad | falta_definicion_metodologica | Requiere definir unidad de conteo ponderado de hogar y evitar doble conteo por persona. |
| Hoja 2 | KPI | Viviendas totales | `DIRECTORIO`, `FEX_C18` | si | `DIRECTORIO`, `FEX_C18` si | no | vivienda, nacional/departamento/ciudad | falta_definicion_metodologica | Requiere definir regla de deduplicacion a nivel vivienda. |
| Hoja 2 | Visual | Piramide poblacional | `P3271`, `P6040`, `FEX_C18` | si | si | `P3271` ya usa `MAPEOS_COMPLEMENTARIOS`; rangos finos de edad faltan | persona, nacional/departamento/ciudad | parcial | Hay sexo y edad, pero hoy los grupos son amplios (`15-24`, `25-34`, etc.), no una piramide completa. |
| Hoja 2 | Visual | Nivel educativo | `P3042` o variable homologada | `P3042` existe; `P6210` no se encontro en CSV 2025 | no | si; hay que homologar spec (`P6210`) con base real (`P3042`) y recodificar a niveles analiticos | persona | falta_etl | Falta cargar `P3042` al ETL y documentar equivalencia con la spec. |
| Hoja 2 | Visual | Estado civil | `P6070` | si | no | si; requiere labels analiticos | persona | falta_etl | La variable existe en microdato, pero no entra hoy al pipeline. |
| Hoja 2 | Visual | Poblacion por sexo | `P3271`, `FEX_C18` | si | si | `P3271_label` ya resuelto | persona | parcial | Hay datos suficientes, pero el parquet actual no expone conteo de poblacion total por sexo, solo indicadores laborales. |
| Hoja 2 | Visual | Poblacion por clase urbano/rural | `CLASE`, `FEX_C18` | si | no | si; falta mapeo semantico de `CLASE` | persona | falta_etl | Variable disponible en microdato pero fuera de `VARS_DASHBOARD`. |
| Hoja 3 | KPI | Total ocupados | `OCI`, `FEX_C18` | si | si | no | persona | listo | Ya sale como `ocupados_exp`. |
| Hoja 3 | KPI | Tasa de empleo | `OCI`, `P6040`, `FEX_C18` | si | si | no | persona | listo | Equivale a `TO`. |
| Hoja 3 | KPI | Promedio/mediana de ingresos | `OCI`, `P6500`, `FEX_C18` | si | si | no | persona ocupada | parcial | El pipeline actual calcula ingreso mediano ponderado, no promedio. La spec debe confirmar si acepta mediana o requiere otra metrica. |
| Hoja 3 | Visual | Rama de actividad | `RAMA2D_R4`, `OCI`, `FEX_C18` | si | si | `RAMA2D_R4_label` ya se construye en `MAPEOS_COMPLEMENTARIOS` | persona ocupada, sector | listo | Ya es calculable y parcialmente visible en la app actual. |
| Hoja 3 | Visual | Piramide de ocupados | `OCI`, `P3271`, `P6040`, `FEX_C18` | si | si | falta recodificacion de bandas finas de edad | persona ocupada | parcial | Hay insumo, pero no una salida analitica especifica para piramide. |
| Hoja 3 | Visual | Posicion ocupacional | `OCI`, `P6430`, `FEX_C18` | si | `P6430` si | si; faltan labels de `P6430` expuestos en capa analitica | persona ocupada | falta_recodificacion | El ETL carga `P6430`, pero no produce dimension ni agregacion por posicion ocupacional. |
| Hoja 3 | Visual | Ocupados por sexo | `OCI`, `P3271`, `FEX_C18` | si | si | `P3271_label` ya existe | persona ocupada | parcial | Hay insumo, pero falta agregacion analitica dedicada. |
| Hoja 3 | Visual | Informalidad | `OCI`, `P6090`, `P6100`, `P6920`, `FEX_C18` | si | no | si; ademas requiere regla formal de formal vs informal | persona ocupada | falta_definicion_metodologica | La spec dice "basado en seguridad social", pero falta fijar la definicion exacta. |
| Hoja 3 | Visual | Ocupados por ciudades | `OCI`, `AREA`, `FEX_C18` | si | `AREA` si | `AREA_label` ya existe | ciudad | parcial | Hay ciudad y ocupados; falta una agregacion especifica de volumen absoluto por ciudad en parquet. |
| Hoja 3 | Visual | Ocupados por nivel educativo | `OCI`, `P3042`, `FEX_C18` | si | no | si; requiere homologar y recodificar `P3042` | persona ocupada | falta_etl | Misma brecha de nivel educativo. |
| Hoja 3 | Visual | Ingresos por nivel educativo | `OCI`, `P6500`, `P3042`, `FEX_C18` | si | `P6500` si, `P3042` no | si | persona ocupada | falta_etl | Falta cargar educacion al ETL y definir si se usara ingreso promedio o mediano. |
| Hoja 4 | KPI | Total desocupados | `DSI`, `FEX_C18` | si | si | no | persona | listo | Ya sale como `desocupados_exp`. |
| Hoja 4 | KPI | Tasa de desempleo | `OCI`, `DSI`, `P6040`, `FEX_C18` | si | si | no | persona | listo | Ya sale como `TD`. |
| Hoja 4 | KPI | Tiempo promedio de busqueda | `P6240`, `DSI`, `FEX_C18` | si | no | no necesariamente; falta definir transformacion analitica | persona desocupada | falta_etl | `P6240` existe en microdato, pero no se carga hoy al ETL. |
| Hoja 4 | Visual | Piramide desocupados | `DSI`, `P3271`, `P6040`, `FEX_C18` | si | si | falta una banda etaria mas fina | persona desocupada | parcial | Hay insumo, no salida analitica dedicada. |
| Hoja 4 | Visual | Desocupados por sexo | `DSI`, `P3271`, `FEX_C18` | si | si | `P3271_label` ya existe | persona desocupada | parcial | La spec dice "ocupacional por sexo" pero operativamente parece una composicion de desocupados por sexo. Conviene corregir redaccion. |
| Hoja 4 | Visual | Desocupados por ciudades | `DSI`, `AREA`, `FEX_C18` | si | `AREA` si | `AREA_label` ya existe | ciudad | parcial | Requiere agregacion especifica de volumen absoluto por ciudad. |
| Hoja 4 | Visual | Desocupados por nivel educativo | `DSI`, `P3042`, `FEX_C18` | si | no | si | persona desocupada | falta_etl | Falta cargar educacion y construir agregacion. |
| Hoja 5 | Visual | Brecha de genero | `OCI`, `DSI`, `P3271`, `P6040`, `FEX_C18`, `MES` | si | si | `P3271_label` ya existe | persona, sexo, mensual | listo | Ya es calculable con la dimension `sexo`. |
| Hoja 5 | Visual | Brecha por edad 15-28 vs resto | `OCI`, `DSI`, `P6040`, `FEX_C18` | si | si | si; falta una nueva recodificacion `15-28` vs `29+` | persona, mensual | falta_recodificacion | El pipeline actual usa grupos `15-24`, `25-34`, `35-44`, `45-54`, `55-64`, `65+`. |
| Hoja 5 | Visual | Comparativa regional | `DPTO`, `OCI`, `DSI`, `P6040`, `FEX_C18` | si | `DPTO` si | si; falta `DPTO_label` y dimension departamental | departamento, nacional | falta_etl | No hay agregacion departamental en parquet actual. |
| Hoja 6 | Ficha tecnica | Fuente, periodos, ultima actualizacion | `ano`, `MES`, metadata del proyecto | si | si | no | documental | listo | Se puede completar desde repo y pipeline. |
| Hoja 6 | Conceptos | TGP, TO, TD, PFT | conceptos metodologicos | no aplica | no aplica | no | documental | parcial | TGP, TO y TD estan claros; `PFT` no aparece definida hoy en el pipeline y debe aclararse si es Poblacion Fuera de la Fuerza de Trabajo. |
| Hoja 6 | Notas tecnicas | Factor de expansion y cambios metodologicos | `FEX_C18`, decisiones tecnicas | si | si | no | documental | listo | Hay sustento en `decisiones_tecnicas.md` y en el ETL. |

### Sintesis operativa

**Ya implementable**

- Ocupados.
- Desocupados.
- TD, TO y TGP.
- Tendencias mensuales.
- Brecha de genero.
- Rama de actividad.

**Implementable ampliando ETL o agregaciones**

- Poblacion total.
- PEA explicita.
- Coropletas y comparativos departamentales.
- Nivel educativo.
- Estado civil.
- Clase urbano/rural.
- Posicion ocupacional.
- Ocupados y desocupados por ciudad en volumen absoluto.
- Tiempo de busqueda.

**Requiere decision metodologica**

- Granularidad trimestral movil.
- Hogares totales.
- Viviendas totales.
- Informalidad.
- Brecha de edad 15-28 vs resto.
- PFT en glosario si se quiere alinear plenamente con OIT/DANE.

### Hallazgos de coherencia entre spec y base real

- La spec menciona `P6210` para nivel educativo, pero en el encabezado real de `geih_2025.csv` no aparece; la variable disponible es `P3042`.
- El microdato si contiene `DPTO`, `CLASE`, `P6070`, `P3042`, `P6090`, `P6100`, `P6920`, `P6240`, pero varias no estan hoy en `VARS_DASHBOARD`.
- El ETL actual solo produce dimensiones `nacional`, `ciudad`, `sexo`, `edad` y `sector`.

---

## 8. Resumen simple para construir el dashboard completo

### Lo que ya esta listo

- TD, TO y TGP.
- Ocupados y desocupados.
- Series mensuales.
- Brecha de genero.
- Rama de actividad.
- Ingreso mediano.
- Cortes por nacional, ciudad, sexo, edad y sector.

### Lo que falta cargar al ETL

- `PT` para poblacion total.
- `FT` para fuerza de trabajo explicita.
- `CLASE` para urbano/rural.
- `P6070` para estado civil.
- `P3042` para nivel educativo.
- `P6090`, `P6100`, `P6920` para informalidad.
- `P6240` para tiempo de busqueda.
- Agregacion por `DPTO` para nivel departamental.

### Lo que falta recodificar o modelar

- `P3042` en niveles educativos analiticos.
- `P6070` en categorias legibles.
- `CLASE` en urbano/rural.
- `P6430` en posicion ocupacional visible en dashboard.
- `DPTO` en etiquetas departamentales.
- Grupo especial de edad `15-28` vs resto.
- Bandas de edad mas finas para piramides.

### Lo que requiere definicion metodologica

- Como calcular hogares totales.
- Como calcular viviendas totales.
- Como definir informalidad.
- Como construir trimestre movil.
- Si ingresos se mostraran como promedio, mediana o ambos.
- Que significa `PFT` en el glosario final.

### Variables minimas para cumplir toda la spec

`DIRECTORIO`, `HOGAR`, `PER`, `MES`, `AREA`, `DPTO`, `CLASE`, `FEX_C18`, `PT`, `FT`, `PET`, `OCI`, `DSI`, `P3271`, `P6040`, `P6070`, `P3042`, `P6090`, `P6100`, `P6240`, `P6430`, `P6500`, `RAMA2D_R4`.

### Conclusión operativa

Si se quiere construir el dashboard completo con todas las especificaciones, no hace falta cambiar de fuente de datos.
La GEIH ya tiene casi todo lo necesario.
Lo que falta es ampliar el ETL, agregar nuevas recodificaciones y cerrar algunas decisiones metodologicas antes de construir las hojas faltantes.

### Estado actual de filtros territoriales en la app

- El filtro por `Departamento` y `Ciudad` ya debe cambiar el contexto principal de las vistas que usan dimensiones geograficas directas.
- Esto incluye KPIs y series cuando la hoja trabaja con `departamento` o `ciudad`.
- Las vistas demograficas como sexo, edad, educacion, clase y estado civil todavia no responden completamente al filtro territorial.
- La razon tecnica es que el parquet actual no guarda todos los cruces `geografia + demografia`.
- Para que esos graficos tambien cambien por territorio, el ETL debe generar dimensiones geo-demograficas adicionales.

