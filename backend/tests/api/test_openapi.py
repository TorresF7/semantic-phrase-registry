"""Tests de T-12b: documentación OpenAPI de cada operación y cada código.

No cubren ningún AC: son el Definition of Done explícito de T-12b ("Ejemplos
en `/docs` para cada endpoint y cada código de error" / "`/docs` muestra
ejemplos en cada endpoint"), así que se nombran de forma descriptiva, sin
prefijo `ac` (skill de testing, sección "Nomenclatura").

Se recorre `app.openapi()` en lugar de golpear `/docs`: es el mismo esquema
que Swagger UI renderiza y es estable frente a cambios de estilo en la UI.
Un ejemplo se acepta en cualquiera de las formas habituales de OpenAPI 3:
`example` o `examples` en el objeto del tipo de medio (`content["application/
json"]`), o `example`/`examples` en el esquema referenciado por `$ref`.

`GET /frases` no existe todavía (T-12b sin implementar) y `GET /salud` no
declara sus respuestas: la operación "listar" falla con `KeyError` al buscar
la ruta, y "salud" falla porque le falta el código `503`. Ambos son el
comportamiento esperado en rojo, no un error de importación.
"""

from collections.abc import Mapping
from typing import Any

import pytest

from app.main import app

# (nombre, ruta, método HTTP en minúsculas, códigos que debe documentar)
_OPERACIONES: list[tuple[str, str, str, set[str]]] = [
    ("validar", "/api/v1/frases/validar", "post", {"200", "422", "500", "503"}),
    ("guardar", "/api/v1/frases", "post", {"201", "409", "422", "500", "503"}),
    ("listar", "/api/v1/frases", "get", {"200", "422", "500", "503"}),
    ("salud", "/api/v1/salud", "get", {"200", "503"}),
]


@pytest.fixture(scope="module")
def esquema_openapi() -> dict[str, Any]:
    return app.openapi()


def _resolver_referencia(esquema_openapi: Mapping[str, Any], referencia: str) -> Mapping[str, Any]:
    """`"#/components/schemas/FraseRespuesta"` -> el nodo correspondiente."""
    nodo: Any = esquema_openapi
    for parte in referencia.lstrip("#/").split("/"):
        nodo = nodo[parte]
    return nodo  # type: ignore[no-any-return]


def _tiene_ejemplo(esquema_openapi: Mapping[str, Any], contenido_json: Mapping[str, Any]) -> bool:
    if contenido_json.get("example") is not None:
        return True
    if contenido_json.get("examples"):
        return True
    esquema = contenido_json.get("schema", {})
    if esquema.get("example") is not None or esquema.get("examples"):
        return True
    referencia = esquema.get("$ref")
    if referencia:
        definicion = _resolver_referencia(esquema_openapi, referencia)
        if definicion.get("example") is not None or definicion.get("examples"):
            return True
    return False


@pytest.mark.parametrize(("nombre_operacion", "ruta", "metodo", "codigos_esperados"), _OPERACIONES)
def test_cada_operacion_documenta_todos_los_codigos_que_puede_devolver(
    esquema_openapi: dict[str, Any],
    nombre_operacion: str,
    ruta: str,
    metodo: str,
    codigos_esperados: set[str],
) -> None:
    operacion = esquema_openapi["paths"][ruta][metodo]
    codigos_documentados = operacion["responses"].keys()

    faltantes = codigos_esperados - codigos_documentados
    assert not faltantes, f"{nombre_operacion}: faltan los códigos {faltantes} en `responses`"


@pytest.mark.parametrize(("nombre_operacion", "ruta", "metodo", "codigos_esperados"), _OPERACIONES)
def test_cada_respuesta_documentada_incluye_al_menos_un_ejemplo(
    esquema_openapi: dict[str, Any],
    nombre_operacion: str,
    ruta: str,
    metodo: str,
    codigos_esperados: set[str],
) -> None:
    operacion = esquema_openapi["paths"][ruta][metodo]
    respuestas = operacion["responses"]

    sin_ejemplo = [
        codigo
        for codigo in codigos_esperados
        if (contenido := respuestas.get(codigo, {}).get("content", {}).get("application/json"))
        is None
        or not _tiene_ejemplo(esquema_openapi, contenido)
    ]

    assert not sin_ejemplo, f"{nombre_operacion}: sin ejemplo en los códigos {sin_ejemplo}"
