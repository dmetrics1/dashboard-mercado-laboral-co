"""
Configuración central del proyecto.
Rutas, variables clave, tipado y mapeos complementarios.
"""
from pathlib import Path


def _build_rama2d_r4_mapping() -> dict[str, str]:
    """Agrupa divisiones CIIU Rev. 4 en sectores amplios del dashboard."""
    mapping: dict[str, str] = {"0": "No clasificado"}

    grupos = [
        (range(1, 4), "Agro, caza, pesca"),
        (list(range(5, 10)) + list(range(35, 40)), "Electricidad, gas, agua, desechos"),
        (range(10, 34), "Industria manufacturera"),
        (range(41, 44), "Construccion"),
        (range(45, 48), "Comercio y reparacion vehiculos"),
        (range(49, 54), "Transporte y almacenamiento"),
        (range(55, 57), "Alojamiento y comida"),
        (range(58, 64), "Informacion y comunicaciones"),
        (range(64, 67), "Financieras y seguros"),
        ([68], "Inmobiliarias"),
        (range(69, 83), "Profesionales, cientificas y tecnicas"),
        (range(84, 89), "Administracion publica, educacion, salud"),
        (range(90, 100), "Artes, recreacion y otros servicios"),
    ]

    for codigos, etiqueta in grupos:
        for codigo in codigos:
            mapping[str(codigo)] = etiqueta

    return mapping


def _build_clase_mapping() -> dict[str, str]:
    """Recodifica clase geográfica de la GEIH para dashboard."""
    return {
        "1": "Urbana",
        "2": "Rural",
    }


def _build_nivel_educativo_mapping() -> dict[str, str]:
    """Agrupa niveles educativos en categorías analíticas amplias."""
    mapping: dict[str, str] = {
        "1": "Sin nivel",
        "2": "Primaria",
        "3": "Primaria",
        "4": "Secundaria",
        "5": "Media",
        "6": "Media",
        "7": "Superior",
        "8": "Superior",
        "9": "Superior",
        "10": "Superior",
        "11": "Superior",
        "12": "Superior",
        "13": "Superior",
        "99": "No sabe",
    }
    return mapping

# ── Rutas ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Ruta real de las bases (fuera del repo, en bases_datos/)
BASES_DIR = PROJECT_ROOT.parent / "bases_datos" / "geih" / "datos"

# Diccionario: primero busca en bases_datos, fallback a data/reference
_dic_externo = PROJECT_ROOT.parent / "bases_datos" / "geih" / "diccionario.xlsx"
_dic_interno = DATA_REFERENCE_DIR / "diccionario.xlsx"
DICCIONARIO_PATH = _dic_externo if _dic_externo.exists() else _dic_interno

AÑOS = [2022, 2023, 2024, 2025]

# ── Variables clave ───────────────────────────────────────────────────────────
VARS_ID = ["DIRECTORIO", "SECUENCIA_P", "ORDEN", "HOGAR", "PER"]
VARS_GEO = ["AREA", "DPTO"]
VARS_DEMO = ["P3271", "P6040"]
VARS_LABORAL = ["OCI", "DSI", "P6430", "RAMA2D_R4", "RAMA4D_R4"]
VARS_INGRESO = ["P6500"]
FACTOR_EXPANSION = "FEX_C18"
VARS_POBLACION = ["PT", "FT", "PET", "CLASE", "P6070", "P3042", "P6090", "P6100", "P6920", "P6240"]

# Columnas mínimas que necesita el dashboard
VARS_DASHBOARD = (
    VARS_ID
    + VARS_GEO
    + VARS_DEMO
    + VARS_LABORAL
    + VARS_INGRESO
    + VARS_POBLACION
    + [FACTOR_EXPANSION, "MES"]
)

# ── Tipado estricto (DT-003) ──────────────────────────────────────────────────
DTYPE_MAP: dict[str, str] = {
    # Geográficas: string para preservar ceros a la izquierda
    "AREA": "string",
    "DPTO": "string",
    # Identificadores
    "DIRECTORIO": "Int64",
    "SECUENCIA_P": "Int64",
    "ORDEN": "Int64",
    "HOGAR": "Int64",
    "PER": "Int64",
    # Temporales
    "MES": "Int8",
    # Demográficas y laborales
    "P3271": "Int8",
    "P6040": "Int8",
    "PT": "Int8",
    "FT": "Int8",
    "PET": "Int8",
    "CLASE": "Int8",
    "P6070": "Int8",
    "P3042": "Int8",
    "P6090": "Int8",
    "P6100": "Int8",
    "P6920": "Int8",
    "P6240": "Int16",
    "OCI": "Int8",
    "DSI": "Int8",
    "P6430": "Int8",
    # Ingresos y factor
    "P6500": "Float64",
    "FEX_C18": "Float64",
}

# ── Mapeos complementarios (DT-002) ──────────────────────────────────────────
# Fuente: Manual Metodológico GEIH 2025, DANE DIMPE versión 55.
# P3271 aparece en el diccionario con metadata pero sin filas de codigo_categoria.
MAPEOS_COMPLEMENTARIOS: dict[str, dict[str, str]] = {
    "P3271": {
        "1": "Hombre",
        "2": "Mujer",
    },
    "CLASE": _build_clase_mapping(),
    "P3042": _build_nivel_educativo_mapping(),
    "RAMA2D_R4": _build_rama2d_r4_mapping(),
}

# ── Grupos de edad ────────────────────────────────────────────────────────────
GRUPOS_EDAD: dict[str, tuple[int, int]] = {
    "15-24": (15, 24),
    "25-34": (25, 34),
    "35-44": (35, 44),
    "45-54": (45, 54),
    "55-64": (55, 64),
    "65+": (65, 120),
}

# ── Umbrales de validación ────────────────────────────────────────────────────
TD_TOLERANCIA_PP: float = 0.2   # puntos porcentuales vs cifra DANE oficial
COBERTURA_MINIMA: float = 0.95  # 95% variables codificadas con mapeo

# ── Salidas procesadas ────────────────────────────────────────────────────────
DICCIONARIO_LIMPIO_PATH = DATA_PROCESSED_DIR / "diccionario_limpio.parquet"
MAPEOS_JSON_PATH = DATA_PROCESSED_DIR / "mapeos_variables.json"
METADATA_VARS_PATH = DATA_PROCESSED_DIR / "metadata_variables.parquet"
REPORTE_COBERTURA_PATH = DATA_PROCESSED_DIR / "reporte_cobertura_diccionario.md"
INDICADORES_PATH = DATA_PROCESSED_DIR / "indicadores_mensuales.parquet"
