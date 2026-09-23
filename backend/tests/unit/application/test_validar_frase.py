"""Tests de T-07 (Caso de uso `ValidarFrase`).

Cubre AC-03 a AC-08 y AC-17 mediante el caso de uso completo, con
`FakeEmbedder` y `RepositorioEnMemoria`: sin base de datos y en milisegundos
(plan §4, §7). Cada test fija su propio umbral: ninguno depende del valor por
defecto de `SIMILARITY_THRESHOLD` (D-07).

Convención para no contaminar el espía del embedder: cuando hace falta
generarle un vector a una frase ya registrada (para poder sembrarla en el
repositorio en memoria), se genera antes de construir el caso de uso y se
limpia `embedder.textos_recibidos` justo después. Así `textos_recibidos` solo
recoge lo que el caso de uso bajo prueba pidió.
"""

import math

import pytest

# Módulo que esta tarea aún no implementa (T-07): el import falla con
# `ModuleNotFoundError` hasta que exista `app/application/validar_frase.py`.
from app.application.validar_frase import ValidarFrase
from app.domain.entidades import MotivoDuplicado
from app.domain.errores import ErrorProveedorEmbeddings
from app.domain.normalizacion import normalizar
from tests.dobles.embedder_falso import FakeEmbedder
from tests.dobles.repositorio_en_memoria import RepositorioEnMemoria


def _crear_caso_uso(
    repositorio: RepositorioEnMemoria,
    embedder: FakeEmbedder,
    umbral: float = 0.80,
    longitud_maxima: int = 280,
) -> ValidarFrase:
    return ValidarFrase(
        repositorio=repositorio,
        embedder=embedder,
        umbral=umbral,
        longitud_maxima=longitud_maxima,
    )


# --------------------------------------------------------------------------
# AC-03 — Duplicado exacto ignorando mayúsculas y espacios
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "texto_a_validar",
    [
        "  el PAGO   fue rechazado ",
        "el pago\tfue\nrechazado",
        "el\u00a0pago\u2003fue rechazado",  # espacio duro y espacio de ancho fijo (B-17)
    ],
)
def test_ac03_duplicado_exacto_ignora_mayusculas_y_espacios_y_no_invoca_al_embedder(
    texto_a_validar: str,
) -> None:
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    frase_existente = repo.sembrar(
        "El pago fue rechazado", embedder.generar("El pago fue rechazado")
    )
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder)

    resultado = caso_uso.validar(texto_a_validar)

    assert resultado.es_posible_duplicado is True
    assert resultado.motivo == MotivoDuplicado.EXACTO
    assert resultado.puntaje == 1.0
    assert resultado.mas_parecida is not None
    assert resultado.mas_parecida.id == frase_existente.id
    assert resultado.mas_parecida.texto_original == "El pago fue rechazado"
    assert resultado.embedding is None
    assert embedder.llamadas == 0


# --------------------------------------------------------------------------
# AC-03 (último «Y», CH-04) — Los caracteres de formato (Cf) se eliminan
# antes de comparar: siguen dando duplicado exacto (B-28)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "texto_a_validar",
    [
        "El pago fue rechazado\ufeff",
        "El pago\u200b fue rechazado",
    ],
    ids=["ufeff_final", "u200b_junto_al_espacio"],
)
def test_ac03_caracteres_de_formato_se_eliminan_y_da_exacto_sin_invocar_al_embedder_b28(
    texto_a_validar: str,
) -> None:
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    frase_existente = repo.sembrar(
        "El pago fue rechazado", embedder.generar("El pago fue rechazado")
    )
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder)

    resultado = caso_uso.validar(texto_a_validar)

    assert resultado.es_posible_duplicado is True
    assert resultado.motivo == MotivoDuplicado.EXACTO
    assert resultado.puntaje == 1.0
    assert resultado.mas_parecida is not None
    assert resultado.mas_parecida.id == frase_existente.id
    assert resultado.embedding is None
    assert embedder.llamadas == 0


# --------------------------------------------------------------------------
# AC-06 (segunda cláusula, B-18) — Duplicado exacto entre varias registradas
# con el mismo texto normalizado: gana la de identificador menor
# --------------------------------------------------------------------------


def test_ac06_duplicado_exacto_con_varias_registradas_devuelve_la_de_id_menor_b18() -> None:
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    vector = embedder.generar("Hola mundo")
    primera = repo.sembrar("Hola Mundo", vector)
    segunda = repo.sembrar("hola   mundo", vector)
    assert primera.id < segunda.id
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder)

    resultado = caso_uso.validar("HOLA MUNDO")

    assert resultado.motivo == MotivoDuplicado.EXACTO
    assert resultado.mas_parecida is not None
    assert resultado.mas_parecida.id == primera.id


# --------------------------------------------------------------------------
# AC-04 — Duplicado semántico por encima del umbral
# --------------------------------------------------------------------------


def test_ac04_duplicado_semantico_sobre_el_umbral_devuelve_mas_parecida() -> None:
    texto_registrada = "El pago fue rechazado por el banco"
    texto_nuevo = "La entidad bancaria rechazó la transacción"
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    embedder.fijar_similitud(texto_registrada, texto_nuevo, 0.89)
    frase_registrada = repo.sembrar(texto_registrada, embedder.generar(texto_registrada))
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80)

    resultado = caso_uso.validar(texto_nuevo)

    assert resultado.es_posible_duplicado is True
    assert resultado.motivo == MotivoDuplicado.SEMANTICO
    assert resultado.puntaje == pytest.approx(0.89, abs=1e-6)
    assert resultado.mas_parecida is not None
    assert resultado.mas_parecida.id == frase_registrada.id
    assert resultado.mas_parecida.texto_original == texto_registrada
    assert resultado.umbral_aplicado == 0.80
    assert resultado.modelo == embedder.nombre_modelo


def test_ac04_el_embedder_recibe_el_texto_normalizado_de_la_frase_nueva_rn05() -> None:
    texto_registrada = "El pago fue rechazado por el banco"
    texto_nuevo = "  La ENTIDAD bancaria   rechazó la transacción  "
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    embedder.fijar_similitud(texto_registrada, texto_nuevo, 0.89)
    repo.sembrar(texto_registrada, embedder.generar(texto_registrada))
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80)

    caso_uso.validar(texto_nuevo)

    assert embedder.textos_recibidos == [normalizar(texto_nuevo)]


def test_puntaje_igual_al_umbral_en_el_caso_de_uso_es_posible_duplicado_b08() -> None:
    texto_registrada = "Frase ancla registrada"
    texto_nuevo = "Frase nueva a comparar"
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    embedder.fijar_similitud(texto_registrada, texto_nuevo, 0.5)
    repo.sembrar(texto_registrada, embedder.generar(texto_registrada))
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.5)

    resultado = caso_uso.validar(texto_nuevo)

    assert resultado.puntaje == pytest.approx(0.5, abs=1e-9)
    assert resultado.es_posible_duplicado is True
    assert resultado.motivo == MotivoDuplicado.SEMANTICO


# --------------------------------------------------------------------------
# AC-05 — Frase distinta por debajo del umbral
# --------------------------------------------------------------------------


def test_ac05_frase_distinta_por_debajo_del_umbral_devuelve_mas_parecida() -> None:
    texto_registrada = "Actualiza tu contraseña cada tres meses"
    texto_nuevo = "El restaurante abre a las ocho"
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    embedder.fijar_similitud(texto_registrada, texto_nuevo, 0.42)
    frase_registrada = repo.sembrar(texto_registrada, embedder.generar(texto_registrada))
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80)

    resultado = caso_uso.validar(texto_nuevo)

    assert resultado.es_posible_duplicado is False
    assert resultado.motivo is None
    assert resultado.puntaje == pytest.approx(0.42, abs=1e-6)
    assert resultado.mas_parecida is not None
    assert resultado.mas_parecida.id == frase_registrada.id


def test_puntaje_negativo_se_recorta_a_cero_y_no_es_duplicado_b15() -> None:
    texto_registrada = "El pago fue rechazado por el banco"
    texto_nuevo = "Mañana lloverá en la costa"
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    embedder.fijar_similitud(texto_registrada, texto_nuevo, -0.3)
    repo.sembrar(texto_registrada, embedder.generar(texto_registrada))
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80)

    resultado = caso_uso.validar(texto_nuevo)

    assert resultado.puntaje == 0.0
    assert resultado.es_posible_duplicado is False


# --------------------------------------------------------------------------
# AC-06 — Empate resuelto de forma determinista (rama semántica)
# --------------------------------------------------------------------------


def test_ac06_empate_semantico_resuelto_por_id_menor_es_determinista() -> None:
    texto_nuevo = "Frase nueva a validar"
    texto_a = "Primera candidata registrada"
    texto_b = "Segunda candidata registrada"
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    embedder.fijar_similitud(texto_nuevo, texto_a, 0.85)
    embedder.fijar_similitud(texto_nuevo, texto_b, 0.85)
    frase_a = repo.sembrar(texto_a, embedder.generar(texto_a))
    frase_b = repo.sembrar(texto_b, embedder.generar(texto_b))
    assert frase_a.id < frase_b.id
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80)

    primer_resultado = caso_uso.validar(texto_nuevo)
    segundo_resultado = caso_uso.validar(texto_nuevo)

    for resultado in (primer_resultado, segundo_resultado):
        assert resultado.es_posible_duplicado is True
        assert resultado.puntaje == pytest.approx(0.85, abs=1e-6)
        assert resultado.mas_parecida is not None
        assert resultado.mas_parecida.id == frase_a.id
    assert primer_resultado.es_posible_duplicado == segundo_resultado.es_posible_duplicado
    assert primer_resultado.puntaje == pytest.approx(segundo_resultado.puntaje)
    assert primer_resultado.mas_parecida.id == segundo_resultado.mas_parecida.id


# --------------------------------------------------------------------------
# AC-07 — Base de datos vacía
# --------------------------------------------------------------------------


def test_ac07_base_vacia_devuelve_puntaje_nulo_y_frase_unica() -> None:
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80)

    resultado = caso_uso.validar("Una frase cualquiera y válida")

    assert resultado.es_posible_duplicado is False
    assert resultado.motivo is None
    assert resultado.puntaje is None
    assert resultado.mas_parecida is None


# --------------------------------------------------------------------------
# AC-08 — Validar no persiste
# --------------------------------------------------------------------------


def test_ac08_validar_no_persiste_ninguna_frase_sea_unica_semantica_o_exacta() -> None:
    texto_existente = "El pago fue rechazado"
    texto_unica = "Una frase completamente distinta"
    texto_semantica = "Una frase muy parecida a la existente"
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    embedder.fijar_similitud(texto_existente, texto_unica, 0.10)
    embedder.fijar_similitud(texto_existente, texto_semantica, 0.95)
    repo.sembrar(texto_existente, embedder.generar(texto_existente))
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80)
    _, total_antes = repo.listar(limite=100, desplazamiento=0)

    resultado_unica = caso_uso.validar(texto_unica)
    resultado_semantica = caso_uso.validar(texto_semantica)
    resultado_exacta = caso_uso.validar("el pago fue rechazado")

    assert resultado_unica.es_posible_duplicado is False
    assert resultado_semantica.es_posible_duplicado is True
    assert resultado_exacta.motivo == MotivoDuplicado.EXACTO
    _, total_despues = repo.listar(limite=100, desplazamiento=0)
    assert total_despues == total_antes
    assert repo.guardadas == []


# --------------------------------------------------------------------------
# AC-17 — Vectores normalizados
# --------------------------------------------------------------------------


def test_ac17_embedding_de_validar_tiene_norma_uno_aunque_el_proveedor_no_normalice() -> None:
    texto_existente = "El pago fue rechazado"
    texto_nuevo = "La entidad bancaria rechazó la transacción"
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder(factor_escala=5.0)
    repo.sembrar(texto_existente, embedder.generar(texto_existente))
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80)

    resultado = caso_uso.validar(texto_nuevo)

    assert resultado.embedding is not None
    norma = math.sqrt(sum(componente**2 for componente in resultado.embedding))
    assert norma == pytest.approx(1.0, abs=1e-6)


def test_ac17_vector_de_norma_cero_del_proveedor_se_trata_como_fallo_y_no_se_guarda_nada() -> None:
    texto_existente = "El pago fue rechazado"
    texto_nuevo = "La entidad bancaria rechazó la transacción"
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    repo.sembrar(texto_existente, embedder.generar(texto_existente))
    embedder.fijar_vector(texto_nuevo, [0.0] * embedder.dimension)
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80)
    _, total_antes = repo.listar(limite=100, desplazamiento=0)

    with pytest.raises(ErrorProveedorEmbeddings):
        caso_uso.validar(texto_nuevo)

    _, total_despues = repo.listar(limite=100, desplazamiento=0)
    assert total_despues == total_antes
    assert repo.guardadas == []
