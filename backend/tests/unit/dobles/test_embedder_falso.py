"""Tests de T-06 (Puertos y dobles de prueba): `FakeEmbedder`.

T-06 no tiene AC propios: este doble sirve a AC-03 a AC-18 en T-07/T-08/T-12,
por eso los nombres no llevan el prefijo `ac`. Fija el contrato acordado en
`plan.md` §3: mismo texto normalizado da el mismo vector, se pueden fijar
vectores y puntajes concretos, cuenta invocaciones y puede simular un fallo
del proveedor.
"""

import math

import pytest

from app.domain.errores import ErrorProveedorEmbeddings
from tests.dobles.embedder_falso import FakeEmbedder


def _norma(vector: list[float]) -> float:
    return math.sqrt(sum(componente**2 for componente in vector))


def _coseno(a: list[float], b: list[float]) -> float:
    producto_punto = sum(x * y for x, y in zip(a, b, strict=True))
    return producto_punto / (_norma(a) * _norma(b))


def test_nombre_modelo_y_dimension_usan_los_valores_por_defecto() -> None:
    embedder = FakeEmbedder()

    assert embedder.nombre_modelo == "modelo-falso"
    assert embedder.dimension == 384


def test_nombre_modelo_y_dimension_se_pueden_configurar() -> None:
    embedder = FakeEmbedder(nombre_modelo="otro-modelo", dimension=10)

    assert embedder.nombre_modelo == "otro-modelo"
    assert embedder.dimension == 10


def test_generar_sin_nada_fijado_devuelve_un_vector_de_la_dimension_configurada() -> None:
    embedder = FakeEmbedder(dimension=10)

    vector = embedder.generar("una frase cualquiera")

    assert len(vector) == 10


def test_generar_sin_nada_fijado_es_determinista_para_el_mismo_texto() -> None:
    embedder = FakeEmbedder()

    primero = embedder.generar("El pago fue rechazado")
    segundo = embedder.generar("El pago fue rechazado")

    assert primero == segundo


def test_generar_sin_nada_fijado_da_el_mismo_vector_entre_instancias_distintas() -> None:
    primera_instancia = FakeEmbedder()
    segunda_instancia = FakeEmbedder()

    vector_a = primera_instancia.generar("El pago fue rechazado")
    vector_b = segunda_instancia.generar("El pago fue rechazado")

    assert vector_a == vector_b


def test_generar_sin_nada_fijado_da_vectores_distintos_para_textos_distintos() -> None:
    embedder = FakeEmbedder()

    vector_a = embedder.generar("El pago fue rechazado")
    vector_b = embedder.generar("Mañana lloverá en la costa")

    assert vector_a != vector_b


def test_generar_sin_nada_fijado_pasa_el_texto_por_normalizar_antes_de_derivar_el_vector() -> None:
    embedder = FakeEmbedder()

    vector_con_mayusculas = embedder.generar("El Pago")
    vector_normalizado_a_mano = embedder.generar("el pago")

    assert vector_con_mayusculas == vector_normalizado_a_mano


def test_generar_sin_nada_fijado_tiene_norma_uno_por_defecto() -> None:
    embedder = FakeEmbedder()

    vector = embedder.generar("cualquier frase")

    assert _norma(vector) == pytest.approx(1.0, abs=1e-9)


def test_generar_sin_nada_fijado_tiene_norma_igual_al_factor_de_escala() -> None:
    embedder = FakeEmbedder(factor_escala=5.0)

    vector = embedder.generar("cualquier frase")

    assert _norma(vector) == pytest.approx(5.0, abs=1e-9)


def test_generar_devuelve_una_copia_no_la_misma_lista_interna() -> None:
    embedder = FakeEmbedder(dimension=4)
    embedder.fijar_vector("frase fijada", [1.0, 2.0, 3.0, 4.0])

    primera_llamada = embedder.generar("frase fijada")
    primera_llamada[0] = 999.0
    segunda_llamada = embedder.generar("frase fijada")

    assert segunda_llamada[0] != 999.0


def test_fijar_vector_hace_que_generar_devuelva_ese_vector_tal_cual() -> None:
    embedder = FakeEmbedder(dimension=4)
    embedder.fijar_vector("frase fijada", [1.0, 2.0, 3.0, 4.0])

    assert embedder.generar("frase fijada") == [1.0, 2.0, 3.0, 4.0]


def test_fijar_vector_permite_un_vector_de_ceros_para_probar_la_norma_cero() -> None:
    embedder = FakeEmbedder(dimension=4)
    embedder.fijar_vector("frase sin significado util", [0.0, 0.0, 0.0, 0.0])

    assert embedder.generar("frase sin significado util") == [0.0, 0.0, 0.0, 0.0]


def test_fijar_vector_usa_la_clave_normalizada() -> None:
    embedder = FakeEmbedder(dimension=3)
    embedder.fijar_vector("El Pago", [1.0, 0.0, 0.0])

    assert embedder.generar("el   pago") == [1.0, 0.0, 0.0]


def test_fijar_similitud_produce_el_coseno_pedido_entre_ancla_y_otra() -> None:
    embedder = FakeEmbedder()
    embedder.fijar_similitud("El pago fue rechazado", "La transacción fue rechazada", 0.89)

    vector_ancla = embedder.generar("El pago fue rechazado")
    vector_otra = embedder.generar("La transacción fue rechazada")

    assert _coseno(vector_ancla, vector_otra) == pytest.approx(0.89, abs=1e-9)


def test_fijar_similitud_acepta_puntajes_negativos_b15() -> None:
    embedder = FakeEmbedder()
    embedder.fijar_similitud("El pago fue rechazado", "Mañana lloverá en la costa", -0.5)

    vector_ancla = embedder.generar("El pago fue rechazado")
    vector_otra = embedder.generar("Mañana lloverá en la costa")

    assert _coseno(vector_ancla, vector_otra) == pytest.approx(-0.5, abs=1e-9)


def test_fijar_similitud_acepta_el_extremo_uno() -> None:
    embedder = FakeEmbedder()
    embedder.fijar_similitud("El pago fue rechazado", "El pago fue rechazado otra vez", 1.0)

    vector_ancla = embedder.generar("El pago fue rechazado")
    vector_otra = embedder.generar("El pago fue rechazado otra vez")

    assert _coseno(vector_ancla, vector_otra) == pytest.approx(1.0, abs=1e-9)


@pytest.mark.parametrize("puntaje_invalido", [1.5, -1.5, 1.0000001, -1.0000001])
def test_fijar_similitud_fuera_de_rango_lanza_value_error(puntaje_invalido: float) -> None:
    embedder = FakeEmbedder()

    with pytest.raises(ValueError):
        embedder.fijar_similitud("ancla", "otra", puntaje_invalido)


def test_fijar_similitud_usa_las_claves_normalizadas() -> None:
    embedder = FakeEmbedder()
    embedder.fijar_similitud("El Pago", "La Entidad Bancaria", 0.7)

    vector_ancla = embedder.generar("el pago")
    vector_otra = embedder.generar("la entidad bancaria")

    assert _coseno(vector_ancla, vector_otra) == pytest.approx(0.7, abs=1e-9)


def test_fijar_similitud_sobre_una_otra_ya_fijada_con_vector_lanza_value_error() -> None:
    embedder = FakeEmbedder()
    embedder.fijar_vector("otra ya fijada", [1.0] * embedder.dimension)

    with pytest.raises(ValueError):
        embedder.fijar_similitud("ancla", "otra ya fijada", 0.5)


def test_fijar_similitud_dos_veces_sobre_la_misma_otra_lanza_value_error() -> None:
    embedder = FakeEmbedder()
    embedder.fijar_similitud("ancla", "otra", 0.5)

    with pytest.raises(ValueError):
        embedder.fijar_similitud("otra ancla", "otra", 0.6)


def test_una_misma_ancla_admite_varias_otras_con_puntajes_distintos() -> None:
    embedder = FakeEmbedder()
    embedder.fijar_similitud("ancla", "cerca", 0.9)
    embedder.fijar_similitud("ancla", "lejos", 0.2)

    vector_ancla = embedder.generar("ancla")

    assert _coseno(vector_ancla, embedder.generar("cerca")) == pytest.approx(0.9, abs=1e-9)
    assert _coseno(vector_ancla, embedder.generar("lejos")) == pytest.approx(0.2, abs=1e-9)


def test_dos_otras_con_el_mismo_puntaje_empatan_exactamente_para_el_desempate_ac06() -> None:
    embedder = FakeEmbedder()
    embedder.fijar_similitud("ancla", "primera candidata", 0.85)
    embedder.fijar_similitud("ancla", "segunda candidata", 0.85)

    vector_ancla = embedder.generar("ancla")
    coseno_primera = _coseno(vector_ancla, embedder.generar("primera candidata"))
    coseno_segunda = _coseno(vector_ancla, embedder.generar("segunda candidata"))

    assert coseno_primera == coseno_segunda


def test_fijar_similitud_con_factor_de_escala_no_cambia_el_coseno_pero_si_la_norma() -> None:
    embedder = FakeEmbedder(factor_escala=5.0)
    embedder.fijar_similitud("ancla", "otra", 0.6)

    vector_ancla = embedder.generar("ancla")
    vector_otra = embedder.generar("otra")

    assert _norma(vector_ancla) == pytest.approx(5.0, abs=1e-9)
    assert _norma(vector_otra) == pytest.approx(5.0, abs=1e-9)
    assert _coseno(vector_ancla, vector_otra) == pytest.approx(0.6, abs=1e-9)


def test_textos_recibidos_registra_el_texto_tal_como_llego_sin_normalizar() -> None:
    embedder = FakeEmbedder()

    embedder.generar("El Pago")
    embedder.generar("el pago")

    assert embedder.textos_recibidos == ["El Pago", "el pago"]


def test_llamadas_cuenta_las_invocaciones_a_generar() -> None:
    embedder = FakeEmbedder()

    embedder.generar("una")
    embedder.generar("dos")
    embedder.generar("tres")

    assert embedder.llamadas == 3


def test_sin_llamar_a_generar_llamadas_es_cero() -> None:
    embedder = FakeEmbedder()

    assert embedder.llamadas == 0


def test_fijar_vector_y_fijar_similitud_no_cuentan_como_llamadas() -> None:
    embedder = FakeEmbedder()
    embedder.fijar_vector("frase fijada", [1.0] * embedder.dimension)
    embedder.fijar_similitud("ancla", "otra", 0.5)

    assert embedder.llamadas == 0


def test_fallo_por_defecto_es_ninguno() -> None:
    embedder = FakeEmbedder()

    assert embedder.fallo is None


def test_con_fallo_configurado_generar_lanza_esa_excepcion() -> None:
    embedder = FakeEmbedder()
    embedder.fallo = ErrorProveedorEmbeddings("caído")

    with pytest.raises(ErrorProveedorEmbeddings):
        embedder.generar("cualquier frase")


def test_con_fallo_configurado_admite_cualquier_excepcion() -> None:
    embedder = FakeEmbedder()
    embedder.fallo = RuntimeError("boom")

    with pytest.raises(RuntimeError):
        embedder.generar("cualquier frase")


def test_con_fallo_configurado_la_llamada_igual_se_registra() -> None:
    embedder = FakeEmbedder()
    embedder.fallo = ErrorProveedorEmbeddings("caído")

    with pytest.raises(ErrorProveedorEmbeddings):
        embedder.generar("frase que falla")

    assert embedder.textos_recibidos == ["frase que falla"]
    assert embedder.llamadas == 1
