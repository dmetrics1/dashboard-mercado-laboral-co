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
| **Resumen** | KPIs nacionales, tendencia TD/TO/TGP, mapa regional independiente de filtros |
| **Población** | Pirámide poblacional (quinquenios), educación, estado civil, sexo, clase |
| **Ocupados** | Rama de actividad, pirámide de ocupados, posición, ciudades, informalidad, salarios |
| **Desocupados** | Perfil de desocupados por edad/sexo, ciudades, educación, tendencia FFT |
| **Brechas** | Brecha de género, brecha etaria (15-28 vs 29+), mapa regional e indicadores |
| **Instrucciones** | Guía de lectura para facultades y programas |
| **Metodología** | Ficha técnica, definiciones, notas de cobertura |

---

## Funcionalidades clave

- **Mapa regional desacoplado:** El mapa de departamentos permite comparativas globales constantes, incluso al aplicar filtros de ciudad específica.
- **Homogeneidad visual:** Sistema de alturas estándar para gráficos (`H_PAIRED`, `H_PYRAMID`, `H_SINGLE`) que garantiza simetría en el layout.
- **Pirámide poblacional** en quinquenios (intervalos de 5 años: 15-19, 20-24 … 65+)
- **Tasa de informalidad** calculada con regla DANE y visualización por rama de actividad.
- **Población FFT:** Métrica y tendencia de personas Fuera de la Fuerza de Trabajo (inactivos).
- **Tema dual** oscuro / claro con inyección de CSS personalizada y tipografía premium (`Fraunces` & `Manrope`).
- **Filtros globales** por año y nivel territorial con resumen de chips activos.

---

## Datos

- **Fuente:** [Gran Encuesta Integrada de Hogares (GEIH)](https://microdatos.dane.gov.co) — DANE
- **Cobertura:** 2022 a 2025 · bases anuales consolidadas
- **Unidad de análisis:** persona
- **Factor de expansión:** `FEX_C18`
- **Indicadores:** TD, TO, TGP, informalidad, ingreso laboral mediano ponderado, FFT

---

## Stack técnico

| Capa | Tecnología |
|---|---|
| Dashboard | Streamlit |
| Gráficos | Plotly (Scatter/Choropleth Mapbox, subplots) |
| ETL | Polars + pandas + pyarrow |
| Persistencia | Parquet (`indicadores_mensuales.parquet`) |
| Estilos | CSS dinámico (Dark/Light mode) |
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
python src/etl.py
```
Genera `data/processed/indicadores_mensuales.parquet`.

### 4. Lanzar el dashboard

```bash
streamlit run app/main.py
```

---

## Estructura del repositorio

```
dashboard_mercado_laboral_co/
├── app/
│   └── main.py              # Dashboard Streamlit (~2 500 líneas)
├── src/
│   ├── config.py            # Rutas, grupos de edad, mapeos DIVIPOLA
│   ├── etl.py               # Pipeline principal
│   ├── indicators.py        # TD, TO, TGP, informalidad, ingreso mediano ponderado
│   ├── loaders.py           # Carga multi-formato (CSV, Parquet, SAV)
│   ├── dictionary.py        # Procesamiento diccionario GEIH
│   └── validate.py          # Validación vs. cifras oficiales DANE
├── data/
│   ├── reference/           # GeoJSON departamental
│   └── processed/           # Parquet de salida y productos del diccionario
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
