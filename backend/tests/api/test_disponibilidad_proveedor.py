"""Tests de T-12a: disponibilidad del proveedor de embeddings por HTTP (AC-13)."""

from fastapi.testclient import TestClient

from app.config import Configuracion
from app.domain.errores import ErrorProveedorEmbeddings
from tests.dobles.embedder_falso import FakeEmbedder
from tests.dobles.repositorio_en_memoria import RepositorioEnMemoria


def test_ac13_proveedor_caido_al_validar_frase_nueva_devuelve_503_sin_trazas(
    cliente: TestClient, embedder: FakeEmbedder
) -> None:
    embedder.fallo = ErrorProveedorEmbeddings("el proveedor de embeddings no está disponible")

    respuesta = cliente.post(
        "/api/v1/frases/validar", json={"texto": "Una frase nueva sin duplicado exacto"}
    )

    assert respuesta.status_code == 503
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "SERVICIO_IA_NO_DISPONIBLE"
    cuerpo_texto = respuesta.text
    assert "Traceback" not in cuerpo_texto
    assert "ErrorProveedorEmbeddings" not in cuerpo_texto


def test_ac13_proveedor_caido_al_guardar_frase_nueva_devuelve_503_y_no_persiste(
    cliente: TestClient, embedder: FakeEmbedder, repositorio: RepositorioEnMemoria
) -> None:
    embedder.fallo = ErrorProveedorEmbeddings("el proveedor de embeddings no está disponible")

    respuesta = cliente.post(
        "/api/v1/frases",
        json={"texto": "Otra frase nueva sin duplicado exacto", "confirmar_duplicado": False},
    )

    assert respuesta.status_code == 503
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "SERVICIO_IA_NO_DISPONIBLE"
    assert repositorio.guardadas == []
    cuerpo_texto = respuesta.text
    assert "Traceback" not in cuerpo_texto
    assert "ErrorProveedorEmbeddings" not in cuerpo_texto


def test_ac13_proveedor_caido_validar_duplicado_exacto_sigue_respondiendo_200(
    cliente: TestClient, embedder: FakeEmbedder, repositorio: RepositorioEnMemoria
) -> None:
    repositorio.sembrar("El pago fue rechazado", embedder.generar("El pago fue rechazado"))
    embedder.textos_recibidos.clear()
    embedder.fallo = ErrorProveedorEmbeddings("el proveedor de embeddings no está disponible")

    respuesta = cliente.post("/api/v1/frases/validar", json={"texto": "el pago fue rechazado"})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["es_posible_duplicado"] is True
    assert cuerpo["motivo"] == "EXACTO"


def test_b09_embedder_none_en_app_state_devuelve_503_sin_sustituir_obtener_embedder(
    cliente_con_arranque_degradado: TestClient,
) -> None:
    # B-09: la fábrica falló al arrancar, `app.state.embedder` quedó en
    # `None`. Sin sustituir `obtener_embedder`, es la propia dependencia la
    # que debe leer ese estado y lanzar `ErrorProveedorEmbeddings`.
    respuesta = cliente_con_arranque_degradado.post(
        "/api/v1/frases/validar", json={"texto": "Una frase nueva que nadie ha registrado"}
    )

    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "SERVICIO_IA_NO_DISPONIBLE"


def test_b20_modelo_sin_cargar_validar_un_duplicado_exacto_sigue_respondiendo_200(
    cliente_con_arranque_degradado: TestClient,
    repositorio: RepositorioEnMemoria,
    configuracion_prueba: Configuracion,
) -> None:
    # RN-15 y B-20: el duplicado exacto no necesita al proveedor, tampoco
    # cuando el modelo no llegó a cargarse al arrancar (B-09).
    repositorio.sembrar("El pago fue rechazado", FakeEmbedder().generar("El pago fue rechazado"))

    respuesta = cliente_con_arranque_degradado.post(
        "/api/v1/frases/validar", json={"texto": "  el PAGO fue rechazado "}
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["motivo"] == "EXACTO"
    assert cuerpo["modelo"] == configuracion_prueba.nombre_modelo
