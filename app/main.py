"""
Dashboard GEIH 2022-2025 — Mercado Laboral Colombiano.
"""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
# Paleta y temas
# ---------------------------------------------------------------------------
THEMES = {
    "Dark": {
        "accent": "#7C3AED",
        "accent_2": "#06B6D4",
        "accent_3": "#F59E0B",
        "positive": "#10B981",
        "negative": "#F43F5E",
        "text": "#F1F5F9",
        "muted": "#94A3B8",
        "line": "rgba(255,255,255,0.07)",
        "app_bg": "linear-gradient(160deg, #080c1a 0%, #07091a 60%, #04060f 100%)",
        "sidebar_bg": "rgba(10,14,28,0.98)",
        "panel_bg": "rgba(15,21,40,0.92)",
        "panel_solid": "rgba(12,18,35,0.98)",
        "soft_text": "#CBD5E1",
        "eyebrow_bg": "rgba(124,58,237,0.16)",
        "eyebrow_text": "#c4b5fd",
        "input_bg": "rgba(255,255,255,0.04)",
        "chart_grid": "rgba(255,255,255,0.05)",
        "chart_bg": "rgba(0,0,0,0)",
    },
    "Light": {
        "accent": "#6D28D9",
        "accent_2": "#0284C7",
        "accent_3": "#D97706",
        "positive": "#059669",
        "negative": "#E11D48",
        "text": "#0F172A",
        "muted": "#64748B",
        "line": "rgba(15,23,42,0.09)",
        "app_bg": "linear-gradient(160deg, #f8fafc 0%, #eef2ff 50%, #f8fafc 100%)",
        "sidebar_bg": "rgba(255,255,255,0.98)",
        "panel_bg": "rgba(255,255,255,0.92)",
        "panel_solid": "rgba(255,255,255,0.98)",
        "soft_text": "#334155",
        "eyebrow_bg": "rgba(109,40,217,0.08)",
        "eyebrow_text": "#6D28D9",
        "input_bg": "rgba(15,23,42,0.03)",
        "chart_grid": "rgba(0,0,0,0.05)",
        "chart_bg": "rgba(0,0,0,0)",
    },
}

ACTIVE_THEME = THEMES["Dark"]

AGE_ORDER = ["65+", "55-64", "45-54", "35-44", "25-34", "15-24"]

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

# Gradiente de colores para barras múltiples
BAR_COLORS_DARK = [
    "#7C3AED", "#6D28D9", "#5B21B6", "#4C1D95",
    "#06B6D4", "#0891B2", "#0E7490", "#155E75",
]
BAR_COLORS_LIGHT = [
    "#6D28D9", "#7C3AED", "#8B5CF6", "#A78BFA",
    "#0284C7", "#0369A1", "#075985", "#0C4A6E",
]


# ---------------------------------------------------------------------------
# Estilos globales
# ---------------------------------------------------------------------------
def inject_styles(theme_name: str) -> None:
    t = THEMES[theme_name]
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');

        html, body, [class*="css"] {{
            font-family: "IBM Plex Sans", system-ui, sans-serif;
            color: {t['text']};
        }}

        /* Fondo app */
        .stApp {{ background: {t['app_bg']}; }}

        /* Ocultar sidebar nativo, header y botones Streamlit */
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"],
        .stAppDeployButton,
        [data-testid="stSidebar"],
        [data-testid="stSidebarContent"],
        section[data-testid="stSidebar"] > div {{
            display: none !important;
            width: 0 !important;
            min-width: 0 !important;
        }}
        /* Eliminar el header nativo y su espacio */
        header[data-testid="stHeader"] {{
            display: none !important;
            height: 0 !important;
        }}
        /* Usar toda la pantalla — quitar márgenes de Streamlit */
        .block-container,
        [data-testid="stAppViewContainer"] > section > div.block-container {{
            padding-top: 0.75rem !important;
            padding-bottom: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }}
        /* Forzar que el app view ocupe el 100% */
        [data-testid="stAppViewContainer"] {{
            padding: 0 !important;
        }}
        [data-testid="stAppViewContainer"] > section {{
            padding: 0 !important;
            max-width: 100% !important;
            width: 100% !important;
        }}
        /* Sidebar fija: position fixed + ancho determinista */
        .app-shell-nav {{
            position: fixed !important;
            top: 0.75rem !important;
            bottom: 0.75rem !important;
            left: 1rem !important;
            width: 230px !important;
            z-index: 200 !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
        }}
        /* La columna del nav se colapsa (el nav está fuera del flujo) */
        [data-testid="stColumn"]:first-child {{
            flex: 0 0 246px !important;
            min-width: 246px !important;
            max-width: 246px !important;
            visibility: hidden !important;
        }}
        /* La columna de contenido ocupa el resto */
        [data-testid="stHorizontalBlock"] {{
            align-items: flex-start !important;
        }}
        /* Quitar puntos/bullets de cualquier lista dentro del nav */
        .app-shell-nav ul, .app-shell-nav li,
        .app-shell-nav nav {{ list-style: none !important; margin: 0 !important; padding: 0 !important; }}
        /* Quitar puntos que Streamlit puede agregar en columnas */
        [data-testid="stColumn"] > div > ul,
        [data-testid="stColumn"] > div > li {{ list-style: none !important; }}

        /* ---------- Panel de navegacion lateral ---------- */
        .app-shell-nav {{
            background: {t['sidebar_bg']};
            border: 1px solid {t['line']};
            border-radius: 22px;
            padding: 0;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}

        /* Cabecera del nav */
        .nav-header {{
            display: flex;
            align-items: center;
            gap: 0.7rem;
            padding: 1rem 0.9rem 0.9rem;
            border-bottom: 1px solid {t['line']};
        }}
        .nav-logo-box {{
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: {t['eyebrow_bg']};
            border: 1px solid rgba(124,58,237,0.28);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}
        .nav-logo-initials {{
            font-size: 1rem;
            font-weight: 800;
            color: {t['eyebrow_text']};
            letter-spacing: -0.03em;
        }}
        .nav-title-block {{ min-width: 0; }}
        .nav-title {{
            color: {t['text']};
            font-size: 0.92rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            line-height: 1.2;
        }}
        .nav-subtitle {{
            color: {t['muted']};
            font-size: 0.62rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-top: 0.1rem;
        }}

        /* Cuerpo del nav — crece para empujar footer al fondo */
        .nav-body {{ padding: 0.7rem 0.65rem 0.55rem; flex: 1; }}
        .sidebar-section {{
            color: {t['muted']};
            font-size: 0.63rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.13em;
            margin: 0 0.3rem 0.5rem;
            opacity: 0.65;
        }}

        /* Items de navegacion — links HTML puros */
        .nav-item {{
            display: flex;
            align-items: center;
            gap: 0.8rem;
            padding: 0.78rem 0.9rem;
            border-radius: 14px;
            margin-bottom: 0.1rem;
            text-decoration: none !important;
            color: {t['muted']} !important;
            font-size: 0.95rem;
            font-weight: 500;
            transition: background 0.12s ease, color 0.12s ease;
            cursor: pointer;
        }}
        .nav-item:hover {{
            background: {t['input_bg']};
            color: {t['soft_text']} !important;
            text-decoration: none !important;
        }}
        .nav-item.active {{
            background: {"#FFFFFF" if theme_name == "Dark" else t['accent']} !important;
            color: {"#0F172A" if theme_name == "Dark" else "#FFFFFF"} !important;
            font-weight: 600;
            box-shadow: {"0 2px 14px rgba(0,0,0,0.3)" if theme_name == "Dark" else "0 2px 12px rgba(109,40,217,0.25)"};
        }}
        .nav-item .nav-icon {{
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            opacity: 0.5;
        }}
        .nav-item:hover .nav-icon {{ opacity: 0.85; }}
        .nav-item.active .nav-icon {{ opacity: 1; }}
        .nav-item-label {{ line-height: 1; }}

        /* Footer del nav — toggle de tema (botón Streamlit estilizado) */
        .nav-footer {{
            border-top: 1px solid {t['line']};
            padding: 0.6rem 0.65rem 0.75rem;
        }}
        .nav-footer .stButton > button {{
            display: flex !important;
            align-items: center !important;
            gap: 0.5rem !important;
            width: 100% !important;
            padding: 0.62rem 0.9rem !important;
            border-radius: 13px !important;
            background: {t['input_bg']} !important;
            border: 1px solid {t['line']} !important;
            color: {t['muted']} !important;
            font-size: 0.88rem !important;
            font-weight: 500 !important;
            text-align: left !important;
            box-shadow: none !important;
            transition: background 0.12s ease, color 0.12s ease !important;
        }}
        .nav-footer .stButton > button:hover {{
            background: {t['panel_bg']} !important;
            color: {t['soft_text']} !important;
            border-color: {t['accent']} !important;
        }}
        /* Ocultar radio nativo residual de Streamlit */
        .app-shell-nav [role="radiogroup"],
        .app-shell-nav [data-baseweb="radio-group"] {{
            display: none !important;
        }}

        /* Footer del nav — 3 íconos en fila */
        .nav-footer {{
            border-top: 1px solid {t['line']};
            padding: 0.75rem 0.65rem 0.85rem;
            display: flex;
            gap: 0.45rem;
            align-items: center;
        }}
        .nav-icon-btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex: 1;
            height: 40px;
            border-radius: 12px;
            border: 1px solid {t['line']};
            background: {t['input_bg']};
            color: {t['muted']} !important;
            text-decoration: none !important;
            font-size: 0.82rem;
            font-weight: 700;
            transition: all 0.13s ease;
            cursor: pointer;
        }}
        .nav-icon-btn:hover {{
            border-color: {t['accent']};
            color: {t['soft_text']} !important;
            background: {t['panel_bg']};
        }}

        /* ---------- Topbar / cabecera de vista ---------- */
        .topbar {{
            background: {t['panel_bg']};
            border: 1px solid {t['line']};
            border-radius: 18px;
            padding: 0.9rem 1.1rem 0.85rem;
            margin-bottom: 0.4rem;
        }}
        .topbar-icon {{
            font-size: 1.4rem;
            margin-right: 0.55rem;
            vertical-align: middle;
        }}
        .topbar-title {{
            color: {t['text']};
            font-size: 1.12rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            vertical-align: middle;
        }}
        .topbar-sub {{
            color: {t['muted']};
            font-size: 0.82rem;
            margin-top: 0.18rem;
            line-height: 1.35;
        }}

        /* ---------- Control bar / filtros ---------- */
        .control-bar {{
            background: {t['panel_bg']};
            border: 1px solid {t['line']};
            border-radius: 18px;
            padding: 0.65rem 0.9rem;
            margin-bottom: 0.5rem;
        }}
        .control-title {{
            color: {t['muted']};
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.45rem;
        }}

        /* ---------- Chips de filtros activos ---------- */
        .pill-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin: 0.3rem 0 0.15rem;
        }}
        .pill {{
            background: {t['input_bg']};
            border: 1px solid {t['line']};
            border-radius: 999px;
            padding: 0.28rem 0.65rem;
            color: {t['soft_text']};
            font-size: 0.78rem;
        }}

        /* ---------- Tarjetas KPI grandes ---------- */
        .card {{
            background: {t['panel_bg']};
            border: 1px solid {t['line']};
            border-radius: 18px;
            padding: 1.1rem 1rem 1rem;
        }}
        .kpi-label {{
            color: {t['muted']};
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.4rem;
        }}
        .kpi-value {{
            color: {t['text']};
            font-size: 2.4rem;
            font-weight: 700;
            letter-spacing: -0.04em;
            line-height: 1.05;
            word-break: normal;
            overflow-wrap: anywhere;
        }}
        .kpi-delta {{
            display: inline-flex;
            align-items: center;
            gap: 0.2rem;
            font-size: 0.83rem;
            font-weight: 600;
            margin-top: 0.35rem;
            padding: 0.2rem 0.5rem;
            border-radius: 999px;
        }}
        .kpi-delta.up {{
            background: rgba(16,185,129,0.14);
            color: {t['positive']};
        }}
        .kpi-delta.down {{
            background: rgba(244,63,94,0.14);
            color: {t['negative']};
        }}
        .kpi-delta.neutral {{
            background: {t['input_bg']};
            color: {t['muted']};
        }}
        .kpi-foot {{
            color: {t['muted']};
            font-size: 0.82rem;
            margin-top: 0.5rem;
            line-height: 1.45;
        }}

        /* ---------- Tarjetas mini ---------- */
        .mini-card {{
            background: {t['panel_bg']};
            border: 1px solid {t['line']};
            border-radius: 16px;
            padding: 0.95rem 1rem;
        }}
        .mini-label {{
            color: {t['muted']};
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}
        .mini-value {{
            color: {t['text']};
            font-size: 1.55rem;
            font-weight: 700;
            margin-top: 0.35rem;
            letter-spacing: -0.03em;
        }}
        .mini-foot {{
            color: {t['muted']};
            font-size: 0.82rem;
            margin-top: 0.4rem;
            line-height: 1.4;
        }}

        /* ---------- Encabezados de sección ---------- */
        .section-header {{
            margin: 1.1rem 0 0.55rem 0;
            padding-bottom: 0.45rem;
            border-bottom: 1px solid {t['line']};
        }}
        .section-header-title {{
            color: {t['text']};
            font-size: 0.95rem;
            font-weight: 600;
            letter-spacing: -0.02em;
        }}
        .section-header-sub {{
            color: {t['muted']};
            font-size: 0.8rem;
            margin-top: 0.12rem;
        }}

        /* ---------- Placeholder para datos faltantes ---------- */
        .placeholder-card {{
            background: {t['input_bg']};
            border: 1px dashed {t['line']};
            border-radius: 16px;
            padding: 1.2rem 1rem;
            text-align: center;
            color: {t['muted']};
            font-size: 0.86rem;
            line-height: 1.5;
        }}
        .placeholder-card .placeholder-icon {{
            font-size: 1.6rem;
            display: block;
            margin-bottom: 0.45rem;
            opacity: 0.6;
        }}

        /* ---------- Contexto activo ---------- */
        .context-label {{
            color: {t['muted']};
            font-size: 0.9rem;
            margin: 0.1rem 0 0.55rem 0;
        }}
        .context-label strong {{
            color: {t['soft_text']};
        }}

        /* ---------- Spacers ---------- */
        .section-gap {{ height: 0.5rem; }}
        .section-gap-lg {{ height: 1rem; }}

        /* ---------- Charts ---------- */
        .stPlotlyChart > div {{
            border-radius: 16px;
            overflow: hidden;
        }}

        @media (max-width: 1100px) {{
            .kpi-value {{ font-size: 1.9rem; }}
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
        font=dict(color=t["text"], family="IBM Plex Sans, sans-serif", size=12),
        title=dict(
            text=full_title,
            font=dict(color=t["text"], size=13, weight=600),
            x=0.0,
            xanchor="left",
            pad=dict(l=4),
        ),
        margin=dict(l=10, r=10, t=52 if full_title else 18, b=10),
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
        ),
        yaxis=dict(
            gridcolor=t["chart_grid"],
            gridwidth=1,
            zeroline=False,
            linecolor="rgba(0,0,0,0)",
            tickfont=dict(color=t["soft_text"], size=11),
            title_font=dict(color=t["muted"], size=11),
        ),
        legend=dict(
            orientation="h",
            y=1.04,
            x=0,
            bgcolor="rgba(0,0,0,0)",
            title_text="",
            font=dict(color=t["soft_text"], size=11),
        ),
    )
    return fig


def fig_base_h(fig, title: str = "", subtitle: str = ""):
    """Base para gráficos horizontales (intercambia grid de ejes)."""
    fig = fig_base(fig, title, subtitle)
    fig.update_layout(
        xaxis=dict(
            gridcolor=ACTIVE_THEME["chart_grid"],
            gridwidth=1,
            zeroline=False,
            linecolor="rgba(0,0,0,0)",
            tickfont=dict(color=ACTIVE_THEME["soft_text"], size=11),
            title_font=dict(color=ACTIVE_THEME["muted"], size=11),
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            linecolor=ACTIVE_THEME["line"],
            tickfont=dict(color=ACTIVE_THEME["soft_text"], size=11),
            title_font=dict(color=ACTIVE_THEME["muted"], size=11),
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# Formateo
# ---------------------------------------------------------------------------
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
        f"""<section class='topbar'>
              <span class='topbar-title'>{label}</span>
              <div class='topbar-sub'>
                Mercado laboral colombiano · GEIH DANE &nbsp;|&nbsp; Corte: {ultimo_txt}
                &nbsp;|&nbsp; Contexto: <strong>{context_label}</strong>
              </div>
            </section>""",
        unsafe_allow_html=True,
    )


def render_side_nav() -> str:
    """Nav lateral con links HTML puros. Devuelve la clave de vista activa."""
    # Vista activa desde query params (persiste al hacer clic)
    vista = st.query_params.get("view", "resumen")
    if vista not in VIEWS:
        vista = "resumen"

    # Logo
    logo_html = "<div class='nav-logo-box'><span class='nav-logo-initials'>DM</span></div>"

    # Construir items del nav
    items_html = ""
    for key, label, icon_svg in NAV_ITEMS:
        active_cls = " active" if (vista == key) else ""
        # Preservar el query param de view al hacer clic
        items_html += (
            f"<a href='?view={key}' class='nav-item{active_cls}' target='_self'>"
            f"<span class='nav-icon'>{icon_svg}</span>"
            f"<span class='nav-item-label'>{label}</span>"
            f"</a>"
        )

    # Botón de tema (oscuro/claro) — texto según estado actual
    is_dark = st.session_state.get("theme_mode", "Dark") == "Dark"
    new_theme = "Light" if is_dark else "Dark"
    theme_label = "Cambiar a modo claro" if is_dark else "Cambiar a modo oscuro"
    # SVG luna (para cambiar a claro) y sol (para cambiar a oscuro)
    _s2 = 'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    theme_svg = (
        f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" {_s2}>'
        '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
        if is_dark else
        f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" {_s2}>'
        '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/>'
        '<line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>'
        '<line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/>'
        '<line x1="21" y1="12" x2="23" y2="12"/></svg>'
    )

    # SVG ícono LinkedIn
    li_svg = (
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">'
        '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/>'
        '<rect x="2" y="9" width="4" height="12"/>'
        '<circle cx="4" cy="4" r="2"/>'
        '</svg>'
    )
    # SVG ícono GitHub
    gh_svg = (
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">'
        '<path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 '
        '6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 '
        '0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 '
        '6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>'
        '</svg>'
    )

    st.markdown(
        f"""<div class='app-shell-nav'>
              <div class='nav-header'>
                {logo_html}
                <div class='nav-title-block'>
                  <div class='nav-title'>Mercado Laboral</div>
                  <div class='nav-subtitle'>GEIH · DANE</div>
                </div>
              </div>
              <div class='nav-body'>
                <div class='sidebar-section'>Navegación</div>
                <nav>{items_html}</nav>
              </div>
              <div class='nav-footer'>
                <a href='{AUTHOR_LINKEDIN}' class='nav-icon-btn' target='_blank' rel='noopener' title='LinkedIn'>{li_svg}</a>
                <a href='{AUTHOR_GITHUB}' class='nav-icon-btn' target='_blank' rel='noopener' title='GitHub'>{gh_svg}</a>
                <a href='?view={vista}&theme={new_theme}' class='nav-icon-btn' title='{theme_label}' target='_self'>{theme_svg}</a>
              </div>
            </div>""",
        unsafe_allow_html=True,
    )

    return vista


def render_controls(df_all):
    st.markdown("<div class='control-title'>Navegación y filtros</div>", unsafe_allow_html=True)
    year_col, level_col, geo_col = st.columns([0.85, 0.95, 1.2], gap="small")
    anos_disp = sorted(df_all["ano"].dropna().unique().tolist())
    with year_col:
        ano_ui = st.selectbox("Periodo anual", ["Todos"] + [str(a) for a in anos_disp], index=0)
    anos_sel = anos_disp if ano_ui == "Todos" else [int(ano_ui)]
    with level_col:
        geo_level = st.selectbox("Nivel territorial", ["Sin filtro", "Departamento", "Ciudad"], index=0)
    with geo_col:
        if geo_level == "Departamento":
            geo_sel = st.selectbox("Ubicacion", ["Todos"] + opciones(df_all, "departamento", "DPTO_label"), index=0)
        elif geo_level == "Ciudad":
            geo_sel = st.selectbox("Ubicacion", ["Todas"] + opciones(df_all, "ciudad", "AREA_label"), index=0)
        else:
            geo_sel = "Todas"
            st.selectbox("Ubicacion", ["Sin filtro"], index=0, disabled=True)
    return ano_ui, anos_sel, geo_level, geo_sel


def render_filters_summary(ano_ui, geo_level, geo_sel):
    chips = "".join([
        f"<span class='pill'>📅 {ano_ui}</span>",
        f"<span class='pill'>🗺 {geo_level}</span>",
        f"<span class='pill'>📍 {geo_sel}</span>",
    ])
    st.markdown(f"<div class='pill-row'>{chips}</div>", unsafe_allow_html=True)


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
    data["grupo_edad"] = pd.Categorical(data["grupo_edad"], AGE_ORDER, ordered=True)
    data = data.sort_values("grupo_edad")
    is_h = data["P3271_label"].astype(str).str.lower().eq("hombre")
    data["plot"] = data[value_col]
    data.loc[is_h, "plot"] *= -1

    fig = px.bar(
        data,
        x="plot",
        y="grupo_edad",
        color="P3271_label",
        orientation="h",
        color_discrete_map={"Hombre": t["soft_text"], "Mujer": t["accent"]},
        barmode="relative",
    )
    fig = fig_base_h(fig, title, subtitle)
    fig.update_traces(
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>%{customdata[0]}: %{x:,.0f}<extra></extra>",
    )
    # Eje X con valores absolutos
    max_val = data[value_col].abs().max()
    fig.update_xaxes(
        tickvals=[-max_val * 0.6, -max_val * 0.3, 0, max_val * 0.3, max_val * 0.6],
        ticktext=[
            fmt_metric(max_val * 0.6), fmt_metric(max_val * 0.3),
            "0", fmt_metric(max_val * 0.3), fmt_metric(max_val * 0.6),
        ],
    )
    # Línea central
    fig.add_vline(x=0, line_width=1.5, line_color=ACTIVE_THEME["line"])
    st.plotly_chart(fig, use_container_width=True)


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

    # Tendencia principal + mini-cards
    render_section("Tendencia de indicadores laborales", "Serie mensual — TD, TO y TGP ponderados con FEX_C18")
    lead, side = st.columns([1.9, 1], gap="large")

    with lead:
        trend = (
            df_context.sort_values("periodo")
            .melt(id_vars=["periodo"], value_vars=["TD", "TO", "TGP"], var_name="Indicador", value_name="Valor")
        )
        fig = go.Figure()
        color_map = {"TD": t["accent"], "TO": t["accent_2"], "TGP": t["soft_text"]}
        for ind in ["TGP", "TO", "TD"]:
            sub = trend[trend["Indicador"] == ind]
            fig.add_trace(go.Scatter(
                x=sub["periodo"],
                y=sub["Valor"],
                name=ind,
                mode="lines",
                line=dict(color=color_map[ind], width=2.5, shape="spline", smoothing=0.6),
                hovertemplate=f"<b>{ind}</b>: %{{y:.1f}}%<br>%{{x|%b %Y}}<extra></extra>",
                fill="tozeroy" if ind == "TD" else "none",
                fillcolor=f"rgba({','.join(str(int(color_map[ind].lstrip('#')[i:i+2], 16)) for i in (0,2,4))},0.07)"
                if ind == "TD" else "rgba(0,0,0,0)",
            ))
        fig = fig_base(fig, "TD · TO · TGP", f"Contexto: {context_label}")
        fig.update_xaxes(tickformat="%b %Y", dtick="M3")
        fig.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True)

    with side:
        tgp_val = f"{row.get('TGP', 0):.1f}%"
        to_val = f"{row.get('TO', 0):.1f}%"
        desoc_val = fmt_metric(row.get("desocupados_exp", 0))
        ingreso_val = f"${fmt_metric(row.get('ingreso_mediano', 0))}" if row.get("ingreso_mediano") else "s/d"

        for label, val, foot in [
            ("Tasa de participación (TGP)", tgp_val, "Fuerza de trabajo / PET × 100"),
            ("Tasa de ocupación (TO)", to_val, "Ocupados / PET × 100"),
            ("Desocupados", desoc_val, "Personas que buscan empleo activamente"),
            ("Ingreso mediano", ingreso_val, "COP corrientes · Ocupados con P6500"),
        ]:
            st.markdown(
                f"<div class='mini-card' style='margin-bottom:0.55rem'>"
                f"<div class='mini-label'>{label}</div>"
                f"<div class='mini-value'>{val}</div>"
                f"<div class='mini-foot'>{foot}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # Comparativo departamental
    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    render_section("Comparativo departamental", "Último período disponible por dimensión departamental")
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
            d = dep.sort_values("TD").head(12)
            d["txt"] = d["TD"].map(lambda x: f"{x:.1f}%")
            fig = px.bar(
                d, x="TD", y="DPTO_label", orientation="h",
                text="txt",
                color="TD",
                color_continuous_scale=[[0, t["accent_2"]], [1, t["accent"]]],
            )
            fig = fig_base_h(fig, "TD por departamento", "Menor a mayor · últimos datos")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_coloraxes(showscale=False)
            fig.update_xaxes(ticksuffix="%")
            st.plotly_chart(fig, use_container_width=True)
        with right:
            d2 = dep.sort_values("TO", ascending=False).head(12)
            d2["txt"] = d2["TO"].map(lambda x: f"{x:.1f}%")
            fig = px.bar(
                d2, x="TO", y="DPTO_label", orientation="h",
                text="txt",
                color="TO",
                color_continuous_scale=[[0, t["accent"]], [1, t["accent_2"]]],
            )
            fig = fig_base_h(fig, "TO por departamento", "Mayor a menor · últimos datos")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_coloraxes(showscale=False)
            fig.update_xaxes(ticksuffix="%")
            st.plotly_chart(fig, use_container_width=True)


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
                color_discrete_sequence=[t["accent"]],
            )
            fig = fig_base_h(fig, "Población por nivel educativo", "Promedio del periodo · P3042")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
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
                color_discrete_sequence=[t["accent_3"]],
            )
            fig = fig_base_h(fig, "Estado civil", "P6070 · promedio del periodo")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
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
                color_discrete_map={"Hombre": t["soft_text"], "Mujer": t["accent"]},
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
                color_discrete_sequence=[t["accent_2"], t["accent_3"]],
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
        cols = st.columns(3, gap="small")
        render_kpi(
            cols[0], "Total ocupados",
            fmt_metric(row.get("ocupados_exp", 0)),
            "Último periodo disponible",
            fmt_delta_html(row.get("ocupados_exp"), prev.get("ocupados_exp") if prev is not None else None),
        )
        render_kpi(
            cols[1], "Tasa de ocupación (TO)",
            f"{row.get('TO', 0):.1f}%",
            "Ocupados / PET × 100",
            fmt_delta_html(row.get("TO"), prev.get("TO") if prev is not None else None, mode="pct"),
        )
        render_kpi(
            cols[2], "Ingreso mediano",
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
            colors = [t["accent"]] * len(sec)
            colors[-1] = t["accent_2"]  # Destacar el mayor
            fig = px.bar(
                sec, x="ocupados_exp", y="RAMA2D_R4_label", orientation="h",
                text="txt",
                color_discrete_sequence=[t["accent"]],
            )
            fig = fig_base_h(fig, "Ocupados por rama de actividad", "CIIU Rev.4 a 2 dígitos · promedio del periodo")
            fig.update_traces(
                textposition="outside", cliponaxis=False, marker_line_width=0,
                hovertemplate="<b>%{y}</b><br>%{x:,.0f} ocupados<extra></extra>",
            )
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
            pos["txt"] = pos["ocupados_exp"].map(fmt_metric)
            fig = px.bar(
                pos, x="ocupados_exp", y="P6430_label", orientation="h",
                text="txt",
                color_discrete_sequence=[t["accent_3"]],
            )
            fig = fig_base_h(fig, "Posición ocupacional", "P6430 · promedio del periodo")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
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
                color_continuous_scale=[[0, t["accent"]], [1, t["accent_2"]]],
            )
            fig = fig_base_h(fig, "Ocupados por ciudad", "23 áreas metropolitanas GEIH · promedio del periodo")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_coloraxes(showscale=False)
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
                         color_discrete_sequence=[t["accent"]])
            fig = fig_base_h(fig, "Ocupados por nivel educativo", "P3042 · promedio del periodo")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)
        with right:
            d2 = edu.sort_values("ingreso_mediano")
            d2["txt"] = d2["ingreso_mediano"].map(lambda x: f"${fmt_metric(x)}")
            fig = px.bar(d2, x="ingreso_mediano", y="P3042_label", orientation="h", text="txt",
                         color_discrete_sequence=[t["accent_2"]])
            fig = fig_base_h(fig, "Ingreso mediano por nivel educativo", "COP corrientes · P6500 ponderado FEX_C18")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_xaxes(tickprefix="$", separatethousands=True)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        placeholder(
            "Educación × ingresos sin datos. Agregar <code>P3042</code> al ETL y regenerar el parquet.",
            "📚",
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
                color_continuous_scale=[[0, t["accent_3"]], [1, t["negative"]]],
            )
            fig = fig_base_h(fig, "Desocupados por ciudad", "23 áreas metropolitanas GEIH · promedio del periodo")
            fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
            fig.update_coloraxes(showscale=False)
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
            color_discrete_sequence=[t["accent_3"]],
        )
        fig = fig_base_h(fig, "Desocupados por nivel educativo", "P3042 · promedio del periodo")
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
        placeholder("Educación de desocupados sin datos. Agregar <code>P3042</code> al ETL.", "📚")


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
                color_discrete_map={"Hombre": t["soft_text"], "Mujer": t["accent"]},
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
                color_discrete_sequence=[t["accent_2"], t["accent_3"]],
            )
            fig = fig_base(fig, "Brecha etaria en TD", "Jóvenes 15-28 vs. Adultos 29+")
            fig.update_traces(textposition="outside", marker_line_width=0)
            fig.update_xaxes(title_text="")
            fig.update_yaxes(ticksuffix="%")
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

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
            color_continuous_scale=[[0, t["positive"]], [0.5, t["accent_3"]], [1, t["negative"]]],
        )
        fig = fig_base_h(fig, "Brecha departamental vs. nacional", f"Referencia nacional: {nacional_td:.1f}%")
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        fig.update_coloraxes(showscale=False)
        fig.update_xaxes(ticksuffix=" pp")
        fig.add_vline(x=0, line_width=1.5, line_dash="dot", line_color=ACTIVE_THEME["muted"])
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Vista 6: Metodología
# ---------------------------------------------------------------------------
def view_metodologia(df):
    years = sorted(df["ano"].dropna().unique().tolist()) if "ano" in df.columns else []
    year_range = f"{years[0]}–{years[-1]}" if len(years) >= 2 else (str(years[0]) if years else "s/d")

    render_section("Ficha técnica y fuentes")
    c1, c2, c3 = st.columns(3, gap="small")
    for col, label, val, foot in [
        (c1, "Fuente", "DANE · GEIH", "Gran Encuesta Integrada de Hogares. Indicadores ponderados con FEX_C18 (post-rediseño)."),
        (c2, "Cobertura", year_range, "4 años de microdatos anuales consolidados por el usuario."),
        (c3, "Actualización", "Manual", "Regenerar <code>indicadores_mensuales.parquet</code> con <code>python src/etl.py</code>."),
    ]:
        with col:
            st.markdown(
                f"<div class='card'><div class='kpi-label'>{label}</div>"
                f"<div class='mini-value'>{val}</div>"
                f"<div class='kpi-foot'>{foot}</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    render_section("Definiciones y notas técnicas")
    defs = [
        ("PET", "Población en edad de trabajar. Personas con P6040 ≥ 15 años."),
        ("PEA / FT", "Fuerza de trabajo. Ocupados + Desocupados."),
        ("TGP", "Tasa global de participación = PEA / PET × 100."),
        ("TO", "Tasa de ocupación = Ocupados / PET × 100."),
        ("TD", "Tasa de desempleo = Desocupados / PEA × 100."),
        ("FEX_C18", "Factor de expansión post-rediseño 2022+. Obligatorio para cualquier agregado expandido."),
        ("P3271", "Sexo al nacer (variable rediseñada 2022+). 1 = Hombre, 2 = Mujer. Antes era P6020."),
    ]
    for term, defn in defs:
        st.markdown(
            f"<div class='mini-card' style='margin-bottom:0.4rem;display:flex;gap:0.75rem;align-items:flex-start'>"
            f"<span style='color:{ACTIVE_THEME['accent']};font-weight:700;font-size:0.88rem;min-width:80px'>{term}</span>"
            f"<span style='color:{ACTIVE_THEME['soft_text']};font-size:0.88rem;line-height:1.5'>{defn}</span>"
            f"</div>",
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

nav_col, main_col = st.columns([1.1, 2.9], gap="medium")

with nav_col:
    vista = render_side_nav()

with main_col:
    st.markdown("<div class='control-bar'>", unsafe_allow_html=True)
    ano_ui, anos_sel, geo_level, geo_sel = render_controls(df_all)
    st.markdown("</div>", unsafe_allow_html=True)

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
    with main_col:
        st.warning("No hay datos nacionales para los filtros seleccionados. Relaja los filtros o regenera el parquet.")
    st.stop()

ultimo       = latest_row(df_nac)
df_context   = active_context_df(df_nac, df_dep, df_city, geo_level, geo_sel)
context_label = active_context_label(geo_level, geo_sel)

with main_col:
    render_header(vista, ultimo["periodo"].strftime("%B %Y").capitalize(), context_label)
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
    else:
        view_metodologia(df_all)

st.divider()
st.caption("Daniel Molina · Economista & Data Scientist · Fuente: DANE — Gran Encuesta Integrada de Hogares (GEIH)")
