"""Tests de T-05 (Dominio: política de umbral y recorte de puntaje).

Cubre RN-05 y RN-06 mediante `es_posible_duplicado` y `recortar_puntaje`.
No cubren un AC concreto: la política se ejercita completa dentro de los
casos de uso de T-07/T-08. Por eso los nombres no llevan el prefijo `ac`.
"""

from app.domain.politica import es_posible_duplicado, recortar_puntaje


def test_puntaje_igual_al_umbral_es_posible_duplicado_b08() -> None:
    assert es_posible_duplicado(0.80, umbral=0.80) is True


def test_puntaje_justo_debajo_del_umbral_no_es_posible_duplicado() -> None:
    assert es_posible_duplicado(0.7999999999, umbral=0.80) is False


def test_puntaje_redondeado_alcanza_el_umbral_pero_sin_redondear_no_b16() -> None:
    assert es_posible_duplicado(0.79996, umbral=0.80) is False


def test_puntaje_nulo_no_es_posible_duplicado() -> None:
    assert es_posible_duplicado(None, umbral=0.80) is False


def test_umbral_cero_con_puntaje_cero_es_posible_duplicado() -> None:
    assert es_posible_duplicado(0.0, umbral=0.0) is True


def test_puntaje_negativo_se_recorta_a_cero_b15() -> None:
    assert recortar_puntaje(-0.033) == 0.0


def test_puntaje_mayor_a_uno_por_redondeo_se_recorta_a_uno_b15() -> None:
    assert recortar_puntaje(1.0000002) == 1.0


def test_puntaje_dentro_de_rango_no_cambia() -> None:
    assert recortar_puntaje(0.5) == 0.5
