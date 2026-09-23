"""Tests de integración de T-09 (Repositorio PostgreSQL con pgvector).

Cubren, contra un PostgreSQL real con `pgvector`:

- AC-12: los metadatos y el vector del embedding quedan persistidos, leídos
  con SQL directo porque `Frase` no transporta el embedding (plan §3, §7).
- AC-06 y B-18: el desempate por identificador menor, tanto en el vecino más
  parecido (RN-08) como en el duplicado exacto (RN-04, RN-08).
- La última cláusula de AC-15: el listado desempata por `id` cuando dos filas
  comparten `creada_en`, y respeta la fecha por encima del `id` en general.
- Las tres consultas del plan §2 (vecino más cercano, duplicado exacto,
  listado), la traducción de cualquier fallo de conexión a `ErrorRepositorio`
  (RN-15) y `esta_disponible()`.

Cada test parte de la tabla `frases` vacía (fixture `_tabla_frases_vacia` de
`conftest.py`, autouse) y usa vectores construidos a mano
(`conftest.vector_unitario`, `conftest.vector_con_coseno`) para fijar cosenos
exactos sin depender de ningún modelo real, igual que `FakeEmbedder.
fijar_similitud` en los tests de aplicación de T-07 y T-08.

Requiere `docker compose up -d db` y `bash scripts/preparar_base_test.sh`: ver
la nota en `conftest.py` sobre por qué no se ejecuta Alembic desde los fixtures.
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import DataError

from app.domain.entidades import EstadoFrase
from app.domain.errores import ErrorRepositorio
from tests.integration.conftest import (
    frase_nueva,
    vector_con_coseno,
    vector_desde_columna,
    vector_unitario,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session, sessionmaker

    from app.adapters.persistence.repositorio import RepositorioPostgres

pytestmark = pytest.mark.integration


# --------------------------------------------------------------------------
# AC-12 — Metadatos persistidos, incluido el vector, leídos con SQL directo
# --------------------------------------------------------------------------


def test_ac12_guarda_metadatos_y_vector_del_embedding_leidos_con_sql_directo(
    repositorio: "RepositorioPostgres", sesion_sql: "Session"
) -> None:
    existente = repositorio.guardar(
        frase_nueva("El pago fue rechazado por el banco", vector_unitario(0))
    )

    nueva = frase_nueva(
        "  La entidad BANCARIA rechazó  la transacción ",
        vector_con_coseno(0.87, eje_base=0, eje_ortogonal=1),
        estado=EstadoFrase.DUPLICADO_CONFIRMADO,
        puntaje_similitud=0.87,
        id_mas_parecida=existente.id,
        modelo="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        umbral_aplicado=0.80,
    )

    guardada = repositorio.guardar(nueva)

    # Lo que devuelve `guardar` ya trae `id` y `creada_en` asignados por la base.
    assert guardada.id is not None
    assert guardada.id != existente.id
    assert guardada.creada_en.tzinfo is not None
    assert guardada.creada_en.utcoffset() == timedelta(0)
    assert guardada.estado == EstadoFrase.DUPLICADO_CONFIRMADO
    assert guardada.puntaje_similitud == pytest.approx(0.87, abs=1e-9)
    assert guardada.id_mas_parecida == existente.id
    assert guardada.modelo == nueva.modelo
    assert guardada.umbral_aplicado == 0.80
    assert guardada.texto_original == nueva.texto_original

    fila = sesion_sql.execute(
        text(
            "SELECT texto_original, texto_normalizado, embedding, estado, "
            "       puntaje_similitud, id_mas_parecida, modelo, umbral_aplicado, creada_en "
            "  FROM frases WHERE id = :id"
        ),
        {"id": guardada.id},
    ).one()

    assert fila.texto_original == nueva.texto_original
    assert fila.texto_normalizado == nueva.texto_normalizado
    assert vector_desde_columna(fila.embedding) == pytest.approx(nueva.embedding, abs=1e-6)
    assert fila.estado == "DUPLICADO_CONFIRMADO"
    assert fila.puntaje_similitud == pytest.approx(0.87, abs=1e-9)
    assert fila.id_mas_parecida == existente.id
    assert fila.modelo == nueva.modelo
    # DOUBLE PRECISION (plan §2): 0.80 se lee de vuelta exactamente igual, a
    # diferencia de REAL, que perdería precisión (AC-12).
    assert fila.umbral_aplicado == 0.80
    assert fila.creada_en.tzinfo is not None
    assert fila.creada_en.utcoffset() == timedelta(0)


# --------------------------------------------------------------------------
# Vecino más cercano (plan §2, RN-05)
# --------------------------------------------------------------------------


def test_buscar_mas_parecida_devuelve_el_vecino_mas_cercano_y_su_puntaje_exacto(
    repositorio: "RepositorioPostgres",
) -> None:
    repositorio.guardar(frase_nueva("Frase lejana", vector_con_coseno(0.3, eje_ortogonal=2)))
    cercana = repositorio.guardar(
        frase_nueva("Frase cercana", vector_con_coseno(0.6, eje_ortogonal=1))
    )
    repositorio.guardar(frase_nueva("Frase casi opuesta", vector_con_coseno(-0.5, eje_ortogonal=3)))

    resultado = repositorio.buscar_mas_parecida(vector_unitario(0))

    assert resultado is not None
    frase, puntaje = resultado
    assert frase.id == cercana.id
    assert puntaje == pytest.approx(0.6, abs=1e-6)


def test_buscar_mas_parecida_devuelve_similitud_negativa_sin_recortar(
    repositorio: "RepositorioPostgres",
) -> None:
    """El recorte a [0, 1] es del dominio (RN-05); el repositorio no recorta nada."""
    repositorio.guardar(frase_nueva("Frase de referencia", vector_unitario(0)))
    vector_opuesto = [-componente for componente in vector_unitario(0)]

    resultado = repositorio.buscar_mas_parecida(vector_opuesto)

    assert resultado is not None
    _, puntaje = resultado
    assert puntaje == pytest.approx(-1.0, abs=1e-6)
    assert puntaje < 0


def test_base_vacia_buscar_mas_parecida_y_buscar_por_texto_devuelven_none(
    repositorio: "RepositorioPostgres",
) -> None:
    assert repositorio.buscar_mas_parecida(vector_unitario(0)) is None
    assert repositorio.buscar_por_texto_normalizado("cualquier texto normalizado") is None


# --------------------------------------------------------------------------
# AC-06 / B-18 — Desempates deterministas por identificador menor
# --------------------------------------------------------------------------


def test_ac06_buscar_mas_parecida_desempata_por_identificador_menor_rn08(
    repositorio: "RepositorioPostgres",
) -> None:
    primera = repositorio.guardar(
        frase_nueva("Primera frase, registrada antes", vector_unitario(0))
    )
    repositorio.guardar(frase_nueva("Segunda frase, registrada después", vector_unitario(0)))

    resultado = repositorio.buscar_mas_parecida(vector_unitario(0))

    assert resultado is not None
    frase, puntaje = resultado
    assert frase.id == primera.id
    assert puntaje == pytest.approx(1.0, abs=1e-6)


def test_b18_buscar_por_texto_normalizado_desempata_por_id_menor_y_no_normaliza(
    repositorio: "RepositorioPostgres",
) -> None:
    primera = repositorio.guardar(
        frase_nueva("Hola Mundo", vector_unitario(0), texto_normalizado="hola mundo")
    )
    repositorio.guardar(
        frase_nueva("HOLA MUNDO", vector_unitario(1), texto_normalizado="hola mundo")
    )

    resultado = repositorio.buscar_por_texto_normalizado("hola mundo")
    assert resultado is not None
    assert resultado.id == primera.id

    # El adaptador no normaliza (plan §3, "buscar_por_texto_normalizado recibe
    # el texto YA normalizado"): un texto que no llega ya normalizado no
    # encuentra la fila, aunque represente la misma frase para una persona.
    assert repositorio.buscar_por_texto_normalizado("HOLA MUNDO") is None


# --------------------------------------------------------------------------
# AC-15 — Listado paginado y ordenado (última cláusula: fechas iguales)
# --------------------------------------------------------------------------


def test_ac15_listado_pagina_y_desempata_por_id_descendente_con_fechas_iguales(
    repositorio: "RepositorioPostgres", sesion_sql: "Session"
) -> None:
    ids = [
        repositorio.guardar(frase_nueva(f"Frase número {indice:02d}", vector_unitario(indice))).id
        for indice in range(25)
    ]
    # Simula 25 filas insertadas en la misma transacción (plan §2: "varias
    # filas insertadas juntas comparten fecha"): todas comparten `creada_en`.
    sesion_sql.execute(
        text("UPDATE frases SET creada_en = :fecha"), {"fecha": datetime(2026, 1, 1, tzinfo=UTC)}
    )
    sesion_sql.commit()

    primera_pagina, total_primera = repositorio.listar(limite=20, desplazamiento=0)
    assert total_primera == 25
    assert [frase.id for frase in primera_pagina] == sorted(ids, reverse=True)[:20]

    segunda_pagina, total_segunda = repositorio.listar(limite=100, desplazamiento=20)
    assert total_segunda == 25
    assert [frase.id for frase in segunda_pagina] == sorted(ids, reverse=True)[20:]

    pagina_fuera_de_rango, total_tercera = repositorio.listar(limite=20, desplazamiento=1000)
    assert pagina_fuera_de_rango == []
    assert total_tercera == 25


def test_ac15_listado_ordena_por_fecha_descendente_por_encima_del_id(
    repositorio: "RepositorioPostgres", sesion_sql: "Session"
) -> None:
    frase_a = repositorio.guardar(frase_nueva("Frase A, guardada primero", vector_unitario(0)))
    frase_b = repositorio.guardar(frase_nueva("Frase B, guardada después", vector_unitario(1)))
    assert frase_a.id < frase_b.id

    # Se invierten las fechas respecto al orden de inserción: si el listado
    # ordenara por `id` en vez de por `creada_en`, este test fallaría.
    sesion_sql.execute(
        text("UPDATE frases SET creada_en = :fecha WHERE id = :id"),
        {"fecha": datetime(2030, 1, 1, tzinfo=UTC), "id": frase_a.id},
    )
    sesion_sql.execute(
        text("UPDATE frases SET creada_en = :fecha WHERE id = :id"),
        {"fecha": datetime(2020, 1, 1, tzinfo=UTC), "id": frase_b.id},
    )
    sesion_sql.commit()

    pagina, total = repositorio.listar(limite=20, desplazamiento=0)

    assert total == 2
    assert [frase.id for frase in pagina] == [frase_a.id, frase_b.id]


# --------------------------------------------------------------------------
# AC-19 — El listado incluye la frase más parecida
# --------------------------------------------------------------------------


def test_ac19_listar_incluye_texto_original_de_la_mas_parecida_y_none_sin_ella(
    repositorio: "RepositorioPostgres",
) -> None:
    # El texto original de "auto" no está normalizado, para comprobar que
    # `texto_mas_parecida` es el texto ORIGINAL de la frase referida.
    auto = repositorio.guardar(
        frase_nueva("  Compré un AUTO  ", vector_unitario(0), texto_normalizado="compré un auto")
    )
    carro = repositorio.guardar(
        frase_nueva(
            "Compré un carro",
            vector_con_coseno(0.95, eje_ortogonal=1),
            estado=EstadoFrase.DUPLICADO_CONFIRMADO,
            puntaje_similitud=0.95,
            id_mas_parecida=auto.id,
        )
    )

    pagina, total = repositorio.listar(limite=20, desplazamiento=0)

    assert total == 2
    por_id = {item.id: item for item in pagina}
    assert por_id[carro.id].texto_mas_parecida == "  Compré un AUTO  "
    assert por_id[auto.id].texto_mas_parecida is None


def _contar_sentencias_del_listado(repositorio: "RepositorioPostgres", engine: "Engine") -> int:
    """Cuenta las sentencias ejecutadas por `repositorio.listar(...)`.

    El listener se registra y se retira alrededor de la propia llamada, para
    no contar las sentencias de preparación de cada escenario (plan §1.3,
    AC-19: dos sentencias fijas —página y `COUNT`— sin importar la cantidad
    de filas).
    """
    contador = {"n": 0}

    def _contar(*_args: object, **_kwargs: object) -> None:
        contador["n"] += 1

    event.listen(engine, "before_cursor_execute", _contar)
    try:
        repositorio.listar(limite=20, desplazamiento=0)
    finally:
        event.remove(engine, "before_cursor_execute", _contar)

    return contador["n"]


def test_ac19_numero_de_sentencias_del_listado_es_igual_con_una_frase_que_con_veinte(
    repositorio: "RepositorioPostgres",
    sesion_sql: "Session",
    fabrica_sesiones: "sessionmaker[Session]",
) -> None:
    engine = sesion_sql.get_bind()

    repositorio.guardar(frase_nueva("Única frase registrada", vector_unitario(0)))
    sentencias_con_una = _contar_sentencias_del_listado(repositorio, engine)  # type: ignore[arg-type]

    with fabrica_sesiones() as sesion_limpieza:
        sesion_limpieza.execute(text("TRUNCATE TABLE frases RESTART IDENTITY"))
        sesion_limpieza.commit()

    # Cada frase (salvo la primera) apunta a la anterior por `id_mas_parecida`:
    # una implementación N+1 (una consulta extra por fila para resolver el
    # texto de la más parecida) se delata en el conteo de sentencias, en vez
    # de pasar en falso por casualidad.
    textos_por_id: dict[int, str] = {}
    anterior_id: int | None = None
    for indice in range(20):
        texto = f"Frase encadenada número {indice:02d}"
        guardada = repositorio.guardar(
            frase_nueva(
                texto,
                vector_unitario(indice),
                estado=EstadoFrase.DUPLICADO_CONFIRMADO
                if anterior_id is not None
                else EstadoFrase.UNICA,
                puntaje_similitud=0.99 if anterior_id is not None else None,
                id_mas_parecida=anterior_id,
            )
        )
        textos_por_id[guardada.id] = texto
        anterior_id = guardada.id

    sentencias_con_veinte = _contar_sentencias_del_listado(repositorio, engine)  # type: ignore[arg-type]

    assert sentencias_con_veinte == sentencias_con_una

    pagina, total = repositorio.listar(limite=20, desplazamiento=0)
    assert total == 20
    for item in pagina:
        if item.id_mas_parecida is None:
            assert item.texto_mas_parecida is None
        else:
            assert item.texto_mas_parecida == textos_por_id[item.id_mas_parecida]


# --------------------------------------------------------------------------
# `esta_disponible()`
# --------------------------------------------------------------------------


def test_esta_disponible_es_verdadero_con_la_base_de_test_accesible(
    repositorio: "RepositorioPostgres",
) -> None:
    assert repositorio.esta_disponible() is True


def test_esta_disponible_es_falso_con_una_fabrica_inaccesible(
    repositorio_inaccesible: "RepositorioPostgres",
) -> None:
    assert repositorio_inaccesible.esta_disponible() is False


# --------------------------------------------------------------------------
# Traducción de errores de conexión a `ErrorRepositorio` (RN-15)
# --------------------------------------------------------------------------


def _guardar(repositorio: "RepositorioPostgres") -> None:
    repositorio.guardar(frase_nueva("Cualquier frase válida", vector_unitario(0)))


def _listar(repositorio: "RepositorioPostgres") -> None:
    repositorio.listar(limite=20, desplazamiento=0)


def _buscar_por_texto_normalizado(repositorio: "RepositorioPostgres") -> None:
    repositorio.buscar_por_texto_normalizado("cualquier texto normalizado")


def _buscar_mas_parecida(repositorio: "RepositorioPostgres") -> None:
    repositorio.buscar_mas_parecida(vector_unitario(0))


@pytest.mark.parametrize(
    "operacion",
    [_guardar, _listar, _buscar_por_texto_normalizado, _buscar_mas_parecida],
    ids=["guardar", "listar", "buscar_por_texto_normalizado", "buscar_mas_parecida"],
)
def test_operaciones_contra_una_base_inaccesible_lanzan_errorrepositorio(
    repositorio_inaccesible: "RepositorioPostgres",
    operacion: Callable[["RepositorioPostgres"], None],
) -> None:
    with pytest.raises(ErrorRepositorio):
        operacion(repositorio_inaccesible)


def test_b27_error_de_datos_no_se_traduce_a_errorrepositorio(
    repositorio: "RepositorioPostgres",
) -> None:
    # Un dato que PostgreSQL rechaza (U+0000 en texto) no significa que la base
    # esté caída: no debe responder 503. El dominio ya lo impide (RN-01); si
    # llegara aquí, sube tal cual y el manejador genérico responde 500.
    with pytest.raises(DataError):
        repositorio.buscar_por_texto_normalizado("a" + chr(0) + "b")
