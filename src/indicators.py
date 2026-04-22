"""
Indicadores de mercado laboral ponderados con FEX_C18 — backend Polars.
Las funciones de aggregation usan group_by nativo; la mediana ponderada usa numpy.
"""
import numpy as np
import polars as pl

from src.config import FACTOR_EXPANSION, GRUPOS_EDAD

FEX = FACTOR_EXPANSION

FORMALIDAD_DANE_COLS = {
    "P6430", "P6100", "P6110", "P6450", "P6920", "P6930", "P6940",
    "RAMA2D_R4", "P3045S1", "P3046", "P3069", "P6765", "P3065",
    "P3066", "P3067", "P3067S1", "P3067S2", "P6775", "P3068",
    "OFICIO_C8",
}


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

def _calcular_formalidad_dane(df: pl.DataFrame) -> pl.Expr:
    """
    Traduce la lógica de Stata a expresiones de Polars para determinar formalidad (EI=1).
    """
    # Pre-procesamiento de variables auxiliares
    # ANIOS: PER - 1 (usamos _año como proxy de PER si es el año)
    anios = (pl.col("_año") if "_año" in df.columns else pl.col("PER")).cast(pl.Int32) - 1
    
    # OFICIO_C8_2D: Primeros 2 dígitos
    oficio_2d = pl.col("OFICIO_C8").str.slice(0, 2).cast(pl.Int16, strict=False).fill_null(0)

    # 1. Definición de SALUD (1 = Formal por salud)
    # replace SALUD=1 if (P6430 ==1 | P6430 ==3 | P6430 ==7 ) & (P6100 ==1 |P6100 ==2) & (P6110 ==1 | P6110 ==2 | P6110 ==4)
    salud_cond1 = (pl.col("P6430").is_in([1, 3, 7])) & (pl.col("P6100").is_in([1, 2])) & (pl.col("P6110").is_in([1, 2, 4]))
    salud_cond2 = (pl.col("P6430").is_in([1, 3, 7])) & (pl.col("P6100") == 9) & (pl.col("P6450") == 2)
    salud_cond3 = (pl.col("P6430").is_in([1, 3, 7])) & (pl.col("P6110") == 9) & (pl.col("P6450") == 2)
    salud = pl.when(salud_cond1 | salud_cond2 | salud_cond3).then(1).otherwise(0)

    # 2. Definición de PENSION (1 = Formal por pensión)
    pension_cond1 = (pl.col("P6430").is_in([1, 3, 7])) & (pl.col("P6920") == 3)
    pension_cond2 = (pl.col("P6430").is_in([1, 3, 7])) & (pl.col("P6920") == 1) & (pl.col("P6930").is_in([1, 2, 3])) & (pl.col("P6940").is_in([1, 3]))
    pension = pl.when(pension_cond1 | pension_cond2).then(1).otherwise(0)

    # 3. Definición de FORMAL (Base para independientes y otros)
    formal = (
        pl.when(pl.col("RAMA2D_R4").cast(pl.Utf8).is_in(["84", "99"])).then(1)
        .when(pl.col("P6430") == 6).then(0)
        .when(pl.col("P6430") == 8).then(0)
        # Asalariados (P6430: 1-Obrero/Emp Privado, 2-Obrero/Emp Público, 7-Jornalero)
        .when(pl.col("P6430") == 2).then(1)
        .when((pl.col("P6430").is_in([1, 7])) & (pl.col("P3045S1") == 1)).then(1)
        .when((pl.col("P6430").is_in([1, 7])) & (pl.col("P3045S1").is_in([2, 9])) & (pl.col("P3046") == 1)).then(1)
        .when((pl.col("P6430").is_in([1, 7])) & (pl.col("P3045S1").is_in([2, 9])) & (pl.col("P3046") == 2)).then(0)
        .when((pl.col("P6430").is_in([1, 7])) & (pl.col("P3045S1").is_in([2, 9])) & (pl.col("P3046") == 9) & (pl.col("P3069") >= 4)).then(1)
        .when((pl.col("P6430").is_in([1, 7])) & (pl.col("P3045S1").is_in([2, 9])) & (pl.col("P3046") == 9) & (pl.col("P3069") <= 3)).then(0)
        # Independientes (P6430: 4-Cuenta Propia, 5-Patrón)
        # Sin negocio (P6765 != 7)
        .when((pl.col("P6430").is_in([4, 5])) & (pl.col("P6765").is_in([1,2,3,4,5,6,8])) & (pl.col("P3065") == 1)).then(1)
        .when((pl.col("P6430").is_in([4, 5])) & (pl.col("P6765").is_in([1,2,3,4,5,6,8])) & (pl.col("P3065").is_in([2, 9])) & (pl.col("P3066") == 1)).then(1)
        .when((pl.col("P6430").is_in([4, 5])) & (pl.col("P6765").is_in([1,2,3,4,5,6,8])) & (pl.col("P3065").is_in([2, 9])) & (pl.col("P3066") == 2)).then(0)
        .when((pl.col("P6430") == 5) & (pl.col("P6765").is_in([1,2,3,4,5,6,8])) & (pl.col("P3065").is_in([2, 9])) & (pl.col("P3066") == 9) & (pl.col("P3069") >= 4)).then(1)
        .when((pl.col("P6430") == 5) & (pl.col("P6765").is_in([1,2,3,4,5,6,8])) & (pl.col("P3065").is_in([2, 9])) & (pl.col("P3066") == 9) & (pl.col("P3069") <= 3)).then(0)
        .when((pl.col("P6430") == 4) & (pl.col("P6765").is_in([1,2,3,4,5,6,8])) & (pl.col("P3065").is_in([2, 9])) & (pl.col("P3066") == 9) & (oficio_2d <= 20)).then(1)
        .when((pl.col("P6430") == 4) & (pl.col("P6765").is_in([1,2,3,4,5,6,8])) & (pl.col("P3065").is_in([2, 9])) & (pl.col("P3066") == 9) & (oficio_2d >= 21)).then(0)
        # Con negocio (P6765 == 7)
        # Con registro mercantil
        .when((pl.col("P6430").is_in([4, 5])) & (pl.col("P6765") == 7) & (pl.col("P3067") == 1) & (pl.col("P3067S1") == 1) & (pl.col("P3067S2") >= anios)).then(1)
        .when((pl.col("P6430").is_in([4, 5])) & (pl.col("P6765") == 7) & (pl.col("P3067") == 1) & (pl.col("P3067S1") == 1) & (pl.col("P3067S2") < anios)).then(0)
        .when((pl.col("P6430").is_in([4, 5])) & (pl.col("P6765") == 7) & (pl.col("P3067") == 1) & (pl.col("P3067S1") == 2) & (pl.col("P6775") == 1)).then(1)
        .when((pl.col("P6430").is_in([4, 5])) & (pl.col("P6765") == 7) & (pl.col("P3067") == 1) & (pl.col("P3067S1") == 2) & (pl.col("P6775") == 3) & (oficio_2d <= 20)).then(1)
        .when((pl.col("P6430").is_in([4, 5])) & (pl.col("P6765") == 7) & (pl.col("P3067") == 1) & (pl.col("P3067S1") == 2) & (pl.col("P6775") == 3) & (oficio_2d >= 21)).then(0)
        .when((pl.col("P6430").is_in([4, 5])) & (pl.col("P6765") == 7) & (pl.col("P3067") == 1) & (pl.col("P3067S1") == 2) & (pl.col("P6775") == 2)).then(0)
        .when((pl.col("P6430") == 4) & (pl.col("P6765") == 7) & (pl.col("P3067") == 1) & (pl.col("P3067S1") == 2) & (pl.col("P6775") == 9) & (oficio_2d <= 20)).then(1)
        .when((pl.col("P6430") == 4) & (pl.col("P6765") == 7) & (pl.col("P3067") == 1) & (pl.col("P3067S1") == 2) & (pl.col("P6775") == 9) & (oficio_2d >= 21)).then(0)
        .when((pl.col("P6430") == 5) & (pl.col("P6765") == 7) & (pl.col("P3067") == 1) & (pl.col("P3067S1") == 2) & (pl.col("P6775") == 9) & (pl.col("P3069") >= 4)).then(1)
        .when((pl.col("P6430") == 5) & (pl.col("P6765") == 7) & (pl.col("P3067") == 1) & (pl.col("P3067S1") == 2) & (pl.col("P6775") == 9) & (pl.col("P3069") <= 3)).then(0)
        # Sin registro mercantil
        .when((pl.col("P6430").is_in([4, 5])) & (pl.col("P6765") == 7) & (pl.col("P3067") == 2) & (pl.col("P6775") == 1) & (pl.col("P3068") == 1)).then(1)
        .when((pl.col("P6430").is_in([4, 5])) & (pl.col("P6765") == 7) & (pl.col("P3067") == 2) & (pl.col("P6775") == 1) & (pl.col("P3068") == 2)).then(0)
        .when((pl.col("P6430").is_in([4, 5])) & (pl.col("P6765") == 7) & (pl.col("P3067") == 2) & (pl.col("P6775") == 3) & (oficio_2d <= 20)).then(1)
        .when((pl.col("P6430").is_in([4, 5])) & (pl.col("P6765") == 7) & (pl.col("P3067") == 2) & (pl.col("P6775") == 3) & (oficio_2d >= 21)).then(0)
        .when((pl.col("P6430").is_in([4, 5])) & (pl.col("P6765") == 7) & (pl.col("P3067") == 2) & (pl.col("P6775") == 1) & (pl.col("P3068").is_in([3, 9]))).then(0)
        .when((pl.col("P6430").is_in([4, 5])) & (pl.col("P6765") == 7) & (pl.col("P3067") == 2) & (pl.col("P6775") == 2)).then(0)
        .when((pl.col("P6430") == 5) & (pl.col("P6765") == 7) & (pl.col("P3067") == 2) & (pl.col("P6775") == 9) & (pl.col("P3069") >= 4)).then(1)
        .when((pl.col("P6430") == 5) & (pl.col("P6765") == 7) & (pl.col("P3067") == 2) & (pl.col("P6775") == 9) & (pl.col("P3069") <= 3)).then(0)
        .when((pl.col("P6430") == 4) & (pl.col("P6765") == 7) & (pl.col("P3067") == 2) & (pl.col("P6775") == 9) & (oficio_2d <= 20)).then(1)
        .when((pl.col("P6430") == 4) & (pl.col("P6765") == 7) & (pl.col("P3067") == 2) & (pl.col("P6775") == 9) & (oficio_2d >= 21)).then(0)
        .otherwise(None)
    ).alias("_formal_base")

    # 4. Cálculo final de EI (Formalidad según DANE)
    ei = (
        pl.when(pl.col("P6430") == 2).then(1)
        .when(pl.col("P6430").is_in([4, 5])).then(formal)
        .when(pl.col("P6430").is_in([1, 2, 3, 7]) & (salud == 1) & (pension == 1)).then(1)
        .when(pl.col("P6430").is_in([1, 2, 3, 4, 5, 7]) & pl.col("RAMA2D_R4").cast(pl.Utf8).is_in(["84", "99"])).then(1)
        .otherwise(0)
    ).alias("EI")

    return ei


def _agg_mercado_laboral(df: pl.DataFrame, por: list[str]) -> pl.DataFrame:
    """
    TD, TO, TGP para una lista de columnas de agrupación.
    group_by calcula todos los (año, mes, dim) a la vez — sin loop Python.
    """
    columnas_requeridas = ["OCI", "DSI", "P6040", FEX]
    _validar_cols(df, columnas_requeridas)
    
    # Agregar EI al dataframe si no existe. En bases completas se usa la
    # regla DANE; en datasets mínimos se degrada sin romper TD/TO/TGP.
    if "EI" not in df.columns:
        if FORMALIDAD_DANE_COLS.issubset(set(df.columns)):
            df = df.with_columns(_calcular_formalidad_dane(df))
        elif "P6090" in df.columns:
            df = df.with_columns(
                pl.when((pl.col("OCI").fill_null(0) == 1) & (pl.col("P6090").cast(pl.Int8) == 2))
                .then(0)
                .otherwise(1)
                .alias("EI")
            )
        else:
            df = df.with_columns(pl.lit(None).cast(pl.Int8).alias("EI"))
        
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
            (
                pl.when((pl.col("OCI").fill_null(0) == 1) & (pl.col("EI") == 0))
                .then(pl.col(FEX))
                .otherwise(0.0)
            ).sum().alias("informales_exp"),
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
            (pl.col("informales_exp") / pl.col("ocupados_exp") * 100)
            .alias("tasa_informalidad"),
        )
    )


def _agg_resumen_poblacional(df: pl.DataFrame, por: list[str]) -> pl.DataFrame:
    """Agrega población total y fuerza de trabajo sobre toda la base, sin filtrar PET."""
    _validar_cols(df, [FEX])

    faltantes_opcionales = [col for col in ["PT", "FT", "FFT"] if col not in df.columns]
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
            (pl.col("FFT").fill_null(0).cast(pl.Float64) * pl.col(FEX))
            .sum().alias("FFT_exp"),
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
    """Crea columna grupo_edad en quinquenios según P6040 (intervalos de 5 años)."""
    _validar_cols(df, ["P6040"])
    edad = pl.col("P6040").cast(pl.Int16)
    return df.with_columns(
        pl.when(edad.is_between(15, 19)).then(pl.lit("15-19"))
        .when(edad.is_between(20, 24)).then(pl.lit("20-24"))
        .when(edad.is_between(25, 29)).then(pl.lit("25-29"))
        .when(edad.is_between(30, 34)).then(pl.lit("30-34"))
        .when(edad.is_between(35, 39)).then(pl.lit("35-39"))
        .when(edad.is_between(40, 44)).then(pl.lit("40-44"))
        .when(edad.is_between(45, 49)).then(pl.lit("45-49"))
        .when(edad.is_between(50, 54)).then(pl.lit("50-54"))
        .when(edad.is_between(55, 59)).then(pl.lit("55-59"))
        .when(edad.is_between(60, 64)).then(pl.lit("60-64"))
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
