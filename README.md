# Dashboard del Mercado Laboral Colombiano

**Análisis interactivo de la Gran Encuesta Integrada de Hogares (GEIH) · 2022–2025**

[![Streamlit](https://img.shields.io/badge/Streamlit-Community%20Cloud-red)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![Licencia](https://img.shields.io/badge/licencia-MIT-green)](LICENSE)

---

## ¿Qué responde este dashboard?

1. ¿Cómo viene el desempleo nacional vs. los últimos 12 meses?
2. ¿En qué ciudades está más duro el mercado y en cuáles más fácil?
3. ¿Qué sectores económicos están creando o perdiendo empleo?
4. ¿Cómo se comporta la brecha de género y por grupos de edad?
5. ¿Cuál es el ingreso laboral mediano y cómo ha evolucionado?

---

## Caso de uso

Consultoras laborales, fondos de inversión y medios económicos que hoy consumen boletines PDF del DANE y necesitan análisis interactivo por ciudad, sector, género y edad — sin depender del ciclo de publicación del DANE.

---

## Datos

- **Fuente:** [Gran Encuesta Integrada de Hogares (GEIH)](https://microdatos.dane.gov.co) — DANE
- **Cobertura:** 2022 a 2025 (bases anuales consolidadas)
- **Unidad de análisis:** persona
- **Factor de expansión:** `FEX_C18`
- **Indicadores:** Tasa de Desempleo, Tasa de Ocupación, TGP, Ingreso mediano

---

## Stack técnico

| Capa | Tecnología |
|---|---|
| Dashboard | Streamlit |
| Gráficos | Plotly |
| ETL | pandas + pyarrow |
| Persistencia intermedia | Parquet |
| Tests | pytest |
| Deploy | Streamlit Community Cloud |

---

## Reproducibilidad

### 1. Clonar y crear ambiente

```bash
git clone <repo-url>
cd dashboard-mercado-laboral-co
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Colocar bases de datos

Las bases anuales **no se versionan en git** por tamaño. Coloca los archivos en `data/raw/`:

```
data/raw/geih_2022.csv
data/raw/geih_2023.csv
data/raw/geih_2024.csv
data/raw/geih_2025.csv
```

O ajusta `BASES_DIR` en `src/config.py` para apuntar a la ruta donde tengas los archivos.

### 3. Correr el pipeline

```bash
python src/etl.py
```

Esto genera `data/processed/indicadores_mensuales.parquet` y el reporte de cobertura del diccionario.

### 4. Lanzar el dashboard

```bash
streamlit run app/main.py
```

---

## Estructura del repositorio

```
dashboard-mercado-laboral-co/
├── docs/                    # Protocolo técnico y decisiones
├── data/
│   ├── raw/                 # Bases anuales (no versionadas)
│   ├── reference/           # Diccionario de variables
│   └── processed/           # Salidas del pipeline
├── src/                     # ETL, indicadores, loaders
├── app/main.py              # Dashboard Streamlit
├── notebooks/               # Exploración y validación
└── tests/                   # pytest
```

---

## Autor

**Daniel Molina** — Economista & Data Scientist · Santa Marta, Colombia

> *"Transformo datos en soluciones, productos y decisiones."*

[LinkedIn](https://linkedin.com/in/danielmolina) · [Portafolio](https://danielmolina.dev)
