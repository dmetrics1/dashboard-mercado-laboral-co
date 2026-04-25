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
from plotly.subplots import make_subplots
import streamlit as st

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


def plot_mapa_departamentos(df, indicador="TD", title=""):
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
        marker_opacity=0.88,
        marker_line_width=0.65,
        marker_line_color=t["panel_solid"],
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
    
    fig.update_layout(
        mapbox_style="carto-positron" if st.session_state.get("theme_mode") == "Light" else "carto-darkmatter",
        mapbox_zoom=4.18,
        mapbox_center={"lat": 4.55, "lon": -74.20},
        mapbox=dict(pitch=10, bearing=0),
        height=500,
        margin={"r":0,"t":42 if title else 0,"l":0,"b":0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=dict(text=title, font=dict(size=14, color=t["text"]), x=0.05, y=0.95) if title else None,
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

ACTIVE_THEME = THEMES["Dark"]

AGE_ORDER = ["15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65+"]

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

MAP_INDICATORS = {
    "TD": {"label": "Tasa de desempleo (TD)", "select": "TD - Desempleo", "short": "TD", "suffix": "%", "kind": "pct"},
    "TO": {"label": "Tasa de ocupación (TO)", "select": "TO - Ocupación", "short": "TO", "suffix": "%", "kind": "pct"},
    "TGP": {"label": "Tasa global de participación", "select": "TGP - Participación", "short": "TGP", "suffix": "%", "kind": "pct"},
    "tasa_informalidad": {"label": "Tasa de informalidad", "select": "Informalidad", "short": "Informalidad", "suffix": "%", "kind": "pct"},
    "ocupados_exp": {"label": "Ocupados", "select": "Ocupados", "short": "Ocupados", "suffix": "", "kind": "count"},
    "desocupados_exp": {"label": "Desocupados", "select": "Desocupados", "short": "Desocupados", "suffix": "", "kind": "count"},
    "poblacion_total_exp": {"label": "Población total", "select": "Población", "short": "Población", "suffix": "", "kind": "count"},
    "ingreso_mediano": {"label": "Ingreso mediano", "select": "Ingreso", "short": "Ingreso", "suffix": "", "kind": "money"},
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
AUTHOR_GITHUB = "https://github.com/dmgsjj"
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
    dropdown_hover = "rgba(30,45,85,0.08)" if theme_name == "Light" else "rgba(81,166,174,0.16)"
    chrome_shadow = "0 6px 18px rgba(139,110,75,0.10)" if theme_name == "Light" else "0 10px 24px rgba(0,0,0,0.18)"
    chart_shadow = "0 10px 24px rgba(15,23,42,0.07)" if theme_name == "Light" else "0 12px 28px rgba(0,0,0,0.16)"
    sidebar_width = "15.5rem"
    sidebar_gap = "0.9rem"
    content_left = "16.85rem"
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
            padding-top: 1rem !important;
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
            padding: 0.95rem 1rem 0.9rem;
            min-height: 116px;
            position: relative;
            overflow: hidden;
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
            padding: 0.9rem 1rem;
        }}
        /* Tarjeta-contenedor para cada st.plotly_chart (visualmente la del spec) */
        [data-testid="stPlotlyChart"] {{
            background: {t['panel_bg']} !important;
            border: 1px solid {t['line']} !important;
            border-radius: 10px !important;
            padding: 0.55rem 0.55rem 0.4rem !important;
            box-shadow: {chart_shadow} !important;
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

        .section-gap {{ height: 0.85rem; }}
        .section-gap-lg {{ height: 1.45rem; }}
        .section-header {{
            margin: 0.65rem 0 0.55rem;
            padding-top: 0.05rem;
            border-top: 1px solid {t['line']};
            padding-top: 0.85rem;
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
        [data-baseweb="popover"],
        [data-baseweb="menu"],
        ul[role="listbox"] {{
            background: {dropdown_bg} !important;
            color: {select_text} !important;
            border: 1px solid {select_border} !important;
            box-shadow: {chrome_shadow} !important;
        }}
        li[role="option"],
        [role="option"] {{
            background: {dropdown_bg} !important;
            color: {select_text} !important;
        }}
        li[role="option"]:hover,
        [role="option"]:hover {{
            background: {dropdown_hover} !important;
            color: {select_text} !important;
        }}
        li[role="option"] div,
        li[role="option"] span,
        [role="option"] div,
        [role="option"] span {{
            color: {select_text} !important;
        }}

        /* Ocultar Chrome Nativo */
        [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
        [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"],
        .stAppDeployButton {{ display: none !important; }}
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
        font=dict(color=t["text"], family="IBM Plex Sans, sans-serif", size=12),
        title=dict(
            text=full_title,
            font=dict(color=t["text"], size=13, weight=600),
            x=0.0,
            xanchor="left",
            pad=dict(l=4),
        ),
        margin=dict(l=20, r=22, t=90 if full_title else 24, b=48),
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
            y=1.06,
            x=0,
            yanchor="bottom",
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
        margin=dict(l=28, r=34, t=90 if (title or subtitle) else 24, b=52),
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


def filtrar(df, dim, anos_sel, geo_level, geo_sel):
    base = df[(df["dimension"] == dim) & (df["ano"].isin(anos_sel))].copy()
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
def render_kpi(col, label: str, value: str, foot: str, delta_html: str = ""):
    with col:
        delta_block = f"<div style='margin-top:0.3rem'>{delta_html}</div>" if delta_html else ""
        foot_block = f"<div class='kpi-foot'>{foot}</div>" if foot else ""
        st.markdown(
            f"""<div class='card'>
                  <div class='kpi-label'>{label}</div>
                  <div class='kpi-value'>{value}</div>
                  {delta_block}
                  {foot_block}
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

    current_theme = st.session_state.get("theme_mode", "Dark")
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
    return vista


def render_controls(df_all):
    st.markdown(
        "<div class='filters-title'>Filtros territoriales</div>",
        unsafe_allow_html=True
    )
    year_col, level_col, geo_col = st.columns([0.85, 0.95, 1.2], gap="small")
    anos_disp = sorted(df_all["ano"].dropna().unique().tolist())
    with year_col:
        ano_ui = st.selectbox("Periodo anual", ["Todos"] + [str(a) for a in anos_disp], index=0)
    anos_sel = anos_disp if ano_ui == "Todos" else [int(ano_ui)]
    with level_col:
        geo_level = st.selectbox("Nivel territorial", ["Sin filtro", "Departamento", "Ciudad"], index=0)
    with geo_col:
        if geo_level == "Departamento":
            geo_sel = st.selectbox("Ubicación", ["Todos"] + opciones(df_all, "departamento", "DPTO_label"), index=0)
        elif geo_level == "Ciudad":
            geo_sel = st.selectbox("Ubicación", ["Todas"] + opciones(df_all, "ciudad", "AREA_label"), index=0)
        else:
            geo_sel = "Todas"
            st.selectbox("Ubicación", ["Sin filtro"], index=0, disabled=True)
    return ano_ui, anos_sel, geo_level, geo_sel


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


def render_filters_summary(ano_ui, geo_level, geo_sel):
    # Solo mostrar chips si hay algo filtrado (no default)
    is_default = (ano_ui == "Todos" and geo_level == "Sin filtro" and geo_sel == "Todas")
    if is_default:
        return

    chips = "".join([
        f"<span class='pill'>📅 {ano_ui}</span>" if ano_ui != "Todos" else "",
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


def render_map_module(df_dep: pd.DataFrame, default_indicator: str, key_prefix: str, title_prefix: str):
    if df_dep.empty or "DPTO_label" not in df_dep.columns:
        placeholder(
            "El mapa regional aparecerá al regenerar el parquet con la dimensión <code>departamento</code>.",
            "🗺️",
        )
        return

    options = available_map_indicators(df_dep)
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
        st.markdown(
            f"<div class='map-plot-title'>{title_prefix}: {meta['short']}</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            plot_mapa_departamentos(df_dep, indicador, ""),
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
        height=max(440, len(AGE_ORDER) * 32 + 170),
        margin=dict(l=24, r=28, t=112, b=48),
        legend=dict(
            orientation="h",
            x=0.5,
            xanchor="center",
            y=1.08,
            yanchor="bottom",
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
def view_resumen(df_context, df_dep, context_label):
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

    # Tendencia principal a ancho completo (las mini-cards laterales duplicaban KPIs)
    render_section("Tendencia de indicadores laborales", "Serie mensual — TD, TO y TGP ponderados con FEX_C18")
    trend = df_context.sort_values("periodo")
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

    fig = fig_base(fig, "Dinámica laboral mensual", f"Doble eje · contexto: {context_label}")
    fig.update_yaxes(title_text="TO / TGP (%)", ticksuffix="%", secondary_y=False)
    fig.update_yaxes(
        title_text="TD (%)", ticksuffix="%", secondary_y=True, showgrid=False,
        tickfont=dict(color=t["soft_text"], size=11),
        title_font=dict(color=t["muted"], size=11),
    )
    fig.update_xaxes(tickformat="%b %Y", dtick="M3")
    fig.update_layout(height=380)
    fig = add_eventos_geih(fig, t)
    st.plotly_chart(fig, use_container_width=True)

    # Comparativo departamental: prioridad de política pública = mayor desempleo
    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    render_section("Prioridades territoriales", "Departamentos con mayor presión laboral · último período")
    if df_dep.empty or "DPTO_label" not in df_dep.columns:
        placeholder(
            "El comparativo departamental aparecerá al regenerar el parquet<br>"
            "con la dimensión <code>departamento</code> en <code>src/etl.py</code>.",
            "🗺️",
        )
    else:
        dep = (
            df_dep.sort_values("periodo")
            .groupby("DPTO_label", as_index=False)[["TD", "TO"]]
            .last()
        )
        left, right = st.columns(2, gap="large")
        with left:
            d = dep.sort_values("TD", ascending=False).head(12).sort_values("TD")
            d["txt"] = d["TD"].map(lambda x: f"{x:.1f}%")
            fig = px.bar(
                d, x="TD", y="DPTO_label", orientation="h",
                text="txt", color="TD",
                color_continuous_scale=BLUE_TEAL_SCALE,
            )
            fig = fig_base_h(fig, "Mayor desempleo (TD)", "Top 12 departamentos · ascendente")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_coloraxes(showscale=False)
            fig.update_xaxes(ticksuffix="%")
            fig.update_layout(height=max(420, len(d) * 32 + 150))
            st.plotly_chart(fig, use_container_width=True)
        with right:
            d2 = dep.sort_values("TO").head(12).sort_values("TO", ascending=False)
            d2["txt"] = d2["TO"].map(lambda x: f"{x:.1f}%")
            fig = px.bar(
                d2, x="TO", y="DPTO_label", orientation="h",
                text="txt", color="TO",
                color_continuous_scale=BLUE_TEAL_SCALE,
            )
            fig = fig_base_h(fig, "Menor ocupación (TO)", "12 departamentos con menor TO · descendente")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_coloraxes(showscale=False)
            fig.update_xaxes(ticksuffix="%")
            fig.update_layout(height=max(420, len(d2) * 32 + 150))
            st.plotly_chart(fig, use_container_width=True)

    if not df_dep.empty and "DPTO_label" in df_dep.columns:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        render_section("Mapa regional", "Cambia el indicador para ver la geografía del mercado")
        render_map_module(df_dep, "TD", "resumen", "")

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
def view_caracterizacion(df_sx_age, df_edu, df_civil, df_sexo, df_clase, geo_level, geo_sel):
    t = ACTIVE_THEME
    if geo_level != "Sin filtro":
        st.markdown(
            "<div class='placeholder-card' style='margin-bottom:0.7rem'>ℹ️ "
            "El filtro territorial aún no modifica las vistas demográficas porque el parquet "
            "no guarda cruces <em>geografía × demografía</em>. Aplicar en próxima versión del ETL."
            "</div>",
            unsafe_allow_html=True,
        )

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
            )
            fig = fig_base_h(fig, "Población por nivel educativo", "Promedio del periodo · P3042")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_layout(height=max(360, len(edu) * 34 + 140))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    render_section("Composición por estado civil, sexo y clase", "Distribuciones relativas · promedio del periodo")
    a, b, c = st.columns(3, gap="small")

    with a:
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
            )
            fig = fig_base_h(fig, "Estado civil", "P6070 · promedio del periodo")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_layout(height=max(340, len(civil) * 38 + 140))
            st.plotly_chart(fig, use_container_width=True)

    with b:
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

    with c:
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


# ---------------------------------------------------------------------------
# Vista 3: Mercado de ocupados
# ---------------------------------------------------------------------------
def view_ocupados(df_context, df_sector, df_sx_age, df_pos, df_city, df_edu, context_label, geo_level):
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
            )
            fig = fig_base_h(fig, "Ocupados por rama de actividad", "CIIU Rev.4 a 2 dígitos · menor a mayor")
            fig.update_traces(
                textposition="outside", cliponaxis=False, marker_line_width=0,
                hovertemplate="<b>%{y}</b><br>%{x:,.0f} ocupados<extra></extra>",
            )
            fig.update_layout(height=max(420, len(sec) * 30 + 150))
            st.plotly_chart(fig, use_container_width=True)
    with right:
        plot_pyramid(df_sx_age, "ocupados_exp", "Pirámide de ocupados", "Por sexo y grupo de edad · P3271 × P6040")

    if geo_level != "Sin filtro":
        st.markdown(
            "<div class='placeholder-card' style='margin:0.5rem 0'>ℹ️ "
            "Pirámidas y cruces educación/posición permanecen nacionales hasta ampliar el ETL "
            "con dimensiones geo-demográficas."
            "</div>",
            unsafe_allow_html=True,
        )

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
        )
        fig = fig_base_h(fig, "Tasa de informalidad por rama", "Top 10 · menor a mayor · DANE 2022")
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        fig.update_xaxes(ticksuffix="%")
        fig.update_layout(height=max(380, len(inf_sec) * 34 + 140))
        st.plotly_chart(fig, use_container_width=True)
        
        render_interpretation(
            "La informalidad laboral en Colombia es estructural: oscila entre 55% y 60% a nivel nacional. "
            "La concentración crítica está en agricultura, ganadería y comercio menor, donde la falta de "
            "afiliación al sistema contributivo es la norma. Cualquier política de formalización debe "
            "atacar primero estos sectores.",
            title="Lectura de informalidad",
        )

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
            )
            fig = fig_base_h(fig, "Posición ocupacional", "P6430 · menor a mayor")
            fig.update_traces(
                textposition="outside", cliponaxis=False, marker_line_width=0,
                hovertemplate="<b>%{customdata[0]}</b><br>%{x:,.0f} ocupados<extra></extra>"
            )
            fig.update_layout(
                margin=dict(l=200, r=34, t=74, b=52),
                height=max(380, len(pos) * 38 + 140),
            )
            fig.update_yaxes(tickfont=dict(size=11))
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
            )
            fig = fig_base_h(fig, "Ocupados por ciudad", "Top 12 áreas metropolitanas · menor a mayor")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_coloraxes(showscale=False)
            fig.update_layout(height=max(380, len(city) * 32 + 140))
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
                         color_discrete_sequence=[BT_BLUE])
            fig = fig_base_h(fig, "Ocupados por nivel educativo", "P3042 · menor a mayor")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_layout(height=max(360, len(d) * 34 + 140))
            st.plotly_chart(fig, use_container_width=True)
        with right:
            d2 = edu.sort_values("ingreso_mediano")
            d2["txt"] = d2["ingreso_mediano"].map(lambda x: f"${fmt_metric(x)}")
            fig = px.bar(d2, x="ingreso_mediano", y="P3042_label", orientation="h", text="txt",
                         color_discrete_sequence=[BT_TEAL])
            fig = fig_base_h(fig, "Ingreso mediano por nivel educativo", "COP corrientes · menor a mayor")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_xaxes(tickprefix="$", separatethousands=True)
            fig.update_layout(height=max(360, len(d2) * 34 + 140))
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


# ---------------------------------------------------------------------------
# Vista 4: Dinámica de desocupados
# ---------------------------------------------------------------------------
def view_desocupados(df_context, df_sx_age, df_city, df_edu, context_label, geo_level):
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
        with cols[2]:
            st.markdown(
                "<div class='card'>"
                "<div class='kpi-label'>Tiempo prom. de búsqueda</div>"
                "<div class='kpi-value' style='font-size:1.5rem;opacity:0.5'>Pronto</div>"
                "<div class='kpi-foot'><code>P6240</code> pendiente de agregar al parquet.</div>"
                "</div>",
                unsafe_allow_html=True,
            )

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
            )
            fig = fig_base_h(fig, "Desocupados por ciudad", "Top 12 áreas metropolitanas · menor a mayor")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_coloraxes(showscale=False)
            fig.update_layout(height=max(380, len(city) * 32 + 140))
            st.plotly_chart(fig, use_container_width=True)

    if geo_level != "Sin filtro":
        st.markdown(
            "<div class='placeholder-card' style='margin:0.5rem 0'>ℹ️ "
            "Pirámide y educación permanecen nacionales hasta ampliar el ETL con cruces geo-demográficos.</div>",
            unsafe_allow_html=True,
        )

    if not df_edu.empty and "P3042_label" in df_edu.columns:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        render_section("Desocupados por nivel educativo", "P3042 · promedio del periodo seleccionado")
        edu = df_edu.groupby("P3042_label", as_index=False)["desocupados_exp"].mean().sort_values("desocupados_exp")
        edu["txt"] = edu["desocupados_exp"].map(fmt_metric)
        fig = px.bar(
            edu, x="desocupados_exp", y="P3042_label", orientation="h",
            text="txt",
            color_discrete_sequence=[BT_TEAL],
        )
        fig = fig_base_h(fig, "Desocupados por nivel educativo", "P3042 · menor a mayor")
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        fig.update_layout(height=max(360, len(edu) * 34 + 140))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        placeholder("Educación de desocupados sin datos. Agregar <code>P3042</code> al ETL.", "📚")

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
def view_brechas(df_sexo, df_edad_brecha, df_dep, df_nac, geo_level):
    t = ACTIVE_THEME
    if geo_level != "Sin filtro":
        st.markdown(
            "<div class='placeholder-card' style='margin-bottom:0.7rem'>ℹ️ "
            "Brecha de género y edad son nacionales en esta versión. "
            "El filtro territorial ya impacta el comparativo departamental.</div>",
            unsafe_allow_html=True,
        )

    render_section("Brechas estructurales", "Diferencias por sexo y por cohorte de edad en la TD")
    left, right = st.columns(2, gap="large")

    with left:
        if df_sexo.empty or "P3271_label" not in df_sexo.columns:
            placeholder("Sin datos de brecha de género.", "⚧")
        else:
            serie = df_sexo.groupby(["periodo", "P3271_label"], as_index=False)["TD"].mean()
            fig = px.line(
                serie, x="periodo", y="TD", color="P3271_label",
                color_discrete_map=SEX_COLORS,
                line_shape="spline",
            )
            fig = fig_base(fig, "Brecha de género en TD", "Serie mensual · Mujer vs. Hombre")
            fig.update_traces(
                line=dict(width=2.5),
                hovertemplate="<b>%{fullData.name}</b><br>TD: %{y:.1f}%<br>%{x|%b %Y}<extra></extra>",
            )
            fig.update_xaxes(tickformat="%b %Y", dtick="M3")
            fig.update_yaxes(ticksuffix="%")
            st.plotly_chart(fig, use_container_width=True)

    with right:
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
            )
            fig = fig_base(fig, "Brecha etaria en TD", "Jóvenes 15-28 vs. Adultos 29+")
            fig.update_traces(textposition="outside", marker_line_width=0)
            fig.update_xaxes(title_text="")
            fig.update_yaxes(ticksuffix="%")
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    render_interpretation(
        "La <b>TD femenina</b> es sistemáticamente superior a la masculina en todo el periodo: la diferencia "
        "promedia entre 3 y 5 puntos porcentuales. La <b>brecha etaria</b> es aún más severa: la TD juvenil "
        "(15-28) duplica con frecuencia a la de los mayores de 29, evidenciando barreras de entrada al primer "
        "empleo formal. Ambas brechas deben leerse junto con la TGP, no aisladas de la inactividad por desaliento.",
        title="Lectura de brechas",
    )

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
        )
        fig = fig_base_h(fig, "Brecha departamental vs. nacional", f"Referencia nacional: {nacional_td:.1f}% · menor a mayor")
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        fig.update_coloraxes(showscale=False)
        fig.update_xaxes(ticksuffix=" pp")
        fig.add_vline(x=0, line_width=1.5, line_dash="dot", line_color=ACTIVE_THEME["muted"])
        fig.update_layout(height=max(520, len(dep) * 24 + 160))
        st.plotly_chart(fig, use_container_width=True)

    if not df_dep.empty and "DPTO_label" in df_dep.columns:
        st.markdown("<div class='section-gap-lg'></div>", unsafe_allow_html=True)
        render_section("Mapa de distribución regional", "Selecciona el indicador que quieres comparar por departamento")
        render_map_module(df_dep, "TD", "brechas", "")

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

    st.markdown(
        f"""
        <div style="margin-bottom:1.1rem">
          <div class="topbar-title" style="font-size:1.85rem; margin-bottom:0.35rem;">
            Cómo leer este tablero
          </div>
          <div class="topbar-sub" style="max-width:62rem;">
            Una guía corta para que cualquier lector — facultad, decanatura, periodista económico
            o analista de política — extraiga decisiones útiles en menos de cinco minutos.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Bloque 1: filtros y mapa de vistas
    render_section("1 · Filtros y vistas", "Cómo orientarte en el dashboard")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(
            f"""
            <div class='mini-card'>
              <div class='mini-label' style='color:{BT_DEEP}'>Filtros globales</div>
              <ul style='color:{t["soft_text"]}; line-height:1.6; margin:0.4rem 0 0 1rem; padding:0;'>
                <li><b>Periodo:</b> selecciona el año o "Todos" para ver la serie completa.</li>
                <li><b>Nivel territorial:</b> elige Departamento o Ciudad para enfocar el contexto.</li>
                <li><b>Ubicación:</b> aparece según el nivel anterior (32 dptos. o 23 áreas metropolitanas).</li>
              </ul>
              <div class='mini-foot' style='margin-top:0.55rem'>
                Las vistas <b>Guía Usuario</b> y <b>Metodología</b> no usan filtros: son material de referencia.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class='mini-card'>
              <div class='mini-label' style='color:{BT_DEEP}'>Las 5 vistas analíticas</div>
              <ul style='color:{t["soft_text"]}; line-height:1.6; margin:0.4rem 0 0 1rem; padding:0;'>
                <li><b>Resumen:</b> KPIs nacionales, tendencia mensual y mapa territorial.</li>
                <li><b>Población:</b> pirámide, educación, estado civil, urbano/rural.</li>
                <li><b>Ocupados:</b> sectores, informalidad, ciudades e ingreso por educación.</li>
                <li><b>Desocupados:</b> perfil del desempleo por sexo, edad, ciudad y nivel educativo.</li>
                <li><b>Brechas:</b> género, edad 15-28 vs 29+, comparativa departamental vs. nacional.</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Bloque 2: glosario rápido de indicadores
    render_section("2 · Indicadores en 30 segundos", "Definiciones operativas DANE / OIT")
    g1, g2, g3 = st.columns(3, gap="medium")
    glossary = [
        (g1, "TD", "Tasa de desempleo", "Desocupados ÷ PEA × 100", "Mide cuántos de los que buscan trabajo no lo encuentran."),
        (g2, "TO", "Tasa de ocupación", "Ocupados ÷ PET × 100", "Qué proporción de la población en edad de trabajar tiene empleo."),
        (g3, "TGP", "Tasa global de participación", "Fuerza de trabajo ÷ PET × 100", "Cuántas personas en edad de trabajar están activas (trabajando o buscando)."),
    ]
    for col, code, name, formula, desc in glossary:
        with col:
            st.markdown(
                f"""
                <div class='mini-card'>
                  <div style='display:flex; align-items:baseline; gap:0.55rem; margin-bottom:0.35rem;'>
                    <div class='display-serif' style='font-size:1.7rem; font-weight:700; color:{BT_DEEP};'>{code}</div>
                    <div style='color:{t["text"]}; font-weight:700; font-size:0.95rem;'>{name}</div>
                  </div>
                  <code style='background:{t["input_bg"]}; padding:0.2rem 0.45rem; border-radius:5px; font-size:0.8rem; color:{t["text"]}'>{formula}</code>
                  <div class='mini-foot' style='margin-top:0.55rem;'>{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    g4, g5, g6 = st.columns(3, gap="medium")
    glossary2 = [
        (g4, "Informalidad", "Tasa de informalidad", "Informales ÷ Ocupados × 100", "Trabajadores sin afiliación al sistema contributivo (regla DANE 2022)."),
        (g5, "Ingreso mediano", "Mediana ponderada", "P6500 entre ocupados", "El valor del trabajador del medio: más robusto que el promedio."),
        (g6, "FEX_C18", "Factor de expansión", "Peso muestral", "Convierte cada encuestado en miles de personas representadas."),
    ]
    for col, code, name, formula, desc in glossary2:
        with col:
            st.markdown(
                f"""
                <div class='mini-card'>
                  <div style='display:flex; align-items:baseline; gap:0.55rem; margin-bottom:0.35rem;'>
                    <div class='display-serif' style='font-size:1.4rem; font-weight:700; color:{BT_DEEP};'>{code}</div>
                  </div>
                  <div style='color:{t["text"]}; font-weight:700; font-size:0.92rem; margin-bottom:0.3rem;'>{name}</div>
                  <code style='background:{t["input_bg"]}; padding:0.2rem 0.45rem; border-radius:5px; font-size:0.8rem; color:{t["text"]}'>{formula}</code>
                  <div class='mini-foot' style='margin-top:0.55rem;'>{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Bloque 3: rutas de lectura por perfil
    render_section("3 · Rutas de lectura por perfil", "Por dónde empezar según tu rol")

    rutas = [
        (
            "Facultades técnicas e ingeniería",
            "STEM, formación dual, oferta académica",
            [
                "<b>Ocupados → Estructura sectorial:</b> identifica si Información, Comunicaciones y Manufactura crecen o se contraen.",
                "<b>Brechas → Brecha de género:</b> evalúa retención de mujeres en sectores intensivos en ingeniería.",
                "<b>Ocupados → Educación e ingresos:</b> compara el retorno salarial del nivel universitario vs. técnico.",
            ],
        ),
        (
            "Ciencias sociales, salud y humanidades",
            "Política pública, salud, derecho, economía",
            [
                "<b>Ocupados → Informalidad:</b> identifica los sectores donde la prestación de servicios sustituye al contrato laboral.",
                "<b>Brechas → Comparativa regional:</b> mide la heterogeneidad territorial del mercado laboral.",
                "<b>Desocupados → Educación:</b> mide la subutilización del capital humano universitario.",
            ],
        ),
        (
            "Decanaturas y dirección de programa",
            "Diseño curricular, convenios, planeación",
            [
                "<b>Brechas → Brecha etaria 15-28 vs 29+:</b> sustenta convenios de Primer Empleo y prácticas tempranas.",
                "<b>Desocupados → Pirámide:</b> distingue entre desempleo abierto e inactividad por desaliento (clave en mujeres jóvenes).",
                "<b>Resumen → Mapa regional:</b> prioriza territorios para extensión universitaria.",
            ],
        ),
        (
            "Periodismo económico y consultoría",
            "Notas, informes, asesoría a empresa o gobierno",
            [
                "<b>Resumen → Tendencia laboral:</b> identifica quiebres y comparaciones interanuales.",
                "<b>Brechas → Mapa regional:</b> base territorial para reportajes con enfoque local.",
                "<b>Metodología:</b> referencias técnicas para citar correctamente las cifras.",
            ],
        ),
    ]
    for i in range(0, len(rutas), 2):
        cols = st.columns(2, gap="large")
        for j, col in enumerate(cols):
            if i + j >= len(rutas):
                break
            title, sub, items = rutas[i + j]
            li_html = "".join(f"<li style='margin-bottom:0.4rem;'>{x}</li>" for x in items)
            with col:
                st.markdown(
                    f"""
                    <div class='mini-card' style='margin-bottom:0.85rem;'>
                      <div style='display:flex; align-items:baseline; gap:0.5rem; margin-bottom:0.15rem;'>
                        <div class='display-serif' style='font-size:1.2rem; font-weight:600; color:{t["text"]};'>{title}</div>
                      </div>
                      <div class='mini-foot' style='margin-top:0; margin-bottom:0.6rem;'>{sub}</div>
                      <ul style='color:{t["soft_text"]}; line-height:1.55; margin:0 0 0 1rem; padding:0; font-size:0.92rem;'>
                        {li_html}
                      </ul>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Bloque 4: tips de lectura
    render_section("4 · Buenas prácticas al interpretar", "Reglas para no malinterpretar las cifras")
    st.markdown(
        f"""
        <div class='interpretation-block'>
          <div class='interpretation-title'>Cinco reglas básicas</div>
          <div class='interpretation-text'>
            <ol style='margin:0.4rem 0 0 1.1rem; padding:0; line-height:1.65;'>
              <li><b>TD baja no es siempre buena:</b> puede caer porque la gente deja de buscar empleo (sale de la PEA), no porque encuentre trabajo. Léela junto a la TGP.</li>
              <li><b>Los KPIs son del último mes disponible:</b> el delta vs. periodo anterior compara mes vs. mes inmediato.</li>
              <li><b>El ingreso es mediano, no promedio:</b> la mediana es robusta a outliers (millonarios o salarios muy bajos no la sesgan).</li>
              <li><b>Toda cifra está expandida:</b> son personas representadas, no encuestadas. El factor es <code>FEX_C18</code>.</li>
              <li><b>Las brechas son persistentes:</b> género, edad y geografía cambian poco mes a mes. Si ves un quiebre brusco, sospecha del dato antes que del fenómeno.</li>
            </ol>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def view_metodologia(df):
    t = ACTIVE_THEME
    years = sorted(df["ano"].dropna().unique().tolist()) if "ano" in df.columns else []
    year_range = f"{years[0]}–{years[-1]}" if len(years) >= 2 else (str(years[0]) if years else "s/d")

    st.markdown(
        f"""
        <div style="margin-bottom:1.1rem">
          <div class="topbar-title" style="font-size:1.85rem; margin-bottom:0.35rem;">
            Ficha técnica
          </div>
          <div class="topbar-sub" style="max-width:62rem;">
            Procesamiento de microdatos de la Gran Encuesta Integrada de Hogares (GEIH) rediseñada
            del DANE para el período <b>{year_range}</b>. Toda cifra de este dashboard es trazable
            hasta el código de variable original.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Bloque 1: parámetros técnicos
    render_section("Parámetros estadísticos", "Lo que necesitas saber antes de citar")
    c1, c2, c3, c4 = st.columns(4, gap="small")
    for col, label, val, foot in [
        (c1, "Fuente", "DANE GEIH", "Encuesta rediseñada (2022). Bases anuales consolidadas."),
        (c2, "Marco muestral", "Probabilístico", "Multietápico, estratificado, por conglomerados. 23 áreas metropolitanas."),
        (c3, "Precisión", "CV < 5%", "Indicadores publicados solo para niveles con suficiencia muestral."),
        (c4, "Expansión", "FEX_C18", "Factor post-rediseño 2022. Toda cifra está expandida a personas."),
    ]:
        with col:
            st.markdown(
                f"<div class='card'>"
                f"<div class='kpi-label'>{label}</div>"
                f"<div class='mini-value' style='font-size:1.3rem'>{val}</div>"
                f"<div class='kpi-foot'>{foot}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # Bloque 2: cobertura del dataset (un solo gráfico, ya no dos)
    render_section("Cobertura procesada", f"Registros agregados por dimensión analítica · {year_range}")
    coverage = (
        df.groupby("dimension", as_index=False)
        .size()
        .rename(columns={"size": "registros"})
        .sort_values("registros")
    )
    coverage["dimension_label"] = coverage["dimension"].str.replace("_", " ").str.title()
    fig = px.bar(
        coverage,
        x="registros",
        y="dimension_label",
        orientation="h",
        color="registros",
        color_continuous_scale=BLUE_TEAL_SCALE,
        text=coverage["registros"].map(lambda x: f"{x:,.0f}"),
    )
    fig = fig_base_h(fig, "Filas agregadas por dimensión", "Cada barra es una tabla independiente del parquet")
    fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(title_text="Registros")
    fig.update_yaxes(title_text="")
    fig.update_layout(height=max(360, len(coverage) * 28 + 130), margin=dict(l=146, r=34, t=90, b=48))
    st.plotly_chart(fig, use_container_width=True)

    # Bloque 3: definiciones operativas
    render_section("Definiciones operativas (OIT / DANE)", "Cómo entender los términos técnicos")
    defs = [
        ("PET", "Población en edad de trabajar", "Personas de 15 años o más (criterio DANE post-2022)."),
        ("PEA / FT", "Población económicamente activa", "Ocupados + desocupados. La 'fuerza de trabajo' del país."),
        ("OCI", "Ocupados", "Personas que trabajaron al menos una hora remunerada o sin remuneración en la semana de referencia."),
        ("DSI", "Desocupados", "Personas sin empleo que realizaron búsqueda activa y están disponibles."),
        ("FFT", "Fuera de fuerza de trabajo", "Personas en edad de trabajar que ni trabajan ni buscan: estudiantes, hogar, jubilados, desalentados."),
        ("Informalidad", "Tasa de informalidad (DANE 2022)", "Combina posición ocupacional, tamaño de empresa, afiliación a salud y pensión, registro mercantil, oficio y rama. Implementación en src/indicators.py."),
    ]
    cols = st.columns(2, gap="large")
    for i, (code, name, desc) in enumerate(defs):
        with cols[i % 2]:
            st.markdown(
                f"<div class='mini-card' style='margin-bottom:0.55rem; border-left: 4px solid {BT_DEEP};'>"
                f"<div style='display:flex; align-items:baseline; gap:0.55rem; margin-bottom:0.25rem;'>"
                f"  <div class='display-serif' style='font-size:1.25rem; font-weight:700; color:{BT_DEEP};'>{code}</div>"
                f"  <div style='color:{t['text']}; font-weight:700; font-size:0.92rem;'>{name}</div>"
                f"</div>"
                f"<div style='color:{t['soft_text']}; font-size:0.88rem; line-height:1.5'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # Bloque 4: trazabilidad de variables
    render_section("Trazabilidad de variables", "De qué columna del microdato sale cada cifra")
    st.markdown(
        f"""
        <div class='mini-card' style='margin-bottom:0.7rem;'>
          <table style='width:100%; border-collapse:collapse; font-size:0.88rem; color:{t["soft_text"]};'>
            <thead>
              <tr style='border-bottom:1px solid {t["line"]}; text-align:left;'>
                <th style='padding:0.5rem 0.6rem; color:{t["text"]};'>Indicador</th>
                <th style='padding:0.5rem 0.6rem; color:{t["text"]};'>Variables GEIH</th>
                <th style='padding:0.5rem 0.6rem; color:{t["text"]};'>Cálculo</th>
              </tr>
            </thead>
            <tbody>
              <tr style='border-bottom:1px solid {t["line"]};'>
                <td style='padding:0.5rem 0.6rem;'><b>TD</b></td>
                <td style='padding:0.5rem 0.6rem;'><code>OCI</code>, <code>DSI</code>, <code>FEX_C18</code></td>
                <td style='padding:0.5rem 0.6rem;'>Σ(DSI·FEX) ÷ Σ((OCI+DSI)·FEX) × 100</td>
              </tr>
              <tr style='border-bottom:1px solid {t["line"]};'>
                <td style='padding:0.5rem 0.6rem;'><b>TO</b></td>
                <td style='padding:0.5rem 0.6rem;'><code>OCI</code>, <code>P6040</code>, <code>FEX_C18</code></td>
                <td style='padding:0.5rem 0.6rem;'>Σ(OCI·FEX) ÷ Σ(PET·FEX) × 100, PET = P6040 ≥ 15</td>
              </tr>
              <tr style='border-bottom:1px solid {t["line"]};'>
                <td style='padding:0.5rem 0.6rem;'><b>TGP</b></td>
                <td style='padding:0.5rem 0.6rem;'><code>OCI</code>, <code>DSI</code>, <code>P6040</code></td>
                <td style='padding:0.5rem 0.6rem;'>Σ((OCI+DSI)·FEX) ÷ Σ(PET·FEX) × 100</td>
              </tr>
              <tr style='border-bottom:1px solid {t["line"]};'>
                <td style='padding:0.5rem 0.6rem;'><b>Informalidad</b></td>
                <td style='padding:0.5rem 0.6rem;'><code>P6430</code>, <code>P6920</code>, <code>P6090</code>, +13 más</td>
                <td style='padding:0.5rem 0.6rem;'>Regla DANE en src/indicators.py</td>
              </tr>
              <tr style='border-bottom:1px solid {t["line"]};'>
                <td style='padding:0.5rem 0.6rem;'><b>Ingreso mediano</b></td>
                <td style='padding:0.5rem 0.6rem;'><code>P6500</code>, <code>FEX_C18</code></td>
                <td style='padding:0.5rem 0.6rem;'>Mediana ponderada por FEX entre ocupados</td>
              </tr>
              <tr style='border-bottom:1px solid {t["line"]};'>
                <td style='padding:0.5rem 0.6rem;'><b>Sexo</b></td>
                <td style='padding:0.5rem 0.6rem;'><code>P3271</code></td>
                <td style='padding:0.5rem 0.6rem;'>Sexo al nacer (post-rediseño; reemplaza P6020)</td>
              </tr>
              <tr style='border-bottom:1px solid {t["line"]};'>
                <td style='padding:0.5rem 0.6rem;'><b>Edad / Pirámide</b></td>
                <td style='padding:0.5rem 0.6rem;'><code>P6040</code></td>
                <td style='padding:0.5rem 0.6rem;'>Quinquenios 15-19, 20-24 … 65+ (estándar OIT)</td>
              </tr>
              <tr>
                <td style='padding:0.5rem 0.6rem;'><b>Sector</b></td>
                <td style='padding:0.5rem 0.6rem;'><code>RAMA2D_R4</code></td>
                <td style='padding:0.5rem 0.6rem;'>CIIU Rev.4 a 2 dígitos</td>
              </tr>
            </tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Bloque 5: notas críticas
    render_section("Notas y advertencias", "Lo que debes citar al usar estas cifras")
    st.markdown(
        f"""
        <div class='interpretation-block'>
          <div class='interpretation-title'>Comparabilidad y supuestos</div>
          <div class='interpretation-text'>
            <ul style='margin:0.4rem 0 0 1.1rem; padding:0; line-height:1.65;'>
              <li><b>Ruptura de serie:</b> los datos desde 2022 <b>no son comparables</b> con series anteriores a 2021.
                  La GEIH fue rediseñada y se aplica el marco poblacional Censo 2018.</li>
              <li><b>Variable de sexo:</b> a partir de 2022 se usa <code>P3271</code> (sexo al nacer);
                  el código <code>P6020</code> del diseño anterior queda obsoleto.</li>
              <li><b>Nivel educativo:</b> se usa <code>P3042</code> en lugar de <code>P6210</code> porque
                  esta última no aparece en el encabezado de <code>geih_2025.csv</code>.</li>
              <li><b>Ingreso:</b> se reporta como mediana ponderada en pesos corrientes, sin deflactar.
                  Para series reales, ajusta por IPC fuera del dashboard.</li>
              <li><b>Granularidad:</b> el parquet está en frecuencia mensual; no se reportan trimestres móviles.</li>
              <li><b>Cita sugerida:</b> "Elaboración propia con microdatos de la GEIH-DANE,
                  ponderados con FEX_C18".</li>
            </ul>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "Dark"

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
with page_shell:
    hero_card = st.container(border=True, key="hero_filters_card")
    with hero_card:
        title_slot = st.container()
        filters_slot = st.container()
    body_slot = st.container()

# Metodología y manual no necesitan filtros — usar defaults sin renderizar el control
if vista in ("metodologia", "instrucciones"):
    anos_sel   = sorted(df_all["ano"].dropna().unique().tolist())
    geo_level  = "Sin filtro"
    geo_sel    = "Todas"
    ano_ui     = "Todos"
else:
    with filters_slot:
        ano_ui, anos_sel, geo_level, geo_sel = render_controls(df_all)

# Filtrar dimensiones
df_nac         = filtrar(df_all, "nacional",            anos_sel, geo_level, geo_sel)
df_dep         = filtrar(df_all, "departamento",        anos_sel, geo_level, geo_sel)
df_city        = filtrar(df_all, "ciudad",              anos_sel, geo_level, geo_sel)
df_sexo        = filtrar(df_all, "sexo",                anos_sel, geo_level, geo_sel)
df_sx_age      = filtrar(df_all, "sexo_edad",           anos_sel, geo_level, geo_sel)
df_edad_brecha = filtrar(df_all, "edad_brecha",         anos_sel, geo_level, geo_sel)
df_sector      = filtrar(df_all, "sector",              anos_sel, geo_level, geo_sel)
df_clase       = filtrar(df_all, "clase",               anos_sel, geo_level, geo_sel)
df_civil       = filtrar(df_all, "estado_civil",        anos_sel, geo_level, geo_sel)
df_edu         = filtrar(df_all, "educacion",           anos_sel, geo_level, geo_sel)
df_pos         = filtrar(df_all, "posicion_ocupacional", anos_sel, geo_level, geo_sel)

if df_nac.empty:
    st.warning("No hay datos nacionales para los filtros seleccionados. Relaja los filtros o regenera el parquet.")
    st.stop()

ultimo       = latest_row(df_nac)
df_context   = active_context_df(df_nac, df_dep, df_city, geo_level, geo_sel)
context_label = active_context_label(geo_level, geo_sel)

with title_slot:
    render_header(vista, ultimo["periodo"].strftime("%B %Y").capitalize(), context_label)

with body_slot:
    if vista not in ("metodologia", "instrucciones"):
        render_filters_summary(ano_ui, geo_level, geo_sel)
        st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)

    if vista == "resumen":
        view_resumen(df_context, df_dep, context_label)
    elif vista == "poblacion":
        view_caracterizacion(df_sx_age, df_edu, df_civil, df_sexo, df_clase, geo_level, geo_sel)
    elif vista == "ocupados":
        view_ocupados(df_context, df_sector, df_sx_age, df_pos, df_city, df_edu, context_label, geo_level)
    elif vista == "desocupados":
        view_desocupados(df_context, df_sx_age, df_city, df_edu, context_label, geo_level)
    elif vista == "brechas":
        view_brechas(df_sexo, df_edad_brecha, df_dep, df_nac, geo_level)
    elif vista == "instrucciones":
        view_instrucciones(df_nac, df_dep)
    else:
        view_metodologia(df_all)

st.divider()
st.caption("Daniel Molina · Economista & Data Scientist · Fuente: DANE — Gran Encuesta Integrada de Hogares (GEIH)")
