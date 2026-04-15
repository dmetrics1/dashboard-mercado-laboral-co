"""
Validación de la TD calculada vs cifras oficiales DANE.
Tolerancia: TD_TOLERANCIA_PP (0.2 p.p.) definida en config.py.

Fuente oficial:
https://www.dane.gov.co/index.php/estadisticas-por-tema/mercado-laboral/empleo-y-desempleo
"""
import sys
from pathlib import Path

# Permite ejecutar directamente: python src/validate.py
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from src.config import INDICADORES_PATH, TD_TOLERANCIA_PP

# ── Cifras oficiales DANE (boletines mensuales, total nacional) ───────────────
# Actualizar con cada publicación del DANE.
# Formato: (año, mes): TD_porcentaje
TD_OFICIAL: dict[tuple[int, int], float] = {
    (2022, 1): 13.7,
    (2022, 2): 12.9,
    (2022, 3): 12.5,
    (2022, 4): 11.3,
    (2022, 5): 10.6,
    (2022, 6): 10.8,
    (2022, 7): 10.7,
    (2022, 8): 10.0,
    (2022, 9): 10.5,
    (2022, 10): 9.7,
    (2022, 11): 9.9,
    (2022, 12): 10.3,
    (2023, 1): 13.3,
    (2023, 2): 12.3,
    (2023, 3): 11.3,
    (2023, 4): 10.3,
    (2023, 5): 9.3,
    (2023, 6): 9.5,
    (2023, 7): 9.7,
    (2023, 8): 9.4,
    (2023, 9): 10.0,
    (2023, 10): 9.0,
    (2023, 11): 9.1,
    (2023, 12): 9.5,
    (2024, 1): 12.2,
    (2024, 2): 11.7,
    (2024, 3): 10.5,
    (2024, 4): 9.5,
    (2024, 5): 9.0,
    (2024, 6): 9.4,
    (2024, 7): 9.8,
    (2024, 8): 9.3,
    (2024, 9): 9.5,
    (2024, 10): 8.9,
    (2024, 11): 9.4,
    (2024, 12): 9.7,
}


def comparar_td(
    df_ind: pd.DataFrame,
    tolerancia: float = TD_TOLERANCIA_PP,
) -> pd.DataFrame:
    """
    Compara TD calculada vs cifras oficiales DANE (nivel nacional).

    Parámetros
    ----------
    df_ind : DataFrame con columnas año, mes, dimension, TD
    tolerancia : diferencia máxima aceptable en puntos porcentuales

    Retorna
    -------
    DataFrame con columnas: año, mes, TD, TD_oficial, diferencia, pasa
    """
    nacional = df_ind[df_ind["dimension"] == "nacional"][
        ["año", "mes", "TD"]
    ].copy()

    nacional["TD_oficial"] = nacional.apply(
        lambda r: TD_OFICIAL.get((int(r["año"]), int(r["mes"]))),
        axis=1,
    )
    nacional = nacional[nacional["TD_oficial"].notna()].copy()

    if nacional.empty:
        return nacional

    nacional["diferencia"] = (nacional["TD"] - nacional["TD_oficial"]).abs()
    nacional["pasa"] = nacional["diferencia"] <= tolerancia

    return nacional.sort_values(["año", "mes"]).reset_index(drop=True)


def reporte_validacion(df_ind: pd.DataFrame | None = None) -> None:
    """
    Imprime reporte de validación. Si df_ind es None, carga desde parquet.
    """
    if df_ind is None:
        if not INDICADORES_PATH.exists():
            print(
                "[validate] No existe indicadores_mensuales.parquet. "
                "Ejecuta primero: python src/etl.py"
            )
            return
        df_ind = pd.read_parquet(INDICADORES_PATH)

    comp = comparar_td(df_ind)

    if comp.empty:
        print("[validate] Sin cifras oficiales para comparar.")
        return

    total = len(comp)
    pasa = int(comp["pasa"].sum())

    print(f"\n{'='*60}")
    print(f"Validación TD — tolerancia ±{TD_TOLERANCIA_PP} p.p.")
    print(f"{'='*60}")
    print(f"  Periodos comparados : {total}")
    print(f"  Pasan               : {pasa}/{total}  ({pasa/total:.0%})")
    print(f"  Diferencia máxima   : {comp['diferencia'].max():.2f} p.p.")
    print(f"  Diferencia media    : {comp['diferencia'].mean():.2f} p.p.")

    fallos = comp[~comp["pasa"]]
    if not fallos.empty:
        print("\n  Periodos fuera de tolerancia:")
        print(
            fallos[["año", "mes", "TD", "TD_oficial", "diferencia"]]
            .to_string(index=False)
        )
    else:
        print("\n  Todos los periodos dentro de tolerancia.")


if __name__ == "__main__":
    reporte_validacion()
