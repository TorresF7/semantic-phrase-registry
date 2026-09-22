"""Tests de T-12a: flujo de validar y guardar extremo a extremo por HTTP.

Cubre AC-09, AC-10, AC-11 (y de paso AC-04, pieza necesaria para llegar al
409 de AC-10) contra el contrato de `plan.md` §1.1 y §1.2, con `TestClient` y
las dependencias sustituidas. Los AC-12b y AC-12 (metadatos y revalidación) ya
están cubiertos en `tests/unit/application/test_guardar_frase.py`; aquí solo
se comprueba que la capa HTTP serializa correctamente esos mismos datos.
"""

import pytest
from fastapi.testclient import TestClient

from tests.dobles.embedder_falso import FakeEmbedder
from tests.dobles.repositorio_en_memoria import RepositorioEnMemoria

# --------------------------------------------------------------------------
# AC-09 — Guardado de frase única
# --------------------------------------------------------------------------


def test_ac09_validar_y_guardar_una_frase_unica_devuelve_200_y_201(
    cliente: TestClient, embedder: FakeEmbedder
) -> None:
    texto = "Una frase completamente nueva y sin relación con ninguna otra"

    respuesta_validar = cliente.post("/api/v1/frases/validar", json={"texto": texto})
    assert respuesta_validar.status_code == 200
    cuerpo_validar = respuesta_validar.json()
    assert cuerpo_validar["es_posible_duplicado"] is False
    assert cuerpo_validar["motivo"] is None
    assert cuerpo_validar["mas_parecida"] is None

    respuesta_guardar = cliente.post(
        "/api/v1/frases", json={"texto": texto, "confirmar_duplicado": False}
    )

    assert respuesta_guardar.status_code == 201
    cuerpo = respuesta_guardar.json()
    assert cuerpo["texto"] == texto
    assert cuerpo["estado"] == "UNICA"
    assert cuerpo["umbral_aplicado"] == 0.80
    assert cuerpo["modelo"] == embedder.nombre_modelo
    assert isinstance(cuerpo["id"], int)
    assert "creada_en" in cuerpo


# --------------------------------------------------------------------------
# AC-04 — Duplicado semántico por encima del umbral (soporte de AC-10)
# --------------------------------------------------------------------------


def test_ac04_validar_duplicado_semantico_sobre_el_umbral_devuelve_motivo_y_mas_parecida(
    cliente: TestClient, embedder: FakeEmbedder, repositorio: RepositorioEnMemoria
) -> None:
    texto_registrada = "El pago fue rechazado por el banco"
    texto_nuevo = "La entidad bancaria rechazó la transacción"
    embedder.fijar_similitud(texto_registrada, texto_nuevo, 0.89)
    frase_registrada = repositorio.sembrar(texto_registrada, embedder.generar(texto_registrada))
    embedder.textos_recibidos.clear()

    respuesta = cliente.post("/api/v1/frases/validar", json={"texto": texto_nuevo})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["es_posible_duplicado"] is True
    assert cuerpo["motivo"] == "SEMANTICO"
    assert cuerpo["puntaje"] == pytest.approx(0.89, abs=1e-4)
    assert cuerpo["umbral_aplicado"] == 0.80
    assert cuerpo["mas_parecida"]["id"] == frase_registrada.id
    assert cuerpo["mas_parecida"]["texto"] == texto_registrada


# --------------------------------------------------------------------------
# AC-10 — Guardado bloqueado por posible duplicado
# --------------------------------------------------------------------------


def test_ac10_guardar_sin_confirmar_un_posible_duplicado_devuelve_409_y_no_persiste(
    cliente: TestClient, embedder: FakeEmbedder, repositorio: RepositorioEnMemoria
) -> None:
    texto_registrada = "El pago fue rechazado por el banco"
    texto_nuevo = "La entidad bancaria rechazó la transacción"
    embedder.fijar_similitud(texto_registrada, texto_nuevo, 0.89)
    frase_registrada = repositorio.sembrar(texto_registrada, embedder.generar(texto_registrada))
    embedder.textos_recibidos.clear()

    respuesta = cliente.post(
        "/api/v1/frases", json={"texto": texto_nuevo, "confirmar_duplicado": False}
    )

    assert respuesta.status_code == 409
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "POSIBLE_DUPLICADO"
    detalles = cuerpo["detalles"]
    assert detalles["puntaje"] == pytest.approx(0.89, abs=1e-4)
    assert detalles["umbral_aplicado"] == 0.80
    assert detalles["motivo"] == "SEMANTICO"
    assert detalles["mas_parecida"]["id"] == frase_registrada.id
    assert detalles["mas_parecida"]["texto"] == texto_registrada
    assert repositorio.guardadas == []


# --------------------------------------------------------------------------
# AC-11 — Guardado confirmado pese a la alerta
# --------------------------------------------------------------------------


def test_ac11_guardar_confirmando_un_posible_duplicado_devuelve_201_duplicado_confirmado(
    cliente: TestClient, embedder: FakeEmbedder, repositorio: RepositorioEnMemoria
) -> None:
    texto_registrada = "El pago fue rechazado por el banco"
    texto_nuevo = "La entidad bancaria rechazó la transacción"
    embedder.fijar_similitud(texto_registrada, texto_nuevo, 0.89)
    repositorio.sembrar(texto_registrada, embedder.generar(texto_registrada))
    embedder.textos_recibidos.clear()

    respuesta = cliente.post(
        "/api/v1/frases", json={"texto": texto_nuevo, "confirmar_duplicado": True}
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "DUPLICADO_CONFIRMADO"
    assert cuerpo["puntaje_similitud"] == pytest.approx(0.89, abs=1e-4)
    assert len(repositorio.guardadas) == 1


# --------------------------------------------------------------------------
# Redondeo de presentación (plan §1.1): puntaje y puntaje_similitud a 4 decimales
# --------------------------------------------------------------------------


def test_puntaje_y_puntaje_similitud_se_redondean_a_cuatro_decimales_al_serializar(
    cliente: TestClient, embedder: FakeEmbedder, repositorio: RepositorioEnMemoria
) -> None:
    texto_registrada = "El pedido llegará en tres días"
    texto_nuevo = "Recibirás tu compra en un plazo de tres días"
    embedder.fijar_similitud(texto_registrada, texto_nuevo, 0.891234567)
    repositorio.sembrar(texto_registrada, embedder.generar(texto_registrada))
    embedder.textos_recibidos.clear()

    respuesta_validar = cliente.post("/api/v1/frases/validar", json={"texto": texto_nuevo})
    assert respuesta_validar.json()["puntaje"] == 0.8912

    respuesta_guardar = cliente.post(
        "/api/v1/frases", json={"texto": texto_nuevo, "confirmar_duplicado": True}
    )
    assert respuesta_guardar.json()["puntaje_similitud"] == 0.8912
