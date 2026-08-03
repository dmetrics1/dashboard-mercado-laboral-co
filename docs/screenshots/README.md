# Capturas del dashboard

Esta carpeta aloja las capturas que se embeben en el README principal.

## Convención de nombres

| Archivo | Vista del dashboard |
| :--- | :--- |
| `01-overview-light.png` | Resumen — KPIs nacionales y tendencia (modo claro, el predeterminado) |
| `02-employment-informality.png` | Ocupados — informalidad, ingreso mediano COP y tendencia TO (modo claro) |
| `03-regional-unemployment.png` | Mapa departamental de tasa de desempleo (modo claro) |
| `04-overview-dark.png` | Resumen en modo oscuro — identidad Premium Dark Tech |

## Cómo regenerar

1. Lanza el dashboard local: `streamlit run app/main.py`.
2. Captura cada vista a **1600×900 px** (16:9), formato PNG, peso < 700 KB.
   El modo se controla con el query param `?theme=Light|Dark`.
3. Reemplaza los archivos en esta carpeta manteniendo los nombres exactos.
4. Commit con mensaje `docs: actualiza capturas del dashboard`.
