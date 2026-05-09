"""
Tabla de validación: indicadores calculados vs cifras oficiales DANE.

Ejecutar desde la raíz del proyecto:
    python scripts/tabla_validacion.py

Fuente oficial: data/raw/Danes_datos_en_miles.xlsx
  - Tasas (TD, TO, TGP) en porcentaje
  - Poblaciones en miles de personas

Fuente calculada: data/processed/indicadores_mensuales.parquet
  - Tasas en porcentaje
  - Poblaciones en personas (se convierten a miles para comparar)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np

from src.config import INDICADORES_PATH

EXCEL_PATH = Path(__file__).parent.parent / "data" / "raw" / "Danes_datos_en_miles.xlsx"

MESES_ES = {
    "Ene": 1, "Feb": 2, "Mar": 3, "Abr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Ago": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dic": 12,
}

# Filas del Excel → nombre interno
FILAS_INTERES = {
    "Tasa Global de Participaci��m (TGP)": "TGP_dane",
    "Tasa de Ocupaci��m (TO)":              "TO_dane",
    "Tasa de Desocupaci��m (TD)":           "TD_dane",
    "Poblaci��m total":                     "pob_total_miles_dane",
    "Poblaci��m en edad de trabajar (PET)": "PET_miles_dane",
    "Fuerza de trabajo":                             "PEA_miles_dane",
    "Poblaci��m ocupada":                   "ocupados_miles_dane",
    "Poblaci��m desocupada":                "desocupados_miles_dane",
}

# Versión con tildes tal como puede venir según la codificación
FILAS_INTERES_ALT = {
    "Tasa Global de Participación (TGP)": "TGP_dane",
    "Tasa de Ocupación (TO)":             "TO_dane",
    "Tasa de Desocupación (TD)":          "TD_dane",
    "Población total":                    "pob_total_miles_dane",
    "Población en edad de trabajar (PET)":"PET_miles_dane",
    "Fuerza de trabajo":                  "PEA_miles_dane",
    "Población ocupada":                  "ocupados_miles_dane",
    "Población desocupada":               "desocupados_miles_dane",
}


def leer_excel_dane() -> pd.DataFrame:
    """
    Carga el Excel DANE (formato ancho: filas=indicadores, columnas=meses).
    Devuelve DataFrame largo con columnas: _año, MES, + un col por indicador.
    """
    raw = pd.read_excel(EXCEL_PATH, header=None)

    # Fila 0: años repetidos (2022, 2022, ..., 2025)
    # Fila 1: meses (Ene, Feb, ..., Dic) × 4 años
    # Col 0 : nombre del indicador
    años_row  = raw.iloc[0, 1:].values
    meses_row = raw.iloc[1, 1:].values

    # Construir índice temporal
    periodos = []
    for año, mes in zip(años_row, meses_row):
        try:
            periodos.append((int(año), MESES_ES.get(str(mes).strip(), None)))
        except (ValueError, TypeError):
            periodos.append((None, None))

    # Detectar mapeo correcto de filas (tolera diferencias de codificación)
    mapeo = {}
    for i, row in raw.iterrows():
        nombre = str(row.iloc[0]).strip()
        for diccionario in (FILAS_INTERES_ALT, FILAS_INTERES):
            if nombre in diccionario:
                mapeo[diccionario[nombre]] = raw.iloc[i, 1:].values
                break

    # Armar DataFrame largo
    filas = []
    for (año, mes), col_idx in zip(periodos, range(len(periodos))):
        if año is None or mes is None:
            continue
        fila = {"_año": int(año), "MES": int(mes)}
        for col_name, valores in mapeo.items():
            try:
                fila[col_name] = float(valores[col_idx])
            except (ValueError, TypeError):
                fila[col_name] = np.nan
        filas.append(fila)

    return pd.DataFrame(filas).sort_values(["_año", "MES"]).reset_index(drop=True)


def leer_parquet_nacional() -> pd.DataFrame:
    if not INDICADORES_PATH.exists():
        raise FileNotFoundError(
            f"No existe {INDICADORES_PATH}.\n"
            "Ejecuta primero: python src/etl.py"
        )
    df = pd.read_parquet(INDICADORES_PATH)
    nac = df[df["dimension"] == "nacional"].copy()

    # Convertir poblaciones a miles para comparar con DANE
    for col_exp, col_miles in [
        ("poblacion_total_exp", "pob_total_miles_calc"),
        ("PEA_exp",             "PEA_miles_calc"),
        ("ocupados_exp",        "ocupados_miles_calc"),
        ("desocupados_exp",     "desocupados_miles_calc"),
    ]:
        if col_exp in nac.columns:
            nac[col_miles] = nac[col_exp] / 1_000

    return nac[
        ["_año", "MES"]
        + [c for c in ["TD", "TO", "TGP", "tasa_informalidad",
                        "pob_total_miles_calc", "PEA_miles_calc",
                        "ocupados_miles_calc", "desocupados_miles_calc",
                        "ingreso_mediano"]
           if c in nac.columns]
    ].sort_values(["_año", "MES"]).reset_index(drop=True)


def construir_comparacion(calc: pd.DataFrame, dane: pd.DataFrame) -> pd.DataFrame:
    comp = calc.merge(dane, on=["_año", "MES"], how="left")

    # Diferencias absolutas en tasas
    for indicador in ["TD", "TO", "TGP"]:
        col_calc = indicador
        col_dane = f"{indicador}_dane"
        if col_calc in comp.columns and col_dane in comp.columns:
            comp[f"dif_{indicador}"] = (comp[col_calc] - comp[col_dane]).abs()

    # Diferencias en poblaciones (miles)
    for par in [("pob_total_miles_calc", "pob_total_miles_dane", "dif_pob_total_miles"),
                ("PEA_miles_calc",       "PEA_miles_dane",       "dif_PEA_miles"),
                ("ocupados_miles_calc",  "ocupados_miles_dane",  "dif_ocupados_miles"),
                ("desocupados_miles_calc","desocupados_miles_dane","dif_desocupados_miles")]:
        c, d, dif = par
        if c in comp.columns and d in comp.columns:
            comp[dif] = (comp[c] - comp[d]).abs()

    return comp


def tabla_anual(comp: pd.DataFrame) -> pd.DataFrame:
    agg = {}
    for col in comp.columns:
        if col not in ("_año", "MES"):
            agg[col] = "mean"
    agg["MES"] = "count"

    t = comp.groupby("_año").agg(agg).reset_index()
    t = t.rename(columns={"MES": "meses"})
    return t.sort_values("_año")


def imprimir_mensual(comp: pd.DataFrame) -> None:
    sep = "=" * 120
    cols_tasas = ["_año", "MES",
                  "TD", "TD_dane", "dif_TD",
                  "TO", "TO_dane", "dif_TO",
                  "TGP", "TGP_dane", "dif_TGP"]
    cols_pob   = ["_año", "MES",
                  "pob_total_miles_calc", "pob_total_miles_dane", "dif_pob_total_miles",
                  "PEA_miles_calc",       "PEA_miles_dane",       "dif_PEA_miles",
                  "ocupados_miles_calc",  "ocupados_miles_dane",  "dif_ocupados_miles",
                  "desocupados_miles_calc","desocupados_miles_dane","dif_desocupados_miles"]

    disponibles_tasas = [c for c in cols_tasas if c in comp.columns]
    disponibles_pob   = [c for c in cols_pob   if c in comp.columns]

    print(f"\n{sep}")
    print("COMPARACIÓN MENSUAL — TASAS (%) vs DANE oficial")
    print(sep)
    with pd.option_context("display.float_format", "{:.3f}".format,
                           "display.max_rows", 200, "display.width", 130):
        print(comp[disponibles_tasas].to_string(index=False))

    print(f"\n{sep}")
    print("COMPARACIÓN MENSUAL — POBLACIONES (miles de personas) vs DANE oficial")
    print(sep)
    with pd.option_context("display.float_format", "{:,.1f}".format,
                           "display.max_rows", 200, "display.width", 160):
        print(comp[disponibles_pob].to_string(index=False))


def imprimir_anual(t: pd.DataFrame) -> None:
    sep = "=" * 120
    print(f"\n{sep}")
    print("RESUMEN ANUAL — Promedios de meses disponibles")
    print(sep)

    header = (
        f"{'Año':>4}  {'Meses':>5}  "
        f"{'TD_calc':>7}  {'TD_DANE':>7}  {'±TD':>5}  "
        f"{'TO_calc':>7}  {'TO_DANE':>7}  {'±TO':>5}  "
        f"{'TGP_calc':>8}  {'TGP_DANE':>8}  {'±TGP':>5}  "
        f"{'Pob_calc(MM)':>12}  {'Pob_DANE(MM)':>12}  {'±Pob':>8}  "
        f"{'PEA_calc(MM)':>12}  {'PEA_DANE(MM)':>12}  {'±PEA':>8}"
    )
    print(header)
    print("-" * 120)

    def fmt(v, decimales=2):
        return f"{v:.{decimales}f}" if pd.notna(v) else "  n/d "

    for _, r in t.iterrows():
        pob_c = r.get("pob_total_miles_calc", np.nan) / 1_000 if pd.notna(r.get("pob_total_miles_calc")) else np.nan
        pob_d = r.get("pob_total_miles_dane", np.nan) / 1_000 if pd.notna(r.get("pob_total_miles_dane")) else np.nan
        dif_p = r.get("dif_pob_total_miles", np.nan)  / 1_000 if pd.notna(r.get("dif_pob_total_miles"))  else np.nan
        pea_c = r.get("PEA_miles_calc", np.nan) / 1_000 if pd.notna(r.get("PEA_miles_calc")) else np.nan
        pea_d = r.get("PEA_miles_dane", np.nan) / 1_000 if pd.notna(r.get("PEA_miles_dane")) else np.nan
        dif_a = r.get("dif_PEA_miles",  np.nan) / 1_000 if pd.notna(r.get("dif_PEA_miles"))  else np.nan

        print(
            f"{int(r['_año']):>4}  {int(r['meses']):>5}  "
            f"{fmt(r.get('TD')):>7}  {fmt(r.get('TD_dane')):>7}  {fmt(r.get('dif_TD')):>5}  "
            f"{fmt(r.get('TO')):>7}  {fmt(r.get('TO_dane')):>7}  {fmt(r.get('dif_TO')):>5}  "
            f"{fmt(r.get('TGP')):>8}  {fmt(r.get('TGP_dane')):>8}  {fmt(r.get('dif_TGP')):>5}  "
            f"{fmt(pob_c, 3):>12}  {fmt(pob_d, 3):>12}  {fmt(dif_p, 3):>8}  "
            f"{fmt(pea_c, 3):>12}  {fmt(pea_d, 3):>12}  {fmt(dif_a, 3):>8}"
        )

    print(sep)
    print("Notas:")
    print("  · TD / TO / TGP  : puntos porcentuales (%)")
    print("  · Pob / PEA      : millones de personas (promedio mensual del año)")
    print("  · ±              : diferencia absoluta calc vs DANE")
    print("  · n/d            : sin cifra DANE para ese período\n")


if __name__ == "__main__":
    print("Cargando Excel DANE ...")
    dane = leer_excel_dane()
    print(f"  OK: {len(dane)} meses DANE cargados ({dane['_año'].min()}-{dane['_año'].max()})")

    print("Cargando parquet calculado ...")
    calc = leer_parquet_nacional()
    print(f"  OK: {len(calc)} meses calculados ({calc['_año'].min()}-{calc['_año'].max()})")

    comp = construir_comparacion(calc, dane)
    t_anual = tabla_anual(comp)

    imprimir_anual(t_anual)
    imprimir_mensual(comp)

    # Exportar CSVs
    out = Path(__file__).parent.parent / "data" / "processed"
    comp.to_csv(out / "validacion_mensual.csv",   index=False, float_format="%.4f")
    t_anual.to_csv(out / "validacion_anual.csv",  index=False, float_format="%.4f")
    print(f"CSVs exportados en {out}/")
    print("  · validacion_mensual.csv")
    print("  · validacion_anual.csv")
