# PROMPT MAESTRO â€” Dashboard del Mercado Laboral Colombiano (GEIH)

> Pega este documento como contexto inicial en Claude Code, Cursor u otro agente.
> Al leerlo, el agente debe tener todo lo necesario para trabajar el proyecto sin preguntas sobre el fondo.

---

## 0. Instrucciones para el agente

1. Leer este documento completo antes de escribir cÃ³digo.
2. Respetar las decisiones tÃ©cnicas ya fijadas (stack, estructura, protocolo del diccionario). No proponer cambios salvo que el usuario lo pida.
3. Antes de tocar cualquier variable codificada, leer `docs/protocolo_diccionario.md`.
4. Todo cÃ³digo nuevo debe pasar `ruff` y `black`.
5. Actuar primero, preguntar solo cuando la ambigÃ¼edad bloquee. Una pregunta por turno, mÃ¡ximo tres.
6. Responder en espaÃ±ol. Tono directo, tÃ©cnico, sin adulaciÃ³n.
7. Al entregar cÃ³digo, crear/editar archivos reales, no pegar bloques sueltos.

---

## 1. QuÃ© es este proyecto

Dashboard interactivo sobre microdatos de la Gran Encuesta Integrada de Hogares (GEIH) del DANE, construido en Streamlit, desplegado en Streamlit Community Cloud. Cubre 4 aÃ±os (2022â€“2025).

**Doble propÃ³sito:**
- Demo funcional del Servicio A (Dashboard Ejecutivo) del portafolio profesional del usuario.
- Pieza de autoridad tÃ©cnica en el nicho de mercado laboral colombiano.

**Caso de negocio (cliente tipo imaginario).** Consultora laboral / fondo de inversiÃ³n / medio econÃ³mico que hoy consume boletines PDF del DANE y necesita anÃ¡lisis interactivo por dimensiÃ³n (ciudad, sector, gÃ©nero, edad).

**Usuario/autor del proyecto.** Daniel Molina â€” Economista & Data Scientist, Santa Marta, Colombia. Frase de marca: "Transformo datos en soluciones, productos y decisiones."

---

## 2. Las 5 preguntas que debe responder el dashboard

1. Â¿CÃ³mo viene el desempleo nacional vs. los Ãºltimos 12 meses?
2. Â¿En quÃ© ciudades estÃ¡ mÃ¡s duro el mercado y en cuÃ¡les mÃ¡s fÃ¡cil?
3. Â¿QuÃ© sectores econÃ³micos estÃ¡n creando o perdiendo empleo?
4. Â¿CÃ³mo se comporta la brecha de gÃ©nero y por grupos de edad?
5. Â¿CuÃ¡l es el ingreso laboral mediano y cÃ³mo ha evolucionado?

---

## 3. Datos de entrada

### 3.1 Bases de datos
- **Origen:** el usuario YA tiene 4 bases anuales consolidadas (2022, 2023, 2024, 2025), con mÃ³dulos pegados.
- **NO hay fase de descarga ni consolidaciÃ³n mensual.** El pipeline recibe las bases como input.
- **UbicaciÃ³n esperada:** `portafolio\bases_datos\geih\datos` (o .csv / .sav).

### 3.2 Diccionario de variables
- **Ruta en el repo:** `portafolio\bases_datos\geih\diccionario.xlsx`
- **Hoja Ãºnica:** `Hoja1`
- **Columnas:** `nombre_variable, etiqueta_variable, descripcion, pregunta_literal, tipo_variable, codigo_categoria, categoria`
- **Contenido real medido:** 3.096 filas, 676 variables Ãºnicas, 188 con mapeos cÃ³digoâ†’categorÃ­a, 488 solo metadata (continuas).
- **Protocolo oficial:** `portafolio\bases_datos\geih\instructivo_trabajo_geih.md` â€” lectura obligatoria antes de tocar variables codificadas.

---

## 4. Variables clave (confirmadas contra diccionario real)

### IdentificaciÃ³n
`DIRECTORIO, SECUENCIA_P, ORDEN, HOGAR, PER, MES`

### GeogrÃ¡ficas â€” SIEMPRE como texto (ceros a la izquierda crÃ­ticos)
- `AREA` â€” 23 ciudades/Ã¡reas metropolitanas. CÃ³digos `05`, `08`, `11`, etc.
- `DPTO` â€” 24 departamentos.

### DemogrÃ¡ficas
- `P3271` â€” **Sexo al nacer** (1=Hombre, 2=Mujer). âš ï¸ En la GEIH pre-2022 era `P6020`. Este proyecto usa la rediseÃ±ada, por eso `P3271`.
- `P6040` â€” Edad en aÃ±os cumplidos.
- `P3042` â€” Nivel educativo homologado para el dashboard. Nota: la especificaciÃ³n inicial mencionaba `P6210`, pero en la base real 2025 la variable disponible es `P3042`.

### CondiciÃ³n laboral
- `OCI` â€” Indicador de ocupado.
- `DSI` â€” Indicador de desocupado.
- `P6430` â€” PosiciÃ³n ocupacional (9 categorÃ­as, mapeadas en el diccionario).
- `RAMA2D_R4` â€” Rama de actividad a 2 dÃ­gitos (CIIU rev.4).
- `RAMA4D_R4` â€” Rama de actividad a 4 dÃ­gitos.

### Ingresos
- `P6500` â€” Ingreso laboral principal antes de descuentos.

### Factor de expansiÃ³n
- `FEX_C18` â€” Factor oficial post-rediseÃ±o. **Indispensable para cualquier agregado.**

### Variables que requieren mapeo complementario
`P3271` (sexo) aparece como metadata pero sin cÃ³digos en el diccionario oficial. Se resuelve con `MAPEOS_COMPLEMENTARIOS` en `src/config.py`, citando el Manual GEIH del DANE.

---

## 5. Protocolo del diccionario (resumen obligatorio)

Texto completo en `portafolio\bases_datos\geih\instructivo_trabajo_geih.md`. Puntos no negociables:

1. **Leer `codigo_categoria` como string.** Nunca como entero. `dtype=str` al abrir el Excel.
2. **Ceros a la izquierda se preservan.** `05` jamÃ¡s puede volverse `5`.
3. **Regla central:** `nombre_variable + codigo_categoria â†’ categoria`.
4. **Estrategia de recodificaciÃ³n: OpciÃ³n 1.** Conservar columna original y agregar `<col>_label`.
   - Ejemplo: `AREA` se conserva, se crea `AREA_label` con el nombre de la ciudad.
   - El dashboard siempre muestra `_label`; los filtros y joins usan el original.
5. **Validaciones obligatorias:**
   - Cobertura: quÃ© variables de la base tienen mapeo en el diccionario.
   - CÃ³digos sin mapeo: reportar explÃ­citamente.
   - Duplicados (variable, cÃ³digo) con categorÃ­as distintas: warning.
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
â”‚
â”œâ”€â”€ spec.MD                              â† Doc tÃ©cnico maestro del proyecto
â”œâ”€â”€ README.md                            â† Orientado a reclutadores/clientes
â”œâ”€â”€ LICENSE                              â† MIT
â”‚
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ protocolo_diccionario.md         â† Protocolo oficial (lectura obligatoria)
â”‚   â””â”€â”€ decisiones_tecnicas.md           â† Log de decisiones (DT-001, DT-002, ...)
â”‚
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ reference/
â”‚   â”‚   â””â”€â”€ colombia_departamentos.geojson
â”‚   â””â”€â”€ processed/                       â† Salidas del pipeline y diccionario procesado
â”‚
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ config.py                        â† Rutas, variables clave, mapeos complementarios
â”‚   â”œâ”€â”€ dictionary.py                    â† ImplementaciÃ³n del protocolo
â”‚   â”œâ”€â”€ loaders.py                       â† Carga de bases anuales (tipado estricto)
â”‚   â”œâ”€â”€ etl.py                           â† Pipeline principal
â”‚   â”œâ”€â”€ indicators.py                    â† CÃ¡lculo TD, TGP, TO, ingresos (con FEX_C18)
â”‚   â””â”€â”€ validate.py                      â† ValidaciÃ³n contra cifras oficiales DANE
â”‚
â”œâ”€â”€ app/
â”‚   â””â”€â”€ main.py                          â† Streamlit
â”‚
â”œâ”€â”€ notebooks/
â”‚   â”œâ”€â”€ 00_explorar_diccionario.ipynb
â”‚   â””â”€â”€ 01_explorar_base_anual.ipynb
â”‚
â”œâ”€â”€ tests/
â”‚   â”œâ”€â”€ test_dictionary.py
â”‚   â””â”€â”€ test_indicators.py
â”‚
â”œâ”€â”€ requirements.txt
â””â”€â”€ .gitignore
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
TGP = (Ocupados + Desocupados) / PET Ã— 100
TO  = Ocupados / PET Ã— 100
TD  = Desocupados / (Ocupados + Desocupados) Ã— 100
Ingreso mediano = mediana ponderada de P6500 entre ocupados
```

Dimensiones de corte:
- Total nacional
- Por `DPTO_label` (departamento)
- Por `AREA_label` (ciudad)
- Por `P3271_label` (sexo)
- Por grupos de edad quinquenales: 15-19, 20-24, 25-29, 30-34, 35-39, 40-44, 45-49, 50-54, 55-59, 60-64, 65+
- Por brecha etaria: 15-28 vs 29+
- Por `RAMA2D_R4_label` (sector econÃ³mico)
- Por `CLASE_label`, `P6070_label`, `P3042_label` y `P6430_label`

---

## 9. Stack tÃ©cnico (fijado, no discutir)

| Capa | TecnologÃ­a |
|---|---|
| Dashboard | **Streamlit** (no Dash, no Power BI) |
| GrÃ¡ficos | Plotly |
| ETL | Polars + pandas + pyarrow |
| Persistencia intermedia | Parquet |
| Lectura diccionario | pandas (`dtype=str`) |
| Calidad cÃ³digo | ruff + black |
| Tests | pytest |
| Deploy | Streamlit Community Cloud |
| GestiÃ³n de ambientes | venv + requirements.txt |

**Python 3.11+** obligatorio.

---

## 10. Criterios de aceptaciÃ³n del proyecto

- [ ] Las 4 bases anuales cargan sin errores de tipado.
- [ ] `python src/etl.py` corre el pipeline completo.
- [ ] Reporte de cobertura del diccionario generado automÃ¡ticamente.
- [ ] Cobertura >= 95% en variables codificadas usadas por el dashboard.
- [ ] TD calculada difiere < 0.2 puntos porcentuales de la cifra oficial DANE mensual.
- [ ] Dashboard carga en < 3 segundos.
- [ ] Las 5 vistas analÃ­ticas responden a filtros globales; Instrucciones y MetodologÃ­a son vistas de lectura.
- [ ] README con caso de negocio y reproducibilidad.
- [ ] Repo pÃºblico con licencia MIT y `.gitignore` correcto.
- [ ] Dashboard desplegado en Streamlit Community Cloud con URL pÃºblica.

---

## 11. Decisiones tÃ©cnicas ya tomadas

Ver `docs/decisiones_tecnicas.md`. Resumen:

- **DT-001** Sexo = `P3271`, no `P6020`. RazÃ³n: GEIH rediseÃ±ada 2022+.
- **DT-002** Mapeos complementarios en `config.py` para variables con metadata pero sin cÃ³digos (caso `P3271`). Trazabilidad al Manual DANE.
- **DT-003** `AREA`, `DPTO` siempre como `string`. Ceros a la izquierda se preservan.
- **DT-004** Duplicados `(variable, cÃ³digo)` en diccionario: conservar primero, warning. Detectados 43 en el diccionario real.
- **DT-005** RecodificaciÃ³n OpciÃ³n 1: conservar + `_label`.
- **DT-006** Parquet para tabular, JSON solo para mapeos.
- **DT-011** Eliminación de indentación en `st.markdown`. Evita que el HTML se interprete como bloques de código Markdown.

---

## 12. Fuera de alcance (MVP)

NO incluir en esta versiÃ³n:
- Deflactar ingresos por IPC (va en iteraciÃ³n 2).
- Modelos predictivos (ARIMA/Prophet) â€” eso es el Proyecto 2 separado.
- Export a PDF automÃ¡tico.
- AutenticaciÃ³n.
- Fuentes fuera de la GEIH.

---

## 13. Estado actual del proyecto

**Ãšltima revisiÃ³n documental:** 2026-04-25.

### Ya construido
- `spec.MD`
- `README.md` (orientado a reclutadores)
- `LICENSE` (MIT)
- `.gitignore`
- `requirements.txt`
- `docs/protocolo_diccionario.md` (Ã­ntegro)
- `docs/decisiones_tecnicas.md` (DT-001 a DT-011)
- `src/config.py` (con mapeos complementarios)
- `src/dictionary.py` (implementaciÃ³n completa del protocolo)
- `data/reference/colombia_departamentos.geojson`
- Diccionario GEIH resuelto por `src/config.py`: ruta externa `portafolio/bases_datos/geih/diccionario.xlsx` con fallback a `data/reference/diccionario.xlsx`
- `notebooks/00_explorar_diccionario.ipynb`
- âœ… `src/loaders.py` â€” carga .parquet / .csv / .sav con tipado estricto
- âœ… `src/indicators.py` â€” TD, TO, TGP, informalidad e ingreso mediano ponderados con FEX_C18
- âœ… `src/etl.py` â€” pipeline end-to-end, genera `indicadores_mensuales.parquet` con 12 dimensiones
- âœ… `src/validate.py` â€” compara TD vs cifras DANE, tolerancia 0.2 p.p.
- âœ… `notebooks/01_explorar_base_anual.ipynb`
- âœ… `app/main.py` â€” Streamlit rediseÃ±ado: 7 vistas, nav lateral custom con Ã­conos SVG, KPIs con delta, grÃ¡ficos Plotly pulidos, mapa coroplÃ©tico, bloques interpretativos, toggle oscuro/claro via query param, sidebar sticky
- âœ… `tests/test_dictionary.py` y `tests/test_indicators.py` â€” pytest
- âœ… `docs/especificaciones.md` â€” matriz actualizada contra el cÃ³digo y el parquet vigente
- âœ… `data/processed/indicadores_mensuales.parquet` â€” 6.160 filas, 25 columnas y 12 dimensiones

### Decisiones de diseÃ±o UI (2026-04-14)
- Nav lateral: links HTML puros con `?view=<key>` en query param. Sin `st.radio`.
- Vistas identificadas por clave corta: `resumen`, `poblacion`, `ocupados`, `desocupados`, `brechas`, `instrucciones`, `metodologia`.
- Toggle de tema: `?theme=Dark|Light` en query param, leÃ­do al inicio del script.
- Ãconos: SVG inline estilo Feather/Lucide (16-20 px, stroke 1.8).
- Paleta: accent `#7C3AED`, accent_2 `#06B6D4`, accent_3 `#F59E0B`, positive `#10B981`, negative `#F43F5E`.

### Pendiente por construir (prioridad en este orden)
1. **`notebooks/03_validar_indicadores.ipynb`** â€” comparaciÃ³n con cifras oficiales DANE.
2. **Tiempo promedio de bÃºsqueda (`P6240`)** â€” ya se carga la variable, falta agregar mÃ©trica al parquet y UI.
3. **Granularidad trimestral/anual** â€” definir regla y exponer controles si se mantiene en alcance.
4. **Deploy en Streamlit Community Cloud.**
5. **Post de lanzamiento en LinkedIn** con narrativa y capturas.

---

## 14. CÃ³mo trabajar con el usuario

- El usuario tiene 10â€“20 horas semanales para el proyecto.
- Sabe Python, pandas, econometrÃ­a. Streamlit 
- Maneja microdatos GEIH (familiar con la estructura).
- No le gusta sobre-explicaciÃ³n. Quiere cÃ³digo funcional con comentarios breves.
- Cuando el usuario dice "continuemos", seguir con la siguiente tarea pendiente del orden listado en secciÃ³n 13.
- Al terminar una tarea, actualizar la secciÃ³n 13 de este documento marcÃ¡ndola como hecha.

---

## 15. Referencias externas

- Portal oficial microdatos DANE: https://microdatos.dane.gov.co
- Boletines GEIH: https://www.dane.gov.co/index.php/estadisticas-por-tema/mercado-laboral/empleo-y-desempleo
- CatÃ¡logo GEIH 2025: https://microdatos.dane.gov.co/index.php/catalog/853
- CatÃ¡logo GEIH 2024: https://microdatos.dane.gov.co/index.php/catalog/819
- Manual metodolÃ³gico GEIH 2025 â€” DANE DIMPE, versiÃ³n 55
