# Dashboard del Mercado Laboral Colombiano

**Análisis interactivo de la Gran Encuesta Integrada de Hogares (GEIH) · 2022–2025**

[![Streamlit](https://img.shields.io/badge/Streamlit-Community%20Cloud-red)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-25%20passing-brightgreen)](#tests)
[![Licencia](https://img.shields.io/badge/licencia-MIT-green)](LICENSE)

---

## ¿Qué responde este dashboard?

1. ¿Cómo viene el desempleo nacional vs. los últimos meses y vs. el mismo mes del año anterior?
2. ¿En qué departamentos y ciudades está más duro el mercado?
3. ¿Qué sectores económicos están creando o perdiendo empleo?
4. ¿Cómo se comporta la brecha de género y por grupos de edad?
5. ¿Cuál es el ingreso laboral mediano y cuántos niveles educativos quedan por debajo del SMMLV?

---

## Vistas del dashboard

| Vista | Contenido |
|---|---|
| **Resumen** | KPIs nacionales, tendencia TD/TO/TGP, comparación interanual TD, mapa departamental, mapa de ciudades |
| **Población** | Pirámide poblacional, educación, estado civil, sexo, clase, mapa poblacional |
| **Ocupados** | Tendencia TO/informalidad, rama, pirámide, posición, salarios por educación con línea SMMLV, mapa departamental y de ciudades |
| **Desocupados** | Tendencia TD/inactivos, perfil edad/sexo, educación, mapa departamental y de ciudades |
| **Brechas** | KPIs de brecha género, brecha TD/informalidad/ingreso por sexo, brecha etaria (15-28 vs 29+), ingreso mediano × sexo con SMMLV, mapa regional — **filtros territoriales activos** |
| **Instrucciones** | Guía de lectura en documento HTML único — indicadores, brechas, rutas por perfil |
| **Metodología** | Ficha técnica, parámetros estadísticos, cobertura, definiciones OIT/DANE, trazabilidad variable → código |

---

## Funcionalidades clave

- **Filtros globales** por año, mes y nivel territorial (nacional / departamento / ciudad) con resumen de chips activos.
- **Gráfico de tendencia interactivo:** muestra la serie completa o los 12 meses de un año; añade un marcador puntual cuando se selecciona un mes específico.
- **Comparación interanual:** cuando se seleccionan todos los años, aparece un gráfico de TD mes a mes con cada año como línea separada — captura estacionalidad y tendencia estructural.
- **Brechas territoriales:** los gráficos de género e informalidad responden al filtro de departamento y ciudad (dimensiones `dpto_sexo`, `ciudad_sexo`, `dpto_edad_brecha`, `ciudad_edad_brecha` en el parquet).
- **Línea SMMLV:** los gráficos de ingreso mediano incluyen una referencia al Salario Mínimo del año correspondiente.
- **Resaltado geográfico:** al seleccionar un departamento o ciudad se resalta en el mapa con borde naranja sin ocultar el resto del territorio.
- **Mapas independientes:** el mapa de ciudades siempre muestra todas las áreas metropolitanas independientemente del filtro de departamento activo.
- **KPI cards compactas:** título y valor centrados, sin texto de delta ni pie de página.
- **Tema dual** oscuro / claro con inyección de CSS personalizada y tipografía premium (`Fraunces` & `Manrope`).
- **Métricas avanzadas:** TD, TO, TGP, informalidad, ingreso laboral mediano, FFT por periodo, departamento y ciudad.

---

## Datos

- **Fuente:** [Gran Encuesta Integrada de Hogares (GEIH)](https://microdatos.dane.gov.co) — DANE
- **Cobertura:** 2022 a 2025 · bases anuales consolidadas
- **Unidad de análisis:** persona
- **Factor de expansión:** `FEX_C18` (post-rediseño 2022)
- **Indicadores:** TD, TO, TGP, informalidad, ingreso laboral mediano ponderado, FFT
- **Nota de comparabilidad:** los datos desde 2022 **no son comparables** con series anteriores a 2021 (rediseño GEIH + marco Censo 2018)

---

## Stack técnico

| Capa | Tecnología |
|---|---|
| Dashboard | Streamlit |
| Gráficos | Plotly (Scatter/Choropleth Mapbox, subplots) |
| ETL | Polars + pandas + pyarrow |
| Persistencia | Parquet (`indicadores_mensuales.parquet`) |
| Estilos | CSS dinámico (Dark/Light mode) |
| Tests | pytest — 25 tests unitarios (indicadores + diccionario) |
| Deploy | Streamlit Community Cloud |

---

## Reproducibilidad

### 1. Clonar y crear ambiente

```bash
git clone <repo-url>
cd portafolio/dashboard_mercado_laboral_co
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt          # solo runtime
pip install -r requirements-dev.txt      # + ETL, linters y tests
```

### 2. Colocar bases de datos

Las bases anuales **no se versionan en git** por tamaño. Descárgalas desde
[microdatos.dane.gov.co](https://microdatos.dane.gov.co) → GEIH → año correspondiente → módulo consolidado anual.

Colócalas aquí:

```
portafolio/bases_datos/geih/datos/
    geih_2022.csv
    geih_2023.csv
    geih_2024.csv
    geih_2025.csv
```

O ajusta `BASES_DIR` en `src/config.py`. Formato esperado: CSV con separador coma, encoding UTF-8, con las columnas listadas en `config.VARS_DASHBOARD`.

### 3. Correr el pipeline ETL

```bash
python src/etl.py
```

Genera `data/processed/indicadores_mensuales.parquet` (~110 000 filas × 25 columnas).
Tiempo estimado: 3–6 minutos dependiendo del hardware.

### 4. Lanzar el dashboard

```bash
streamlit run app/main.py
```

---

## Tests

```bash
pytest tests/ -v
```

25 tests cubriendo:
- `_mediana_ponderada` — casos borde (array vacío, pesos concentrados, pesos cero)
- Fórmulas TD, TO, TGP — verificadas contra valores calculados a mano
- Invarianza ante escala del factor de expansión
- Agrupación por ciudad y dimensión faltante
- Diccionario GEIH — limpieza, mapeos, cobertura, labels

---

## Estructura del repositorio

```
dashboard_mercado_laboral_co/
├── app/
│   └── main.py                  # Dashboard Streamlit
├── src/
│   ├── config.py                # Rutas, grupos de edad, mapeos DIVIPOLA
│   ├── etl.py                   # Pipeline principal (24 dimensiones)
│   ├── indicators.py            # TD, TO, TGP, informalidad, ingreso mediano ponderado
│   ├── loaders.py               # Carga multi-formato (CSV, Parquet, SAV)
│   ├── dictionary.py            # Procesamiento diccionario GEIH
│   └── validate.py              # Validación vs. cifras oficiales DANE
├── data/
│   ├── reference/               # GeoJSON departamental
│   └── processed/               # Parquet de salida y productos del diccionario
├── docs/
│   ├── especificaciones.md      # Matriz de variables por vista
│   └── decisiones_tecnicas.md
├── notebooks/                   # Exploración y validación
├── tests/                       # pytest — 25 tests unitarios
├── requirements.txt             # Runtime (Streamlit Community Cloud)
└── requirements-dev.txt         # ETL + linters + tests (solo local)
```

---

## Dimensiones del parquet

El ETL genera 24 dimensiones analíticas independientes:

| Dimensión | Variables de agrupación |
|---|---|
| `nacional` | — |
| `departamento` / `ciudad` | `DPTO_label` / `AREA_label` |
| `sexo` / `edad` / `sexo_edad` | `P3271_label` / `grupo_edad` |
| `edad_brecha` | `grupo_edad_brecha` (15-28 vs 29+) |
| `sector` / `clase` / `estado_civil` / `educacion` / `posicion_ocupacional` | variables demográficas |
| `dpto_sexo` / `dpto_sexo_edad` / `dpto_educacion` / `dpto_estado_civil` / `dpto_clase` / `dpto_edad_brecha` | cruce geo × demográfico |
| `ciudad_sexo` / `ciudad_sexo_edad` / `ciudad_educacion` / `ciudad_estado_civil` / `ciudad_clase` / `ciudad_edad_brecha` | cruce geo × demográfico |

---

## Grupos de edad (quinquenios)

La pirámide poblacional usa intervalos de **5 años** según estándar DANE/OIT:

`15-19 · 20-24 · 25-29 · 30-34 · 35-39 · 40-44 · 45-49 · 50-54 · 55-59 · 60-64 · 65+`

Para regenerar el parquet tras cualquier cambio en `src/config.py`:
```bash
python src/etl.py
```

---

## Autor

**Daniel Molina** — Economista & Data Scientist · Santa Marta, Colombia

> *"Transformo datos en soluciones, productos y decisiones."*

[LinkedIn](https://www.linkedin.com/in/daniel-molina-b76a4323b) · [GitHub](https://github.com/dmgsjj)
