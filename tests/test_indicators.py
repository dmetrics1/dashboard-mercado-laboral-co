"""
Tests para src/indicators.py - backend Polars
"""
import numpy as np
import polars as pl
import pytest

from src.indicators import (
    _agg_ingreso_mediano,
    _agg_mercado_laboral,
    _mediana_ponderada,
    asignar_grupo_edad,
    asignar_grupo_edad_brecha,
    calcular_dimension,
)


def _df_base() -> pl.DataFrame:
    """DataFrame minimo con variables laborales y poblacionales."""
    return pl.DataFrame(
        {
            "_ano": [2022] * 8,
            "MES": [1] * 8,
            "PT": [1] * 8,
            "FT": [1, 1, 1, 1, 0, 1, 0, 0],
            "P6040": [20, 30, 45, 60, 17, 25, 35, 50],
            "OCI": [1, 1, 1, 0, 0, 0, 1, 1],
            "DSI": [0, 0, 0, 1, 0, 1, 0, 0],
            "FEX_C18": [100.0, 200.0, 150.0, 80.0, 50.0, 120.0, 90.0, 110.0],
            "P6500": [
                1_500_000.0,
                2_000_000.0,
                1_800_000.0,
                None,
                None,
                None,
                1_200_000.0,
                3_000_000.0,
            ],
            "AREA_label": [
                "Bogota",
                "Bogota",
                "Medellin",
                "Medellin",
                "Bogota",
                "Bogota",
                "Medellin",
                "Medellin",
            ],
        }
    )


def test_mediana_ponderada_pesos_iguales():
    v = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    w = np.ones(5)
    assert _mediana_ponderada(v, w) == 3.0


def test_mediana_ponderada_peso_concentrado():
    v = np.array([1.0, 10.0, 100.0])
    w = np.array([1.0, 100.0, 1.0])
    assert _mediana_ponderada(v, w) == 10.0


def test_mediana_ponderada_todos_nan():
    v = np.array([np.nan, np.nan])
    w = np.array([1.0, 1.0])
    assert np.isnan(_mediana_ponderada(v, w))


def test_td_nacional():
    df = _df_base()
    result = _agg_mercado_laboral(df, ["_ano", "MES"])
    td_esperada = 200 / (650 + 200) * 100
    assert result["TD"][0] == pytest.approx(td_esperada, abs=0.01)


def test_td_por_ciudad():
    df = _df_base()
    result = _agg_mercado_laboral(df, ["_ano", "MES", "AREA_label"])
    assert "AREA_label" in result.columns
    assert set(result["AREA_label"].to_list()) == {"Bogota", "Medellin"}


def test_td_columnas_faltantes():
    df = pl.DataFrame({"OCI": [1], "FEX_C18": [100.0]})
    with pytest.raises(KeyError):
        _agg_mercado_laboral(df, ["_ano"])


def test_tgp_mayor_igual_to():
    df = _df_base()
    result = _agg_mercado_laboral(df, ["_ano", "MES"])
    assert result["TGP"][0] >= result["TO"][0]


def test_ingreso_mediano_solo_ocupados():
    df = _df_base()
    result = _agg_ingreso_mediano(df, ["_ano", "MES"])
    assert "ingreso_mediano" in result.columns
    assert result["ingreso_mediano"][0] > 0


def test_ingreso_mediano_por_ciudad():
    df = _df_base()
    result = _agg_ingreso_mediano(df, ["_ano", "MES", "AREA_label"])
    assert len(result) == 2


def test_asignar_grupo_edad():
    df = pl.DataFrame({"P6040": [15, 24, 25, 34, 65, 80, 14]})
    result = asignar_grupo_edad(df)
    assert result["grupo_edad"][0] == "15-24"
    assert result["grupo_edad"][4] == "65+"
    assert result["grupo_edad"][6] is None


def test_asignar_grupo_edad_brecha():
    df = pl.DataFrame({"P6040": [15, 28, 29, 60, 14]})
    result = asignar_grupo_edad_brecha(df)
    assert result["grupo_edad_brecha"].to_list() == ["15-28", "15-28", "29+", "29+", None]


def test_calcular_dimension_nacional():
    df = _df_base()
    result = calcular_dimension(df, ["_ano", "MES"], None, "nacional")
    for col in ["poblacion_total_exp", "PEA_exp", "TD", "TO", "TGP", "ingreso_mediano", "dimension"]:
        assert col in result.columns
    assert result["dimension"][0] == "nacional"
    assert result["poblacion_total_exp"][0] == pytest.approx(900.0, abs=0.01)


def test_calcular_dimension_ciudad():
    df = _df_base()
    result = calcular_dimension(df, ["_ano", "MES"], ["AREA_label"], "ciudad")
    assert "AREA_label" in result.columns
    assert len(result) == 2


def test_calcular_dimension_columna_faltante():
    df = _df_base()
    with pytest.raises(KeyError):
        calcular_dimension(df, ["_ano", "MES"], ["COLUMNA_INEXISTENTE"], "test")
