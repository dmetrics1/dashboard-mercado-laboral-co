"""
Carga de las bases anuales GEIH con tipado estricto — backend Polars.
Soporta .parquet, .csv y .sav.
"""
from pathlib import Path

import polars as pl

from src.config import AÑOS, BASES_DIR, DATA_RAW_DIR

# Tipos polars por variable (preserva ceros a la izquierda en strings)
POLARS_SCHEMA: dict[str, pl.DataType] = {
    "AREA": pl.Utf8,
    "DPTO": pl.Utf8,
    "DIRECTORIO": pl.Int64,
    "SECUENCIA_P": pl.Int64,
    "ORDEN": pl.Int64,
    "HOGAR": pl.Int64,
    "PER": pl.Int64,
    "MES": pl.Int16,
    "P3271": pl.Int16,
    "P6040": pl.Int16,
    "OCI": pl.Int16,
    "DSI": pl.Int16,
    "P6430": pl.Int16,
    "P6500": pl.Float64,
    "FEX_C18": pl.Float64,
}


def _encontrar_archivo(año: int, directorio: Path) -> Path:
    for ext in ("parquet", "csv", "sav"):
        path = directorio / f"geih_{año}.{ext}"
        if path.exists():
            return path
    raise FileNotFoundError(
        f"No se encontró geih_{año}.[parquet|csv|sav] en {directorio}"
    )


def cargar_año(
    año: int,
    columnas: list[str] | None = None,
    directorio: Path | None = None,
) -> pl.DataFrame:
    """
    Carga base anual GEIH para un año.
    Busca en: directorio (si se pasa) → BASES_DIR → DATA_RAW_DIR.
    """
    rutas = [r for r in [directorio, BASES_DIR, DATA_RAW_DIR] if r]

    path = None
    for d in rutas:
        try:
            path = _encontrar_archivo(año, Path(d))
            break
        except FileNotFoundError:
            continue

    if path is None:
        raise FileNotFoundError(
            f"No se encontró geih_{año}. Rutas revisadas: {rutas}"
        )

    ext = path.suffix.lower()
    print(f"[loaders] Cargando {path.name} ...")

    # Solo aplicar schema_overrides para columnas que existen en el archivo
    # (polars ignora columnas ausentes en schema_overrides)
    if ext == ".parquet":
        df = pl.read_parquet(path, columns=columnas)

    elif ext == ".csv":
        # DANE publica en latin-1; fallback a utf-8
        for enc in ("latin1", "utf8"):
            try:
                df = pl.read_csv(
                    path,
                    columns=columnas,
                    schema_overrides=POLARS_SCHEMA,
                    encoding=enc,
                    infer_schema_length=10000,
                    null_values=["", "NA", "N/A"],
                    ignore_errors=True,
                )
                break
            except Exception:
                continue
        else:
            raise RuntimeError(f"No se pudo leer {path.name}")

    elif ext == ".sav":
        # pyreadstat → pandas → polars
        import pandas as pd
        df_pd = pd.read_spss(path, usecols=columnas)
        df = pl.from_pandas(df_pd)

    else:
        raise ValueError(f"Formato no soportado: {ext}")

    df = df.with_columns(pl.lit(año).cast(pl.Int16).alias("_año"))
    print(f"[loaders] {año}: {df.shape[0]:,} filas × {df.shape[1]} columnas.")
    return df


def cargar_todos(
    años: list[int] | None = None,
    columnas: list[str] | None = None,
) -> pl.DataFrame:
    """
    Carga y concatena todas las bases anuales.
    Usa diagonal_relaxed para tolerar diferencias de columnas entre años
    (el instructivo advierte que no todos los años son idénticos).
    """
    if años is None:
        años = AÑOS

    partes: list[pl.DataFrame] = []
    for año in años:
        try:
            partes.append(cargar_año(año, columnas=columnas))
        except FileNotFoundError as exc:
            print(f"[loaders] AVISO — {exc}")

    if not partes:
        raise RuntimeError(
            "No se cargó ninguna base anual. Verifica las rutas en src/config.py."
        )

    df = pl.concat(partes, how="diagonal_relaxed")
    print(f"[loaders] Consolidado: {df.shape[0]:,} filas × {df.shape[1]} columnas.")
    return df
