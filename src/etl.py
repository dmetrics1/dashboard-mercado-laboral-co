"""
Pipeline ETL principal del proyecto.
Carga datos, aplica diccionario, calcula indicadores y guarda parquet.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import polars as pl

import src.config as config
from src.dictionary import (
    aplicar_labels,
    cargar_diccionario_raw,
    generar_reporte_cobertura,
    limpiar_diccionario,
    procesar_diccionario,
    validar_cobertura,
)
from src.indicators import (
    asignar_grupo_edad,
    asignar_grupo_edad_brecha,
    calcular_dimension,
)
from src.loaders import cargar_todos

DIMENSIONES: dict[str, list[str] | None] = {
    "nacional": None,
    "departamento": ["DPTO_label"],
    "ciudad": ["AREA_label"],
    "sexo": ["P3271_label"],
    "edad": ["grupo_edad"],
    "sexo_edad": ["P3271_label", "grupo_edad"],
    "edad_brecha": ["grupo_edad_brecha"],
    "sector": ["RAMA2D_R4_label"],
    "clase": ["CLASE_label"],
    "estado_civil": ["P6070_label"],
    "educacion": ["P3042_label"],
    "posicion_ocupacional": ["P6430_label"],
}

DATA_PROCESSED_DIR = config.DATA_PROCESSED_DIR
INDICADORES_PATH = config.INDICADORES_PATH
REPORTE_COBERTURA_PATH = config.REPORTE_COBERTURA_PATH


def _resolver_anos() -> list[int]:
    for value in config.__dict__.values():
        if isinstance(value, list) and value == [2022, 2023, 2024, 2025]:
            return value
    raise AttributeError("No se pudo resolver la lista de anos en src.config")


def _resolver_columna_ano(columnas: list[str]) -> str:
    for candidata in ("_año", "_aÃ±o", "_aÃƒÂ±o"):
        if candidata in columnas:
            return candidata
    for columna in columnas:
        if columna.startswith("_a"):
            return columna
    raise KeyError("No se encontro la columna de ano en la base cargada")


def run(anos: list[int] | None = None, guardar: bool = True) -> pl.DataFrame:
    """Pipeline completo del ETL."""
    if anos is None:
        anos = _resolver_anos()

    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Paso 1 - Procesando diccionario")
    _, mapeos, _ = procesar_diccionario(guardar=guardar)

    print("=" * 60)
    print("Paso 2 - Cargando bases anuales")
    df = cargar_todos(anos, columnas=config.VARS_DASHBOARD)
    por_base = [_resolver_columna_ano(df.columns), "MES"]

    print("=" * 60)
    print("Paso 3 - Validando cobertura y aplicando labels")
    df_dic = limpiar_diccionario(cargar_diccionario_raw())
    cob = validar_cobertura(df.columns, mapeos, df_dic)
    print(
        f"  Cobertura: {cob['cobertura']:.1%} "
        f"({cob['vars_con_mapeo']} de {cob['vars_base']} variables)"
    )
    if guardar:
        generar_reporte_cobertura(cob, REPORTE_COBERTURA_PATH)

    df = aplicar_labels(df, mapeos)
    df = asignar_grupo_edad(df)
    df = asignar_grupo_edad_brecha(df)

    print("=" * 60)
    print("Paso 4 - Calculando indicadores")
    resultados: list[pl.DataFrame] = []

    for dim_nombre, dim_cols in DIMENSIONES.items():
        if dim_cols and any(col not in df.columns for col in dim_cols):
            print(f"  AVISO: '{dim_nombre}' omitida - columna {dim_cols} no existe.")
            continue
        try:
            ind = calcular_dimension(df, por_base, dim_cols, dim_nombre)
            resultados.append(ind)
            print(f"  {dim_nombre}: {ind.shape[0]:,} filas")
        except Exception as exc:
            print(f"  AVISO: '{dim_nombre}' fallo - {exc}")

    if not resultados:
        raise RuntimeError("No se calculo ningun indicador.")

    df_ind = pl.concat(resultados, how="diagonal_relaxed")

    if guardar:
        df_ind.write_parquet(INDICADORES_PATH)
        print("=" * 60)
        print(f"Indicadores guardados -> {INDICADORES_PATH}")
        print(f"  {df_ind.shape[0]:,} filas x {df_ind.shape[1]} columnas")

    return df_ind


if __name__ == "__main__":
    run()
