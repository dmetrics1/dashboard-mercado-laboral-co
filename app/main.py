"""
Dashboard GEIH 2022-2025 — Mercado Laboral Colombiano.
"""
import json
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import INDICADORES_PATH

st.set_page_config(
    page_title="Mercado Laboral · Colombia",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Visualización: Mapa
# ---------------------------------------------------------------------------
@st.cache_data
def _load_geojson():
    path = Path(__file__).parent.parent / "data" / "reference" / "colombia_departamentos.geojson"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _geo_key(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.upper().replace(".", " ").split())


def _format_map_value(indicador: str, value) -> str:
    if pd.isna(value):
        return "s/d"
    meta = MAP_INDICATORS.get(indicador, {})
    if meta.get("kind") == "money":
        return f"${fmt_metric(value)}"
    if meta.get("kind") == "count":
        return fmt_metric(value)
    if meta.get("suffix") == "%":
        return f"{float(value):.1f}%"
    return f"{float(value):.1f}"


def plot_mapa_departamentos(df, indicador="TD", title="", geo_sel="Todos"):
    t = ACTIVE_THEME
    geojson = _load_geojson()
    if df.empty or "DPTO_label" not in df.columns or indicador not in df.columns:
        return fig_base(go.Figure(), title)
    data = (
        df.sort_values("periodo")
        .groupby("DPTO_label", as_index=False)[indicador]
        .last()
        .dropna(subset=[indicador])
    )
    geo_names = [f["properties"]["NOMBRE_DPT"] for f in geojson["features"]]
    geo_lookup = {_geo_key(name): name for name in geo_names}

    def match_geo_name(label):
        key = _geo_key(label)
        if "BOGOTA" in key:
            return "SANTAFE DE BOGOTA D.C"
        if "SAN ANDRES" in key:
            return "ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA"
        return geo_lookup.get(key)

    data["_geo_name"] = data["DPTO_label"].map(match_geo_name)
    data = data.dropna(subset=["_geo_name"])
    data["_value_fmt"] = data[indicador].map(lambda value: _format_map_value(indicador, value))
    label = MAP_INDICATORS.get(indicador, {}).get("label", indicador)

    fig = go.Figure(go.Choroplethmapbox(
        geojson=geojson,
        locations=data["_geo_name"],
        z=data[indicador],
        customdata=data[["DPTO_label", "_value_fmt"]],
        featureidkey="properties.NOMBRE_DPT",
        colorscale=BLUE_TEAL_SCALE,
        marker_opacity=1.0,
        marker_line_width=1.0,
        marker_line_color="rgba(255,255,255,0.75)",
        colorbar=dict(
            title="",
            thickness=11,
            len=0.62,
            x=0.965,
            xanchor="right",
            y=0.5,
            tickfont=dict(color=t["soft_text"], size=10),
        ),
        hovertemplate="<b>%{customdata[0]}</b><br>" + f"{label}: %{{customdata[1]}}<extra></extra>",
    ))

    # Highlight del departamento seleccionado: relleno semitransparente + borde grueso
    if geo_sel not in ("Todos", "Todas", "", None):
        sel_row = data[data["DPTO_label"] == geo_sel]
        if not sel_row.empty:
            fig.add_trace(go.Choroplethmapbox(
                geojson=geojson,
                locations=sel_row["_geo_name"],
                z=sel_row[indicador],
                featureidkey="properties.NOMBRE_DPT",
                colorscale=[[0, "rgba(224,90,42,0.20)"], [1, "rgba(224,90,42,0.20)"]],
                marker_opacity=1,
                marker_line_width=3,
                marker_line_color="#E05A2A",
                showscale=False,
                hoverinfo="skip",
            ))

    fig.update_layout(
        mapbox_style="carto-positron" if st.session_state.get("theme_mode") == "Light" else "carto-darkmatter",
        mapbox_zoom=4.18,
        mapbox_center={"lat": 4.55, "lon": -74.20},
        mapbox=dict(pitch=40, bearing=0),
        height=500,
        margin={"r":0,"t":42 if title else 0,"l":0,"b":0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text=title, font=dict(size=14, color=t["text"]), x=0.05, y=0.95) if title else None,
    )
    return fig


def plot_mapa_ciudades(df_city: pd.DataFrame, indicador: str = "TD", geo_sel: str = "Todas"):
    t = ACTIVE_THEME
    if df_city.empty or "AREA_label" not in df_city.columns or indicador not in df_city.columns:
        return go.Figure()
    data = (
        df_city.sort_values("periodo")
        .groupby("AREA_label", as_index=False)[indicador]
        .last()
        .dropna(subset=[indicador])
    )

    # Lookup robusto: strip sufijos " AM"/" DC" + normalización NFKD
    _coord_lookup = {_geo_key(k): v for k, v in CITY_COORDS.items()}

    def _match_coords(label):
        clean = label.replace(" AM", "").replace(" DC", "").strip()
        coords = _coord_lookup.get(_geo_key(clean))
        if coords:
            return coords
        first = _geo_key(clean.split()[0])
        for norm_key, c in _coord_lookup.items():
            if norm_key.startswith(first) or first.startswith(norm_key):
                return c
        return None

    data["_coords"] = data["AREA_label"].map(_match_coords)
    data = data[data["_coords"].notna()].copy()
    data["lat"] = data["_coords"].map(lambda c: c[0])
    data["lon"] = data["_coords"].map(lambda c: c[1])
    data["_value_fmt"] = data[indicador].map(lambda v: _format_map_value(indicador, v))
    label = MAP_INDICATORS.get(indicador, {}).get("label", indicador)
    vmin, vmax = data[indicador].min(), data[indicador].max()

    # ciudad_sel solo es True si geo_sel existe en las ciudades del dataset
    ciudad_sel = (
        geo_sel not in ("Todos", "Todas", "", None)
        and geo_sel in data["AREA_label"].values
    )
    sel_row = data[data["AREA_label"] == geo_sel] if ciudad_sel else pd.DataFrame()

    traces = []

    # Anillo de la ciudad seleccionada en naranja/ámbar para contrastar con el colorscale azul
    _CITY_RING = "#E05A2A"
    if not sel_row.empty:
        base_size = float(18 + (sel_row[indicador].iloc[0] - vmin) / (vmax - vmin + 1e-9) * 26)
        traces.append(go.Scattermapbox(
            lat=sel_row["lat"], lon=sel_row["lon"],
            mode="markers",
            marker=go.scattermapbox.Marker(
                size=base_size + 14,
                color=_CITY_RING,
                opacity=1,
                sizemode="diameter",
            ),
            hoverinfo="skip",
            showlegend=False,
        ))

    # Todas las ciudades con colorscale (siempre visibles)
    traces.append(go.Scattermapbox(
        lat=data["lat"], lon=data["lon"],
        mode="markers",
        marker=go.scattermapbox.Marker(
            size=data[indicador].map(
                lambda v: 18 + (v - vmin) / (vmax - vmin + 1e-9) * 26
            ),
            color=data[indicador],
            colorscale=BLUE_TEAL_SCALE,
            cmin=vmin, cmax=vmax,
            colorbar=dict(
                thickness=11, len=0.6, x=0.965, xanchor="right",
                tickfont=dict(color=t["soft_text"], size=10), title="",
            ),
            opacity=0.9,
            sizemode="diameter",
        ),
        customdata=data[["AREA_label", "_value_fmt"]],
        hovertemplate="<b>%{customdata[0]}</b><br>" + f"{label}: %{{customdata[1]}}<extra></extra>",
    ))

    # Etiqueta de la ciudad seleccionada
    if not sel_row.empty:
        traces.append(go.Scattermapbox(
            lat=sel_row["lat"], lon=sel_row["lon"],
            mode="text",
            text=sel_row["AREA_label"],
            textposition="top right",
            textfont=dict(size=12, color=_CITY_RING, weight=700),
            hoverinfo="skip",
            showlegend=False,
        ))

    fig = go.Figure(data=traces)

    fig.update_layout(
        mapbox_style="carto-positron" if st.session_state.get("theme_mode") == "Light" else "carto-darkmatter",
        mapbox_zoom=4.2,
        mapbox_center={"lat": 4.55, "lon": -74.20},
        height=490,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def render_interpretation(text: str, title: str = "Lectura"):
    st.markdown(f"""
<div class="interpretation-block">
<div class="interpretation-title">{title}</div>
<div class="interpretation-text">{text}</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Paleta y temas
# ---------------------------------------------------------------------------
THEMES = {
    "Dark": {
        "accent": "#338CA1",
        "accent_2": "#7BBDBF",
        "accent_3": "#F59E0B",
        "positive": "#10B981",
        "negative": "#F43F5E",
        "text": "#F1F5F9",
        "muted": "#94A3B8",
        "line": "rgba(255,255,255,0.10)",
        "app_bg": "linear-gradient(160deg, #080c1a 0%, #07091a 60%, #04060f 100%)",
        "sidebar_bg": "rgba(10,14,28,0.98)",
        "panel_bg": "rgba(15,21,40,0.96)",
        "panel_solid": "rgba(12,18,35,0.98)",
        "soft_text": "#CBD5E1",
        "eyebrow_bg": "rgba(81,166,174,0.18)",
        "eyebrow_text": "#7BBDBF",
        "input_bg": "rgba(255,255,255,0.04)",
        "chart_grid": "rgba(255,255,255,0.07)",
        "chart_bg": "rgba(0,0,0,0)",
    },
    "Light": {
        "accent": "#1E2D55",
        "accent_2": "#27638A",
        "accent_3": "#B45309",
        "positive": "#047857",
        "negative": "#B91C1C",
        "text": "#1A1812",
        "muted": "#5C5A52",
        "line": "rgba(26,24,18,0.14)",
        "app_bg": "#F4EFE6",
        "sidebar_bg": "#FBF8F1",
        "panel_bg": "#FBF8F1",
        "panel_solid": "#FBF8F1",
        "soft_text": "#2A2620",
        "eyebrow_bg": "rgba(30,45,85,0.08)",
        "eyebrow_text": "#1E2D55",
        "input_bg": "rgba(26,24,18,0.04)",
        "chart_grid": "rgba(26,24,18,0.08)",
        "chart_bg": "rgba(0,0,0,0)",
    },
}

ACTIVE_THEME = THEMES["Light"]

AGE_ORDER = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]

MESES_NOMBRE = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}
MESES_INVERSO = {v: k for k, v in MESES_NOMBRE.items()}

# Alturas estándar para mantener proporciones homogéneas por fila
H_PAIRED   = 480   # gráficos en columnas de 2 (mismo valor para ambos)
H_PYRAMID  = 480   # pirámide siempre igual a su par
H_SINGLE   = 380   # gráficos que van solos a ancho completo
H_SMALL    = 320   # gráficos pequeños (3 columnas, guía, metodología)

BLUE_TEAL_30 = [
    "#EDF7F7", "#E5F3F3", "#DDEEEF", "#D5EAEB", "#CCE5E6",
    "#C3E0E2", "#B9DBDD", "#AED6D8", "#A2D0D2", "#96CACC",
    "#89C4C5", "#7BBDBF", "#6DB6B9", "#5FAEB3", "#51A6AE",
    "#459EA9", "#3B95A5", "#338CA1", "#2E829D", "#2B7898",
    "#296E91", "#27638A", "#255982", "#244F7A", "#234672",
    "#223F6B", "#213964", "#20345E", "#1F3059", "#1E2D55",
]
BLUE_TEAL_SCALE = [[i / (len(BLUE_TEAL_30) - 1), color] for i, color in enumerate(BLUE_TEAL_30)]
BLUE_TEAL_DISCRETE = ["#1E2D55", "#27638A", "#338CA1", "#51A6AE", "#7BBDBF", "#A2D0D2", "#D5EAEB"]
BT_NAVY, BT_DEEP, BT_BLUE, BT_TEAL, BT_MINT, BT_PALE, BT_ICE = BLUE_TEAL_DISCRETE
SEX_COLORS = {"Hombre": BT_DEEP, "Mujer": BT_TEAL}

# Salario Mínimo Mensual Legal Vigente (COP) — Decreto DANE cada enero
SMMLV = {2022: 1_000_000, 2023: 1_160_000, 2024: 1_300_606, 2025: 1_423_500}

MAP_INDICATORS = {
    "TD": {"label": "Tasa de desempleo (TD)", "select": "TD - Desempleo", "short": "TD", "suffix": "%", "kind": "pct"},
    "TO": {"label": "Tasa de ocupación (TO)", "select": "TO - Ocupación", "short": "TO", "suffix": "%", "kind": "pct"},
    "TGP": {"label": "Tasa global de participación", "select": "TGP - Participación", "short": "TGP", "suffix": "%", "kind": "pct"},
    "tasa_informalidad": {"label": "Tasa de informalidad", "select": "Informalidad", "short": "Informalidad", "suffix": "%", "kind": "pct"},
    "ocupados_exp": {"label": "Ocupados", "select": "Ocupados", "short": "Ocupados", "suffix": "", "kind": "count"},
    "desocupados_exp": {"label": "Desocupados", "select": "Desocupados", "short": "Desocupados", "suffix": "", "kind": "count"},
    "poblacion_total_exp": {"label": "Población total", "select": "Población", "short": "Población", "suffix": "", "kind": "count"},
    "ingreso_mediano": {"label": "Ingreso mediano", "select": "Ingreso", "short": "Ingreso", "suffix": "", "kind": "money"},
    "tasa_inactividad": {
        "label": "Tasa de inactividad (FFT/PET)",
        "select": "Inactividad",
        "short": "Inactividad",
        "suffix": "%",
        "kind": "pct"
    },
    "FFT_exp": {
        "label": "Inactivos (FFT)",
        "select": "Inactivos",
        "short": "Inactivos",
        "suffix": "",
        "kind": "count"
    },
}

CITY_COORDS = {
    "Medellín":       (6.2518,  -75.5636),
    "Barranquilla":   (10.9639, -74.7964),
    "Bogotá":         (4.7110,  -74.0721),
    "Cartagena":      (10.3910, -75.4794),
    "Manizales":      (5.0703,  -75.5138),
    "Montería":       (8.7575,  -75.8811),
    "Villavicencio":  (4.1420,  -73.6266),
    "Pasto":          (1.2136,  -77.2811),
    "Cúcuta":         (7.8939,  -72.5078),
    "Pereira":        (4.8133,  -75.6961),
    "Bucaramanga":    (7.1254,  -73.1198),
    "Ibagué":         (4.4389,  -75.2322),
    "Cali":           (3.4516,  -76.5320),
    "Quibdó":         (5.6919,  -76.6583),
    "Neiva":          (2.9273,  -75.2819),
    "Riohacha":       (11.5444, -72.9072),
    "Santa Marta":    (11.2408, -74.1990),
    "Valledupar":     (10.4631, -73.2532),
    "Sincelejo":      (9.3047,  -75.3978),
    "Armenia":        (4.5339,  -75.6811),
    "Popayán":        (2.4448,  -76.6147),
    "Florencia":      (1.6144,  -75.6062),
    "Tunja":          (5.5353,  -73.3678),
}

# Claves cortas usadas en routing y query_params
# (key, label display, SVG icon inline)
_I = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
NAV_ITEMS = [
    ("resumen",      "Resumen",
     _I + '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>'
          '<rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>'),
    ("poblacion",    "Población",
     _I + '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'
          '<path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>'),
    ("ocupados",     "Ocupados",
     _I + '<rect x="2" y="7" width="20" height="14" rx="2" ry="2"/>'
          '<path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>'),
    ("desocupados",  "Desocupados",
     _I + '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'),
    ("brechas",      "Brechas",
     _I + '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>'
          '<line x1="6" y1="20" x2="6" y2="14"/></svg>'),
    ("instrucciones", "Guía Usuario",
     _I + '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'),
    ("metodologia",  "Metodología",
     _I + '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
          '<polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/>'
          '<line x1="16" y1="17" x2="8" y2="17"/></svg>'),
]
NAV_LABELS = {key: label for key, label, _ in NAV_ITEMS}
VIEWS = [key for key, _, _ in NAV_ITEMS]

AUTHOR_LINKEDIN = "https://www.linkedin.com/in/daniel-molina-b76a4323b"
AUTHOR_GITHUB = "https://github.com/dmetrics1"
AUTHOR_PORTFOLIO = "https://danielmolina.dev"

ICON_LINKEDIN = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path fill="currentColor" d="M6.94 8.98H3.76v10.18h3.18V8.98Zm.27-3.14a1.83 1.83 0 1 0-3.66 0 1.83 1.83 0 0 0 3.66 0Zm12.9 7.5c0-3.06-1.63-4.48-3.8-4.48a3.29 3.29 0 0 0-2.98 1.64h-.04V8.98h-3.05v10.18h3.18v-5.04c0-1.33.25-2.62 1.9-2.62 1.63 0 1.65 1.52 1.65 2.7v4.96h3.18v-5.82h-.04Z"/>'
    '</svg>'
)
ICON_GITHUB = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path fill="currentColor" d="M12.02 2.2a10 10 0 0 0-3.16 19.49c.5.1.68-.21.68-.48v-1.7c-2.78.61-3.37-1.18-3.37-1.18-.45-1.16-1.1-1.47-1.1-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.04 1.53 1.04.9 1.53 2.35 1.09 2.92.83.09-.65.35-1.09.64-1.34-2.22-.25-4.56-1.11-4.56-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02a9.47 9.47 0 0 1 5 0c1.9-1.29 2.74-1.02 2.74-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.69-4.57 4.94.36.31.68.92.68 1.86v2.76c0 .27.18.59.69.48A10 10 0 0 0 12.02 2.2Z"/>'
    '</svg>'
)
ICON_SUN = (
    _I + '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/>'
    '<path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/>'
    '<path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/>'
    '<path d="m19.07 4.93-1.41 1.41"/></svg>'
)
ICON_MOON = _I + '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'


# ---------------------------------------------------------------------------
# Estilos globales
# ---------------------------------------------------------------------------
def inject_styles(theme_name: str) -> None:
    t = THEMES[theme_name]
    # Paleta cálida para modo claro — todos los tonos en la misma familia arena/lino
    sidebar_surface = t["panel_bg"] if theme_name == "Light" else "#0B1020"
    sidebar_border = "rgba(139,110,75,0.18)" if theme_name == "Light" else "rgba(255,255,255,0.08)"
    sidebar_text = "#1A1812" if theme_name == "Light" else "#E5E7EB"
    sidebar_muted = "#6B6355" if theme_name == "Light" else "#9AA4B2"
    sidebar_input = "rgba(26,24,18,0.05)" if theme_name == "Light" else "rgba(255,255,255,0.04)"
    sidebar_accent = f"linear-gradient(135deg, {BT_DEEP} 0%, {BT_BLUE} 56%, {BT_TEAL} 100%)"
    sidebar_accent_soft = "rgba(30,45,85,0.08)" if theme_name == "Light" else "rgba(81,166,174,0.15)"
    sidebar_accent_border = "rgba(30,45,85,0.18)" if theme_name == "Light" else "rgba(123,189,191,0.34)"
    sidebar_accent_shadow = "0 8px 20px rgba(30,45,85,0.18)" if theme_name == "Light" else "0 10px 28px rgba(0,0,0,0.34)"
    select_bg = "#F5F0E6" if theme_name == "Light" else "#0C1223"
    select_text = "#1A1812" if theme_name == "Light" else "#F8FAFC"
    select_muted = "#6B6355" if theme_name == "Light" else "#CBD5E1"
    select_border = "rgba(139,110,75,0.22)" if theme_name == "Light" else "rgba(255,255,255,0.16)"
    dropdown_bg = "#F5F0E6" if theme_name == "Light" else "#0F172A"
    dropdown_hover = "#E2E8F0" if theme_name == "Light" else "rgba(81,166,174,0.16)"
    chrome_shadow = "0 6px 18px rgba(139,110,75,0.10)" if theme_name == "Light" else "0 10px 24px rgba(0,0,0,0.18)"
    chart_shadow = "0 10px 24px rgba(15,23,42,0.07)" if theme_name == "Light" else "0 12px 28px rgba(0,0,0,0.16)"
    sidebar_width = "15.5rem"
    sidebar_gap = "0.9rem"
    content_left = "16.85rem"

    # Color para botón de limpiar
    btn_clear_bg = "#F5F0E6" if theme_name == "Light" else "rgba(255,255,255,0.04)"
    btn_clear_hover = "#E2E8F0" if theme_name == "Light" else "rgba(255,255,255,0.08)"
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700;9..144,800&display=swap');

        html, body, [class*="css"] {{
            font-family: "Manrope", system-ui, sans-serif;
            color: {t['text']};
        }}
        .display-serif {{
            font-family: "Fraunces", Georgia, serif !important;
            font-optical-sizing: auto;
            letter-spacing: -0.01em;
        }}
        body, .stApp, p, span, div, label {{
            color-scheme: {"light" if theme_name == "Light" else "dark"};
        }}
        :root {{
            --accent: {t['accent']};
            --accent-2: {t['accent_2']};
            --accent-3: {t['accent_3']};
            --text: {t['text']};
            --muted: {t['muted']};
            --soft-text: {t['soft_text']};
            --line: {t['line']};
            --panel-bg: {t['panel_bg']};
            --panel-solid: {t['panel_solid']};
            --input-bg: {t['input_bg']};
        }}

        .stApp {{ background: {t['app_bg']}; }}
        .modebar, .modebar-container {{
            display: none !important;
        }}

        /* Tarjeta contenedora del header + filtros */
        .st-key-hero_filters_card,
        .st-key-hero_filters_card [data-testid="stVerticalBlockBorderWrapper"] {{
            background: {t['panel_bg']} !important;
            border: 1px solid {select_border} !important;
            border-radius: 12px !important;
            padding: 0.85rem 1rem !important;
            box-shadow: {"0 2px 8px rgba(139,110,75,0.08)" if theme_name == "Light" else "0 10px 24px rgba(0,0,0,0.20), inset 0 0 0 1px rgba(255,255,255,0.04)"} !important;
            margin-top: -0.85rem !important;
            margin-bottom: 0.68rem !important;
        }}
        .st-key-hero_filters_card > div,
        .st-key-hero_filters_card [data-testid="stVerticalBlockBorderWrapper"] > div {{
            background: transparent !important;
        }}

        /* Contenedor principal para ajustar a sidebar fija */
        .stAppViewContainer {{
            background: {t['app_bg']} !important;
        }}

        .block-container,
        [data-testid="stAppViewMainArea"] .block-container,
        [data-testid="stAppViewContainer"] .block-container {{
            width: calc(100vw - {content_left}) !important;
            max-width: calc(100vw - {content_left}) !important;
            margin-left: {content_left} !important;
            margin-right: 0 !important;
            padding-left: 0.9rem !important;
            padding-right: 1.65rem !important;
            padding-top: 0 !important;
            padding-bottom: 0.9rem !important;
            box-sizing: border-box !important;
        }}

        @media (max-width: 1200px) {{
            .block-container,
            [data-testid="stAppViewMainArea"] .block-container,
            [data-testid="stAppViewContainer"] .block-container {{ 
                width: 100% !important;
                max-width: 100% !important;
                margin-left: 0 !important; 
                padding-left: 1.5rem !important;
                padding-right: 1.5rem !important;
            }}
            .fixed-sidebar {{ display: none !important; }}
        }}

        .fixed-sidebar {{
            position: fixed;
            top: {sidebar_gap};
            left: {sidebar_gap};
            bottom: {sidebar_gap};
            width: {sidebar_width};
            background: {sidebar_surface};
            border: 1px solid {sidebar_border};
            border-radius: 1rem;
            display: flex;
            flex-direction: column;
            padding: 1rem 0.85rem 0.85rem;
            box-sizing: border-box;
            z-index: 10000;
            overflow: hidden;
            box-shadow: {"0 18px 44px rgba(15,23,42,0.10)" if theme_name == "Light" else "0 18px 52px rgba(0,0,0,0.34)"};
        }}
        .nav-brand {{
            display: flex;
            align-items: center;
            gap: 0.72rem;
            padding: 0.15rem 0.2rem 1.05rem 0.2rem;
            margin-bottom: 0.75rem;
            border-bottom: 1px solid {sidebar_border};
        }}
        .nav-brand-logo {{
            width: 2.35rem; height: 2.35rem;
            background: {sidebar_accent_soft};
            border-radius: 0.55rem;
            display: flex; align-items: center; justify-content: center;
            color: {BT_DEEP}; font-weight: 800; font-size: 0.88rem;
            border: 1px solid {sidebar_accent_border};
            flex: 0 0 auto;
        }}
        .nav-brand-text {{
            font-size: 0.83rem;
            font-weight: 800;
            color: {sidebar_text};
            line-height: 1.15;
            letter-spacing: 0;
            min-width: 0;
        }}
        .nav-brand-text span {{
            display: block;
            font-size: 0.58rem;
            color: {sidebar_muted};
            font-weight: 800;
            letter-spacing: 0.13em;
            text-transform: uppercase;
            margin-top: 0.22rem;
        }}

        .sidebar-section-label {{
            font-size: 0.58rem;
            font-weight: 800;
            color: {sidebar_muted};
            text-transform: uppercase;
            letter-spacing: 0.16em;
            margin: 0.25rem 0 0.82rem 0.4rem;
            opacity: 0.82;
        }}

        .nav-list {{
            display: flex;
            flex-direction: column;
            gap: 0.24rem;
        }}
        .nav-item {{
            display: flex;
            align-items: center;
            gap: 0.72rem;
            min-height: 2.55rem;
            padding: 0 0.72rem;
            border-radius: 0.58rem;
            text-decoration: none !important;
            color: {sidebar_muted} !important;
            font-size: 0.82rem;
            font-weight: 750;
            line-height: 1;
            transition: background 0.16s ease, color 0.16s ease, transform 0.16s ease;
        }}
        .nav-item span:not(.nav-icon) {{
            color: inherit !important;
        }}
        .nav-item:hover {{
            background: {sidebar_input};
            color: {sidebar_text} !important;
            transform: translateX(1px);
        }}
        .nav-item.active {{
            background: {sidebar_accent} !important;
            color: #FFFFFF !important;
            font-weight: 850;
            box-shadow: {sidebar_accent_shadow};
        }}
        .nav-icon {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.15rem;
            height: 1.15rem;
            flex: 0 0 1.15rem;
            opacity: 0.86;
        }}
        .nav-icon svg {{
            width: 1.15rem;
            height: 1.15rem;
            stroke-width: 1.75;
        }}

        .nav-footer {{
            margin-top: auto;
            padding-top: 0.9rem;
            border-top: 1px solid {sidebar_border};
        }}
        .nav-footer-btns {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.62rem;
            padding: 0.12rem;
        }}
        .nav-btn {{
            height: 2.48rem;
            border-radius: 0.58rem;
            border: 1px solid {sidebar_border};
            background: {sidebar_input};
            display: flex; align-items: center; justify-content: center;
            color: {sidebar_muted} !important;
            text-decoration: none !important;
            font-size: 0.78rem;
            font-weight: 800;
            transition: all 0.16s ease;
        }}
        .nav-btn span, .nav-btn svg {{
            color: inherit !important;
            width: 1.05rem;
            height: 1.05rem;
        }}
        .nav-btn:hover {{
            border-color: {sidebar_accent_border};
            background: {sidebar_accent_soft};
            color: {BT_DEEP} !important;
        }}

        .topbar-title {{
            color: {t['text']};
            font-family: "Fraunces", Georgia, serif;
            font-optical-sizing: auto;
            font-weight: 600;
            letter-spacing: -0.018em;
            line-height: 1.05;
        }}
        .topbar-sub {{
            color: {t['muted']};
            font-size: 0.82rem;
            line-height: 1.4;
        }}
        .topbar-sub strong {{
            color: {t['text']};
            font-weight: 700;
        }}

        .pill-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin: 0.42rem 0 0.08rem;
        }}
        .pill {{
            background: {t['input_bg']};
            border: 1px solid {t['line']};
            border-radius: 999px;
            padding: 0.32rem 0.7rem;
            color: {t['soft_text']};
            font-size: 0.78rem;
            font-weight: 600;
        }}

        .filters-title {{
            color: {select_muted};
            font-size: 0.68rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.65rem;
            opacity: 0.85;
        }}

        .card, .mini-card, .placeholder-card {{
            background: {t['panel_bg']};
            border: 1px solid {t['line']};
            box-shadow: {chrome_shadow};
        }}
        .card {{
            border-radius: 10px;
            padding: 1.1rem 1rem 1.2rem;
            height: auto;
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .card::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, {BT_DEEP} 0%, {BT_BLUE} 50%, {BT_TEAL} 100%);
            opacity: 0.95;
        }}
        .mini-card {{
            border-radius: 10px;
            padding: 0.7rem 0.85rem;
        }}
        /* Tarjeta-contenedor para cada st.plotly_chart (visualmente la del spec) */
        [data-testid="stPlotlyChart"] {{
            background: {t['panel_bg']} !important;
            border: 1px solid {t['line']} !important;
            border-radius: 10px !important;
            padding: 0.55rem 0.55rem 0.4rem !important;
            box-shadow: {chart_shadow} !important;
            height: 100%;
        }}
        .map-control-card {{
            background: {t['panel_bg']};
            border: 1px solid {t['line']};
            border-radius: 8px;
            padding: 1rem;
            min-height: 520px;
            box-shadow: {chrome_shadow};
        }}
        .map-panel {{
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
        }}
        .map-plot-title {{
            color: {t['text']};
            font-size: 1.02rem;
            font-weight: 850;
            line-height: 1.2;
            margin: 0 0 0.55rem 0.05rem;
        }}
        .map-panel-head {{
            border-bottom: 1px solid {t['line']};
            padding-bottom: 0.7rem;
            margin-bottom: 0.2rem;
        }}
        .map-control-title {{
            color: {t['text']};
            font-size: 0.95rem;
            font-weight: 850;
            line-height: 1.18;
            margin-bottom: 0.25rem;
        }}
        .map-control-sub {{
            color: {t['muted']};
            font-size: 0.78rem;
            line-height: 1.35;
            margin-bottom: 0;
        }}
        .map-field-label {{
            color: {t['muted']};
            font-size: 0.7rem;
            font-weight: 850;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }}
        .map-extreme-card {{
            border: 1px solid {t['line']};
            border-radius: 8px;
            padding: 0.85rem 0.95rem;
            margin-top: 0.72rem;
            background: {t['panel_solid']};
        }}
        .map-extreme-label {{
            color: {t['muted']};
            font-size: 0.68rem;
            font-weight: 850;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.32rem;
        }}
        .map-extreme-value {{
            color: {t['text']};
            font-size: 1.28rem;
            font-weight: 850;
            line-height: 1.05;
            margin-bottom: 0.28rem;
            white-space: nowrap;
        }}
        .map-extreme-name {{
            color: {t['soft_text']};
            font-size: 0.84rem;
            font-weight: 750;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .kpi-label, .mini-label {{
            color: {t['muted']};
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 0.45rem;
        }}
        .kpi-value {{
            color: {t['text']};
            font-family: "Fraunces", Georgia, serif;
            font-optical-sizing: auto;
            font-size: 2.15rem;
            font-weight: 700;
            letter-spacing: -0.015em;
            line-height: 1.0;
            overflow-wrap: anywhere;
        }}
        .kpi-value-sm {{
            color: {t['text']};
            font-family: "Fraunces", Georgia, serif;
            font-optical-sizing: auto;
            font-size: 1.45rem;
            font-weight: 600;
            letter-spacing: -0.01em;
            line-height: 1.15;
            overflow-wrap: anywhere;
        }}
        .mini-value {{
            color: {t['text']};
            font-family: "Fraunces", Georgia, serif;
            font-optical-sizing: auto;
            font-size: 1.55rem;
            font-weight: 700;
            letter-spacing: -0.012em;
            line-height: 1.05;
        }}
        .kpi-foot, .mini-foot {{
            color: {t['muted']};
            font-size: 0.8rem;
            line-height: 1.45;
            margin-top: 0.55rem;
        }}
        .kpi-delta {{
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            border-radius: 999px;
            padding: 0.2rem 0.55rem;
            font-size: 0.8rem;
            font-weight: 700;
        }}
        .kpi-delta.up {{ background: rgba(16,185,129,0.14); color: {t['positive']}; }}
        .kpi-delta.down {{ background: rgba(244,63,94,0.14); color: {t['negative']}; }}
        .kpi-delta.neutral {{ background: {t['input_bg']}; color: {t['muted']}; }}

        .section-gap {{ height: 0.35rem; }}
        .section-gap-lg {{ height: 0.7rem; }}
        .section-header {{
            margin: 0.3rem 0 0.35rem;
            padding-top: 0.05rem;
            border-top: 1px solid {t['line']};
            padding-top: 0.5rem;
        }}
        .section-header:first-of-type {{
            border-top: none;
            padding-top: 0.1rem;
        }}
        .section-header-title {{
            color: {t['text']};
            font-family: "Fraunces", Georgia, serif;
            font-optical-sizing: auto;
            font-size: 1.32rem;
            font-weight: 600;
            letter-spacing: -0.012em;
            line-height: 1.15;
        }}
        .section-header-sub {{
            color: {t['muted']};
            font-size: 0.85rem;
            margin-top: 0.22rem;
        }}

        .placeholder-card {{
            border-radius: 8px;
            padding: 1rem;
            color: {t['soft_text']};
            font-size: 0.9rem;
            line-height: 1.5;
        }}
        .placeholder-icon {{
            display: inline-flex;
            margin-right: 0.35rem;
            color: {t['accent']};
        }}

        .interpretation-block {{
            background: {t['panel_bg']};
            border: 1px solid {t['line']};
            border-left: 4px solid {BT_DEEP};
            border-radius: 10px;
            padding: 1.05rem 1.2rem 1.1rem;
            margin: 1rem 0 1.4rem;
            color: {t['soft_text']};
            line-height: 1.55;
            box-shadow: {chart_shadow};
        }}
        .interpretation-title {{
            color: {t['text']};
            font-family: "Fraunces", Georgia, serif;
            font-optical-sizing: auto;
            font-size: 1rem;
            font-weight: 600;
            letter-spacing: -0.005em;
            margin-bottom: 0.35rem;
        }}
        .interpretation-title::before {{
            content: "—";
            color: {BT_DEEP};
            font-weight: 700;
            margin-right: 0.45rem;
        }}
        .interpretation-text {{
            color: {t['soft_text']};
            font-size: 0.94rem;
        }}

        [data-testid="stSelectbox"] label {{
            color: {select_muted} !important;
            font-weight: 800 !important;
            font-size: 0.78rem !important;
        }}
        [data-baseweb="select"] > div {{
            background: {select_bg} !important;
            border: 1px solid {select_border} !important;
            border-radius: 8px !important;
            min-height: 44px !important;
            box-shadow: none !important;
            opacity: 1 !important;
        }}
        [data-baseweb="select"] div,
        [data-baseweb="select"] span,
        [data-baseweb="select"] input {{
            color: {select_text} !important;
            -webkit-text-fill-color: {select_text} !important;
            font-weight: 700 !important;
            opacity: 1 !important;
        }}
        [data-baseweb="select"][aria-disabled="true"] div,
        [data-baseweb="select"][aria-disabled="true"] span,
        [data-testid="stSelectbox"] [aria-disabled="true"],
        [data-testid="stSelectbox"] [disabled] {{
            color: {select_muted} !important;
            -webkit-text-fill-color: {select_muted} !important;
            opacity: 1 !important;
        }}
        [data-baseweb="select"] svg {{
            color: {select_muted} !important;
            fill: {select_muted} !important;
        }}

        /* Estilo para botón de limpiar filtros */
        div.stButton > button {{
            background: {btn_clear_bg} !important;
            border: 1px solid {select_border} !important;
            border-radius: 8px !important;
            color: {select_muted} !important;
            font-weight: 700 !important;
            font-size: 0.82rem !important;
            height: 44px !important;
            margin-top: 0 !important;
            transition: all 0.2s ease !important;
            width: 100% !important;
        }}
        div.stButton > button:hover {{
            border-color: {t['accent']} !important;
            color: {t['accent']} !important;
            background: {btn_clear_hover} !important;
            box-shadow: none !important;
        }}
        div.stButton > button:active, div.stButton > button:focus {{
            box-shadow: none !important;
            border-color: {t['accent']} !important;
            background: {btn_clear_hover} !important;
        }}
        [data-baseweb="popover"],
        [data-baseweb="menu"],
        ul[role="listbox"] {{
            background: {dropdown_bg} !important;
            color: {select_text} !important;
            border: 1px solid {select_border} !important;
            box-shadow: {chrome_shadow} !important;
        }}
        li[role="option"],
        [role="option"],
        [data-baseweb="list-item"] {{
            background: {dropdown_bg} !important;
            color: {select_text} !important;
        }}
        li[role="option"]:hover,
        li[role="option"][aria-selected="true"],
        [role="option"]:hover,
        [role="option"][aria-selected="true"],
        [data-baseweb="list-item"]:hover,
        [data-baseweb="list-item"][aria-selected="true"] {{
            background: {dropdown_hover} !important;
            color: {select_text} !important;
        }}
        /* Forzar color de texto en hijos para evitar herencia de colores oscuros */
        li[role="option"]:hover *,
        li[role="option"][aria-selected="true"] *,
        [role="option"]:hover *,
        [role="option"][aria-selected="true"] *,
        [data-baseweb="list-item"]:hover *,
        [data-baseweb="list-item"][aria-selected="true"] * {{
            color: {select_text} !important;
        }}

        /* Ocultar Chrome Nativo */
        [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
        [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"],
        .stAppDeployButton {{ display: none !important; }}

        /* ── Tab bar inferior — oculta en desktop ──────────────────────── */
        .mobile-tabbar {{ display: none; }}

        /* ── MOBILE ≤ 768px ─────────────────────────────────────────────── */
        @media (max-width: 768px) {{

            /* Contenido a ancho completo + espacio para tab bar */
            .block-container,
            [data-testid="stAppViewMainArea"] .block-container,
            [data-testid="stAppViewContainer"] .block-container {{
                width: 100% !important;
                max-width: 100% !important;
                margin-left: 0 !important;
                padding-left: 0.75rem !important;
                padding-right: 0.75rem !important;
                padding-top: 0.5rem !important;
                padding-bottom: 5rem !important;
            }}

            /* Sidebar fija — oculta */
            .fixed-sidebar {{ display: none !important; }}

            /* ── Tab bar fija en el fondo ─────────────────────────────── */
            .mobile-tabbar {{
                display: flex !important;
                position: fixed;
                bottom: 0; left: 0; right: 0;
                height: 56px;
                background: {t['panel_bg']};
                border-top: 1px solid {t['line']};
                z-index: 9999;
                padding-bottom: env(safe-area-inset-bottom);
                box-shadow: 0 -2px 12px rgba(0,0,0,0.08);
            }}
            .mobile-tab {{
                flex: 1;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 0.1rem;
                text-decoration: none !important;
                color: {t['muted']} !important;
                font-size: 0;
                font-weight: 700;
                letter-spacing: 0.02em;
                padding: 0.25rem 0.05rem 0.2rem;
                border-top: 2px solid transparent;
                transition: color 0.15s, border-color 0.15s;
                -webkit-tap-highlight-color: transparent;
            }}
            .mobile-tab span {{
                display: none;
            }}
            .mobile-tab svg {{
                width: 1.2rem; height: 1.2rem;
                stroke-width: 1.65;
                flex-shrink: 0;
            }}
            .mobile-tab.active {{
                color: {BT_DEEP} !important;
                border-top-color: {BT_DEEP};
            }}
            .mobile-tab.active svg {{
                stroke-width: 2.1;
            }}
            .mobile-tab.active span {{
                display: block;
                font-size: 0.55rem;
                color: {BT_DEEP} !important;
            }}
            .mobile-tab-extra {{
                flex: 0 0 40px;
            }}

            /* Columnas de Streamlit apiladas */
            [data-testid="column"] {{
                width: 100% !important;
                min-width: 100% !important;
                flex: none !important;
            }}

            /* Grids CSS dentro de HTML inyectado */
            div[style*="grid-template-columns:repeat(4,1fr)"] {{
                grid-template-columns: repeat(2, 1fr) !important;
            }}
            div[style*="grid-template-columns:repeat(2,1fr)"] {{
                grid-template-columns: 1fr !important;
            }}
            div[style*="grid-template-columns:1fr 1fr"] {{
                grid-template-columns: 1fr !important;
            }}
            div[style*="grid-template-columns:repeat(4, 1fr)"] {{
                grid-template-columns: repeat(2, 1fr) !important;
            }}

            /* Tipografía reducida */
            .kpi-value            {{ font-size: 1.65rem !important; }}
            .kpi-label            {{ font-size: 0.65rem !important; }}
            .section-header-title {{ font-size: 1.05rem !important; }}
            .topbar-title         {{ font-size: 1.25rem !important; }}
            .topbar-sub           {{ font-size: 0.78rem !important; }}
            .interpretation-text  {{ font-size: 0.86rem !important; }}

            /* Cards y paddings más compactos */
            .card                {{ padding: 0.85rem 0.75rem 0.9rem !important; }}
            .mini-card           {{ padding: 0.55rem 0.7rem !important; }}
            .interpretation-block{{ padding: 0.8rem 0.9rem !important; }}
            [data-testid="stPlotlyChart"] {{ padding: 0.3rem 0.25rem !important; }}

            /* Hero card sin margen negativo en mobile */
            .st-key-hero_filters_card,
            .st-key-hero_filters_card [data-testid="stVerticalBlockBorderWrapper"] {{
                margin-top: 0 !important;
            }}

            /* Mapas — panel de control va debajo del mapa */
            [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando indicadores...")
def cargar() -> pd.DataFrame:
    if not INDICADORES_PATH.exists():
        return pd.DataFrame()
    df = pd.read_parquet(INDICADORES_PATH)
    col_ano = next((c for c in df.columns if c.startswith("_a")), "año")
    df = df.rename(columns={col_ano: "ano", "MES": "mes", "año": "ano"})
    df["periodo"] = pd.to_datetime(
        df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2) + "-01"
    )
    return df.sort_values("periodo").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Logo SVG inline
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Base de gráficos Plotly
# ---------------------------------------------------------------------------
def fig_base(fig, title: str = "", subtitle: str = ""):
    t = ACTIVE_THEME
    full_title = title
    if subtitle:
        full_title = f"{title}<br><sup style='color:{t['muted']};font-weight:400'>{subtitle}</sup>"
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=t["chart_bg"],
        font=dict(color=t["text"], family="Manrope, sans-serif", size=12),
        title=dict(
            text=full_title,
            font=dict(color=t["text"], size=13, weight=600),
            x=0.0,
            xanchor="left",
            pad=dict(l=4),
        ),
        margin=dict(l=16, r=18, t=72 if full_title else 18, b=56),
        hoverlabel=dict(
            bgcolor=t["panel_solid"],
            bordercolor=t["line"],
            font=dict(color=t["text"], size=12),
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            linecolor=t["line"],
            tickfont=dict(color=t["soft_text"], size=11),
            title_font=dict(color=t["muted"], size=11),
            automargin=True,
        ),
        yaxis=dict(
            gridcolor=t["chart_grid"],
            gridwidth=1,
            zeroline=False,
            linecolor="rgba(0,0,0,0)",
            tickfont=dict(color=t["soft_text"], size=11),
            title_font=dict(color=t["muted"], size=11),
            automargin=True,
        ),
        legend=dict(
            orientation="h",
            y=-0.18,
            x=0,
            yanchor="top",
            xanchor="left",
            bgcolor="rgba(0,0,0,0)",
            title_text="",
            font=dict(color=t["soft_text"], size=11),
        ),
    )
    fig.update_traces(
        textfont=dict(color=t["text"], size=11),
        selector=dict(type="bar"),
    )
    fig.update_traces(
        textfont=dict(color=t["text"], size=12),
        insidetextfont=dict(color="#FFFFFF", size=12),
        outsidetextfont=dict(color=t["text"], size=12),
        selector=dict(type="pie"),
    )
    return fig


def fig_base_h(fig, title: str = "", subtitle: str = ""):
    """Base para gráficos horizontales (intercambia grid de ejes)."""
    fig = fig_base(fig, title, subtitle)
    fig.update_layout(
        margin=dict(l=28, r=28, t=72 if (title or subtitle) else 18, b=38),
        xaxis=dict(
            gridcolor=ACTIVE_THEME["chart_grid"],
            gridwidth=1,
            zeroline=False,
            linecolor="rgba(0,0,0,0)",
            tickfont=dict(color=ACTIVE_THEME["soft_text"], size=11),
            title_font=dict(color=ACTIVE_THEME["muted"], size=11),
            automargin=True,
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            linecolor=ACTIVE_THEME["line"],
            tickfont=dict(color=ACTIVE_THEME["soft_text"], size=11),
            title_font=dict(color=ACTIVE_THEME["muted"], size=11),
            automargin=True,
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# Formateo
# ---------------------------------------------------------------------------
def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def fmt_metric(value) -> str:
    if pd.isna(value):
        return "s/d"
    value = float(value)
    abs_v = abs(value)
    if abs_v >= 1_000_000:
        return f"{value / 1_000_000:.2f} M"
    if abs_v >= 1_000:
        return f"{value / 1_000:.1f} K"
    return f"{value:,.0f}"


def fmt_delta_html(cur, prev, mode: str = "abs", invert: bool = False) -> str:
    """Devuelve HTML del badge delta. mode='abs' o 'pct'."""
    t = ACTIVE_THEME
    if pd.isna(cur) or pd.isna(prev) or float(prev) == 0:
        return ""
    diff = float(cur) - float(prev)
    if mode == "pct":
        label = f"{diff:+.1f} pp"
    else:
        label = f"{fmt_metric(diff)}"
        label = ("+" if diff > 0 else "") + label
    css_class = "neutral" if diff == 0 else ("down" if (diff > 0) != invert else "up")
    arrow = "→" if diff == 0 else ("↑" if diff > 0 else "↓")
    return f"<span class='kpi-delta {css_class}'>{arrow} {label} vs periodo ant.</span>"


# ---------------------------------------------------------------------------
# Helpers de datos
# ---------------------------------------------------------------------------
def opciones(df, dim, col):
    if col not in df.columns:
        return []
    return df.loc[df["dimension"] == dim, col].dropna().astype(str).sort_values().unique().tolist()


def filtrar(df, dim, anos_sel, meses_sel, geo_level, geo_sel):
    base = df[
        (df["dimension"] == dim) &
        (df["ano"].isin(anos_sel)) &
        (df["mes"].isin(meses_sel))
    ].copy()
    if (
        geo_level == "Departamento"
        and geo_sel != "Todos"
        and "DPTO_label" in base.columns
        and base["DPTO_label"].notna().any()
    ):
        base = base[base["DPTO_label"] == geo_sel]
    if (
        geo_level == "Ciudad"
        and geo_sel != "Todas"
        and "AREA_label" in base.columns
        and base["AREA_label"].notna().any()
    ):
        base = base[base["AREA_label"] == geo_sel]
    return base


def latest_row(df):
    return None if df.empty else df.sort_values("periodo").iloc[-1]


def prev_row(df):
    if df.empty or len(df) < 2:
        return None
    return df.sort_values("periodo").iloc[-2]


def active_context_df(df_nac, df_dep, df_city, geo_level, geo_sel):
    if geo_level == "Departamento" and geo_sel != "Todos" and not df_dep.empty:
        return df_dep
    if geo_level == "Ciudad" and geo_sel != "Todas" and not df_city.empty:
        return df_city
    return df_nac


def active_context_label(geo_level, geo_sel):
    if geo_level == "Departamento" and geo_sel != "Todos":
        return geo_sel
    if geo_level == "Ciudad" and geo_sel != "Todas":
        return geo_sel
    return "Nacional"


# ---------------------------------------------------------------------------
# Componentes UI
# ---------------------------------------------------------------------------
def render_kpi(col, label: str, value: str, foot: str = "", delta_html: str = ""):
    with col:
        st.markdown(
            f"""<div class='card' style='text-align:center'>
<div class='kpi-label' style='text-align:center'>{label}</div>
<div class='kpi-value' style='text-align:center'>{value}</div>
</div>""",
            unsafe_allow_html=True,
        )


def render_section(title: str, subtitle: str = ""):
    sub_html = f"<div class='section-header-sub'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""<div class='section-header'>
<div class='section-header-title'>{title}</div>
{sub_html}
</div>""",
        unsafe_allow_html=True,
    )


def placeholder(msg: str, icon: str = "🔧"):
    st.markdown(
        f"""<div class='placeholder-card'>
<span class='placeholder-icon'>{icon}</span>
{msg}
</div>""",
        unsafe_allow_html=True,
    )


def render_header(view_key: str, ultimo_txt: str, context_label: str):
    label = NAV_LABELS.get(view_key, view_key.capitalize())
    st.markdown(
        f"""<div style='padding-top: 0.2rem;'>
<div class='topbar-title' style="font-size: 1.5rem; margin-bottom: 0.2rem;">{label}</div>
<div class='topbar-sub'>
Mercado laboral colombiano · GEIH DANE &nbsp;|&nbsp; Corte: {ultimo_txt}
&nbsp;|&nbsp; Contexto: <strong>{context_label}</strong>
</div>
</div>""",
        unsafe_allow_html=True,
    )


def render_side_nav() -> str:
    """Nav lateral con links HTML puros en st.sidebar. Devuelve la clave de vista activa."""
    vista = st.query_params.get("view", "resumen")
    if vista not in VIEWS: vista = "resumen"

    current_theme = st.session_state.get("theme_mode", "Light")
    t = ACTIVE_THEME

    items_html = ""
    for key, label, icon_svg in NAV_ITEMS:
        active_cls = " active" if (vista == key) else ""
        items_html += (
            f"<a href='?view={key}&theme={current_theme}' class='nav-item{active_cls}' target='_self'>"
            f"<span class='nav-icon'>{icon_svg}</span>"
            f"<span>{label}</span>"
            f"</a>"
        )

    is_dark = current_theme == "Dark"
    new_theme = "Light" if is_dark else "Dark"
    theme_icon = ICON_SUN if is_dark else ICON_MOON
    theme_title = "Modo claro" if is_dark else "Modo oscuro"

    st.markdown(f"""<div class="fixed-sidebar">
<div class="nav-brand">
    <div class="nav-brand-logo">DM</div>
    <div class="nav-brand-text">
        Mercado Laboral
        <span>GEIH • DANE</span>
    </div>
</div>
<div class="sidebar-section-label">Navegación</div>
<div class="nav-list" style="flex: 1;">
    {items_html}
</div>
<div class="nav-footer">
    <div class="nav-footer-btns">
        <a href="{AUTHOR_LINKEDIN}" class="nav-btn" target="_blank" title="LinkedIn">{ICON_LINKEDIN}</a>
        <a href="{AUTHOR_GITHUB}" class="nav-btn" target="_blank" title="GitHub">{ICON_GITHUB}</a>
        <a href="?view={vista}&theme={new_theme}" class="nav-btn" target="_self" title="{theme_title}">{theme_icon}</a>
    </div>
</div>
</div>""", unsafe_allow_html=True)

    # Tab bar fija inferior para móvil
    SHORT_LABELS = {
        "resumen":       "Resumen",
        "poblacion":     "Población",
        "ocupados":      "Ocupados",
        "desocupados":   "Desocup.",
        "brechas":       "Brechas",
        "instrucciones": "Guía",
        "metodologia":   "Método",
    }
    tab_items = "".join(
        f"<a href='?view={key}&theme={current_theme}' class='mobile-tab{' active' if vista == key else ''}' target='_self'>"
        f"{icon_svg}<span>{SHORT_LABELS.get(key, label)}</span></a>"
        for key, label, icon_svg in NAV_ITEMS
    )
    st.markdown(
        f"<div class='mobile-tabbar'>{tab_items}"
        f"<a href='?view={vista}&theme={new_theme}' class='mobile-tab mobile-tab-extra' target='_self' title='{theme_title}'>{theme_icon}</a>"
        f"</div>",
        unsafe_allow_html=True,
    )

    return vista


def render_controls(df_all):
    def reset_filters_cb():
        st.session_state.sel_ano   = "Todos"
        st.session_state.sel_mes   = "Todos"
        st.session_state.sel_level = "Sin filtro"
        st.session_state.sel_geo   = "Todas"

    st.markdown(
        "<div class='filters-title'>Filtros</div>",
        unsafe_allow_html=True
    )
    year_col, mes_col, level_col, geo_col, clear_col = st.columns([0.7, 0.7, 0.9, 1.2, 0.55], gap="small")
    anos_disp  = sorted(df_all["ano"].dropna().unique().tolist())
    meses_disp = sorted(df_all["mes"].dropna().unique().tolist())

    with year_col:
        ano_ui = st.selectbox("Año", ["Todos"] + [str(a) for a in anos_disp], index=0, key="sel_ano")
    anos_sel = anos_disp if ano_ui == "Todos" else [int(ano_ui)]

    # Meses disponibles para el año seleccionado
    meses_en_ano = sorted(
        df_all[df_all["ano"].isin(anos_sel)]["mes"].dropna().unique().tolist()
    ) if ano_ui != "Todos" else meses_disp
    meses_opciones = [MESES_NOMBRE[m] for m in meses_en_ano if m in MESES_NOMBRE]

    with mes_col:
        mes_ui = st.selectbox("Mes", ["Todos"] + meses_opciones, index=0, key="sel_mes")
    meses_sel = meses_disp if mes_ui == "Todos" else [MESES_INVERSO[mes_ui]]

    with level_col:
        geo_level = st.selectbox("Nivel territorial", ["Sin filtro", "Departamento", "Ciudad"], index=0, key="sel_level")

    with geo_col:
        if geo_level == "Departamento":
            geo_sel = st.selectbox("Ubicación", ["Todos"] + opciones(df_all, "departamento", "DPTO_label"), index=0, key="sel_geo")
        elif geo_level == "Ciudad":
            geo_sel = st.selectbox("Ubicación", ["Todas"] + opciones(df_all, "ciudad", "AREA_label"), index=0, key="sel_geo")
        else:
            geo_sel = "Todas"
            st.selectbox("Ubicación", ["Sin filtro"], index=0, disabled=True, key="sel_geo_disabled")

    with clear_col:
        st.markdown("<div style='height:1.62rem'></div>", unsafe_allow_html=True)
        st.button("Limpiar", on_click=reset_filters_cb)

    return ano_ui, anos_sel, mes_ui, meses_sel, geo_level, geo_sel


def add_eventos_geih(fig, t):
    """Agrega línea vertical de cambio metodológico DANE Mar-2022."""
    x_evt = pd.Timestamp("2022-03-01")
    fig.add_shape(
        type="line", x0=x_evt, x1=x_evt, xref="x", yref="paper", y0=0, y1=1,
        line=dict(color=t["muted"], width=1.5, dash="dot"),
    )
    fig.add_annotation(
        x=x_evt, y=1, xref="x", yref="paper",
        text="Cambio GEIH 2022", showarrow=False,
        xanchor="left", yanchor="top",
        font=dict(size=10, color=t["muted"]),
        bgcolor="rgba(0,0,0,0)",
    )
    return fig


def render_filters_summary(ano_ui, mes_ui, geo_level, geo_sel):
    is_default = (ano_ui == "Todos" and mes_ui == "Todos" and geo_level == "Sin filtro" and geo_sel == "Todas")
    if is_default:
        return

    chips = "".join([
        f"<span class='pill'>📅 {ano_ui}</span>" if ano_ui != "Todos" else "",
        f"<span class='pill'>🗓 {mes_ui}</span>" if mes_ui != "Todos" else "",
        f"<span class='pill'>🗺 {geo_level}</span>" if geo_level != "Sin filtro" else "",
        f"<span class='pill'>📍 {geo_sel}</span>" if geo_sel not in ("Todas", "Todos") else "",
    ])
    if chips:
        st.markdown(f"<div class='pill-row'>{chips}</div>", unsafe_allow_html=True)


def available_map_indicators(df: pd.DataFrame) -> list[str]:
    return [
        col for col in MAP_INDICATORS
        if col in df.columns and df[col].notna().any()
    ]


def latest_departments_for_indicator(df_dep: pd.DataFrame, indicador: str) -> pd.DataFrame:
    if df_dep.empty or "DPTO_label" not in df_dep.columns or indicador not in df_dep.columns:
        return pd.DataFrame()
    return (
        df_dep.sort_values("periodo")
        .groupby("DPTO_label", as_index=False)[indicador]
        .last()
        .dropna(subset=[indicador])
    )


def render_map_module(df_dep: pd.DataFrame, default_indicator: str,
                      key_prefix: str, title_prefix: str,
                      indicators: list[str] | None = None,
                      geo_sel: str = "Todos"):
    if df_dep.empty or "DPTO_label" not in df_dep.columns:
        placeholder(
            "El mapa regional aparecerá al regenerar el parquet con la dimensión <code>departamento</code>.",
            "🗺️",
        )
        return

    options = indicators if indicators else available_map_indicators(df_dep)
    if not options:
        placeholder("No hay indicadores departamentales disponibles para el mapa.", "🗺️")
        return

    default_index = options.index(default_indicator) if default_indicator in options else 0
    map_col, control_col = st.columns([4.05, 1.35], gap="medium")

    with control_col:
        with st.container(border=True, height=555, key=f"{key_prefix}_map_panel"):
            st.markdown(
                "<div class='map-panel-head'>"
                "<div class='map-control-title'>Indicador del mapa</div>"
                "<div class='map-control-sub'>Variable territorial para colorear el mapa.</div>"
                "</div>"
                "<div class='map-field-label'>Indicador</div>",
                unsafe_allow_html=True,
            )
            indicador = st.selectbox(
                "Indicador",
                options,
                index=default_index,
                key=f"{key_prefix}_map_indicator",
                format_func=lambda col: MAP_INDICATORS[col]["select"],
                label_visibility="collapsed",
            )
            active_label = MAP_INDICATORS[indicador]["label"]
            st.markdown(
                f"<div class='map-control-sub' style='margin-top:0.35rem'>{active_label}</div>",
                unsafe_allow_html=True,
            )
            values = latest_departments_for_indicator(df_dep, indicador)
            if not values.empty:
                high = values.loc[values[indicador].idxmax()]
                low = values.loc[values[indicador].idxmin()]
                for label, item in [("Mayor", high), ("Menor", low)]:
                    st.markdown(
                        f"<div class='map-extreme-card'>"
                        f"<div class='map-extreme-label'>{label}</div>"
                        f"<div class='map-extreme-value'>{_format_map_value(indicador, item[indicador])}</div>"
                        f"<div class='map-extreme-name'>{item['DPTO_label']}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

    meta = MAP_INDICATORS[indicador]
    with map_col:
        plot_title = f"{title_prefix}: {meta['short']}" if title_prefix else meta['label']
        st.markdown(
            f"<div class='map-plot-title'>{plot_title}</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            plot_mapa_departamentos(df_dep, indicador, "", geo_sel=geo_sel),
            use_container_width=True,
            config={"displayModeBar": False, "responsive": True},
        )


# ---------------------------------------------------------------------------
# Pirámide poblacional
# ---------------------------------------------------------------------------
def plot_pyramid(df, value_col: str, title: str, subtitle: str = ""):
    need = {"P3271_label", "grupo_edad", value_col}
    if df.empty or not need.issubset(df.columns):
        placeholder("Datos insuficientes para la pirámide.<br>Regenera el parquet con dimensiones <code>sexo_edad</code>.", "🔺")
        return
    t = ACTIVE_THEME
    data = df.copy()
    if "periodo" in data.columns:
        data = data[data["periodo"] == data["periodo"].max()].copy()

    data[value_col] = pd.to_numeric(data[value_col], errors="coerce").fillna(0)
    data["grupo_edad"] = pd.Categorical(data["grupo_edad"], AGE_ORDER, ordered=True)
    data = (
        data.dropna(subset=["grupo_edad", "P3271_label"])
        .groupby(["grupo_edad", "P3271_label"], observed=True, as_index=False)[value_col]
        .sum()
    )
    pivot = (
        data.pivot_table(
            index="grupo_edad",
            columns="P3271_label",
            values=value_col,
            aggfunc="sum",
            observed=True,
            fill_value=0,
        )
        .reindex(AGE_ORDER, fill_value=0)
    )
    hombres = pivot["Hombre"] if "Hombre" in pivot.columns else pd.Series(0, index=pivot.index)
    mujeres = pivot["Mujer"] if "Mujer" in pivot.columns else pd.Series(0, index=pivot.index)
    total = float(hombres.sum() + mujeres.sum())
    if total <= 0:
        placeholder("No hay valores suficientes para construir la pirámide con los filtros actuales.", "🔺")
        return

    max_val = float(max(hombres.max(), mujeres.max()))
    magnitude = 10 ** np.floor(np.log10(max_val))
    tick_max = np.ceil(max_val / magnitude) * magnitude
    tick_step = tick_max / 2
    tickvals = [-tick_max, -tick_step, 0, tick_step, tick_max]
    ticktext = [fmt_metric(abs(v)) if v else "0" for v in tickvals]
    marker_line = "rgba(255,255,255,0.65)" if st.session_state.get("theme_mode") == "Light" else "rgba(2,6,23,0.55)"

    fig = go.Figure()
    fig.add_bar(
        y=pivot.index.astype(str),
        x=-hombres,
        name="Hombres",
        orientation="h",
        marker=dict(color=SEX_COLORS["Hombre"], line=dict(width=0.8, color=marker_line)),
        customdata=np.column_stack([hombres, hombres / total * 100]),
        hovertemplate="<b>%{y}</b><br>Hombres: %{customdata[0]:,.0f}<br>Participación: %{customdata[1]:.1f}%<extra></extra>",
    )
    fig.add_bar(
        y=pivot.index.astype(str),
        x=mujeres,
        name="Mujeres",
        orientation="h",
        marker=dict(color=SEX_COLORS["Mujer"], line=dict(width=0.8, color=marker_line)),
        customdata=np.column_stack([mujeres, mujeres / total * 100]),
        hovertemplate="<b>%{y}</b><br>Mujeres: %{customdata[0]:,.0f}<br>Participación: %{customdata[1]:.1f}%<extra></extra>",
    )
    fig = fig_base_h(fig, title, subtitle)
    fig.update_xaxes(
        range=[-tick_max * 1.15, tick_max * 1.15],
        tickvals=tickvals,
        ticktext=ticktext,
        title_text="",
        tickangle=0,
        showgrid=True,
        gridcolor=t["chart_grid"],
        zeroline=True,
        zerolinecolor=t["line"],
        zerolinewidth=1.4,
    )
    fig.update_yaxes(
        title_text="",
        categoryorder="array",
        categoryarray=AGE_ORDER,
        tickfont=dict(color=t["soft_text"], size=12),
    )
    fig.update_layout(
        barmode="relative",
        bargap=0.22,
        height=H_PYRAMID,
        margin=dict(l=24, r=28, t=112, b=48),
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=-0.12,
            yanchor="top",
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=t["soft_text"], size=12),
            traceorder="reversed",
        ),
        hovermode="y unified",
    )
    fig.add_annotation(
        x=-tick_max * 0.72,
        y=1.04,
        xref="x",
        yref="paper",
        text="Hombres",
        showarrow=False,
        font=dict(size=11, color=t["muted"]),
    )
    fig.add_annotation(
        x=tick_max * 0.72,
        y=1.04,
        xref="x",
        yref="paper",
        text="Mujeres",
        showarrow=False,
        font=dict(size=11, color=t["muted"]),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})


# ---------------------------------------------------------------------------
# Vista 1: Resumen ejecutivo
# ---------------------------------------------------------------------------
def view_resumen(df_context, df_dep, df_dep_mapa, df_city, df_city_mapa, context_label,
                 df_tendencia=None, ano_ui="Todos", mes_ui="Todos", geo_sel="Todas"):
    t = ACTIVE_THEME
    row = latest_row(df_context)
    prev = prev_row(df_context)
    if row is None:
        placeholder("No hay datos nacionales para los filtros seleccionados.", "📭")
        return

    # KPIs
    cols = st.columns(4, gap="small")
    render_kpi(
        cols[0], "Población total",
        fmt_metric(row.get("poblacion_total_exp", 0)),
        "Expandida · personas",
        fmt_delta_html(row.get("poblacion_total_exp"), prev.get("poblacion_total_exp") if prev is not None else None),
    )
    render_kpi(
        cols[1], "Fuerza de trabajo (PEA)",
        fmt_metric(row.get("PEA_exp", 0)),
        "Ocupados + Desocupados",
        fmt_delta_html(row.get("PEA_exp"), prev.get("PEA_exp") if prev is not None else None),
    )
    render_kpi(
        cols[2], "Ocupados",
        fmt_metric(row.get("ocupados_exp", 0)),
        "Último periodo disponible",
        fmt_delta_html(row.get("ocupados_exp"), prev.get("ocupados_exp") if prev is not None else None),
    )
    render_kpi(
        cols[3], "Tasa de desempleo (TD)",
        f"{row.get('TD', 0):.1f}%",
        "Desocupados / PEA × 100",
        fmt_delta_html(row.get("TD"), prev.get("TD") if prev is not None else None, mode="pct", invert=True),
    )

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)

    # Tendencia principal a ancho completo
    render_section("Tendencia de indicadores laborales", "Serie mensual — TD, TO y TGP ponderados con FEX_C18")

    # La serie de fondo usa todos los meses del año seleccionado (sin filtro de mes)
    _base_trend = df_tendencia if df_tendencia is not None and not df_tendencia.empty else df_context
    trend = _base_trend.sort_values("periodo")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    color_map = {"TD": BT_NAVY, "TO": BT_BLUE, "TGP": BT_MINT}

    for ind in ["TGP", "TO"]:
        fig.add_trace(go.Scatter(
            x=trend["periodo"], y=trend[ind],
            name=f"{ind} — {'Participación' if ind == 'TGP' else 'Ocupación'}",
            mode="lines",
            line=dict(color=color_map[ind], width=2.2, shape="spline"),
            hovertemplate=f"<b>{ind}</b>: %{{y:.1f}}%<br>%{{x|%b %Y}}<extra></extra>"
        ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=trend["periodo"], y=trend["TD"], name="TD — Desempleo",
        mode="lines",
        line=dict(color=color_map["TD"], width=3, shape="spline"),
        fill="tozeroy",
        fillcolor=hex_to_rgba(BT_NAVY, 0.08),
        hovertemplate="<b>TD</b>: %{y:.1f}%<br>%{x|%b %Y}<extra></extra>"
    ), secondary_y=True)

    # Marcador del mes seleccionado encima de la línea
    if mes_ui != "Todos":
        mes_num = MESES_INVERSO.get(mes_ui)
        trend_mes = trend[trend["mes"] == mes_num] if "mes" in trend.columns else pd.DataFrame()
        if not trend_mes.empty:
            for ind, secondary in [("TGP", False), ("TO", False), ("TD", True)]:
                fig.add_trace(go.Scatter(
                    x=trend_mes["periodo"], y=trend_mes[ind],
                    name=f"{mes_ui} seleccionado",
                    mode="markers+text",
                    marker=dict(
                        color=color_map[ind], size=13, symbol="circle",
                        line=dict(width=2.5, color=t["panel_bg"])
                    ),
                    text=[f"<b>{v:.1f}%</b>" for v in trend_mes[ind]],
                    textposition="top center",
                    textfont=dict(size=10, color=color_map[ind]),
                    showlegend=(ind == "TD"),
                    legendgroup="mes_sel",
                    hovertemplate=f"<b>{ind} — {mes_ui}</b>: %{{y:.1f}}%<br>%{{x|%b %Y}}<extra></extra>",
                ), secondary_y=secondary)

    subtitulo_trend = f"Doble eje · contexto: {context_label}"
    if ano_ui != "Todos":
        subtitulo_trend += f" · {ano_ui}"
    if mes_ui != "Todos":
        subtitulo_trend += f" · {mes_ui} destacado"

    fig = fig_base(fig, "Dinámica laboral mensual", subtitulo_trend)
    fig.update_yaxes(title_text="TO / TGP (%)", ticksuffix="%", secondary_y=False)
    fig.update_yaxes(
        title_text="TD (%)", ticksuffix="%", secondary_y=True, showgrid=False,
        tickfont=dict(color=t["soft_text"], size=11),
        title_font=dict(color=t["muted"], size=11),
    )
    # Eje X: ticks mensuales cuando hay un año específico, trimestrales para la serie completa
    dtick_x = "M1" if ano_ui != "Todos" else "M3"
    fig.update_xaxes(tickformat="%b %Y", dtick=dtick_x)
    fig.update_layout(height=H_SINGLE)
    fig = add_eventos_geih(fig, t)
    st.plotly_chart(fig, use_container_width=True)

    # Comparación interanual — solo cuando hay más de un año seleccionado
    if ano_ui == "Todos" and "ano" in _base_trend.columns and _base_trend["ano"].nunique() > 1:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        render_section(
            "Comparación interanual · TD",
            "Tasa de desempleo mes a mes — cada línea es un año",
        )
        _tr_ia = _base_trend.copy()
        _tr_ia["mes_nombre"] = pd.to_datetime(_tr_ia["periodo"]).dt.month.map(MESES_NOMBRE)
        _tr_ia["año"] = _tr_ia["ano"].astype(str)
        _tr_ia = _tr_ia.sort_values(["ano", "mes"])

        year_colors = dict(zip(
            sorted(_tr_ia["año"].unique()),
            BLUE_TEAL_DISCRETE[:_tr_ia["año"].nunique()]
        ))
        fig_ia = px.line(
            _tr_ia, x="mes_nombre", y="TD", color="año",
            color_discrete_map=year_colors,
            line_shape="spline",
            category_orders={"mes_nombre": list(MESES_NOMBRE.values())},
            labels={"TD": "TD (%)", "mes_nombre": "", "año": "Año"},
        )
        fig_ia = fig_base(fig_ia, "TD por mes — comparativo anual", "Permite ver estacionalidad y tendencia estructural")
        fig_ia.update_traces(line=dict(width=2.5),
                             hovertemplate="<b>%{fullData.name}</b><br>TD: %{y:.1f}%<br>%{x}<extra></extra>")
        fig_ia.update_yaxes(ticksuffix="%")
        fig_ia.update_layout(height=H_PAIRED)
        st.plotly_chart(fig_ia, use_container_width=True)

    # Comparativo departamental: prioridad de política pública = mayor desempleo
    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)

    if not df_dep.empty and "DPTO_label" in df_dep.columns:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        render_section("Mapa regional", "Cambia el indicador para ver la geografía del mercado")
        render_map_module(df_dep_mapa, "TD", "resumen", "", geo_sel=geo_sel)

    # Mapa de ciudades (independiente del mapa departamental)
    if not df_city_mapa.empty and "AREA_label" in df_city_mapa.columns:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        render_section("Mapa de ciudades", "Indicadores por área metropolitana · último periodo")
        city_map_col, city_ctrl_col = st.columns([4.05, 1.35], gap="medium")
        with city_ctrl_col:
            with st.container(border=True, height=530, key="resumen_city_panel"):
                st.markdown(
                    "<div class='map-panel-head'>"
                    "<div class='map-control-title'>Indicador del mapa</div>"
                    "<div class='map-control-sub'>Variable por área metropolitana.</div>"
                    "</div>"
                    "<div class='map-field-label'>Indicador</div>",
                    unsafe_allow_html=True,
                )
                city_ind = st.selectbox(
                    "Indicador ciudad",
                    options=["TD", "TO", "tasa_informalidad"],
                    format_func=lambda c: MAP_INDICATORS[c]["select"],
                    key="resumen_city_indicator",
                    label_visibility="collapsed",
                )
                city_vals = (
                    df_city_mapa.sort_values("periodo")
                    .groupby("AREA_label", as_index=False)[city_ind]
                    .last()
                    .dropna(subset=[city_ind])
                )
                if not city_vals.empty:
                    for lbl, item in [
                        ("Mayor", city_vals.loc[city_vals[city_ind].idxmax()]),
                        ("Menor", city_vals.loc[city_vals[city_ind].idxmin()]),
                    ]:
                        st.markdown(
                            f"<div class='map-extreme-card'>"
                            f"<div class='map-extreme-label'>{lbl}</div>"
                            f"<div class='map-extreme-value'>{_format_map_value(city_ind, item[city_ind])}</div>"
                            f"<div class='map-extreme-name'>{item['AREA_label']}</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
        with city_map_col:
            st.plotly_chart(
                plot_mapa_ciudades(df_city_mapa, city_ind, geo_sel=geo_sel),
                use_container_width=True,
                config={"displayModeBar": False},
            )

    render_interpretation(
        "La tendencia muestra una <b>TD</b> que oscila alrededor del 10% nacional, "
        "mientras la <b>TO</b> y la <b>TGP</b> avanzan con menor volatilidad por encima del 55%. "
        "Territorialmente, los departamentos del Pacífico y la frontera oriental concentran "
        "la mayor presión laboral; las regiones andinas centrales sostienen la ocupación.",
        title="Lectura del periodo",
    )



# ---------------------------------------------------------------------------
# Vista 2: Caracterización poblacional
# ---------------------------------------------------------------------------
def view_caracterizacion(df_sx_age, df_edu, df_civil, df_sexo, df_clase, geo_level, geo_sel, df_dep_mapa=None):
    t = ACTIVE_THEME

    # KPIs de caracterización
    kpi_cols = st.columns(3, gap="small")

    # KPI 1: Población total — usar df_sexo (incluye todos los rangos de edad,
    # no solo PET). df_sx_age excluye menores de 15 porque grupo_edad queda null.
    pop_total = None
    pop_total_prev = None
    if not df_sexo.empty and "poblacion_total_exp" in df_sexo.columns:
        pop_by_period = (
            df_sexo.groupby("periodo")["poblacion_total_exp"].sum().sort_index()
        )
        if len(pop_by_period) >= 1:
            pop_total = pop_by_period.iloc[-1]
        if len(pop_by_period) >= 2:
            pop_total_prev = pop_by_period.iloc[-2]

    render_kpi(
        kpi_cols[0], "Población total",
        fmt_metric(pop_total) if pop_total is not None else "—",
        "Expandida · FEX_C18",
        fmt_delta_html(pop_total, pop_total_prev) if pop_total is not None else "",
    )

    # KPI 2: % Mujeres — último y penúltimo periodo
    pct_mujer = pct_mujer_prev = None
    if not df_sexo.empty and "P3271_label" in df_sexo.columns:
        periodos_sexo = sorted(df_sexo["periodo"].unique())
        for i, p in enumerate([periodos_sexo[-1], periodos_sexo[-2] if len(periodos_sexo) >= 2 else None]):
            if p is None:
                continue
            s = df_sexo[df_sexo["periodo"] == p]
            tot = s["poblacion_total_exp"].sum()
            mujer = s[s["P3271_label"] == "Mujer"]["poblacion_total_exp"].sum()
            val = mujer / tot * 100 if tot > 0 else None
            if i == 0:
                pct_mujer = val
            else:
                pct_mujer_prev = val

    render_kpi(
        kpi_cols[1], "Mujeres",
        f"{pct_mujer:.1f}%" if pct_mujer is not None else "—",
        "Del total de población",
        fmt_delta_html(pct_mujer, pct_mujer_prev, mode="pct") if pct_mujer is not None else "",
    )

    # KPI 3: % Urbana — último y penúltimo periodo
    pct_urbana = pct_urbana_prev = None
    if not df_clase.empty and "CLASE_label" in df_clase.columns:
        periodos_clase = sorted(df_clase["periodo"].unique())
        for i, p in enumerate([periodos_clase[-1], periodos_clase[-2] if len(periodos_clase) >= 2 else None]):
            if p is None:
                continue
            c = df_clase[df_clase["periodo"] == p]
            tot = c["poblacion_total_exp"].sum()
            urb = c[c["CLASE_label"] == "Urbano"]["poblacion_total_exp"].sum()
            val = urb / tot * 100 if tot > 0 else None
            if i == 0:
                pct_urbana = val
            else:
                pct_urbana_prev = val

    render_kpi(
        kpi_cols[2], "Población urbana",
        f"{pct_urbana:.1f}%" if pct_urbana is not None else "—",
        "Cabecera municipal · CLASE",
        fmt_delta_html(pct_urbana, pct_urbana_prev, mode="pct") if pct_urbana is not None else "",
    )

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    render_section("Estructura poblacional", "Distribución por sexo y grupos de edad")
    left, right = st.columns(2, gap="large")
    with left:
        plot_pyramid(df_sx_age, "poblacion_total_exp", "Pirámide poblacional", "Personas expandidas · FEX_C18")
    with right:
        if df_edu.empty or "P3042_label" not in df_edu.columns:
            placeholder("Educación no disponible en el parquet actual.<br>Agregar <code>P3042</code> al ETL.", "🎓")
        else:
            edu = (
                df_edu.groupby("P3042_label", as_index=False)["poblacion_total_exp"]
                .mean()
                .sort_values("poblacion_total_exp")
            )
            edu["txt"] = edu["poblacion_total_exp"].map(fmt_metric)
            fig = px.bar(
                edu, x="poblacion_total_exp", y="P3042_label", orientation="h",
                text="txt",
                color_discrete_sequence=[BT_BLUE],
                labels={"poblacion_total_exp": "Personas", "P3042_label": ""},
            )
            fig = fig_base_h(fig, "Población por nivel educativo", "Promedio del periodo · nivel de estudio")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_xaxes(title_text="Personas")
            fig.update_yaxes(title_text="")
            fig.update_layout(height=H_PYRAMID, margin=dict(r=90))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    render_section("Composición por estado civil, sexo y clase", "Distribuciones relativas · promedio del periodo")
    # Tortas: sexo y clase en la misma fila
    b_col, c_col = st.columns(2, gap="large")
    with b_col:
        if df_sexo.empty or "P3271_label" not in df_sexo.columns:
            placeholder("Datos de sexo no disponibles.", "⚧")
        else:
            sexo = df_sexo.groupby("P3271_label", as_index=False)["poblacion_total_exp"].mean()
            fig = px.pie(
                sexo,
                names="P3271_label",
                values="poblacion_total_exp",
                hole=0.58,
                color="P3271_label",
                color_discrete_map=SEX_COLORS,
            )
            fig = fig_base(fig, "Distribución por sexo", "P3271 · promedio del periodo")
            fig.update_traces(
                textinfo="percent+label",
                textfont=dict(color=t["text"], size=12),
                hovertemplate="<b>%{label}</b><br>%{value:,.0f} personas<br>%{percent}<extra></extra>",
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with c_col:
        if df_clase.empty or "CLASE_label" not in df_clase.columns:
            placeholder("Clase urbano/rural sin datos.<br>Agregar <code>CLASE</code> al ETL.", "🏙️")
        else:
            clase = df_clase.groupby("CLASE_label", as_index=False)["poblacion_total_exp"].mean()
            fig = px.pie(
                clase,
                names="CLASE_label",
                values="poblacion_total_exp",
                hole=0.58,
                color_discrete_sequence=[BT_NAVY, BT_PALE],
            )
            fig = fig_base(fig, "Urbano vs. Rural", "CLASE · promedio del periodo")
            fig.update_traces(
                textinfo="percent+label",
                textfont=dict(color=t["text"], size=12),
                hovertemplate="<b>%{label}</b><br>%{value:,.0f} personas<br>%{percent}<extra></extra>",
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)

    # Barras: estado civil sola abajo para mayor legibilidad
    if df_civil.empty or "P6070_label" not in df_civil.columns:
        placeholder("Estado civil sin datos.<br>Agregar <code>P6070</code> al ETL.", "💍")
    else:
        civil = df_civil.groupby("P6070_label", as_index=False)["poblacion_total_exp"].mean()
        civil["txt"] = civil["poblacion_total_exp"].map(fmt_metric)
        fig = px.bar(
            civil.sort_values("poblacion_total_exp"),
            x="poblacion_total_exp", y="P6070_label", orientation="h",
            text="txt",
            color_discrete_sequence=[BT_TEAL],
            labels={"poblacion_total_exp": "Personas", "P6070_label": ""},
        )
        fig = fig_base_h(fig, "Estado civil", "Promedio del periodo · estado conyugal")
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        fig.update_xaxes(title_text="Personas")
        fig.update_yaxes(title_text="")
        fig.update_layout(height=max(340, len(civil) * 38 + 140), margin=dict(r=90))
        st.plotly_chart(fig, use_container_width=True)

    if df_dep_mapa is not None and not df_dep_mapa.empty and "DPTO_label" in df_dep_mapa.columns:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        render_section("Distribución poblacional por departamento", "Población total expandida · último periodo")
        st.plotly_chart(
            plot_mapa_departamentos(df_dep_mapa, "poblacion_total_exp", "", geo_sel=geo_sel),
            use_container_width=True,
            config={"displayModeBar": False, "responsive": True},
        )

    render_interpretation(
        "La pirámide poblacional revela un proceso de transición demográfica: la base se estrecha "
        "mientras los grupos en edad de trabajar (15-64) concentran el mayor volumen. "
        "En términos de capital humano, el nivel educativo predominante guía la oferta laboral; "
        "una distribución urbana superior al 75% confirma la concentración del mercado en cabeceras.",
        title="Lectura demográfica",
    )


# ---------------------------------------------------------------------------
# Vista 3: Mercado de ocupados
# ---------------------------------------------------------------------------
def view_ocupados(df_context, df_sector, df_sx_age, df_pos, df_city, df_edu, df_dep_mapa, context_label, geo_level,
                  df_tendencia=None, ano_ui="Todos", mes_ui="Todos"):
    t = ACTIVE_THEME
    row = latest_row(df_context)
    prev = prev_row(df_context)

    if row is not None:
        cols = st.columns(4, gap="small")
        render_kpi(
            cols[0], "Total ocupados",
            fmt_metric(row.get("ocupados_exp", 0)),
            "Expandido · personas",
            fmt_delta_html(row.get("ocupados_exp"), prev.get("ocupados_exp") if prev is not None else None),
        )
        render_kpi(
            cols[1], "Tasa de ocupación (TO)",
            f"{row.get('TO', 0):.1f}%",
            "Ocupados / PET × 100",
            fmt_delta_html(row.get("TO"), prev.get("TO") if prev is not None else None, mode="pct"),
        )
        # KPI de Informalidad (Si existe en el dataset)
        tasa_inf = row.get("tasa_informalidad")
        render_kpi(
            cols[2], "Tasa Informalidad",
            f"{tasa_inf:.1f}%" if pd.notna(tasa_inf) and tasa_inf > 0 else "s/d",
            "Metodología DANE 2022",
            fmt_delta_html(tasa_inf, prev.get("tasa_informalidad") if prev is not None else None, mode="pct", invert=True),
        )
        render_kpi(
            cols[3], "Ingreso mediano",
            f"${fmt_metric(row.get('ingreso_mediano', 0))}" if row.get("ingreso_mediano") else "s/d",
            "COP corrientes · P6500",
            fmt_delta_html(row.get("ingreso_mediano"), prev.get("ingreso_mediano") if prev is not None else None),
        )

    # Gráfico de tendencia: TO e informalidad
    _base_oc = df_tendencia if df_tendencia is not None and not df_tendencia.empty else df_context
    trend_oc = _base_oc.sort_values("periodo")
    cols_needed = {"TO", "tasa_informalidad"}
    if not trend_oc.empty and cols_needed.issubset(trend_oc.columns):
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        subtitulo_oc = f"Evolución mensual · {context_label}"
        if ano_ui != "Todos":
            subtitulo_oc += f" · {ano_ui}"
        if mes_ui != "Todos":
            subtitulo_oc += f" · {mes_ui} destacado"
        render_section("Tendencia de ocupación e informalidad", subtitulo_oc)
        color_map_oc = {"TO": BT_BLUE, "tasa_informalidad": BT_TEAL}
        fig_oc = make_subplots(specs=[[{"secondary_y": True}]])
        fig_oc.add_trace(go.Scatter(
            x=trend_oc["periodo"], y=trend_oc["TO"],
            name="Tasa de ocupación (TO)",
            mode="lines",
            line=dict(color=BT_BLUE, width=2.5, shape="spline"),
            hovertemplate="<b>TO</b>: %{y:.1f}%<br>%{x|%b %Y}<extra></extra>",
        ), secondary_y=False)
        fig_oc.add_trace(go.Scatter(
            x=trend_oc["periodo"], y=trend_oc["tasa_informalidad"],
            name="Tasa de informalidad",
            mode="lines",
            line=dict(color=BT_TEAL, width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor=hex_to_rgba(BT_TEAL, 0.08),
            hovertemplate="<b>Informalidad</b>: %{y:.1f}%<br>%{x|%b %Y}<extra></extra>",
        ), secondary_y=True)
        # Marcador del mes seleccionado
        if mes_ui != "Todos":
            mes_num = MESES_INVERSO.get(mes_ui)
            trend_mes_oc = trend_oc[trend_oc["mes"] == mes_num] if "mes" in trend_oc.columns else pd.DataFrame()
            if not trend_mes_oc.empty:
                for ind, nombre, sec in [("TO", "TO", False), ("tasa_informalidad", "Informalidad", True)]:
                    if ind in trend_mes_oc.columns:
                        fig_oc.add_trace(go.Scatter(
                            x=trend_mes_oc["periodo"], y=trend_mes_oc[ind],
                            name=f"{mes_ui} seleccionado",
                            mode="markers+text",
                            marker=dict(
                                color=color_map_oc[ind], size=13, symbol="circle",
                                line=dict(width=2.5, color=t["panel_bg"]),
                            ),
                            text=[f"<b>{v:.1f}%</b>" for v in trend_mes_oc[ind]],
                            textposition="top center",
                            textfont=dict(size=10, color=color_map_oc[ind]),
                            showlegend=(ind == "TO"),
                            legendgroup="mes_sel_oc",
                            hovertemplate=f"<b>{nombre} — {mes_ui}</b>: %{{y:.1f}}%<br>%{{x|%b %Y}}<extra></extra>",
                        ), secondary_y=sec)
        dtick_oc = "M1" if ano_ui != "Todos" else "M3"
        fig_oc = fig_base(fig_oc, "Dinámica de ocupación e informalidad", subtitulo_oc)
        fig_oc.update_yaxes(title_text="TO (%)", ticksuffix="%", secondary_y=False)
        fig_oc.update_yaxes(
            title_text="Informalidad (%)", ticksuffix="%", secondary_y=True,
            showgrid=False,
            tickfont=dict(color=t["soft_text"], size=11),
            title_font=dict(color=t["muted"], size=11),
        )
        fig_oc.update_xaxes(tickformat="%b %Y", dtick=dtick_oc)
        fig_oc.update_layout(height=H_SINGLE)
        st.plotly_chart(fig_oc, use_container_width=True)

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    render_section("Estructura sectorial y pirámide", "Composición del empleo por rama y demografía")
    left, right = st.columns(2, gap="large")
    with left:
        if df_sector.empty or "RAMA2D_R4_label" not in df_sector.columns:
            placeholder("Datos sectoriales no disponibles.<br>Verificar dimensión <code>sector</code> en el parquet.", "🏭")
        else:
            sec = (
                df_sector.groupby("RAMA2D_R4_label", as_index=False)["ocupados_exp"]
                .mean()
                .sort_values("ocupados_exp")
                .tail(14)
            )
            sec["txt"] = sec["ocupados_exp"].map(fmt_metric)
            fig = px.bar(
                sec, x="ocupados_exp", y="RAMA2D_R4_label", orientation="h",
                text="txt",
                color_discrete_sequence=[BT_BLUE],
                labels={"ocupados_exp": "Personas ocupadas", "RAMA2D_R4_label": ""},
            )
            fig = fig_base_h(fig, "Ocupados por rama de actividad", "CIIU Rev.4 · promedio del periodo")
            fig.update_traces(
                textposition="outside", cliponaxis=False, marker_line_width=0,
                hovertemplate="<b>%{y}</b><br>%{x:,.0f} ocupados<extra></extra>",
            )
            fig.update_xaxes(title_text="Personas ocupadas")
            fig.update_yaxes(title_text="")
            fig.update_layout(height=H_PAIRED, margin=dict(r=90))
            st.plotly_chart(fig, use_container_width=True)
    with right:
        plot_pyramid(df_sx_age, "ocupados_exp", "Pirámide de ocupados", "Por sexo y grupo de edad · P3271 × P6040")

    # Tarea 3.c: Sección de Informalidad Laboral
    if not df_sector.empty and {"RAMA2D_R4_label", "tasa_informalidad"}.issubset(df_sector.columns):
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        render_section("Informalidad laboral", "P6090: ocupados sin afiliación contributiva")

        # Top 10 ramas con mayor informalidad
        inf_sec = (
            df_sector.groupby("RAMA2D_R4_label", as_index=False)["tasa_informalidad"]
            .mean()
            .sort_values("tasa_informalidad")
            .tail(10)
        )
        inf_sec["txt"] = inf_sec["tasa_informalidad"].map(lambda x: f"{x:.1f}%")

        fig = px.bar(
            inf_sec, x="tasa_informalidad", y="RAMA2D_R4_label", orientation="h",
            text="txt",
            color_discrete_sequence=[BT_TEAL],
            labels={"tasa_informalidad": "Tasa de informalidad (%)", "RAMA2D_R4_label": ""},
        )
        fig = fig_base_h(fig, "Tasa de informalidad por rama", "Top 10 · promedio del periodo")
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        fig.update_xaxes(title_text="Tasa de informalidad (%)", ticksuffix="%")
        fig.update_yaxes(title_text="")
        fig.update_layout(height=H_SINGLE, margin=dict(r=90))
        st.plotly_chart(fig, use_container_width=True)

        inf_text = "La informalidad laboral en Colombia es estructural: oscila entre 55% y 60% a nivel nacional. La concentración crítica está en agricultura, ganadería y comercio menor, donde la falta de afiliación al sistema contributivo es la norma. Cualquier política de formalización debe atacar primero estos sectores."
        render_interpretation(inf_text, title="Lectura de informalidad")

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    render_section("Posición ocupacional y distribución geográfica")
    left, right = st.columns(2, gap="large")
    with left:
        if df_pos.empty or "P6430_label" not in df_pos.columns:
            placeholder("Posición ocupacional sin datos.<br>Agregar labels de <code>P6430</code> al ETL.", "🪪")
        else:
            pos = (
                df_pos.groupby("P6430_label", as_index=False)["ocupados_exp"]
                .mean()
                .sort_values("ocupados_exp")
            )
            # Tarea 1: Truncar labels largos
            pos["label_display"] = pos["P6430_label"].apply(lambda x: (x[:38] + '...') if len(x) > 38 else x)
            pos["txt"] = pos["ocupados_exp"].map(fmt_metric)
            fig = px.bar(
                pos, x="ocupados_exp", y="label_display", orientation="h",
                text="txt",
                custom_data=["P6430_label"],
                color_discrete_sequence=[BT_TEAL],
                labels={"ocupados_exp": "Personas ocupadas", "label_display": ""},
            )
            fig = fig_base_h(fig, "Posición ocupacional", "Promedio del periodo")
            fig.update_traces(
                textposition="outside", cliponaxis=False, marker_line_width=0,
                hovertemplate="<b>%{customdata[0]}</b><br>%{x:,.0f} ocupados<extra></extra>"
            )
            fig.update_xaxes(title_text="Personas ocupadas")
            fig.update_yaxes(title_text="", tickfont=dict(size=11))
            fig.update_layout(
                margin=dict(l=200, r=90, t=74, b=52),
                height=H_PAIRED,
            )
            st.plotly_chart(fig, use_container_width=True)
    with right:
        if df_city.empty or "AREA_label" not in df_city.columns:
            placeholder("Distribución por ciudad sin datos.", "🏙️")
        else:
            city = (
                df_city.groupby("AREA_label", as_index=False)["ocupados_exp"]
                .mean()
                .sort_values("ocupados_exp")
                .tail(12)
            )
            city["txt"] = city["ocupados_exp"].map(fmt_metric)
            fig = px.bar(
                city, x="ocupados_exp", y="AREA_label", orientation="h",
                text="txt",
                color="ocupados_exp",
                color_continuous_scale=BLUE_TEAL_SCALE,
                labels={"ocupados_exp": "Personas ocupadas", "AREA_label": ""},
            )
            fig = fig_base_h(fig, "Ocupados por ciudad", "Top 12 áreas metropolitanas")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_coloraxes(showscale=False)
            fig.update_xaxes(title_text="Personas ocupadas")
            fig.update_yaxes(title_text="")
            fig.update_layout(height=H_PAIRED, margin=dict(r=90))
            st.plotly_chart(fig, use_container_width=True)

    if not df_edu.empty and "P3042_label" in df_edu.columns:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        render_section("Educación y salarios", "Distribución de ocupados e ingreso mediano por nivel educativo")
        edu = df_edu.groupby("P3042_label", as_index=False)[["ocupados_exp", "ingreso_mediano"]].mean()
        left, right = st.columns(2, gap="large")
        with left:
            d = edu.sort_values("ocupados_exp")
            d["txt"] = d["ocupados_exp"].map(fmt_metric)
            fig = px.bar(d, x="ocupados_exp", y="P3042_label", orientation="h", text="txt",
                         color_discrete_sequence=[BT_BLUE],
                         labels={"ocupados_exp": "Personas ocupadas", "P3042_label": ""})
            fig = fig_base_h(fig, "Ocupados por nivel educativo", "Promedio del periodo · nivel de estudio")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_xaxes(title_text="Personas ocupadas")
            fig.update_yaxes(title_text="")
            fig.update_layout(height=H_PAIRED, margin=dict(r=90))
            st.plotly_chart(fig, use_container_width=True)
        with right:
            d2 = edu.sort_values("ingreso_mediano")
            d2["txt"] = d2["ingreso_mediano"].map(lambda x: f"${fmt_metric(x)}")
            fig = px.bar(d2, x="ingreso_mediano", y="P3042_label", orientation="h", text="txt",
                         color_discrete_sequence=[BT_TEAL],
                         labels={"ingreso_mediano": "Ingreso mediano (COP)", "P3042_label": ""})
            fig = fig_base_h(fig, "Ingreso mediano por nivel educativo", "COP corrientes · promedio del periodo · línea = SMMLV")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_xaxes(title_text="Ingreso mediano (COP)", tickprefix="$", separatethousands=True)
            fig.update_yaxes(title_text="")
            fig.update_layout(height=H_PAIRED, margin=dict(r=90))
            # Línea SMMLV del año con más datos en el filtro
            _smmlv_year = int(df_edu["ano"].mode()[0]) if "ano" in df_edu.columns else max(SMMLV)
            _smmlv_val  = SMMLV.get(_smmlv_year, SMMLV[max(SMMLV)])
            fig.add_vline(
                x=_smmlv_val, line_dash="dash", line_color=BT_NAVY, line_width=1.8,
                annotation_text=f"SMMLV {_smmlv_year}<br>${fmt_metric(_smmlv_val)}",
                annotation_position="top right",
                annotation_font=dict(size=10, color=BT_NAVY),
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        placeholder(
            "Educación × ingresos sin datos. Agregar <code>P3042</code> al ETL y regenerar el parquet.",
            "📚",
        )

    render_interpretation(
        "El empleo se concentra en <b>comercio, reparación y servicios</b>, sectores con tasa de informalidad "
        "estructural superior al 50%. Cuando la TO sube pero el ingreso mediano se estanca o cae en términos "
        "reales, hay señal de precarización: más personas trabajando, peor remuneradas. La distribución por "
        "posición ocupacional (cuenta propia vs. asalariado) confirma esta tendencia hacia la informalidad.",
        title="Lectura ocupacional",
    )

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    render_section("Distribución territorial", "Tasa de ocupación e informalidad por departamento")
    render_map_module(
        df_dep_mapa, "TO", "ocupados",
        "Ocupados",
        indicators=["TO", "tasa_informalidad"],
        geo_sel=geo_sel,
    )

    # Mapa de ciudades — ocupados e informalidad por área metropolitana
    if not df_city_mapa.empty and "AREA_label" in df_city_mapa.columns:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        render_section("Mapa de ciudades", "Indicadores por área metropolitana · último periodo")
        city_map_col, city_ctrl_col = st.columns([4.05, 1.35], gap="medium")
        with city_ctrl_col:
            with st.container(border=True, height=530, key="ocupados_city_panel"):
                st.markdown(
                    "<div class='map-panel-head'>"
                    "<div class='map-control-title'>Indicador del mapa</div>"
                    "<div class='map-control-sub'>Variable por área metropolitana.</div>"
                    "</div>"
                    "<div class='map-field-label'>Indicador</div>",
                    unsafe_allow_html=True,
                )
                city_ind_oc = st.selectbox(
                    "Indicador ciudad ocupados",
                    options=["TO", "tasa_informalidad"],
                    format_func=lambda c: MAP_INDICATORS[c]["select"],
                    key="ocupados_city_indicator",
                    label_visibility="collapsed",
                )
                city_vals_oc = (
                    df_city_mapa.sort_values("periodo")
                    .groupby("AREA_label", as_index=False)[city_ind_oc]
                    .last()
                    .dropna(subset=[city_ind_oc])
                )
                if not city_vals_oc.empty:
                    for lbl, item in [
                        ("Mayor", city_vals_oc.loc[city_vals_oc[city_ind_oc].idxmax()]),
                        ("Menor", city_vals_oc.loc[city_vals_oc[city_ind_oc].idxmin()]),
                    ]:
                        st.markdown(
                            f"<div class='map-extreme-card'>"
                            f"<div class='map-extreme-label'>{lbl}</div>"
                            f"<div class='map-extreme-value'>{_format_map_value(city_ind_oc, item[city_ind_oc])}</div>"
                            f"<div class='map-extreme-name'>{item['AREA_label']}</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
        with city_map_col:
            st.plotly_chart(
                plot_mapa_ciudades(df_city_mapa, city_ind_oc, geo_sel=geo_sel),
                use_container_width=True,
                config={"displayModeBar": False},
            )


# ---------------------------------------------------------------------------
# Vista 4: Dinámica de desocupados
# ---------------------------------------------------------------------------
def view_desocupados(df_context, df_sx_age, df_city, df_edu, df_dep_mapa, context_label, geo_level,
                     df_tendencia=None, ano_ui="Todos", mes_ui="Todos", df_city_mapa=None, geo_sel="Todas"):
    t = ACTIVE_THEME
    row = latest_row(df_context)
    prev = prev_row(df_context)

    if row is not None:
        cols = st.columns(3, gap="small")
        render_kpi(
            cols[0], "Total desocupados",
            fmt_metric(row.get("desocupados_exp", 0)),
            "Último periodo disponible",
            fmt_delta_html(row.get("desocupados_exp"), prev.get("desocupados_exp") if prev is not None else None, invert=True),
        )
        render_kpi(
            cols[1], "Tasa de desempleo (TD)",
            f"{row.get('TD', 0):.1f}%",
            "Desocupados / PEA × 100",
            fmt_delta_html(row.get("TD"), prev.get("TD") if prev is not None else None, mode="pct", invert=True),
        )
        render_kpi(
            cols[2], "Inactivos",
            fmt_metric(row.get("FFT_exp", 0)),
            "Fuera del mercado laboral · FFT_exp",
            fmt_delta_html(row.get("FFT_exp"), prev.get("FFT_exp") if prev is not None else None, invert=True),
        )

    # Gráfico de tendencia: TD y TGP con doble eje
    _base_des = df_tendencia if df_tendencia is not None and not df_tendencia.empty else df_context
    trend_des = _base_des.sort_values("periodo")
    _cols_des = {"TD", "FFT_exp"} if "FFT_exp" in trend_des.columns else {"TD"}
    if not trend_des.empty and "TD" in trend_des.columns:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        subtitulo_des = f"Evolución mensual · {context_label}"
        if ano_ui != "Todos":
            subtitulo_des += f" · {ano_ui}"
        if mes_ui != "Todos":
            subtitulo_des += f" · {mes_ui} destacado"
        render_section("Tendencia de desempleo e inactividad", subtitulo_des)
        color_map_des = {"TD": BT_NAVY, "FFT_exp": BT_TEAL}
        fig_des = make_subplots(specs=[[{"secondary_y": True}]])
        # Eje izquierdo: Inactivos (FFT_exp) en millones
        if "FFT_exp" in trend_des.columns:
            fig_des.add_trace(go.Scatter(
                x=trend_des["periodo"], y=trend_des["FFT_exp"] / 1e6,
                name="Inactivos (FFT)",
                mode="lines",
                line=dict(color=BT_TEAL, width=2.5, shape="spline"),
                hovertemplate="<b>Inactivos</b>: %{y:.2f} M<br>%{x|%b %Y}<extra></extra>",
            ), secondary_y=False)
        # Eje derecho: TD en %
        fig_des.add_trace(go.Scatter(
            x=trend_des["periodo"], y=trend_des["TD"],
            name="Tasa de desempleo (TD)",
            mode="lines",
            line=dict(color=BT_NAVY, width=2.5, shape="spline"),
            fill="tozeroy",
            fillcolor=hex_to_rgba(BT_NAVY, 0.08),
            hovertemplate="<b>TD</b>: %{y:.1f}%<br>%{x|%b %Y}<extra></extra>",
        ), secondary_y=True)
        # Marcador del mes seleccionado
        if mes_ui != "Todos":
            mes_num = MESES_INVERSO.get(mes_ui)
            trend_mes_des = trend_des[trend_des["mes"] == mes_num] if "mes" in trend_des.columns else pd.DataFrame()
            if not trend_mes_des.empty:
                for ind, nombre, sec, fmt_fn in [
                    ("FFT_exp", "Inactivos", False, lambda v: f"<b>{v/1e6:.2f} M</b>"),
                    ("TD",      "TD",        True,  lambda v: f"<b>{v:.1f}%</b>"),
                ]:
                    if ind in trend_mes_des.columns:
                        fig_des.add_trace(go.Scatter(
                            x=trend_mes_des["periodo"],
                            y=trend_mes_des[ind] / 1e6 if ind == "FFT_exp" else trend_mes_des[ind],
                            name=f"{mes_ui} seleccionado",
                            mode="markers+text",
                            marker=dict(
                                color=color_map_des[ind], size=13, symbol="circle",
                                line=dict(width=2.5, color=t["panel_bg"]),
                            ),
                            text=[fmt_fn(v) for v in trend_mes_des[ind]],
                            textposition="top center",
                            textfont=dict(size=10, color=color_map_des[ind]),
                            showlegend=(ind == "TD"),
                            legendgroup="mes_sel_des",
                            hovertemplate=f"<b>{nombre} — {mes_ui}</b>: %{{y}}<br>%{{x|%b %Y}}<extra></extra>",
                        ), secondary_y=sec)
        dtick_des = "M1" if ano_ui != "Todos" else "M3"
        fig_des = fig_base(fig_des, "Dinámica de desempleo e inactividad", subtitulo_des)
        fig_des.update_yaxes(title_text="Inactivos (millones)", ticksuffix=" M", secondary_y=False)
        fig_des.update_yaxes(
            title_text="TD (%)", ticksuffix="%", secondary_y=True,
            showgrid=False,
            tickfont=dict(color=t["soft_text"], size=11),
            title_font=dict(color=t["muted"], size=11),
        )
        fig_des.update_xaxes(tickformat="%b %Y", dtick=dtick_des)
        fig_des.update_layout(height=H_SINGLE)
        st.plotly_chart(fig_des, use_container_width=True)

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    render_section("Perfil de desocupados", "Estructura por sexo, edad y distribución geográfica")
    left, right = st.columns(2, gap="large")
    with left:
        plot_pyramid(df_sx_age, "desocupados_exp", "Pirámide de desocupados", "Por sexo y grupo de edad · P3271 × P6040")
    with right:
        if df_city.empty or "AREA_label" not in df_city.columns:
            placeholder("Distribución por ciudad sin datos.", "🏙️")
        else:
            city = (
                df_city.groupby("AREA_label", as_index=False)["desocupados_exp"]
                .mean()
                .sort_values("desocupados_exp")
                .tail(12)
            )
            city["txt"] = city["desocupados_exp"].map(fmt_metric)
            fig = px.bar(
                city, x="desocupados_exp", y="AREA_label", orientation="h",
                text="txt",
                color="desocupados_exp",
                color_continuous_scale=BLUE_TEAL_SCALE,
                labels={"desocupados_exp": "Personas desocupadas", "AREA_label": ""},
            )
            fig = fig_base_h(fig, "Desocupados por ciudad", "Top 12 áreas metropolitanas")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_coloraxes(showscale=False)
            fig.update_xaxes(title_text="Personas desocupadas")
            fig.update_yaxes(title_text="")
            fig.update_layout(height=H_PYRAMID, margin=dict(r=90))
            st.plotly_chart(fig, use_container_width=True)

    if not df_edu.empty and "P3042_label" in df_edu.columns:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        render_section("Desocupados por nivel educativo", "P3042 · promedio del periodo seleccionado")
        edu = df_edu.groupby("P3042_label", as_index=False)["desocupados_exp"].mean().sort_values("desocupados_exp")
        edu["txt"] = edu["desocupados_exp"].map(fmt_metric)
        fig = px.bar(
            edu, x="desocupados_exp", y="P3042_label", orientation="h",
            text="txt",
            color_discrete_sequence=[BT_TEAL],
            labels={"desocupados_exp": "Personas desocupadas", "P3042_label": ""},
        )
        fig = fig_base_h(fig, "Desocupados por nivel educativo", "Promedio del periodo · nivel de estudio")
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        fig.update_xaxes(title_text="Personas desocupadas")
        fig.update_yaxes(title_text="")
        fig.update_layout(height=H_SINGLE, margin=dict(r=90))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        placeholder("Educación de desocupados sin datos. Agregar <code>P3042</code> al ETL.", "📚")

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    render_section("Distribución territorial", "Desempleo e inactividad por departamento")
    render_map_module(
        df_dep_mapa, "TD", "desocupados",
        "Desocupados",
        indicators=["TD", "tasa_inactividad"],
        geo_sel=geo_sel,
    )

    # Mapa de ciudades — desempleo por área metropolitana
    _df_city_des = df_city_mapa if df_city_mapa is not None and not df_city_mapa.empty else df_city
    if not _df_city_des.empty and "AREA_label" in _df_city_des.columns:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        render_section("Mapa de ciudades", "Indicadores por área metropolitana · último periodo")
        city_map_col, city_ctrl_col = st.columns([4.05, 1.35], gap="medium")
        with city_ctrl_col:
            with st.container(border=True, height=530, key="desocupados_city_panel"):
                st.markdown(
                    "<div class='map-panel-head'>"
                    "<div class='map-control-title'>Indicador del mapa</div>"
                    "<div class='map-control-sub'>Variable por área metropolitana.</div>"
                    "</div>"
                    "<div class='map-field-label'>Indicador</div>",
                    unsafe_allow_html=True,
                )
                city_ind_des = st.selectbox(
                    "Indicador ciudad desocupados",
                    options=["TD", "FFT_exp"],
                    format_func=lambda c: MAP_INDICATORS[c]["select"],
                    key="desocupados_city_indicator",
                    label_visibility="collapsed",
                )
                city_vals_des = (
                    _df_city_des.sort_values("periodo")
                    .groupby("AREA_label", as_index=False)[city_ind_des]
                    .last()
                    .dropna(subset=[city_ind_des])
                )
                if not city_vals_des.empty:
                    for lbl, item in [
                        ("Mayor", city_vals_des.loc[city_vals_des[city_ind_des].idxmax()]),
                        ("Menor", city_vals_des.loc[city_vals_des[city_ind_des].idxmin()]),
                    ]:
                        st.markdown(
                            f"<div class='map-extreme-card'>"
                            f"<div class='map-extreme-label'>{lbl}</div>"
                            f"<div class='map-extreme-value'>{_format_map_value(city_ind_des, item[city_ind_des])}</div>"
                            f"<div class='map-extreme-name'>{item['AREA_label']}</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
        with city_map_col:
            st.plotly_chart(
                plot_mapa_ciudades(_df_city_des, city_ind_des, geo_sel=geo_sel),
                use_container_width=True,
                config={"displayModeBar": False},
            )

    render_interpretation(
        "El desempleo está concentrado: pocas áreas metropolitanas suelen agrupar buena parte de los "
        "desocupados totales. La pirámide muestra un sesgo hacia jóvenes 15-28, especialmente mujeres. "
        "Por nivel educativo, los desocupados se distribuyen en media y técnica con una cola universitaria "
        "no despreciable — señal de subutilización del capital humano formado.",
        title="Lectura del desempleo",
    )



# ---------------------------------------------------------------------------
# Vista 5: Brechas y comparaciones
# ---------------------------------------------------------------------------
def view_brechas(df_sexo, df_edad_brecha, df_dep, df_dep_mapa, df_nac, geo_level, geo_sel="Todas"):
    t = ACTIVE_THEME
    _has_sex = not df_sexo.empty and "P3271_label" in df_sexo.columns

    # ── A: KPI cards de brecha ────────────────────────────────────────────────
    td_gap = to_gap = inf_gap = ing_gap = None
    if _has_sex:
        last_p = df_sexo["periodo"].max()
        ult = df_sexo[df_sexo["periodo"] == last_p].groupby("P3271_label", as_index=False).mean(numeric_only=True)
        hombre = ult[ult["P3271_label"] == "Hombre"]
        mujer  = ult[ult["P3271_label"] == "Mujer"]
        if not hombre.empty and not mujer.empty:
            if "TD" in ult.columns:
                td_gap  = float(mujer["TD"].values[0])  - float(hombre["TD"].values[0])
            if "TO" in ult.columns:
                to_gap  = float(mujer["TO"].values[0])  - float(hombre["TO"].values[0])
            if "tasa_informalidad" in ult.columns:
                inf_gap = float(mujer["tasa_informalidad"].values[0]) - float(hombre["tasa_informalidad"].values[0])
            if "ingreso_mediano" in ult.columns:
                im_h = float(hombre["ingreso_mediano"].values[0])
                im_m = float(mujer["ingreso_mediano"].values[0])
                if not pd.isna(im_h) and im_h > 0 and not pd.isna(im_m):
                    ing_gap = (im_m - im_h) / im_h * 100

    render_section("Brechas de género · Resumen", "Último período disponible · Mujer menos Hombre")
    _v_td  = f"{td_gap:+.1f} pp"  if td_gap  is not None and not pd.isna(td_gap)  else "s/d"
    _v_to  = f"{to_gap:+.1f} pp"  if to_gap  is not None and not pd.isna(to_gap)  else "s/d"
    _v_inf = f"{inf_gap:+.1f} pp" if inf_gap is not None and not pd.isna(inf_gap) else "s/d"
    _v_ing = f"{ing_gap:+.1f}%"   if ing_gap is not None and not pd.isna(ing_gap) else "s/d"
    st.markdown(
        f"""<div style='display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; margin-bottom:0.5rem;'>
  <div class='card' style='text-align:center; min-height:100px; display:flex; flex-direction:column; justify-content:center; align-items:center;'>
    <div class='kpi-label'>BRECHA TD (M−H)</div>
    <div class='kpi-value'>{_v_td}</div>
  </div>
  <div class='card' style='text-align:center; min-height:100px; display:flex; flex-direction:column; justify-content:center; align-items:center;'>
    <div class='kpi-label'>BRECHA TO (M−H)</div>
    <div class='kpi-value'>{_v_to}</div>
  </div>
  <div class='card' style='text-align:center; min-height:100px; display:flex; flex-direction:column; justify-content:center; align-items:center;'>
    <div class='kpi-label'>INFORMALIDAD (M−H)</div>
    <div class='kpi-value'>{_v_inf}</div>
  </div>
  <div class='card' style='text-align:center; min-height:100px; display:flex; flex-direction:column; justify-content:center; align-items:center;'>
    <div class='kpi-label'>INGRESO MEDIANO (M−H)</div>
    <div class='kpi-value'>{_v_ing}</div>
  </div>
</div>""",
        unsafe_allow_html=True,
    )

    # ── Sección: Género — brecha absoluta e informalidad ──────────────────────
    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    render_section("Brechas estructurales · Género", "Diferencias por sexo en TD e informalidad")
    left, right = st.columns(2, gap="large")

    with left:
        # B: Brecha absoluta TD (línea única Mujer − Hombre)
        if not _has_sex or "TD" not in df_sexo.columns:
            placeholder("Sin datos de brecha de género.", "⚧")
        else:
            pivot = (
                df_sexo.groupby(["periodo", "P3271_label"], as_index=False)["TD"].mean()
                .pivot(index="periodo", columns="P3271_label", values="TD")
                .reset_index()
            )
            if "Mujer" in pivot.columns and "Hombre" in pivot.columns:
                pivot["brecha_td"] = pivot["Mujer"] - pivot["Hombre"]
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=pivot["periodo"], y=pivot["brecha_td"],
                    name="Brecha TD (M−H)",
                    fill="tozeroy",
                    fillcolor=hex_to_rgba(BT_TEAL, 0.12),
                    line=dict(color=BT_TEAL, width=2.5, shape="spline"),
                    hovertemplate="<b>Brecha TD</b>: %{y:+.1f} pp<br>%{x|%b %Y}<extra></extra>",
                ))
                fig.add_hline(y=0, line_width=1.2, line_dash="dot", line_color=t["muted"])
                fig = fig_base(fig, "Brecha TD: Mujer − Hombre", "Puntos porcentuales · tendencia mensual")
                fig.update_xaxes(tickformat="%b %Y", dtick="M3")
                fig.update_yaxes(ticksuffix=" pp")
                fig.update_layout(height=H_PAIRED, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                placeholder("Sin datos suficientes de sexo.", "⚧")

    with right:
        # C: Informalidad por sexo (2 líneas)
        if not _has_sex or "tasa_informalidad" not in df_sexo.columns:
            placeholder("Sin datos de informalidad por sexo.", "⚧")
        else:
            serie_inf = df_sexo.groupby(["periodo", "P3271_label"], as_index=False)["tasa_informalidad"].mean()
            fig = px.line(
                serie_inf, x="periodo", y="tasa_informalidad", color="P3271_label",
                color_discrete_map=SEX_COLORS,
                line_shape="spline",
                labels={"tasa_informalidad": "Informalidad (%)", "P3271_label": ""},
            )
            fig = fig_base(fig, "Informalidad por sexo", "Serie mensual · Mujer vs. Hombre")
            fig.update_traces(
                line=dict(width=2.5),
                hovertemplate="<b>%{fullData.name}</b><br>Informalidad: %{y:.1f}%<br>%{x|%b %Y}<extra></extra>",
            )
            fig.update_xaxes(tickformat="%b %Y", dtick="M3")
            fig.update_yaxes(ticksuffix="%")
            fig.update_layout(height=H_PAIRED)
            st.plotly_chart(fig, use_container_width=True)

    render_interpretation(
        "La <b>brecha absoluta de TD</b> (valores positivos = mayor desempleo femenino) ha sido "
        "persistente en todo el periodo: entre 3 y 5 puntos porcentuales adicionales para las mujeres. "
        "La <b>informalidad femenina</b> supera también a la masculina, reflejo de la mayor participación "
        "de mujeres en trabajo doméstico, cuenta propia y sectores de baja productividad. "
        "Ambas brechas deben leerse junto con la TGP: parte de la ventaja masculina en TD se explica "
        "por mayor desaliento y salida de la PEA entre mujeres.",
        title="Lectura de brechas de género",
    )

    # ── Sección: Edad e Ingreso ───────────────────────────────────────────────
    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    render_section("Brechas estructurales · Edad e Ingreso", "TD juvenil vs. adulta e ingreso mediano por sexo")
    left2, right2 = st.columns(2, gap="large")

    with left2:
        if df_edad_brecha.empty or "grupo_edad_brecha" not in df_edad_brecha.columns:
            placeholder("Datos de brecha etaria no disponibles.<br>Requiere recodificación <code>15-28 vs 29+</code> en ETL.", "🧑‍🤝‍🧑")
        else:
            edad = df_edad_brecha.groupby("grupo_edad_brecha", as_index=False)["TD"].mean()
            edad["txt"] = edad["TD"].map(lambda x: f"{x:.1f}%")
            fig = px.bar(
                edad, x="grupo_edad_brecha", y="TD",
                text="txt",
                color="grupo_edad_brecha",
                color_discrete_sequence=[BT_BLUE, BT_MINT],
                labels={"TD": "Tasa de desempleo (%)", "grupo_edad_brecha": ""},
            )
            fig = fig_base(fig, "Brecha etaria en TD", "Jóvenes 15-28 vs. Adultos 29+")
            fig.update_traces(textposition="outside", marker_line_width=0)
            fig.update_xaxes(title_text="")
            fig.update_yaxes(ticksuffix="%", title_text="Tasa de desempleo (%)")
            fig.update_layout(showlegend=False, height=H_PAIRED)
            st.plotly_chart(fig, use_container_width=True)

    with right2:
        # D: Ingreso mediano por sexo — serie temporal
        if not _has_sex or "ingreso_mediano" not in df_sexo.columns:
            placeholder("Sin datos de ingreso mediano por sexo.", "💰")
        else:
            serie_ing = (
                df_sexo.groupby(["periodo", "P3271_label"], as_index=False)["ingreso_mediano"]
                .mean()
                .dropna(subset=["ingreso_mediano"])
            )
            if serie_ing.empty:
                placeholder("Sin datos de ingreso mediano.", "💰")
            else:
                # gap % en el último período para el subtítulo
                last_p2 = serie_ing["periodo"].max()
                ult_ing = serie_ing[serie_ing["periodo"] == last_p2]
                gap_subtitle = ""
                _im_m = ult_ing[ult_ing["P3271_label"] == "Mujer"]["ingreso_mediano"].values
                _im_h = ult_ing[ult_ing["P3271_label"] == "Hombre"]["ingreso_mediano"].values
                if len(_im_m) > 0 and len(_im_h) > 0 and _im_h[0] > 0:
                    _gp = (_im_m[0] - _im_h[0]) / _im_h[0] * 100
                    gap_subtitle = f" · brecha actual: {_gp:+.1f}%"
                fig = px.line(
                    serie_ing, x="periodo", y="ingreso_mediano", color="P3271_label",
                    color_discrete_map=SEX_COLORS,
                    line_shape="spline",
                    labels={"ingreso_mediano": "Ingreso mediano (COP)", "P3271_label": ""},
                )
                fig = fig_base(fig, "Ingreso mediano por sexo", f"Serie mensual · Mujer vs. Hombre{gap_subtitle} · línea = SMMLV")
                fig.update_traces(
                    line=dict(width=2.5),
                    hovertemplate="<b>%{fullData.name}</b><br>Ingreso mediano: $%{y:,.0f}<br>%{x|%b %Y}<extra></extra>",
                )
                fig.update_xaxes(tickformat="%b %Y", dtick="M3")
                fig.update_yaxes(tickprefix="$")
                fig.update_layout(height=H_PAIRED)
                # Línea SMMLV escalonada (sube cada enero)
                _periodos_smmlv = pd.date_range(
                    serie_ing["periodo"].min(), serie_ing["periodo"].max(), freq="MS"
                )
                _smmlv_series = [SMMLV.get(p.year, SMMLV[max(SMMLV)]) for p in _periodos_smmlv]
                fig.add_trace(go.Scatter(
                    x=_periodos_smmlv, y=_smmlv_series,
                    name="SMMLV", mode="lines",
                    line=dict(color=BT_NAVY, width=1.5, dash="dot"),
                    hovertemplate="<b>SMMLV %{x|%Y}</b>: $%{y:,.0f}<extra></extra>",
                ))
                st.plotly_chart(fig, use_container_width=True)

    render_interpretation(
        "La <b>brecha etaria</b> muestra que los jóvenes de 15-28 años duplican con frecuencia "
        "la tasa de desempleo de los adultos de 29 años o más, evidenciando barreras de entrada al primer "
        "empleo formal. La <b>serie de ingreso mediano por sexo</b> expone la brecha salarial en su "
        "evolución: las mujeres reciben sistemáticamente menos que los hombres en todo el período "
        "analizado, y la distancia absoluta tiende a ampliarse en meses de crecimiento económico "
        "porque los sectores que más crecen son predominantemente masculinos (construcción, manufactura). "
        "Ambas brechas son estructurales y cambian muy lentamente.",
        title="Lectura de edad e ingreso",
    )

    # ── Sección: Comparativa regional ─────────────────────────────────────────
    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    render_section("Comparativa regional", "TD departamental vs. promedio nacional · último período")
    if df_dep.empty or "DPTO_label" not in df_dep.columns:
        placeholder(
            "El comparativo regional aparecerá al regenerar el parquet con la dimensión <code>departamento</code>.",
            "🗺️",
        )
    else:
        nacional_td = (
            df_nac.groupby("periodo", as_index=False)["TD"]
            .mean()
            .sort_values("periodo")
            .iloc[-1]["TD"]
        )
        dep = df_dep.sort_values("periodo").groupby("DPTO_label", as_index=False)["TD"].last()
        dep["brecha"] = dep["TD"] - nacional_td
        dep = dep.sort_values("brecha")
        dep["color"] = dep["brecha"].map(lambda x: t["positive"] if x < 0 else t["negative"])
        dep["txt"] = dep["brecha"].map(lambda x: f"{x:+.1f} pp")

        fig = px.bar(
            dep, x="brecha", y="DPTO_label", orientation="h",
            text="txt",
            color="brecha",
            color_continuous_scale=[
                [0, BT_MINT],
                [0.5, BT_PALE],
                [1, BT_NAVY],
            ],
            labels={"brecha": "Diferencia (pp)", "DPTO_label": ""},
        )
        fig = fig_base_h(fig, "Brecha departamental vs. nacional", f"Referencia nacional: {nacional_td:.1f}% · puntos porcentuales")
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        fig.update_coloraxes(showscale=False)
        fig.update_xaxes(title_text="Diferencia (pp)", ticksuffix=" pp")
        fig.update_yaxes(title_text="")
        fig.add_vline(x=0, line_width=1.5, line_dash="dot", line_color=ACTIVE_THEME["muted"])
        fig.update_layout(height=max(H_SINGLE, len(dep) * 22 + 120), margin=dict(r=90))
        st.plotly_chart(fig, use_container_width=True)

    if not df_dep.empty and "DPTO_label" in df_dep.columns:
        st.markdown("<div class='section-gap-lg'></div>", unsafe_allow_html=True)
        render_section("Mapa de distribución regional", "Selecciona el indicador que quieres comparar por departamento")
        render_map_module(df_dep_mapa, "TD", "brechas", "", geo_sel=geo_sel)

    render_interpretation(
        "El comparativo regional separa departamentos por encima y por debajo del promedio nacional. "
        "Los departamentos del Pacífico (Chocó, Quibdó) y la frontera oriental tienden a sostener brechas "
        "positivas (TD muy por encima de la media), mientras Bogotá D.C., Antioquia y Cundinamarca "
        "compensan a la baja. Estas brechas son persistentes año a año, no coyunturales.",
        title="Lectura territorial",
    )


# ---------------------------------------------------------------------------
# Vista 6: Metodología
# ---------------------------------------------------------------------------
def view_instrucciones(df_nac=None, df_dep=None):
    t = ACTIVE_THEME
    _render_guide_doc(t)


def _render_guide_doc(t):
    """Renderiza la guía de usuario como documento HTML único y fluido."""

    TX  = t["text"]
    SF  = t["soft_text"]
    MU  = t["muted"]
    LN  = t["line"]
    PB  = t["panel_bg"]
    IB  = t["input_bg"]

    # ── helpers ───────────────────────────────────────────────────────────────
    def h2(txt):
        return (
            f"<h2 style='font-family:\"Fraunces\",Georgia,serif;font-size:1.32rem;"
            f"font-weight:700;color:{BT_DEEP};margin:2.4rem 0 0.7rem;padding-bottom:0.4rem;"
            f"border-bottom:2px solid {LN};'>{txt}</h2>"
        )

    def h3(txt, color=None):
        c = color or TX
        return (
            f"<h3 style='font-size:0.97rem;font-weight:700;color:{c};"
            f"margin:1.4rem 0 0.2rem;'>{txt}</h3>"
        )

    def pill(txt, color):
        return (
            f"<code style='background:{color}18;color:{color};border:1px solid {color}44;"
            f"padding:0.1rem 0.45rem;border-radius:4px;font-size:0.78rem;"
            f"font-family:monospace;'>{txt}</code>"
        )

    def ind_block(code, name, formula, color, qm, ref, comb, trap):
        row = (
            f"<tr style='border-top:1px solid {LN};'>"
            f"<td style='width:22%;font-weight:600;color:{TX};vertical-align:top;"
            f"padding:0.3rem 0.7rem 0.3rem 0;font-size:0.86rem;white-space:nowrap;'>{{lbl}}</td>"
            f"<td style='color:{SF};padding:0.3rem 0;font-size:0.86rem;line-height:1.55;'>{{val}}</td></tr>"
        )
        rows = (
            row.format(lbl="Qué mide", val=qm)
            + row.format(lbl="Referencia", val=ref)
            + row.format(lbl="Combinar con", val=comb)
            + row.format(lbl="⚠&nbsp;Trampa", val=f"<span style='color:{TX};'>{trap}</span>")
        )
        return (
            f"<div style='border-left:4px solid {color};padding:0.75rem 1rem 0.75rem 1rem;"
            f"margin-bottom:1.5rem;background:{PB};border-radius:0 8px 8px 0;"
            f"border:1px solid {LN};border-left-width:4px;'>"
            f"<div style='display:flex;align-items:baseline;gap:0.6rem;margin-bottom:0.5rem;flex-wrap:wrap;'>"
            f"<span style='font-family:\"Fraunces\",Georgia,serif;font-size:1.45rem;"
            f"font-weight:700;color:{color};line-height:1;'>{code}</span>"
            f"<span style='font-weight:700;color:{TX};font-size:0.92rem;'>&mdash;&nbsp;{name}</span>"
            f"<span style='margin-left:auto;'>{pill(formula, color)}</span>"
            f"</div>"
            f"<table style='width:100%;border-collapse:collapse;'>{rows}</table>"
            f"</div>"
        )

    def brecha_block(titulo, sub, items):
        lis = "".join(
            f"<li style='margin-bottom:0.42rem;color:{SF};font-size:0.88rem;'>{i}</li>"
            for i in items
        )
        return (
            f"{h3(titulo, BT_TEAL)}"
            f"<p style='color:{MU};font-size:0.82rem;margin:0 0 0.35rem;'>{sub}</p>"
            f"<ul style='margin:0 0 0.2rem 1.15rem;padding:0;line-height:1.65;'>{lis}</ul>"
        )

    def ruta_block(titulo, sub, items):
        lis = "".join(
            f"<li style='margin-bottom:0.38rem;color:{SF};font-size:0.88rem;'>{i}</li>"
            for i in items
        )
        return (
            f"<div style='break-inside:avoid;margin-bottom:1.3rem;'>"
            f"<div style='font-weight:700;color:{BT_DEEP};font-size:0.95rem;margin-bottom:0.05rem;'>{titulo}</div>"
            f"<div style='color:{MU};font-size:0.82rem;margin-bottom:0.35rem;'>{sub}</div>"
            f"<ul style='margin:0 0 0 1.1rem;padding:0;line-height:1.6;'>{lis}</ul>"
            f"</div>"
        )

    # ── contenido ─────────────────────────────────────────────────────────────
    header = (
        f"<div style='margin-bottom:2rem;padding-bottom:1.1rem;border-bottom:3px solid {BT_DEEP};'>"
        f"<div style='font-family:\"Fraunces\",Georgia,serif;font-size:2rem;font-weight:700;"
        f"color:{BT_DEEP};margin-bottom:0.35rem;'>Cómo leer este tablero</div>"
        f"<div style='color:{MU};font-size:0.97rem;max-width:680px;line-height:1.6;'>"
        f"Guía completa de indicadores, brechas y navegación &mdash; para que cualquier lector "
        f"extraiga conclusiones correctas en pocos minutos.</div>"
        f"</div>"
    )

    sec1 = (
        h2("1 &middot; Navegación y filtros")
        + "<div style='display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;margin-bottom:0.5rem;'>"
        + "<div>"
        + f"<p style='font-weight:700;color:{BT_DEEP};font-size:0.85rem;letter-spacing:0.06em;"
        f"text-transform:uppercase;margin:0 0 0.4rem;'>Filtros globales</p>"
        + f"<ul style='margin:0 0 0 1.1rem;padding:0;color:{SF};line-height:1.7;font-size:0.9rem;'>"
        + "<li><b>Año:</b> 2022–2025 o &laquo;Todos&raquo; para la serie completa.</li>"
        + "<li><b>Mes:</b> fija un mes para ver el punto exacto; &laquo;Todos&raquo; para la tendencia anual.</li>"
        + "<li><b>Nivel territorial:</b> Sin filtro = nacional; Departamento o Ciudad para enfocar.</li>"
        + "<li><b>Ubicación:</b> aparece según el nivel — 32 departamentos o 23 áreas metropolitanas.</li>"
        + "</ul>"
        + f"<p style='color:{MU};font-size:0.83rem;margin:0.5rem 0 0;'>Las vistas <b>Guía</b> y <b>Metodología</b> no usan filtros.</p>"
        + "</div>"
        + "<div>"
        + f"<p style='font-weight:700;color:{BT_DEEP};font-size:0.85rem;letter-spacing:0.06em;"
        f"text-transform:uppercase;margin:0 0 0.4rem;'>Las 5 vistas analíticas</p>"
        + f"<ul style='margin:0 0 0 1.1rem;padding:0;color:{SF};line-height:1.7;font-size:0.9rem;'>"
        + "<li><b>Resumen:</b> KPIs nacionales, tendencia TD/TO/TGP y mapas territoriales.</li>"
        + "<li><b>Población:</b> pirámide por quinquenios, educación, estado civil, clase.</li>"
        + "<li><b>Ocupados:</b> sectores económicos, informalidad, ingreso mediano, mapa de ciudades.</li>"
        + "<li><b>Desocupados:</b> perfil por sexo, edad, educación, inactivos (FFT) y mapa de ciudades.</li>"
        + "<li><b>Brechas:</b> género (TD, TO, informalidad, ingreso), etaria 15-28 vs 29+ y comparativa departamental.</li>"
        + "</ul>"
        + "</div>"
        + "</div>"
    )

    sec2 = (
        h2("2 &middot; Indicadores del mercado laboral")
        + f"<p style='color:{SF};font-size:0.9rem;margin:0 0 1.1rem;line-height:1.6;'>"
        f"Cada bloque muestra la fórmula, qué valor esperar en Colombia, con qué otro indicador "
        f"combinarlo y cuál es el error de lectura más frecuente.</p>"
        + ind_block("TD", "Tasa de Desempleo", "Desocupados ÷ PEA × 100", BT_NAVY,
            "De cada 100 personas que buscan trabajo activamente, cuántas no lo encuentran.",
            "Colombia oscila entre 9 % y 13 % según el ciclo. Por debajo del 8 %, tensión baja; por encima del 12 %, presión alta.",
            "<b>TGP:</b> si la TD baja pero la TGP también cae, el desempleo mejora por desaliento, no por empleo real. Siempre léelas juntas.",
            "TD baja &ne; mercado sano. Puede caer porque la gente dejó de buscar empleo (salió de la PEA).")
        + ind_block("TO", "Tasa de Ocupación", "Ocupados ÷ PET × 100", BT_BLUE,
            "De cada 100 personas en edad de trabajar (15 + años), cuántas tienen empleo.",
            "Colombia se mueve entre 54 % y 60 %. TO alta indica que la economía absorbe fuerza laboral.",
            "<b>TGP:</b> TO alta con TGP baja = todos los que participan trabajan, pero muchos están al margen. TO alta + TGP alta es el escenario más favorable.",
            "TO alta incluye empleo informal, de subsistencia y trabajadores familiares sin pago. Empleo &ne; empleo de calidad.")
        + ind_block("TGP", "Tasa Global de Participación", "(Ocupados + Desocupados) ÷ PET × 100", BT_TEAL,
            "Qué proporción de la población en edad de trabajar está activa: trabajando o buscando empleo.",
            "En Colombia ronda el 63–68 %. TGP baja puede reflejar desaliento, estudios prolongados o trabajo doméstico no remunerado.",
            "<b>TD:</b> si la TGP sube y la TD también sube, más personas buscan trabajo. Si ambas caen, el mercado se 'limpia' por desaliento.",
            "TGP baja en mujeres no significa que no trabajen. El trabajo del hogar no remunerado no se captura como ocupación.")
        + ind_block("Informalidad", "Tasa de Informalidad", "Informales ÷ Ocupados × 100", BT_MINT,
            "De cada 100 ocupados, cuántos trabajan sin afiliación al sistema de seguridad social contributivo (salud + pensión), según la definición DANE 2022.",
            "Colombia supera el 55 %. En ciudades grandes puede bajar al 40 %; en zonas rurales y el Pacífico supera el 70 %.",
            "<b>TO:</b> TO alta con informalidad alta = mucho empleo pero de baja calidad. <b>Rama económica:</b> comercio, agricultura y construcción concentran la mayor informalidad.",
            "Informal &ne; ilegal ni pobreza absoluta. Hay cuenta propia con ingresos altos clasificados como informales si no cotizan a pensión.")
        + ind_block("Ingreso mediano", "Ingreso Laboral Mediano", "Mediana ponderada de P6500 · entre ocupados", BT_DEEP,
            "El ingreso del trabajador en el centro de la distribución: la mitad gana más y la mitad gana menos. En pesos colombianos (COP) corrientes.",
            "El salario mínimo legal vigente es la referencia principal. Mediano cercano al mínimo indica predominio de empleo de baja remuneración.",
            "<b>Nivel educativo</b> (vista Ocupados): retorno de cada nivel de formación. <b>Rama económica:</b> qué sectores pagan mejor.",
            "La mediana puede enmascarar distribuciones bimodales: un mediano alto puede coexistir con muchos trabajadores de muy bajos ingresos.")
        + ind_block("Inactivos (FFT)", "Fuera de la Fuerza de Trabajo", "Suma expandida · PET con FFT = 1", BT_PALE,
            "Personas en edad de trabajar que ni trabajan ni buscan: estudiantes, personas dedicadas al hogar, pensionados o desalentados.",
            "En Colombia los inactivos superan los 14 millones. Crecimiento de inactivos sin caída de desocupados = señal de desaliento.",
            "<b>TGP:</b> si los inactivos crecen y la TGP cae, el mercado se contrae por el lado de la oferta, no por falta de empleo.",
            "Los inactivos no son desempleados ocultos en todos los casos. Un pensionado o estudiante también es inactivo.")
    )

    sec3 = (
        h2("3 &middot; Cómo leer la vista Brechas")
        + f"<p style='color:{SF};font-size:0.9rem;margin:0 0 1rem;line-height:1.65;'>"
        f"Una <b style='color:{TX};'>brecha laboral</b> es la diferencia sistemática en un indicador entre dos grupos — "
        f"por sexo, por edad o por territorio. Este dashboard mide brechas en "
        f"<b style='color:{TX};'>puntos porcentuales (pp)</b> para tasas (TD, TO, informalidad) y en "
        f"<b style='color:{TX};'>porcentaje (%)</b> para el ingreso mediano. "
        f"Las brechas son <b style='color:{TX};'>estructurales</b>: cambian muy lento; un quiebre brusco en un mes "
        f"debe leerse con cautela antes de atribuirlo a un cambio real.</p>"
        + brecha_block(
            "KPIs de brecha de género",
            "Fila de 4 tarjetas en la parte superior de la vista",
            [
                "<b>Brecha TD (M&minus;H): positivo (+)</b> = las mujeres tienen más desempleo. Valor típico en Colombia: entre +2 y +5 pp.",
                "<b>Brecha TO (M&minus;H): negativo (&minus;)</b> es lo usual — las mujeres participan menos en el mercado. Un &minus;20 pp es habitual.",
                "<b>Brecha Informalidad (M&minus;H): generalmente positiva</b> — las mujeres son más informales (trabajo doméstico, cuenta propia sin seguridad social).",
                "<b>Brecha Ingreso (M&minus;H): generalmente negativa</b> — las mujeres ganan menos. Un &minus;15 % significa que el ingreso mediano femenino es 15 % inferior al masculino.",
            ],
        )
        + brecha_block(
            "Línea: Brecha TD Mujer &minus; Hombre",
            "Gráfico de área con una sola línea — eje en puntos porcentuales",
            [
                "<b>Zona positiva (encima del 0):</b> las mujeres tienen mayor desempleo. Situación habitual en Colombia.",
                "<b>Zona negativa (debajo del 0):</b> los hombres tienen más desempleo. Ocurre en crisis sectoriales que afectan más empleos masculinos (construcción, transporte).",
                "<b>Tendencia creciente:</b> la brecha se amplía — el mercado se vuelve más desigual por género.",
                "<b>Tendencia decreciente:</b> la brecha se cierra. No siempre es buena noticia: puede significar que los hombres están perdiendo empleos.",
            ],
        )
        + brecha_block(
            "Líneas: Informalidad por sexo",
            "Mujer vs. Hombre · serie mensual",
            [
                "Muestra la evolución de la informalidad por separado para cada sexo.",
                "<b>Línea Mujer arriba:</b> las mujeres concentran más trabajo informal. Habitual en Colombia, especialmente en comercio y trabajo doméstico.",
                "<b>Convergencia de líneas:</b> la brecha de informalidad se cierra — señal de mejora en protección laboral femenina.",
                "Combinar con <b>Ocupados &rarr; Sectores</b> para identificar en qué ramas la informalidad femenina es más aguda.",
            ],
        )
        + brecha_block(
            "Barras: Ingreso mediano por sexo",
            "Último periodo disponible · Hombre vs. Mujer",
            [
                "Compara el ingreso mediano ponderado de hombres y mujeres en el último mes.",
                "<b>Brecha en el subtítulo:</b> porcentaje de diferencia del ingreso femenino respecto al masculino. Negativo = mujeres ganan menos.",
                "<b>Nota metodológica:</b> esta es la brecha bruta — no controla por horas, sector ni cargo. La brecha ajustada suele ser menor pero igualmente persistente.",
                "Si las barras son similares pero la informalidad femenina es mayor, el ingreso mediano subestima la desventaja real.",
            ],
        )
        + brecha_block(
            "Barras: Brecha etaria en TD",
            "Jóvenes 15-28 vs. Adultos 29+",
            [
                "Compara la tasa de desempleo promedio entre dos cohortes de edad.",
                "<b>Ratio típico en Colombia:</b> la TD juvenil duplica o triplica la adulta. Un ratio de 2× señala barreras de entrada al primer empleo formal.",
                "<b>Brecha alta:</b> indica rigidez en el mercado (contratos, experiencia requerida) que penaliza a los recién egresados.",
                "Cruzar con <b>Desocupados &rarr; Educación</b>: universitarios desempleados y jóvenes = problema de inserción del talento calificado.",
            ],
        )
        + brecha_block(
            "Barras horizontales: Brecha departamental vs. nacional",
            "TD de cada departamento menos el promedio nacional · en puntos porcentuales",
            [
                "<b>Barra a la derecha (positivo):</b> ese departamento tiene más desempleo que el promedio nacional.",
                "<b>Barra a la izquierda (negativo):</b> ese departamento está por debajo del promedio.",
                "<b>Línea punteada en 0:</b> es la referencia nacional. El subtítulo muestra el valor exacto.",
                "Combinar con el mapa regional (debajo del gráfico) para identificar si las brechas siguen patrones geográficos.",
            ],
        )
    )

    rutas_html = (
        ruta_block("Facultades técnicas e ingeniería", "STEM, formación dual, oferta académica", [
            "<b>Ocupados &rarr; Sectores:</b> identifica si TIC, manufactura e ingeniería crecen o se contraen.",
            "<b>Brechas &rarr; Informalidad por sexo:</b> evalúa si la brecha de género es mayor en tus sectores de egreso.",
            "<b>Ocupados &rarr; Ingreso mediano:</b> compara el retorno del nivel técnico vs. universitario.",
            "<b>Brechas &rarr; Ingreso mediano por sexo:</b> dimensiona la brecha salarial en el mercado al que envías egresadas.",
        ])
        + ruta_block("Ciencias sociales, salud y humanidades", "Política pública, salud, derecho, economía", [
            "<b>Brechas &rarr; KPI brecha TD:</b> línea base para cualquier análisis de equidad de género.",
            "<b>Brechas &rarr; Comparativa departamental:</b> heterogeneidad territorial — base para política focalizada.",
            "<b>Desocupados &rarr; Educación:</b> cuantifica la subutilización del capital humano universitario.",
            "<b>Ocupados &rarr; Informalidad:</b> identifica sectores donde la prestación de servicios reemplaza el contrato.",
        ])
        + ruta_block("Decanaturas y dirección de programa", "Diseño curricular, convenios, planeación", [
            "<b>Brechas &rarr; Brecha etaria 15-28 vs 29+:</b> sustenta convenios de Primer Empleo y prácticas tempranas.",
            "<b>Desocupados &rarr; Perfil por edad:</b> distingue desempleo abierto e inactividad por desaliento.",
            "<b>Brechas &rarr; Ingreso mediano por sexo:</b> argumento para políticas de equidad salarial con empleadores.",
            "<b>Resumen &rarr; Mapa regional:</b> prioriza territorios para extensión universitaria y alianzas.",
        ])
        + ruta_block("Periodismo económico y consultoría", "Notas, informes, asesoría a empresa o gobierno", [
            "<b>Resumen &rarr; Tendencia TD/TO/TGP:</b> identifica quiebres de tendencia y comparaciones interanuales.",
            "<b>Brechas &rarr; Línea brecha absoluta:</b> dato citable: &laquo;la mujer desemplea X pp más que el hombre&raquo;.",
            "<b>Brechas &rarr; Mapa regional:</b> base territorial para reportajes con enfoque departamental.",
            "<b>Metodología &rarr; Definiciones:</b> referencias técnicas para citar correctamente las cifras DANE.",
        ])
    )

    sec4 = (
        h2("4 &middot; Rutas de lectura por perfil")
        + "<div style='display:grid;grid-template-columns:1fr 1fr;gap:0 2rem;'>"
        + rutas_html
        + "</div>"
    )

    sec5 = (
        h2("5 &middot; Reglas de interpretación")
        + f"<p style='color:{SF};font-size:0.9rem;margin:0 0 0.8rem;'>Lo que <b>no</b> debes concluir de una sola cifra.</p>"
        + f"<ol style='margin:0 0 0 1.2rem;padding:0;color:{SF};line-height:1.8;font-size:0.9rem;'>"
        + f"<li style='margin-bottom:0.5rem;'><b style='color:{TX};'>TD baja &ne; mercado sano.</b> Puede caer porque la gente dejó de buscar empleo (salió de la PEA). Léela siempre junto a la TGP.</li>"
        + f"<li style='margin-bottom:0.5rem;'><b style='color:{TX};'>TO alta &ne; empleo de calidad.</b> Incluye trabajo informal, sin contrato y de subsistencia. Combina TO con informalidad para evaluar la calidad del empleo.</li>"
        + f"<li style='margin-bottom:0.5rem;'><b style='color:{TX};'>Las brechas son promedios grupales, no individuales.</b> Una brecha de +3.7 pp en TD no significa que cada mujer tenga ese desempleo adicional; es el diferencial del grupo.</li>"
        + f"<li style='margin-bottom:0.5rem;'><b style='color:{TX};'>Los KPIs muestran el último mes disponible.</b> El delta compara con el mes inmediatamente anterior, no con el mismo mes del año pasado.</li>"
        + f"<li style='margin-bottom:0.5rem;'><b style='color:{TX};'>Ingreso mediano &ne; ingreso promedio.</b> La mediana es robusta a extremos. Un mediano bajo puede coexistir con ingresos muy altos en sectores de élite.</li>"
        + f"<li style='margin-bottom:0.5rem;'><b style='color:{TX};'>Toda cifra está expandida con FEX_C18.</b> Son personas representadas, no encuestadas. No sumes valores de distintas tablas directamente sin considerar el factor de expansión.</li>"
        + f"<li style='margin-bottom:0.5rem;'><b style='color:{TX};'>Las brechas cambian muy lento.</b> Un quiebre brusco en un mes (brecha que salta 5 pp) debe sospecharse de variación muestral antes de atribuirlo a un fenómeno real.</li>"
        + "</ol>"
    )

    doc = (
        f"<div style='max-width:900px;margin:0 auto;padding:0.25rem 0.5rem 3rem;"
        f"font-size:0.94rem;color:{TX};line-height:1.72;'>"
        + header + sec1 + sec2 + sec3 + sec4 + sec5
        + "</div>"
    )
    st.markdown(doc, unsafe_allow_html=True)


def view_metodologia(df):
    t = ACTIVE_THEME
    years = sorted(df["ano"].dropna().unique().tolist()) if "ano" in df.columns else []
    year_range = f"{years[0]}–{years[-1]}" if len(years) >= 2 else (str(years[0]) if years else "s/d")

    TX = t["text"]; SF = t["soft_text"]; MU = t["muted"]
    LN = t["line"]; PB = t["panel_bg"]; IB = t["input_bg"]

    def h2(txt):
        return (
            f"<h2 style='font-family:Fraunces,serif; font-size:1.25rem; font-weight:700; "
            f"color:{BT_DEEP}; margin:2rem 0 0.6rem; padding-bottom:0.35rem; "
            f"border-bottom:2px solid {LN};'>{txt}</h2>"
        )

    def param_card(label, val, foot):
        return (
            f"<div style='background:{IB}; border:1px solid {LN}; border-radius:10px; "
            f"padding:1rem 1.1rem; display:flex; flex-direction:column; gap:0.25rem;'>"
            f"<div style='font-size:0.72rem; font-weight:700; letter-spacing:.06em; "
            f"text-transform:uppercase; color:{MU};'>{label}</div>"
            f"<div style='font-family:Fraunces,serif; font-size:1.4rem; font-weight:700; "
            f"color:{BT_DEEP};'>{val}</div>"
            f"<div style='font-size:0.82rem; color:{SF}; line-height:1.45;'>{foot}</div>"
            f"</div>"
        )

    def def_block(code, name, desc, color=BT_DEEP):
        return (
            f"<div style='border-left:4px solid {color}; padding:0.65rem 0.9rem; "
            f"background:{IB}; border-radius:0 8px 8px 0; margin-bottom:0.55rem;'>"
            f"<div style='display:flex; align-items:baseline; gap:0.5rem; margin-bottom:0.2rem;'>"
            f"<span style='font-family:Fraunces,serif; font-size:1.15rem; font-weight:700; "
            f"color:{color};'>{code}</span>"
            f"<span style='font-size:0.9rem; font-weight:700; color:{TX};'>{name}</span>"
            f"</div>"
            f"<div style='font-size:0.86rem; color:{SF}; line-height:1.5;'>{desc}</div>"
            f"</div>"
        )

    def tr(ind, vars_, calc, last=False):
        border = "" if last else f"border-bottom:1px solid {LN};"
        return (
            f"<tr style='{border}'>"
            f"<td style='padding:0.45rem 0.65rem; font-weight:700; color:{TX}; white-space:nowrap;'>{ind}</td>"
            f"<td style='padding:0.45rem 0.65rem; font-family:monospace; font-size:0.83rem; color:{BT_TEAL};'>{vars_}</td>"
            f"<td style='padding:0.45rem 0.65rem; color:{SF}; font-size:0.86rem;'>{calc}</td>"
            f"</tr>"
        )

    def note_li(txt):
        return f"<li style='margin-bottom:0.45rem; line-height:1.6;'>{txt}</li>"

    # ── Encabezado ────────────────────────────────────────────────────────────
    header = (
        f"<div style='border-bottom:3px solid {BT_DEEP}; padding-bottom:1rem; margin-bottom:0.25rem;'>"
        f"<div style='font-family:Fraunces,serif; font-size:2rem; font-weight:800; color:{BT_DEEP}; "
        f"line-height:1.15; margin-bottom:0.4rem;'>Ficha técnica · Metodología</div>"
        f"<div style='font-size:0.97rem; color:{SF}; max-width:72ch; line-height:1.6;'>"
        f"Procesamiento de microdatos de la <b>Gran Encuesta Integrada de Hogares (GEIH)</b> "
        f"rediseñada del DANE para el período <b>{year_range}</b>. "
        f"Toda cifra de este dashboard es trazable hasta el código de variable original.</div>"
        f"</div>"
    )

    # ── Sección 1: Parámetros ─────────────────────────────────────────────────
    params_grid = (
        "<div style='display:grid; grid-template-columns:repeat(4,1fr); gap:0.85rem; margin-bottom:0.5rem;'>"
        + param_card("Fuente", "DANE GEIH", "Encuesta rediseñada (2022). Bases anuales consolidadas.")
        + param_card("Marco muestral", "Probabilístico", "Multietápico, estratificado, por conglomerados. 23 áreas metropolitanas.")
        + param_card("Precisión", "CV &lt; 5%", "Indicadores publicados solo para niveles con suficiencia muestral.")
        + param_card("Expansión", "FEX_C18", "Factor post-rediseño 2022. Toda cifra está expandida a personas.")
        + "</div>"
    )
    sec1 = h2("1 · Parámetros estadísticos") + params_grid

    # ── Sección 2: Definiciones ───────────────────────────────────────────────
    defs_data = [
        ("PET",        "Población en edad de trabajar",       "Personas de 15 años o más (criterio DANE post-2022).",                                          BT_DEEP),
        ("PEA / FT",   "Población económicamente activa",     "Ocupados + desocupados. La «fuerza de trabajo» del país.",                                       BT_BLUE),
        ("OCI",        "Ocupados",                            "Personas que trabajaron al menos una hora remunerada o sin remuneración en la semana de referencia.", BT_TEAL),
        ("DSI",        "Desocupados",                         "Personas sin empleo que buscaron activamente y están disponibles.",                               BT_NAVY),
        ("FFT",        "Fuera de fuerza de trabajo",          "Personas en edad de trabajar que ni trabajan ni buscan: estudiantes, hogar, jubilados, desalentados.", BT_BLUE),
        ("Informalidad","Tasa de informalidad (DANE 2022)",   "Combina posición ocupacional, tamaño de empresa, afiliación a salud y pensión, registro mercantil, oficio y rama. Implementación en <code>src/indicators.py</code>.", BT_TEAL),
    ]
    defs_left  = "".join(def_block(*d) for d in defs_data[:3])
    defs_right = "".join(def_block(*d) for d in defs_data[3:])
    sec3 = (
        h2("3 · Definiciones operativas (OIT / DANE)")
        + "<div style='display:grid; grid-template-columns:1fr 1fr; gap:1rem;'>"
        + f"<div>{defs_left}</div><div>{defs_right}</div></div>"
    )

    # ── Sección 3: Trazabilidad ───────────────────────────────────────────────
    rows_data = [
        ("TD",             "OCI, DSI, FEX_C18",          "Σ(DSI·FEX) ÷ Σ((OCI+DSI)·FEX) × 100"),
        ("TO",             "OCI, P6040, FEX_C18",         "Σ(OCI·FEX) ÷ Σ(PET·FEX) × 100, PET = P6040 ≥ 15"),
        ("TGP",            "OCI, DSI, P6040",             "Σ((OCI+DSI)·FEX) ÷ Σ(PET·FEX) × 100"),
        ("Informalidad",   "P6430, P6920, P6090, +13",    "Regla DANE en src/indicators.py"),
        ("Ingreso mediano","P6500, FEX_C18",               "Mediana ponderada por FEX entre ocupados"),
        ("Sexo",           "P3271",                        "Sexo al nacer (post-rediseño; reemplaza P6020)"),
        ("Edad / Pirámide","P6040",                        "Quinquenios 15-19, 20-24 … 65+ (estándar OIT)"),
        ("Sector",         "RAMA2D_R4",                   "CIIU Rev.4 a 2 dígitos"),
    ]
    tabla_rows = "".join(
        tr(ind, v, c, last=(i == len(rows_data) - 1))
        for i, (ind, v, c) in enumerate(rows_data)
    )
    sec4 = (
        h2("4 · Trazabilidad de variables")
        + f"<div style='background:{IB}; border:1px solid {LN}; border-radius:10px; overflow:hidden;'>"
        + "<table style='width:100%; border-collapse:collapse; font-size:0.88rem;'>"
        + f"<thead><tr style='background:{PB}; border-bottom:2px solid {LN};'>"
        + f"<th style='padding:0.5rem 0.65rem; text-align:left; color:{TX}; font-size:0.8rem; text-transform:uppercase; letter-spacing:.05em;'>Indicador</th>"
        + f"<th style='padding:0.5rem 0.65rem; text-align:left; color:{TX}; font-size:0.8rem; text-transform:uppercase; letter-spacing:.05em;'>Variables GEIH</th>"
        + f"<th style='padding:0.5rem 0.65rem; text-align:left; color:{TX}; font-size:0.8rem; text-transform:uppercase; letter-spacing:.05em;'>Cálculo</th>"
        + f"</tr></thead><tbody>{tabla_rows}</tbody></table></div>"
    )

    # ── Sección 4: Notas ──────────────────────────────────────────────────────
    notas = "".join([
        note_li("<b>Ruptura de serie:</b> los datos desde 2022 <b>no son comparables</b> con series anteriores a 2021. La GEIH fue rediseñada y se aplica el marco poblacional Censo 2018."),
        note_li("<b>Variable de sexo:</b> a partir de 2022 se usa <code>P3271</code> (sexo al nacer); el código <code>P6020</code> del diseño anterior queda obsoleto."),
        note_li("<b>Nivel educativo:</b> se usa <code>P3042</code> en lugar de <code>P6210</code> porque esta última no aparece en el encabezado de <code>geih_2025.csv</code>."),
        note_li("<b>Ingreso:</b> mediana ponderada en pesos corrientes, sin deflactar. Para series reales, ajusta por IPC fuera del dashboard."),
        note_li("<b>Granularidad:</b> el parquet está en frecuencia mensual; no se reportan trimestres móviles."),
        note_li("<b>Cita sugerida:</b> «Elaboración propia con microdatos de la GEIH-DANE, ponderados con FEX_C18»."),
    ])
    sec5 = (
        h2("5 · Notas y advertencias")
        + f"<div style='background:{IB}; border:1px solid {LN}; border-radius:10px; padding:1rem 1.2rem;'>"
        + f"<ul style='margin:0; padding-left:1.1rem; color:{SF};'>{notas}</ul></div>"
    )

    # ── Render parte A (encabezado + params) ─────────────────────────────────
    doc_a = (
        "<div style='max-width:960px; margin:0 auto; padding:0.25rem 0.5rem 1rem;'>"
        + header + sec1
        + "</div>"
    )
    st.markdown(doc_a, unsafe_allow_html=True)

    # ── Chart de cobertura (Plotly, no embebible en HTML) ────────────────────
    st.markdown(
        "<div style='max-width:960px; margin:0 auto;'>"
        + h2("2 · Cobertura procesada")
        + f"<div style='font-size:0.86rem; color:{SF}; margin-bottom:0.5rem;'>"
        + f"Registros agregados por dimensión analítica · {year_range}</div></div>",
        unsafe_allow_html=True,
    )
    coverage = (
        df.groupby("dimension", as_index=False)
        .size()
        .rename(columns={"size": "registros"})
        .sort_values("registros")
    )
    coverage["dimension_label"] = coverage["dimension"].str.replace("_", " ").str.title()
    fig = px.bar(
        coverage, x="registros", y="dimension_label", orientation="h",
        color="registros", color_continuous_scale=BLUE_TEAL_SCALE,
        text=coverage["registros"].map(lambda x: f"{x:,.0f}"),
    )
    fig = fig_base_h(fig, "", "Cada barra es una tabla independiente del parquet")
    fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(title_text="Registros")
    fig.update_yaxes(title_text="")
    fig.update_layout(height=H_SINGLE, margin=dict(l=146, r=34, t=48, b=48))
    st.plotly_chart(fig, use_container_width=True)

    # ── Render parte B (definiciones + trazabilidad + notas) ─────────────────
    doc_b = (
        "<div style='max-width:960px; margin:0 auto; padding:0 0.5rem 3rem;'>"
        + sec3 + sec4 + sec5
        + "</div>"
    )
    st.markdown(doc_b, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "Light"

# Toggle de tema via query param (clic en ícono luna/sol)
_qtheme = st.query_params.get("theme", None)
if _qtheme in ("Dark", "Light"):
    st.session_state["theme_mode"] = _qtheme

ACTIVE_THEME = THEMES[st.session_state["theme_mode"]]
inject_styles(st.session_state["theme_mode"])

df_all = cargar()
if df_all.empty:
    st.error(
        "No se encontraron indicadores. "
        "Ejecuta `python src/etl.py` antes de abrir la app."
    )
    st.stop()

vista = render_side_nav()

page_shell = st.container()
_vista_sin_filtros = vista in ("metodologia", "instrucciones")

with page_shell:
    if _vista_sin_filtros:
        title_slot   = st.empty()
        filters_slot = st.empty()
    else:
        hero_card = st.container(border=True, key="hero_filters_card")
        with hero_card:
            title_slot   = st.container()
            filters_slot = st.container()
    body_slot = st.container()

# Metodología y manual no necesitan filtros — usar defaults sin renderizar el control
if _vista_sin_filtros:
    anos_sel   = sorted(df_all["ano"].dropna().unique().tolist())
    meses_sel  = sorted(df_all["mes"].dropna().unique().tolist())
    geo_level  = "Sin filtro"
    geo_sel    = "Todas"
    ano_ui     = "Todos"
    mes_ui     = "Todos"
else:
    with filters_slot:
        ano_ui, anos_sel, mes_ui, meses_sel, geo_level, geo_sel = render_controls(df_all)

# Filtrar dimensiones
df_nac         = filtrar(df_all, "nacional",            anos_sel, meses_sel, geo_level, geo_sel)
df_dep         = filtrar(df_all, "departamento",        anos_sel, meses_sel, geo_level, geo_sel)
df_dep_mapa    = filtrar(df_all, "departamento",        anos_sel, meses_sel, "Sin filtro", "Todas")
df_city        = filtrar(df_all, "ciudad",              anos_sel, meses_sel, geo_level, geo_sel)
df_city_mapa   = filtrar(df_all, "ciudad",              anos_sel, meses_sel, "Sin filtro", "Todas")

if "FFT_exp" in df_dep_mapa.columns and "PET_exp" in df_dep_mapa.columns:
    df_dep_mapa = df_dep_mapa.copy()
    df_dep_mapa["tasa_inactividad"] = (
        df_dep_mapa["FFT_exp"] / df_dep_mapa["PET_exp"].replace(0, float("nan")) * 100
    )

# Para la vista Población: usar cruce geo × demográfico cuando hay filtro activo
if geo_level == "Departamento" and geo_sel not in ("Todos", "Todas"):
    _dem_prefix = "dpto_"
elif geo_level == "Ciudad" and geo_sel not in ("Todos", "Todas"):
    _dem_prefix = "ciudad_"
else:
    _dem_prefix = ""

def _dem(base_dim: str):
    if _dem_prefix:
        r = filtrar(df_all, _dem_prefix + base_dim, anos_sel, meses_sel, geo_level, geo_sel)
        if not r.empty:
            return r
    return filtrar(df_all, base_dim, anos_sel, meses_sel, geo_level, geo_sel)

df_sexo        = _dem("sexo")
df_sx_age      = _dem("sexo_edad")
df_edad_brecha = _dem("edad_brecha")
df_sector      = filtrar(df_all, "sector",              anos_sel, meses_sel, geo_level, geo_sel)
df_clase       = _dem("clase")
df_civil       = _dem("estado_civil")
df_edu         = _dem("educacion")
df_pos         = filtrar(df_all, "posicion_ocupacional", anos_sel, meses_sel, geo_level, geo_sel)

if df_nac.empty:
    st.warning("No hay datos nacionales para los filtros seleccionados. Relaja los filtros o regenera el parquet.")
    st.stop()

ultimo       = latest_row(df_nac)
df_context   = active_context_df(df_nac, df_dep, df_city, geo_level, geo_sel)
context_label = active_context_label(geo_level, geo_sel)

# Serie de tendencia: siempre con todos los meses del año seleccionado,
# nunca filtrada por mes (el mes solo añade un marcador encima)
_meses_todos = sorted(df_all["mes"].dropna().unique().tolist())
_df_nac_tr   = filtrar(df_all, "nacional",     anos_sel, _meses_todos, "Sin filtro", "Todas")
_df_dep_tr   = filtrar(df_all, "departamento", anos_sel, _meses_todos, geo_level,    geo_sel)
_df_city_tr  = filtrar(df_all, "ciudad",       anos_sel, _meses_todos, geo_level,    geo_sel)
df_tendencia = active_context_df(_df_nac_tr, _df_dep_tr, _df_city_tr, geo_level, geo_sel)

with title_slot:
    if vista not in ("instrucciones", "metodologia"):
        render_header(vista, ultimo["periodo"].strftime("%B %Y").capitalize(), context_label)

with body_slot:
    if vista not in ("metodologia", "instrucciones"):
        render_filters_summary(ano_ui, mes_ui, geo_level, geo_sel)
        st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)

    if vista == "resumen":
        view_resumen(df_context, df_dep, df_dep_mapa, df_city, df_city_mapa, context_label, df_tendencia, ano_ui, mes_ui, geo_sel=geo_sel)
    elif vista == "poblacion":
        view_caracterizacion(df_sx_age, df_edu, df_civil, df_sexo, df_clase, geo_level, geo_sel, df_dep_mapa=df_dep_mapa)
    elif vista == "ocupados":
        view_ocupados(df_context, df_sector, df_sx_age, df_pos, df_city, df_edu, df_dep_mapa, context_label, geo_level,
                      df_tendencia=df_tendencia, ano_ui=ano_ui, mes_ui=mes_ui)
    elif vista == "desocupados":
        view_desocupados(df_context, df_sx_age, df_city, df_edu, df_dep_mapa, context_label, geo_level,
                         df_tendencia=df_tendencia, ano_ui=ano_ui, mes_ui=mes_ui, df_city_mapa=df_city_mapa, geo_sel=geo_sel)
    elif vista == "brechas":
        view_brechas(df_sexo, df_edad_brecha, df_dep, df_dep_mapa, df_nac, geo_level, geo_sel=geo_sel)
    elif vista == "instrucciones":
        view_instrucciones(df_nac, df_dep)
    else:
        view_metodologia(df_all)

st.divider()
st.caption("Daniel Molina · Economista & Data Scientist · Fuente: DANE — Gran Encuesta Integrada de Hogares (GEIH)")
