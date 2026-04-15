"""
Implementacion del protocolo del diccionario GEIH.
Lectura, limpieza, mapeos, labels y reporte de cobertura.
"""
import json
import warnings
from pathlib import Path

import pandas as pd

from src.config import (
    DATA_PROCESSED_DIR,
    DICCIONARIO_LIMPIO_PATH,
    DICCIONARIO_PATH,
    MAPEOS_COMPLEMENTARIOS,
    MAPEOS_JSON_PATH,
    METADATA_VARS_PATH,
    REPORTE_COBERTURA_PATH,
)


def cargar_diccionario_raw() -> pd.DataFrame:
    """Lee diccionario.xlsx con dtype=str para preservar codigo_categoria."""
    df = pd.read_excel(
        DICCIONARIO_PATH,
        sheet_name="Hoja1",
        dtype=str,
    )
    df.columns = df.columns.str.strip()
    return df


def limpiar_diccionario(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia tabla maestra: espacios, filas vacias y duplicados exactos.
    Detecta y resuelve duplicados (variable, codigo) con categorias distintas.
    """
    df = df.copy()

    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].str.strip()

    df = df.dropna(subset=["nombre_variable"])
    df = df[df["nombre_variable"].str.strip().ne("")]
    df["nombre_variable"] = df["nombre_variable"].str.upper().str.strip()
    df["codigo_categoria"] = df["codigo_categoria"].fillna("").astype(str).str.strip()

    n_antes = len(df)
    df = df.drop_duplicates()
    n_eliminados = n_antes - len(df)
    if n_eliminados > 0:
        print(f"[dict] {n_eliminados} duplicados exactos eliminados.")

    mask_cod = df["codigo_categoria"].ne("")
    dup_mask = df[mask_cod].duplicated(
        subset=["nombre_variable", "codigo_categoria"], keep=False
    )
    dups = df[mask_cod][dup_mask]
    if not dups.empty:
        n_pares = dups.groupby(["nombre_variable", "codigo_categoria"]).ngroups
        warnings.warn(
            f"[dict] {n_pares} pares (variable, codigo) con categorias distintas. "
            "Se conserva la primera ocurrencia (DT-004).",
            stacklevel=2,
        )
        df_cod = df[mask_cod].drop_duplicates(
            subset=["nombre_variable", "codigo_categoria"], keep="first"
        )
        df_sin_cod = df[~mask_cod]
        df = pd.concat([df_cod, df_sin_cod], ignore_index=True)

    return df.reset_index(drop=True)


def construir_mapeos(df: pd.DataFrame) -> dict[str, dict[str, str]]:
    """
    Construye {variable: {codigo: categoria}} desde el diccionario limpio.
    Incorpora MAPEOS_COMPLEMENTARIOS para variables sin codigos.
    """
    mask = df["codigo_categoria"].ne("")
    df_cod = df[mask].copy()

    mapeos: dict[str, dict[str, str]] = {}
    for var, grp in df_cod.groupby("nombre_variable"):
        mapeos[var] = dict(zip(grp["codigo_categoria"], grp["categoria"]))

    for var, mapa in MAPEOS_COMPLEMENTARIOS.items():
        if var not in mapeos:
            mapeos[var] = mapa
        else:
            for key, value in mapa.items():
                mapeos[var].setdefault(key, value)

    return mapeos


def construir_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una fila por variable con sus metadatos."""
    cols_meta = [
        "nombre_variable",
        "etiqueta_variable",
        "descripcion",
        "pregunta_literal",
        "tipo_variable",
    ]
    cols_presentes = [col for col in cols_meta if col in df.columns]
    return (
        df[cols_presentes]
        .drop_duplicates(subset=["nombre_variable"], keep="first")
        .reset_index(drop=True)
    )


def validar_cobertura(
    cols_base: list[str],
    mapeos: dict[str, dict[str, str]],
    df_diccionario: pd.DataFrame,
) -> dict:
    """
    Compara columnas de la base contra mapeos disponibles.
    """
    vars_con_mapeo = [var for var in cols_base if var in mapeos]
    vars_sin_mapeo = [var for var in cols_base if var not in mapeos]
    vars_en_dic = df_diccionario["nombre_variable"].unique().tolist()
    vars_en_dic_no_base = [var for var in vars_en_dic if var not in cols_base]

    return {
        "vars_base": len(cols_base),
        "vars_con_mapeo": len(vars_con_mapeo),
        "vars_sin_mapeo": len(vars_sin_mapeo),
        "lista_sin_mapeo": sorted(vars_sin_mapeo)[:50],
        "vars_en_dic_no_base": len(vars_en_dic_no_base),
        "cobertura": len(vars_con_mapeo) / len(cols_base) if cols_base else 0.0,
    }


def aplicar_labels(
    df,
    mapeos: dict[str, dict[str, str]],
    variables: list[str] | None = None,
):
    """
    Agrega columnas <var>_label para las variables en mapeos.
    Conserva la columna original. Acepta pandas o polars.
    """
    try:
        import polars as pl
    except ModuleNotFoundError:
        pl = None

    if variables is None:
        variables = list(mapeos.keys())

    if pl is not None and isinstance(df, pl.DataFrame):
        exprs = []
        for var in variables:
            if var not in df.columns or var not in mapeos:
                continue
            mapa = mapeos[var]
            exprs.append(
                pl.col(var)
                .cast(pl.Utf8)
                .replace(list(mapa.keys()), list(mapa.values()), default=None)
                .alias(f"{var}_label")
            )
        return df.with_columns(exprs) if exprs else df

    df = df.copy()
    for var in variables:
        if var not in df.columns or var not in mapeos:
            continue
        df[f"{var}_label"] = df[var].astype(str).map(mapeos[var])
    return df


def generar_reporte_cobertura(cobertura: dict, path: Path | None = None) -> None:
    """Escribe reporte_cobertura_diccionario.md."""
    if path is None:
        path = REPORTE_COBERTURA_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Reporte de cobertura del diccionario\n",
        f"- Variables en la base: **{cobertura['vars_base']}**",
        f"- Variables con mapeo: **{cobertura['vars_con_mapeo']}**",
        f"- Variables sin mapeo: **{cobertura['vars_sin_mapeo']}**",
        f"- Cobertura: **{cobertura['cobertura']:.1%}**",
        f"- Variables en diccionario no presentes en base: **{cobertura['vars_en_dic_no_base']}**",
        "\n## Variables sin mapeo (primeras 50)\n",
    ]
    for var in cobertura["lista_sin_mapeo"]:
        lines.append(f"- `{var}`")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[dict] Reporte guardado -> {path}")


def procesar_diccionario(
    guardar: bool = True,
) -> tuple[pd.DataFrame, dict[str, dict[str, str]], pd.DataFrame]:
    """
    Pipeline completo del diccionario.
    """
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df_raw = cargar_diccionario_raw()
    df_limpio = limpiar_diccionario(df_raw)
    mapeos = construir_mapeos(df_limpio)
    metadata = construir_metadata(df_limpio)

    if guardar:
        df_limpio.to_parquet(DICCIONARIO_LIMPIO_PATH, index=False)
        with open(MAPEOS_JSON_PATH, "w", encoding="utf-8") as file:
            json.dump(mapeos, file, ensure_ascii=False, indent=2)
        metadata.to_parquet(METADATA_VARS_PATH, index=False)
        print(
            f"[dict] Procesado: {len(df_limpio)} filas, "
            f"{len(mapeos)} variables con mapeo."
        )

    return df_limpio, mapeos, metadata
