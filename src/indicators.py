"""
Indicadores de mercado laboral ponderados con FEX_C18 — backend Polars.
Las funciones de aggregation usan group_by nativo; la mediana ponderada usa numpy.
"""
import numpy as np
import polars as pl

from src.config import FACTOR_EXPANSION, GRUPOS_EDAD

FEX = FACTOR_EXPANSION


def _validar_cols(df: pl.DataFrame, requeridas: list[str]) -> None:
    faltantes = [c for c in requeridas if c not in df.columns]
    if faltantes:
        raise KeyError(f"Columnas requeridas no encontradas: {faltantes}")


def _pet(df: pl.DataFrame) -> pl.DataFrame:
    """Filtra Población en Edad de Trabajar: P6040 >= 15."""
    return df.filter(pl.col("P6040").cast(pl.Int16) >= 15)


def _mediana_ponderada(v: np.ndarray, w: np.ndarray) -> float:
    """Mediana ponderada por acumulación de pesos."""
    mask = np.isfinite(v) & np.isfinite(w) & (w > 0)
    v, w = v[mask], w[mask]
    if len(v) == 0:
        return float("nan")
    idx = np.argsort(v)
    w_cum = np.cumsum(w[idx])
    return float(v[idx][w_cum >= w_cum[-1] / 2][0])


# ── Indicadores principales ───────────────────────────────────────────────────

def _agg_mercado_laboral(df: pl.DataFrame, por: list[str]) -> pl.DataFrame:
    """
    TD, TO, TGP para una lista de columnas de agrupación.
    group_by calcula todos los (año, mes, dim) a la vez — sin loop Python.
    """
    _validar_cols(df, ["OCI", "DSI", "P6040", FEX])
    df_pet = _pet(df)

    # Filtrar nulls en columnas de dimensión (evita grupo "null")
    for col in por:
        if col not in ("_año", "MES"):
            df_pet = df_pet.filter(pl.col(col).is_not_null())

    return (
        df_pet
        .group_by(por)
        .agg(
            (pl.col("OCI").fill_null(0).cast(pl.Float64) * pl.col(FEX))
            .sum().alias("ocupados_exp"),
            (pl.col("DSI").fill_null(0).cast(pl.Float64) * pl.col(FEX))
            .sum().alias("desocupados_exp"),
            pl.col(FEX).sum().alias("PET_exp"),
        )
        .with_columns(
            (
                pl.col("desocupados_exp")
                / (pl.col("ocupados_exp") + pl.col("desocupados_exp"))
                * 100
            ).alias("TD"),
            (pl.col("ocupados_exp") / pl.col("PET_exp") * 100).alias("TO"),
            (
                (pl.col("ocupados_exp") + pl.col("desocupados_exp"))
                / pl.col("PET_exp")
                * 100
            ).alias("TGP"),
        )
    )


def _agg_resumen_poblacional(df: pl.DataFrame, por: list[str]) -> pl.DataFrame:
    """Agrega población total y fuerza de trabajo sobre toda la base, sin filtrar PET."""
    _validar_cols(df, [FEX])

    faltantes_opcionales = [col for col in ["PT", "FT"] if col not in df.columns]
    if faltantes_opcionales:
        df = df.with_columns(
            [pl.lit(0).cast(pl.Int16).alias(col) for col in faltantes_opcionales]
        )

    for col in por:
        if col not in ("_año", "MES"):
            df = df.filter(pl.col(col).is_not_null())

    return (
        df.group_by(por)
        .agg(
            (pl.col("PT").fill_null(0).cast(pl.Float64) * pl.col(FEX))
            .sum().alias("poblacion_total_exp"),
            (pl.col("FT").fill_null(0).cast(pl.Float64) * pl.col(FEX))
            .sum().alias("PEA_exp"),
        )
    )


def _agg_ingreso_mediano(df: pl.DataFrame, por: list[str]) -> pl.DataFrame:
    """
    Ingreso laboral mediano ponderado entre ocupados (OCI == 1).
    Usa un loop Python sobre los grupos — la mediana ponderada no tiene
    equivalente nativo en polars.
    """
    _validar_cols(df, ["OCI", "P6500", FEX])
    df_ocu = df.filter(pl.col("OCI").fill_null(0) == 1)

    for col in por:
        if col not in ("_año", "MES"):
            df_ocu = df_ocu.filter(pl.col(col).is_not_null())

    filas = []
    for keys, grupo in df_ocu.group_by(por):
        if not isinstance(keys, tuple):
            keys = (keys,)
        v = grupo["P6500"].to_numpy()
        w = grupo[FEX].to_numpy()
        med = _mediana_ponderada(v, w)
        fila = dict(zip(por, [[k] for k in keys]))
        fila["ingreso_mediano"] = [med]
        filas.append(pl.DataFrame(fila))

    if not filas:
        return pl.DataFrame(
            {**{k: pl.Series([], dtype=pl.Utf8) for k in por},
             "ingreso_mediano": pl.Series([], dtype=pl.Float64)}
        )
    return pl.concat(filas, how="diagonal_relaxed")


def calcular_dimension(
    df: pl.DataFrame,
    por_base: list[str],
    dim_col: list[str] | None,
    dim_nombre: str,
) -> pl.DataFrame:
    """
    Calcula TD, TO, TGP e ingreso_mediano para una dimensión.

    por_base  : columnas de agrupación base (normalmente ["_año", "MES"])
    dim_col   : columna de dimensión, p.ej. ["AREA_label"] o None para nacional
    dim_nombre: etiqueta de la dimensión (string)
    """
    por = por_base + (dim_col or [])

    # Verificar que las columnas de dimensión existen
    faltantes = [c for c in (dim_col or []) if c not in df.columns]
    if faltantes:
        raise KeyError(f"Columna de dimensión faltante: {faltantes}")

    resumen = _agg_resumen_poblacional(df, por)
    mercado = _agg_mercado_laboral(df, por)
    ingreso = _agg_ingreso_mediano(df, por)

    result = resumen.join(mercado, on=por, how="left").join(ingreso, on=por, how="left")
    return result.with_columns(pl.lit(dim_nombre).alias("dimension"))


# ── Helpers ───────────────────────────────────────────────────────────────────

def asignar_grupo_edad(df: pl.DataFrame) -> pl.DataFrame:
    """Crea columna grupo_edad según P6040 usando expresiones polars."""
    _validar_cols(df, ["P6040"])
    edad = pl.col("P6040").cast(pl.Int16)
    return df.with_columns(
        pl.when(edad.is_between(15, 24)).then(pl.lit("15-24"))
        .when(edad.is_between(25, 34)).then(pl.lit("25-34"))
        .when(edad.is_between(35, 44)).then(pl.lit("35-44"))
        .when(edad.is_between(45, 54)).then(pl.lit("45-54"))
        .when(edad.is_between(55, 64)).then(pl.lit("55-64"))
        .when(edad >= 65).then(pl.lit("65+"))
        .otherwise(None)
        .alias("grupo_edad")
    )


def asignar_grupo_edad_brecha(df: pl.DataFrame) -> pl.DataFrame:
    """Crea grupo binario para brecha jovenes 15-28 vs resto."""
    _validar_cols(df, ["P6040"])
    edad = pl.col("P6040").cast(pl.Int16)
    return df.with_columns(
        pl.when(edad.is_between(15, 28)).then(pl.lit("15-28"))
        .when(edad >= 29).then(pl.lit("29+"))
        .otherwise(None)
        .alias("grupo_edad_brecha")
    )
