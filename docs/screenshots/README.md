# Capturas del dashboard

Esta carpeta aloja las capturas que se embeben en el README principal.

## Convención de nombres

| Archivo | Vista del dashboard |
| :--- | :--- |
| `01-overview-dark.png` | Resumen — KPIs nacionales y tendencia (modo oscuro) |
| `02-regional-unemployment.png` | Mapa departamental de tasa de desempleo |
| `03-population-pyramid.png` | Pirámide poblacional + nivel educativo |
| `04-employment-trends.png` | Ocupados — tendencia TO/informalidad (modo oscuro) |

## Cómo regenerar

1. Lanza el dashboard local: `streamlit run app/Resumen.py` (o el entry-point que corresponda).
2. Captura cada vista a **1600×900 px** (16:9), formato PNG, peso < 700 KB.
3. Reemplaza los archivos en esta carpeta manteniendo los nombres exactos.
4. Commit con mensaje `docs: actualiza capturas del dashboard`.
