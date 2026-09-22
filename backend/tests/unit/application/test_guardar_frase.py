"""Tests de T-08 (Caso de uso `GuardarFrase`).

Cubre AC-09, AC-10, AC-11, AC-11b, AC-12, AC-12b y la cláusula de persistencia
de AC-17, mediante el caso de uso completo, con `FakeEmbedder` y
`RepositorioEnMemoria`: sin base de datos y en milisegundos (plan §4, §7). Cada
test fija su propio umbral: ninguno depende del valor por defecto de
`SIMILARITY_THRESHOLD` (D-07).

Convención para no contaminar el espía del embedder: cuando hace falta
generarle un vector a una frase ya registrada (para poder sembrarla en el
repositorio en memoria), se genera antes de construir el caso de uso y se
limpia `embedder.textos_recibidos` justo después. Así `textos_recibidos` solo
recoge lo que el caso de uso bajo prueba pidió.

`repo.guardadas` recoge las `FraseNueva` que llegaron a `repositorio.guardar`;
`repo.sembrar` no cuenta ahí, es solo preparación del escenario.
"""

import math

import pytest

# Módulo que esta tarea aún no implementa (T-08): el import falla con
# `ModuleNotFoundError` hasta que exista `app/application/guardar_frase.py`.
from app.application.guardar_frase import GuardarFrase
from app.application.validar_frase import ValidarFrase
from app.domain.entidades import EstadoFrase, MotivoDuplicado
from app.domain.errores import ErrorProveedorEmbeddings, PosibleDuplicado
from app.domain.normalizacion import normalizar
from tests.dobles.embedder_falso import FakeEmbedder
from tests.dobles.repositorio_en_memoria import RepositorioEnMemoria


def _crear_caso_uso(
    repositorio: RepositorioEnMemoria,
    embedder: FakeEmbedder,
    umbral: float = 0.80,
    longitud_maxima: int = 280,
) -> GuardarFrase:
    return GuardarFrase(
        repositorio=repositorio,
        embedder=embedder,
        umbral=umbral,
        longitud_maxima=longitud_maxima,
    )


# --------------------------------------------------------------------------
# AC-09 — Guardado de frase única
# --------------------------------------------------------------------------


def test_ac09_frase_unica_se_guarda_como_unica_y_aparece_en_el_listado() -> None:
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80, longitud_maxima=280)

    frase = caso_uso.guardar("Una frase completamente nueva", confirmar_duplicado=False)

    assert frase.estado == EstadoFrase.UNICA
    listadas, total = repo.listar(limite=100, desplazamiento=0)
    assert total == 1
    assert any(candidata.id == frase.id for candidata in listadas)


def test_ac09_frase_unica_con_confirmar_duplicado_true_tambien_queda_unica_b25() -> None:
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80, longitud_maxima=280)

    frase = caso_uso.guardar("Otra frase única y distinta", confirmar_duplicado=True)

    assert frase.estado == EstadoFrase.UNICA


# --------------------------------------------------------------------------
# AC-10 — Guardado bloqueado por posible duplicado
# --------------------------------------------------------------------------


def test_ac10_semantico_sin_confirmar_lanza_posible_duplicado_y_no_guarda() -> None:
    texto_registrada = "El pago fue rechazado por el banco"
    texto_nuevo = "La entidad bancaria rechazó la transacción"
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    embedder.fijar_similitud(texto_registrada, texto_nuevo, 0.89)
    frase_registrada = repo.sembrar(texto_registrada, embedder.generar(texto_registrada))
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80, longitud_maxima=280)
    _, total_antes = repo.listar(limite=100, desplazamiento=0)

    with pytest.raises(PosibleDuplicado) as excepcion:
        caso_uso.guardar(texto_nuevo, confirmar_duplicado=False)

    resultado = excepcion.value.resultado
    assert resultado.motivo == MotivoDuplicado.SEMANTICO
    assert resultado.puntaje == pytest.approx(0.89, abs=1e-6)
    assert resultado.mas_parecida is not None
    assert resultado.mas_parecida.id == frase_registrada.id
    assert resultado.umbral_aplicado == 0.80
    assert repo.guardadas == []
    _, total_despues = repo.listar(limite=100, desplazamiento=0)
    assert total_despues == total_antes


def test_ac10_exacto_sin_confirmar_lanza_posible_duplicado_motivo_exacto() -> None:
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    frase_registrada = repo.sembrar(
        "El pago fue rechazado", embedder.generar("El pago fue rechazado")
    )
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80, longitud_maxima=280)
    _, total_antes = repo.listar(limite=100, desplazamiento=0)

    with pytest.raises(PosibleDuplicado) as excepcion:
        caso_uso.guardar("el pago fue rechazado", confirmar_duplicado=False)

    resultado = excepcion.value.resultado
    assert resultado.motivo == MotivoDuplicado.EXACTO
    assert resultado.puntaje == 1.0
    assert resultado.mas_parecida is not None
    assert resultado.mas_parecida.id == frase_registrada.id
    assert repo.guardadas == []
    _, total_despues = repo.listar(limite=100, desplazamiento=0)
    assert total_despues == total_antes


# --------------------------------------------------------------------------
# AC-11 — Guardado confirmado pese a la alerta
# --------------------------------------------------------------------------


def test_ac11_semantico_confirmado_se_guarda_como_duplicado_confirmado() -> None:
    texto_registrada = "El pago fue rechazado por el banco"
    texto_nuevo = "La entidad bancaria rechazó la transacción"
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    embedder.fijar_similitud(texto_registrada, texto_nuevo, 0.89)
    frase_registrada = repo.sembrar(texto_registrada, embedder.generar(texto_registrada))
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80, longitud_maxima=280)

    frase = caso_uso.guardar(texto_nuevo, confirmar_duplicado=True)

    assert frase.estado == EstadoFrase.DUPLICADO_CONFIRMADO
    assert frase.puntaje_similitud == pytest.approx(0.89, abs=1e-6)
    assert frase.id_mas_parecida == frase_registrada.id


# --------------------------------------------------------------------------
# AC-11b — Duplicado exacto confirmado se guarda con su embedding
# --------------------------------------------------------------------------


def test_ac11b_duplicado_exacto_confirmado_genera_y_persiste_su_embedding_rn14() -> None:
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    repo.sembrar("Hola mundo", embedder.generar("Hola mundo"))
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80, longitud_maxima=280)

    frase = caso_uso.guardar("hola mundo", confirmar_duplicado=True)

    assert frase.estado == EstadoFrase.DUPLICADO_CONFIRMADO
    assert frase.puntaje_similitud == 1.0
    assert len(repo.guardadas) == 1
    nueva = repo.guardadas[0]
    assert len(nueva.embedding) == embedder.dimension
    norma = math.sqrt(sum(componente**2 for componente in nueva.embedding))
    assert norma == pytest.approx(1.0, abs=1e-6)
    # La validación de un duplicado exacto no invoca al proveedor (RN-04): el
    # embedding se genera al guardar, del texto normalizado, una sola vez.
    assert embedder.textos_recibidos == [normalizar("hola mundo")]


def test_ac11b_fallo_del_proveedor_al_generar_embedding_del_exacto_confirmado_no_guarda() -> None:
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    repo.sembrar("Hola mundo", embedder.generar("Hola mundo"))
    embedder.textos_recibidos.clear()
    embedder.fallo = ErrorProveedorEmbeddings("el proveedor de embeddings no está disponible")
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80, longitud_maxima=280)

    with pytest.raises(ErrorProveedorEmbeddings):
        caso_uso.guardar("hola mundo", confirmar_duplicado=True)

    assert repo.guardadas == []


# --------------------------------------------------------------------------
# AC-12 — Metadatos persistidos
# --------------------------------------------------------------------------


def test_ac12_metadatos_de_la_frase_nueva_persistida() -> None:
    texto_registrada = "Actualiza tu contraseña cada tres meses"
    texto_nuevo = "  El RESTAURANTE   abre a las ocho  "
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder(nombre_modelo="modelo-de-prueba")
    embedder.fijar_similitud(texto_registrada, texto_nuevo, 0.42)
    frase_registrada = repo.sembrar(texto_registrada, embedder.generar(texto_registrada))
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80, longitud_maxima=280)

    frase = caso_uso.guardar(texto_nuevo, confirmar_duplicado=False)

    assert frase.estado == EstadoFrase.UNICA
    assert len(repo.guardadas) == 1
    nueva = repo.guardadas[0]
    assert nueva.puntaje_similitud == pytest.approx(0.42, abs=1e-6)
    assert nueva.id_mas_parecida == frase_registrada.id
    assert nueva.estado == EstadoFrase.UNICA
    assert nueva.modelo == "modelo-de-prueba"
    assert nueva.umbral_aplicado == 0.80
    assert nueva.texto_original == texto_nuevo
    assert nueva.texto_normalizado == normalizar(texto_nuevo)


def test_ac12_base_vacia_puntaje_y_mas_parecida_nulos_estado_unica() -> None:
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80, longitud_maxima=280)

    frase = caso_uso.guardar("Una frase cualquiera y válida", confirmar_duplicado=False)

    assert frase.estado == EstadoFrase.UNICA
    nueva = repo.guardadas[0]
    assert nueva.puntaje_similitud is None
    assert nueva.id_mas_parecida is None


def test_ac12_umbral_aplicado_es_inmutable_para_registros_anteriores_b12() -> None:
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    primer_caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80, longitud_maxima=280)
    frase_primera = primer_caso_uso.guardar(
        "Primera frase única registrada", confirmar_duplicado=False
    )

    segundo_caso_uso = _crear_caso_uso(repo, embedder, umbral=0.95, longitud_maxima=280)
    segundo_caso_uso.guardar(
        "Segunda frase, completamente distinta de la anterior", confirmar_duplicado=False
    )

    listadas, _ = repo.listar(limite=100, desplazamiento=0)
    primera_leida = next(candidata for candidata in listadas if candidata.id == frase_primera.id)
    assert primera_leida.umbral_aplicado == 0.80


# --------------------------------------------------------------------------
# AC-12b — Revalidación del servidor con base modificada
# --------------------------------------------------------------------------


def test_ac12b_revalida_al_guardar_y_bloquea_por_frase_sembrada_tras_la_validacion_rn11() -> None:
    texto_nuevo = "Una frase que se validará y luego se intentará guardar"
    texto_sembrada_despues = "Otra frase muy parecida, sembrada después de validar"
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder()
    validador = ValidarFrase(repositorio=repo, embedder=embedder, umbral=0.80, longitud_maxima=280)

    resultado_inicial = validador.validar(texto_nuevo)
    assert resultado_inicial.es_posible_duplicado is False

    embedder.fijar_similitud(texto_sembrada_despues, texto_nuevo, 0.90)
    repo.sembrar(texto_sembrada_despues, embedder.generar(texto_sembrada_despues))
    embedder.textos_recibidos.clear()
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80, longitud_maxima=280)

    with pytest.raises(PosibleDuplicado) as excepcion:
        caso_uso.guardar(texto_nuevo, confirmar_duplicado=False)

    resultado = excepcion.value.resultado
    assert resultado.es_posible_duplicado is True
    assert resultado.puntaje == pytest.approx(0.90, abs=1e-6)
    assert repo.guardadas == []


# --------------------------------------------------------------------------
# AC-17 — Vectores normalizados (cláusula de persistencia)
# --------------------------------------------------------------------------


def test_ac17_embedding_persistido_tiene_norma_uno_aunque_el_proveedor_no_normalice() -> None:
    repo = RepositorioEnMemoria()
    embedder = FakeEmbedder(factor_escala=5.0)
    caso_uso = _crear_caso_uso(repo, embedder, umbral=0.80, longitud_maxima=280)

    caso_uso.guardar("Una frase válida sin relación con ninguna otra", confirmar_duplicado=False)

    nueva = repo.guardadas[0]
    norma = math.sqrt(sum(componente**2 for componente in nueva.embedding))
    assert norma == pytest.approx(1.0, abs=1e-6)
