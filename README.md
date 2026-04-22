# Dashboard del Mercado Laboral Colombiano

**Análisis interactivo de la Gran Encuesta Integrada de Hogares (GEIH) · 2022–2025**

[![Streamlit](https://img.shields.io/badge/Streamlit-Community%20Cloud-red)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![Licencia](https://img.shields.io/badge/licencia-MIT-green)](LICENSE)

---

## ¿Qué responde este dashboard?

1. ¿Cómo viene el desempleo nacional vs. los últimos meses?
2. ¿En qué departamentos y ciudades está más duro el mercado?
3. ¿Qué sectores económicos están creando o perdiendo empleo?
4. ¿Cómo se comporta la brecha de género y por grupos de edad?
5. ¿Cuál es el ingreso laboral mediano y cómo ha evolucionado?

---

## Vistas del dashboard

| Vista | Contenido |
|---|---|
| **Resumen** | KPIs nacionales, tendencia TD/TO/TGP, mapa de calor departamental |
| **Población** | Pirámide poblacional (quinquenios), educación, estado civil, sexo, clase |
| **Ocupados** | Rama de actividad, pirámide de ocupados, posición, ciudades, salarios |
| **Desocupados** | Perfil de desocupados por edad/sexo, ciudades, educación |
| **Brechas** | Brecha de género, brecha etaria (15-28 vs 29+), mapa departamental |
| **Instrucciones** | Guía de lectura para facultades y programas |
| **Metodología** | Ficha técnica, definiciones, notas de cobertura |

---

## Funcionalidades clave

- **Mapa de calor** interactivo de Colombia por departamento con selector TD / TO / TGP
- **Pirámide poblacional** en quinquenios (intervalos de 5 años: 15-19, 20-24 … 65+)
- **Tasa de informalidad** calculada con regla DANE cuando están las variables completas
- **Tema dual** oscuro / claro con toggle en la barra lateral
- **Filtros globales** por año y nivel territorial (nacional / departamento / ciudad)
- **Todos los indicadores ponderados** con `FEX_C18` (factor post-rediseño 2022+)

---

## Datos

- **Fuente:** [Gran Encuesta Integrada de Hogares (GEIH)](https://microdatos.dane.gov.co) — DANE
- **Cobertura:** 2022 a 2025 · bases anuales consolidadas
- **Unidad de análisis:** persona
- **Factor de expansión:** `FEX_C18`
- **Indicadores:** TD, TO, TGP, informalidad, ingreso laboral mediano ponderado

---

## Stack técnico

| Capa | Tecnología |
|---|---|
| Dashboard | Streamlit |
| Gráficos | Plotly (Scatter/Choropleth Mapbox, go.Figure) |
| ETL | Polars + pandas + pyarrow |
| Persistencia | Parquet (`indicadores_mensuales.parquet`) |
| Tests | pytest |
| Deploy | Streamlit Community Cloud |

---

## Reproducibilidad

### 1. Clonar y crear ambiente

```bash
git clone <repo-url>
cd dashboard_mercado_laboral_co
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Colocar bases de datos

Las bases anuales **no se versionan en git** por tamaño. Colócalas aquí:

```
portafolio/bases_datos/geih/datos/
    geih_2022.csv
    geih_2023.csv
    geih_2024.csv
    geih_2025.csv
```

O ajusta `BASES_DIR` en `src/config.py`.

### 3. Correr el pipeline ETL

```bash
cd portafolio/dashboard_mercado_laboral_co
python src/etl.py
```
Genera `data/processed/indicadores_mensuales.parquet` (6.160 filas, 25 columnas en la corrida actual).

### 4. Lanzar el dashboard

```bash
streamlit run app/main.py
```

---

## Estructura del repositorio

```
dashboard_mercado_laboral_co/
├── app/
│   └── main.py              # Dashboard Streamlit (~2 000 líneas)
├── src/
│   ├── config.py            # Rutas, grupos de edad, mapeos DIVIPOLA
│   ├── etl.py               # Pipeline principal
│   ├── indicators.py        # TD, TO, TGP, informalidad, ingreso mediano ponderado
│   ├── loaders.py           # Carga multi-formato (CSV, Parquet, SAV)
│   ├── dictionary.py        # Procesamiento diccionario GEIH
│   └── validate.py          # Validación vs. cifras oficiales DANE
├── data/
│   ├── raw/                 # Bases anuales (no versionadas)
│   ├── reference/           # Diccionario.xlsx
│   └── processed/           # Parquet de salida
├── docs/
│   ├── especificaciones.md  # Matriz de variables por vista
│   └── decisiones_tecnicas.md
├── notebooks/               # Exploración y validación
└── tests/                   # pytest
```

---

## Grupos de edad (quinquenios)

La pirámide poblacional usa intervalos de **5 años** según estándar DANE/OIT:

`15-19 · 20-24 · 25-29 · 30-34 · 35-39 · 40-44 · 45-49 · 50-54 · 55-59 · 60-64 · 65+`

Para regenerar el parquet con estos grupos tras cualquier cambio en `src/config.py`:
```bash
python src/etl.py
```

---

## Autor

**Daniel Molina** — Economista & Data Scientist · Santa Marta, Colombia

> *"Transformo datos en soluciones, productos y decisiones."*

[LinkedIn](https://www.linkedin.com/in/daniel-molina-b76a4323b) · [GitHub](https://github.com/dmgsjj)
