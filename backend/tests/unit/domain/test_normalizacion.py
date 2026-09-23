"""Tests de T-05 (Dominio: normalización).

Cubre RN-01, RN-02 y RN-03 mediante `normalizar` y `normalizar_y_validar`.
Funciones puras, sin dependencias: no hace falta ningún doble de prueba.
"""

import pytest

from app.domain.errores import FraseInvalida
from app.domain.normalizacion import LONGITUD_MINIMA, normalizar, normalizar_y_validar


def test_ac01_texto_de_solo_espacios_lanza_frase_invalida() -> None:
    with pytest.raises(FraseInvalida):
        normalizar_y_validar("  ", longitud_maxima=280)


def test_ac01_texto_de_dos_caracteres_lanza_frase_invalida() -> None:
    with pytest.raises(FraseInvalida):
        normalizar_y_validar("ab", longitud_maxima=280)


def test_ac01_texto_de_solo_tabulaciones_y_saltos_de_linea_lanza_frase_invalida_b04() -> None:
    with pytest.raises(FraseInvalida):
        normalizar_y_validar("\t\n\t", longitud_maxima=280)


def test_ac01_texto_de_tres_caracteres_se_acepta_b07() -> None:
    resultado = normalizar_y_validar("abc", longitud_maxima=280)

    assert resultado == "abc"
    assert len(resultado) == LONGITUD_MINIMA


def test_ac01_texto_que_normaliza_a_dos_caracteres_lanza_frase_invalida() -> None:
    with pytest.raises(FraseInvalida):
        normalizar_y_validar("  ab  ", longitud_maxima=280)


def test_ac02_texto_normalizado_de_281_caracteres_se_rechaza_y_menciona_el_maximo() -> None:
    texto = "a" * 281

    with pytest.raises(FraseInvalida) as excinfo:
        normalizar_y_validar(texto, longitud_maxima=280)

    assert "280" in str(excinfo.value)


def test_ac02_texto_normalizado_de_280_caracteres_se_acepta_b06() -> None:
    texto = "a" * 280

    resultado = normalizar_y_validar(texto, longitud_maxima=280)

    assert len(resultado) == 280


def test_ac02_texto_crudo_de_300_caracteres_que_normaliza_a_250_se_acepta() -> None:
    # 125 + 51 espacios + 124 = 300 caracteres crudos.
    # Tras colapsar los 51 espacios en uno solo: 125 + 1 + 124 = 250.
    texto_crudo = ("a" * 125) + (" " * 51) + ("b" * 124)
    assert len(texto_crudo) == 300

    resultado = normalizar_y_validar(texto_crudo, longitud_maxima=280)

    assert len(resultado) == 250


def test_ac02_la_longitud_se_mide_en_puntos_de_codigo_280_emojis_se_acepta() -> None:
    texto = "😀" * 280
    assert len(texto) == 280

    resultado = normalizar_y_validar(texto, longitud_maxima=280)

    assert len(resultado) == 280


def test_ac03_espacios_sobrantes_mayusculas_y_bordes_se_normalizan() -> None:
    assert normalizar("  el PAGO   fue rechazado ") == "el pago fue rechazado"


def test_ac03_tabulaciones_y_saltos_de_linea_cuentan_como_espacios() -> None:
    assert normalizar("el pago\tfue\nrechazado") == "el pago fue rechazado"


def test_espacio_duro_y_espacio_de_ancho_fijo_se_colapsan_b17() -> None:
    texto = "el pago fue rechazado"  # noqa: RUF001

    assert normalizar(texto) == "el pago fue rechazado"


def test_ligadura_nfkc_se_descompone_en_letras_separadas() -> None:
    assert normalizar("ﬁnanzas") == "finanzas"


def test_caracteres_de_ancho_completo_nfkc_se_normalizan_a_ascii() -> None:
    assert normalizar("Ｈｏｌａ") == "hola"  # noqa: RUF001


def test_los_acentos_se_conservan_y_no_igualan_a_su_forma_sin_acento_b11() -> None:
    normalizado = normalizar("Teléfono")

    assert normalizado == "teléfono"
    assert normalizado != "telefono"


def test_los_emojis_se_conservan_b05() -> None:
    assert normalizar("Todo salió bien 🎉") == "todo salió bien 🎉"


@pytest.mark.parametrize("control", ["\x00", "\x07", "\x1b", "\x7f", "\x9f"])
def test_ac01_caracter_de_control_que_no_es_espacio_lanza_frase_invalida_b27(
    control: str,
) -> None:
    with pytest.raises(FraseInvalida) as excinfo:
        normalizar_y_validar(f"el pago{control} fue rechazado", longitud_maxima=280)

    assert str(excinfo.value) == "La frase contiene caracteres no permitidos."


@pytest.mark.parametrize(
    "espacio", ["\t", "\n", "\r", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x1f", "\x85"]
)
def test_ac01_caracter_de_control_que_es_espacio_se_colapsa_y_se_acepta_b27(
    espacio: str,
) -> None:
    resultado = normalizar_y_validar(f"el pago{espacio}fue rechazado", longitud_maxima=280)

    assert resultado == "el pago fue rechazado"
