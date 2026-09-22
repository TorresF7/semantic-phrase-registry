"""Tests de T-03 (Configuración por entorno).

No cubren ningún AC: la tarea es andamiaje puro (RN-06, B-24). Por eso los
nombres no llevan el prefijo `ac`.

Todas las construcciones usan `_env_file=None` para que la `Configuracion` no
lea ningún `.env` de la máquina de quien ejecuta los tests: el resultado debe
depender únicamente de las variables de entorno que cada test fija.
"""

import pytest
from pydantic import ValidationError

from app.config import Configuracion


def test_sin_variable_definida_existe_un_valor_por_defecto_dentro_de_rango_valido(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SIMILARITY_THRESHOLD", raising=False)

    configuracion = Configuracion(_env_file=None)

    assert 0.0 <= configuracion.umbral_similitud <= 1.0


def test_umbral_mayor_a_uno_hace_fallar_la_construccion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SIMILARITY_THRESHOLD", "1.5")

    with pytest.raises(ValidationError):
        Configuracion(_env_file=None)


def test_umbral_negativo_hace_fallar_la_construccion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SIMILARITY_THRESHOLD", "-0.1")

    with pytest.raises(ValidationError):
        Configuracion(_env_file=None)


def test_umbral_no_numerico_hace_fallar_la_construccion_b24(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SIMILARITY_THRESHOLD", "alto")

    with pytest.raises(ValidationError):
        Configuracion(_env_file=None)


@pytest.mark.parametrize("valor_extremo", ["0", "1"])
def test_los_extremos_del_rango_son_inclusivos_y_llegan_al_campo(
    monkeypatch: pytest.MonkeyPatch, valor_extremo: str
) -> None:
    monkeypatch.setenv("SIMILARITY_THRESHOLD", valor_extremo)

    configuracion = Configuracion(_env_file=None)

    assert configuracion.umbral_similitud == float(valor_extremo)
