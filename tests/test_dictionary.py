"""
Tests para src/dictionary.py
"""
import warnings

import pandas as pd
import pytest

from src.dictionary import (
    aplicar_labels,
    construir_mapeos,
    construir_metadata,
    limpiar_diccionario,
    validar_cobertura,
)
from src.config import MAPEOS_COMPLEMENTARIOS


def _dic_minimo() -> pd.DataFrame:
    """DataFrame mínimo con la estructura del diccionario real."""
    return pd.DataFrame(
        {
            "nombre_variable": ["AREA", "AREA", "AREA", "P6430", "P6430", "P3271"],
            "etiqueta_variable": [
                "Área",
                "Área",
                "Área",
                "Posición ocupacional",
                "Posición ocupacional",
                "Sexo",
            ],
            "descripcion": [""] * 6,
            "pregunta_literal": [""] * 6,
            "tipo_variable": ["categórica"] * 6,
            "codigo_categoria": ["05", "08", "11", "1", "2", ""],
            "categoria": [
                "Medellín AM",
                "Barranquilla AM",
                "Bogotá DC",
                "Empleado particular",
                "Empleado del gobierno",
                "",
            ],
        }
    )


def test_limpiar_preserva_ceros():
    df = _dic_minimo()
    limpio = limpiar_diccionario(df)
    codigos_area = limpio[limpio["nombre_variable"] == "AREA"]["codigo_categoria"].tolist()
    assert "05" in codigos_area, "El cero a la izquierda de '05' se perdió"


def test_limpiar_elimina_duplicados_exactos():
    df = _dic_minimo()
    df_dup = pd.concat([df, df], ignore_index=True)
    limpio = limpiar_diccionario(df_dup)
    assert len(limpio) == len(_dic_minimo())


def test_limpiar_detecta_conflicto_codigos():
    df = _dic_minimo().copy()
    # Agregar fila conflictiva: mismo (variable, código), distinta categoría
    conflicto = pd.DataFrame(
        {
            "nombre_variable": ["AREA"],
            "etiqueta_variable": ["Área"],
            "descripcion": [""],
            "pregunta_literal": [""],
            "tipo_variable": ["categórica"],
            "codigo_categoria": ["05"],
            "categoria": ["Otra ciudad"],
        }
    )
    df_conflicto = pd.concat([df, conflicto], ignore_index=True)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        limpiar_diccionario(df_conflicto)
    assert any("DT-004" in str(x.message) for x in w), "No se emitió warning DT-004"


def test_construir_mapeos_incluye_complementarios():
    df = _dic_minimo()
    limpio = limpiar_diccionario(df)
    mapeos = construir_mapeos(limpio)
    # P3271 no tiene codigo_categoria en el fixture → viene de MAPEOS_COMPLEMENTARIOS
    assert "P3271" in mapeos
    assert mapeos["P3271"].get("1") == "Hombre"
    assert mapeos["P3271"].get("2") == "Mujer"


def test_construir_mapeos_rama2d_r4_desde_protocolo():
    df = _dic_minimo()
    limpio = limpiar_diccionario(df)
    mapeos = construir_mapeos(limpio)
    assert "RAMA2D_R4" in mapeos
    assert mapeos["RAMA2D_R4"]["1"] == "Agro, caza, pesca"
    assert mapeos["RAMA2D_R4"]["35"] == "Electricidad, gas, agua, desechos"
    assert mapeos["RAMA2D_R4"]["68"] == "Inmobiliarias"
    assert mapeos["RAMA2D_R4"]["96"] == "Artes, recreacion y otros servicios"


def test_construir_mapeos_area():
    df = _dic_minimo()
    limpio = limpiar_diccionario(df)
    mapeos = construir_mapeos(limpio)
    assert mapeos["AREA"]["05"] == "Medellín AM"
    assert mapeos["AREA"]["11"] == "Bogotá DC"


def test_aplicar_labels_crea_columna():
    df_datos = pd.DataFrame({"AREA": ["05", "08", "11", None]})
    mapeos = {"AREA": {"05": "Medellín AM", "08": "Barranquilla AM", "11": "Bogotá DC"}}
    resultado = aplicar_labels(df_datos, mapeos)
    assert "AREA_label" in resultado.columns
    assert resultado.loc[0, "AREA_label"] == "Medellín AM"
    assert resultado.loc[2, "AREA_label"] == "Bogotá DC"
    # Columna original intacta
    assert resultado.loc[0, "AREA"] == "05"


def test_aplicar_labels_no_modifica_original():
    df_datos = pd.DataFrame({"AREA": ["05", "08"]})
    mapeos = {"AREA": {"05": "Medellín AM", "08": "Barranquilla AM"}}
    resultado = aplicar_labels(df_datos, mapeos)
    assert list(resultado["AREA"]) == ["05", "08"]


def test_aplicar_labels_rama2d_r4_con_codigos_enteros():
    df_datos = pd.DataFrame({"RAMA2D_R4": [1, 35, 68, 96, 0]})
    resultado = aplicar_labels(
        df_datos,
        {"RAMA2D_R4": MAPEOS_COMPLEMENTARIOS["RAMA2D_R4"]},
    )
    assert resultado["RAMA2D_R4_label"].tolist() == [
        "Agro, caza, pesca",
        "Electricidad, gas, agua, desechos",
        "Inmobiliarias",
        "Artes, recreacion y otros servicios",
        "No clasificado",
    ]


def test_validar_cobertura():
    df = _dic_minimo()
    limpio = limpiar_diccionario(df)
    mapeos = construir_mapeos(limpio)
    cols_base = ["AREA", "P6430", "P3271", "COLUMNA_SIN_MAPEO"]
    cob = validar_cobertura(cols_base, mapeos, limpio)
    assert cob["vars_base"] == 4
    assert cob["vars_con_mapeo"] == 3
    assert "COLUMNA_SIN_MAPEO" in cob["lista_sin_mapeo"]
    assert cob["cobertura"] == pytest.approx(0.75)


def test_construir_metadata_una_fila_por_variable():
    df = _dic_minimo()
    limpio = limpiar_diccionario(df)
    meta = construir_metadata(limpio)
    # AREA aparece 3 veces en el diccionario, metadata debe tener 1 fila
    assert meta[meta["nombre_variable"] == "AREA"].shape[0] == 1
