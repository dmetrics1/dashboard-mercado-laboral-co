# PROMPT MAESTRO — Dashboard del Mercado Laboral Colombiano (GEIH)

> Pega este documento como contexto inicial en Claude Code, Cursor u otro agente.
> Al leerlo, el agente debe tener todo lo necesario para trabajar el proyecto sin preguntas sobre el fondo.

---

## 0. Instrucciones para el agente

1. Leer este documento completo antes de escribir código.
2. Respetar las decisiones técnicas ya fijadas (stack, estructura, protocolo del diccionario). No proponer cambios salvo que el usuario lo pida.
3. Antes de tocar cualquier variable codificada, leer `docs/protocolo_diccionario.md`.
4. Todo código nuevo debe pasar `ruff` y `black`.
5. Actuar primero, preguntar solo cuando la ambigüedad bloquee. Una pregunta por turno, máximo tres.
6. Responder en español. Tono directo, técnico, sin adulación.
7. Al entregar código, crear/editar archivos reales, no pegar bloques sueltos.

---

## 1. Qué es este proyecto

Dashboard interactivo sobre microdatos de la Gran Encuesta Integrada de Hogares (GEIH) del DANE, construido en Streamlit, desplegado en Streamlit Community Cloud. Cubre 4 años (2022–2025).

**Doble propósito:**
- Demo funcional del Servicio A (Dashboard Ejecutivo) del portafolio profesional del usuario.
- Pieza de autoridad técnica en el nicho de mercado laboral colombiano.

**Caso de negocio (cliente tipo imaginario).** Consultora laboral / fondo de inversión / medio económico que hoy consume boletines PDF del DANE y necesita análisis interactivo por dimensión (ciudad, sector, género, edad).

**Usuario/autor del proyecto.** Daniel Molina — Economista & Data Scientist, Santa Marta, Colombia. Frase de marca: "Transformo datos en soluciones, productos y decisiones."

---

## 2. Las 5 preguntas que debe responder el dashboard

1. ¿Cómo viene el desempleo nacional vs. los últimos 12 meses?
2. ¿En qué ciudades está más duro el mercado y en cuáles más fácil?
3. ¿Qué sectores económicos están creando o perdiendo empleo?
4. ¿Cómo se comporta la brecha de género y por grupos de edad?
5. ¿Cuál es el ingreso laboral mediano y cómo ha evolucionado?

---

## 3. Datos de entrada

### 3.1 Bases de datos
- **Origen:** el usuario YA tiene 4 bases anuales consolidadas (2022, 2023, 2024, 2025), con módulos pegados.
- **NO hay fase de descarga ni consolidación mensual.** El pipeline recibe las bases como input.
- **Ubicación esperada:** `portafolio\bases_datos\geih\datos` (o .csv / .sav).

### 3.2 Diccionario de variables
- **Ruta en el repo:** `portafolio\bases_datos\geih\diccionario.xlsx`
- **Hoja única:** `Hoja1`
- **Columnas:** `nombre_variable, etiqueta_variable, descripcion, pregunta_literal, tipo_variable, codigo_categoria, categoria`
- **Contenido real medido:** 3.096 filas, 676 variables únicas, 188 con mapeos código→categoría, 488 solo metadata (continuas).
- **Protocolo oficial:** `portafolio\bases_datos\geih\instructivo_trabajo_geih.md` — lectura obligatoria antes de tocar variables codificadas.

---

## 4. Variables clave (confirmadas contra diccionario real)

### Identificación
`DIRECTORIO, SECUENCIA_P, ORDEN, HOGAR, PER, MES`

### Geográficas — SIEMPRE como texto (ceros a la izquierda críticos)
- `AREA` — 23 ciudades/áreas metropolitanas. Códigos `05`, `08`, `11`, etc.
- `DPTO` — 24 departamentos.

### Demográficas
- `P3271` — **Sexo al nacer** (1=Hombre, 2=Mujer). ⚠️ En la GEIH pre-2022 era `P6020`. Este proyecto usa la rediseñada, por eso `P3271`.
- `P6040` — Edad en años cumplidos.
- `P3042` — Nivel educativo homologado para el dashboard. Nota: la especificación inicial mencionaba `P6210`, pero en la base real 2025 la variable disponible es `P3042`.

### Condición laboral
- `OCI` — Indicador de ocupado.
- `DSI` — Indicador de desocupado.
- `P6430` — Posición ocupacional (9 categorías, mapeadas en el diccionario).
- `RAMA2D_R4` — Rama de actividad a 2 dígitos (CIIU rev.4).
- `RAMA4D_R4` — Rama de actividad a 4 dígitos.

### Ingresos
- `P6500` — Ingreso laboral principal antes de descuentos.

### Factor de expansión
- `FEX_C18` — Factor oficial post-rediseño. **Indispensable para cualquier agregado.**

### Variables que requieren mapeo complementario
`P3271` (sexo) aparece como metadata pero sin códigos en el diccionario oficial. Se resuelve con `MAPEOS_COMPLEMENTARIOS` en `src/config.py`, citando el Manual GEIH del DANE.

---

## 5. Protocolo del diccionario (resumen obligatorio)

Texto completo en `portafolio\bases_datos\geih\instructivo_trabajo_geih.md`. Puntos no negociables:

1. **Leer `codigo_categoria` como string.** Nunca como entero. `dtype=str` al abrir el Excel.
2. **Ceros a la izquierda se preservan.** `05` jamás puede volverse `5`.
3. **Regla central:** `nombre_variable + codigo_categoria → categoria`.
4. **Estrategia de recodificación: Opción 1.** Conservar columna original y agregar `<col>_label`.
   - Ejemplo: `AREA` se conserva, se crea `AREA_label` con el nombre de la ciudad.
   - El dashboard siempre muestra `_label`; los filtros y joins usan el original.
5. **Validaciones obligatorias:**
   - Cobertura: qué variables de la base tienen mapeo en el diccionario.
   - Códigos sin mapeo: reportar explícitamente.
   - Duplicados (variable, código) con categorías distintas: warning.
   - Columnas en la base no documentadas en el diccionario: reportar.
6. **Productos estandarizados que debe generar el pipeline del diccionario:**
   - `data/processed/diccionario_limpio.parquet`
   - `data/processed/mapeos_variables.json`
   - `data/processed/metadata_variables.parquet`
   - `data/processed/reporte_cobertura_diccionario.md`

---

## 6. Estructura del repositorio

```
dashboard-mercado-laboral-co/
│
├── SPEC.md                              ← Doc técnico maestro del proyecto
├── README.md                            ← Orientado a reclutadores/clientes
├── LICENSE                              ← MIT
│
├── docs/
│   ├── protocolo_diccionario.md         ← Protocolo oficial (lectura obligatoria)
│   └── decisiones_tecnicas.md           ← Log de decisiones (DT-001, DT-002, ...)
│
├── data/
│   ├── raw/                             ← 4 bases anuales (no versionadas en git)
│   │   ├── geih_2022.csv
│   │   ├── geih_2023.csv
│   │   ├── geih_2024.csv
│   │   └── geih_2025.csv
│   ├── reference/
│   │   └── diccionario.xlsx
│   └── processed/                       ← Salidas del pipeline
│
├── src/
│   ├── config.py                        ← Rutas, variables clave, mapeos complementarios
│   ├── dictionary.py                    ← Implementación del protocolo
│   ├── loaders.py                       ← Carga de bases anuales (tipado estricto)
│   ├── etl.py                           ← Pipeline principal
│   ├── indicators.py                    ← Cálculo TD, TGP, TO, ingresos (con FEX_C18)
│   └── validate.py                      ← Validación contra cifras oficiales DANE
│
├── app/
│   └── main.py                          ← Streamlit
│
├── notebooks/
│   ├── 00_explorar_diccionario.ipynb
│   ├── 01_explorar_base_anual.ipynb
│   ├── 02_aplicar_diccionario.ipynb
│   └── 03_validar_indicadores.ipynb
│
├── tests/
│   ├── test_dictionary.py
│   └── test_indicators.py
│
├── requirements.txt
└── .gitignore
```

---

## 7. Reglas de tipado estricto

Aplican en `loaders.py`. Son no negociables.

| Variable | Tipo Python |
|---|---|
| `AREA`, `DPTO` | `string` |
| `DIRECTORIO`, `SECUENCIA_P`, `ORDEN`, `HOGAR`, `PER` | `Int64` |
| `MES` | `Int8` |
| `P3271`, `P6040`, `OCI`, `DSI`, `P6430` | `Int8` |
| `P6500`, `FEX_C18` | `Float64` |
| `codigo_categoria` (en diccionario) | `string` |

---

## 8. Indicadores a calcular

Todos ponderados con `FEX_C18`.

```
PET = Personas con P6040 >= 15
TGP = (Ocupados + Desocupados) / PET × 100
TO  = Ocupados / PET × 100
TD  = Desocupados / (Ocupados + Desocupados) × 100
Ingreso mediano = mediana ponderada de P6500 entre ocupados
```

Dimensiones de corte:
- Total nacional
- Por `AREA_label` (ciudad)
- Por `P3271_label` (sexo)
- Por grupos de edad: 15-24, 25-34, 35-44, 45-54, 55-64, 65+
- Por `RAMA2D_R4_label` (sector económico)

---

## 9. Stack técnico (fijado, no discutir)

| Capa | Tecnología |
|---|---|
| Dashboard | **Streamlit** (no Dash, no Power BI) |
| Gráficos | Plotly |
| ETL | Polars + pandas + pyarrow |
| Persistencia intermedia | Parquet |
| Lectura diccionario | pandas (`dtype=str`) |
| Calidad código | ruff + black |
| Tests | pytest |
| Deploy | Streamlit Community Cloud |
| Gestión de ambientes | venv + requirements.txt |

**Python 3.11+** obligatorio.

---

## 10. Criterios de aceptación del proyecto

- [ ] Las 4 bases anuales cargan sin errores de tipado.
- [ ] `python src/etl.py` corre el pipeline completo.
- [ ] Reporte de cobertura del diccionario generado automáticamente.
- [ ] Cobertura >= 95% en variables codificadas usadas por el dashboard.
- [ ] TD calculada difiere < 0.2 puntos porcentuales de la cifra oficial DANE mensual.
- [ ] Dashboard carga en < 3 segundos.
- [ ] Las 5 vistas responden a filtros (periodo, ciudad, sexo, edad, sector).
- [ ] README con caso de negocio y reproducibilidad.
- [ ] Repo público con licencia MIT y `.gitignore` correcto.
- [ ] Dashboard desplegado en Streamlit Community Cloud con URL pública.

---

## 11. Decisiones técnicas ya tomadas

Ver `docs/decisiones_tecnicas.md`. Resumen:

- **DT-001** Sexo = `P3271`, no `P6020`. Razón: GEIH rediseñada 2022+.
- **DT-002** Mapeos complementarios en `config.py` para variables con metadata pero sin códigos (caso `P3271`). Trazabilidad al Manual DANE.
- **DT-003** `AREA`, `DPTO` siempre como `string`. Ceros a la izquierda se preservan.
- **DT-004** Duplicados `(variable, código)` en diccionario: conservar primero, warning. Detectados 43 en el diccionario real.
- **DT-005** Recodificación Opción 1: conservar + `_label`.
- **DT-006** Parquet para tabular, JSON solo para mapeos.

---

## 12. Fuera de alcance (MVP)

NO incluir en esta versión:
- Deflactar ingresos por IPC (va en iteración 2).
- Modelos predictivos (ARIMA/Prophet) — eso es el Proyecto 2 separado.
- Export a PDF automático.
- Autenticación.
- Fuentes fuera de la GEIH.

---

## 13. Estado actual del proyecto

**Última revisión documental:** 2026-04-22.

### Ya construido
- `SPEC.md`
- `README.md` (orientado a reclutadores)
- `LICENSE` (MIT)
- `.gitignore`
- `requirements.txt`
- `docs/protocolo_diccionario.md` (íntegro)
- `docs/decisiones_tecnicas.md` (DT-001 a DT-009)
- `src/config.py` (con mapeos complementarios)
- `src/dictionary.py` (implementación completa del protocolo)
- `data/reference/diccionario.xlsx` (en el repo)
- `notebooks/00_explorar_diccionario.ipynb`
- ✅ `src/loaders.py` — carga .parquet / .csv / .sav con tipado estricto
- ✅ `src/indicators.py` — TD, TO, TGP, informalidad e ingreso mediano ponderados con FEX_C18
- ✅ `src/etl.py` — pipeline end-to-end, genera `indicadores_mensuales.parquet` con 12 dimensiones
- ✅ `src/validate.py` — compara TD vs cifras DANE, tolerancia 0.2 p.p.
- ✅ `notebooks/01_explorar_base_anual.ipynb`
- ✅ `app/main.py` — Streamlit rediseñado: 7 vistas, nav lateral custom con íconos SVG, KPIs con delta, gráficos Plotly pulidos, mapa coroplético, bloques interpretativos, toggle oscuro/claro via query param, sidebar sticky
- ✅ `tests/test_dictionary.py` y `tests/test_indicators.py` — pytest
- ✅ `docs/especificaciones.md` — matriz actualizada contra el código y el parquet vigente

### Decisiones de diseño UI (2026-04-14)
- Nav lateral: links HTML puros con `?view=<key>` en query param. Sin `st.radio`.
- Vistas identificadas por clave corta: `resumen`, `poblacion`, `ocupados`, `desocupados`, `brechas`, `instrucciones`, `metodologia`.
- Toggle de tema: `?theme=Dark|Light` en query param, leído al inicio del script.
- Íconos: SVG inline estilo Feather/Lucide (16-20 px, stroke 1.8).
- Paleta: accent `#7C3AED`, accent_2 `#06B6D4`, accent_3 `#F59E0B`, positive `#10B981`, negative `#F43F5E`.

### Pendiente por construir (prioridad en este orden)
1. **`notebooks/03_validar_indicadores.ipynb`** — comparación con cifras oficiales DANE.
2. **Tiempo promedio de búsqueda (`P6240`)** — ya se carga la variable, falta agregar métrica al parquet y UI.
3. **Granularidad trimestral/anual** — definir regla y exponer controles si se mantiene en alcance.
4. **Deploy en Streamlit Community Cloud.**
5. **Post de lanzamiento en LinkedIn** con narrativa y capturas.

---

## 14. Cómo trabajar con el usuario

- El usuario tiene 10–20 horas semanales para el proyecto.
- Sabe Python, pandas, econometría. Streamlit 
- Maneja microdatos GEIH (familiar con la estructura).
- No le gusta sobre-explicación. Quiere código funcional con comentarios breves.
- Cuando el usuario dice "continuemos", seguir con la siguiente tarea pendiente del orden listado en sección 13.
- Al terminar una tarea, actualizar la sección 13 de este documento marcándola como hecha.

---

## 15. Referencias externas

- Portal oficial microdatos DANE: https://microdatos.dane.gov.co
- Boletines GEIH: https://www.dane.gov.co/index.php/estadisticas-por-tema/mercado-laboral/empleo-y-desempleo
- Catálogo GEIH 2025: https://microdatos.dane.gov.co/index.php/catalog/853
- Catálogo GEIH 2024: https://microdatos.dane.gov.co/index.php/catalog/819
- Manual metodológico GEIH 2025 — DANE DIMPE, versión 55
