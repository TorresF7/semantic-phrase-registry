"""Tests de T-06 (Puertos y dobles de prueba): `RepositorioEnMemoria`.

T-06 no tiene AC propios: este doble sirve a AC-03 a AC-18 en T-07/T-08/T-12,
por eso los nombres no llevan el prefijo `ac`. Fija el contrato acordado en
`plan.md` §3: implementa `RepositorioFrases` con una lista, respetando los
mismos desempates por identificador menor que la consulta SQL (RN-08) y
pudiendo simular la caída de la base (RN-15).
"""

from datetime import UTC, datetime

import pytest

from app.domain.entidades import EstadoFrase, FraseNueva
from app.domain.errores import ErrorRepositorio
from tests.dobles.repositorio_en_memoria import RepositorioEnMemoria


def _frase_nueva(
    texto_original: str,
    texto_normalizado: str,
    embedding: list[float],
    *,
    estado: EstadoFrase = EstadoFrase.UNICA,
    puntaje_similitud: float | None = None,
    id_mas_parecida: int | None = None,
    modelo: str = "modelo-falso",
    umbral_aplicado: float = 0.80,
) -> FraseNueva:
    return FraseNueva(
        texto_original=texto_original,
        texto_normalizado=texto_normalizado,
        embedding=embedding,
        estado=estado,
        puntaje_similitud=puntaje_similitud,
        id_mas_parecida=id_mas_parecida,
        modelo=modelo,
        umbral_aplicado=umbral_aplicado,
    )


# --- sembrar --------------------------------------------------------------


def test_sembrar_asigna_ids_consecutivos_desde_uno() -> None:
    repositorio = RepositorioEnMemoria()

    primera = repositorio.sembrar("Hola", [1.0, 0.0])
    segunda = repositorio.sembrar("Chau", [0.0, 1.0])

    assert primera.id == 1
    assert segunda.id == 2


def test_sembrar_no_se_registra_en_guardadas() -> None:
    repositorio = RepositorioEnMemoria()

    repositorio.sembrar("Hola", [1.0, 0.0])

    assert repositorio.guardadas == []


def test_sembrar_crea_una_frase_unica_sin_puntaje_ni_mas_parecida() -> None:
    repositorio = RepositorioEnMemoria()

    frase = repositorio.sembrar("El pago fue rechazado", [1.0, 0.0])

    assert frase.texto_original == "El pago fue rechazado"
    assert frase.estado == EstadoFrase.UNICA
    assert frase.puntaje_similitud is None
    assert frase.id_mas_parecida is None


def test_sembrar_normaliza_el_texto_para_la_busqueda_exacta() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.sembrar("El Pago", [1.0, 0.0])

    # El puerto recibe el texto ya normalizado, igual que la consulta SQL.
    encontrada = repositorio.buscar_por_texto_normalizado("el pago")

    assert encontrada is not None
    assert encontrada.texto_original == "El Pago"


def test_sembrar_ignora_un_fallo_configurado() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.fallo = ErrorRepositorio("caída")

    frase = repositorio.sembrar("Hola", [1.0, 0.0])

    assert frase.id == 1


# --- guardar ---------------------------------------------------------------


def test_guardar_registra_la_frase_nueva_en_guardadas_en_orden() -> None:
    repositorio = RepositorioEnMemoria()
    primera = _frase_nueva("Hola", "hola", [1.0, 0.0])
    segunda = _frase_nueva("Chau", "chau", [0.0, 1.0])

    repositorio.guardar(primera)
    repositorio.guardar(segunda)

    assert repositorio.guardadas == [primera, segunda]


def test_guardar_devuelve_una_frase_con_los_metadatos_de_la_frase_nueva() -> None:
    repositorio = RepositorioEnMemoria()
    frase_nueva = _frase_nueva(
        "El pago fue rechazado",
        "el pago fue rechazado",
        [1.0, 0.0],
        estado=EstadoFrase.DUPLICADO_CONFIRMADO,
        puntaje_similitud=0.91,
        id_mas_parecida=7,
        modelo="modelo-de-prueba",
        umbral_aplicado=0.85,
    )

    guardada = repositorio.guardar(frase_nueva)

    assert guardada.texto_original == "El pago fue rechazado"
    assert guardada.estado == EstadoFrase.DUPLICADO_CONFIRMADO
    assert guardada.puntaje_similitud == 0.91
    assert guardada.id_mas_parecida == 7
    assert guardada.modelo == "modelo-de-prueba"
    assert guardada.umbral_aplicado == 0.85


def test_guardar_asigna_ids_consecutivos_desde_uno() -> None:
    repositorio = RepositorioEnMemoria()

    primera = repositorio.guardar(_frase_nueva("Hola", "hola", [1.0]))
    segunda = repositorio.guardar(_frase_nueva("Chau", "chau", [1.0]))

    assert primera.id == 1
    assert segunda.id == 2


def test_sin_reloj_todas_las_frases_guardadas_comparten_la_misma_fecha() -> None:
    repositorio = RepositorioEnMemoria()

    primera = repositorio.guardar(_frase_nueva("Hola", "hola", [1.0]))
    segunda = repositorio.guardar(_frase_nueva("Chau", "chau", [1.0]))

    assert primera.creada_en == segunda.creada_en
    assert primera.creada_en.tzinfo is not None
    assert primera.creada_en.utcoffset() == UTC.utcoffset(None)


def test_guardar_usa_el_reloj_inyectado_para_creada_en() -> None:
    fechas = iter(
        [
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 2, tzinfo=UTC),
        ]
    )
    repositorio = RepositorioEnMemoria(reloj=lambda: next(fechas))

    primera = repositorio.guardar(_frase_nueva("Hola", "hola", [1.0]))
    segunda = repositorio.guardar(_frase_nueva("Chau", "chau", [1.0]))

    assert primera.creada_en == datetime(2026, 1, 1, tzinfo=UTC)
    assert segunda.creada_en == datetime(2026, 1, 2, tzinfo=UTC)


# --- buscar_por_texto_normalizado ------------------------------------------


def test_buscar_por_texto_normalizado_sin_coincidencias_devuelve_none() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.sembrar("Hola", [1.0])

    assert repositorio.buscar_por_texto_normalizado("adiós") is None


def test_buscar_por_texto_normalizado_no_hace_coincidencia_parcial() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.sembrar("hola mundo", [1.0])

    assert repositorio.buscar_por_texto_normalizado("hola") is None


def test_buscar_por_texto_normalizado_con_varias_coincidencias_devuelve_la_de_id_menor_b18() -> (
    None
):
    repositorio = RepositorioEnMemoria()
    primera = repositorio.guardar(_frase_nueva("Hola primero", "hola", [1.0]))
    repositorio.guardar(_frase_nueva("Hola segundo", "hola", [1.0]))

    encontrada = repositorio.buscar_por_texto_normalizado("hola")

    assert encontrada is not None
    assert encontrada.id == primera.id


def test_con_fallo_configurado_buscar_por_texto_normalizado_lanza() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.fallo = ErrorRepositorio("caída")

    with pytest.raises(ErrorRepositorio):
        repositorio.buscar_por_texto_normalizado("hola")


def test_con_fallo_generico_configurado_buscar_por_texto_normalizado_lanza() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.fallo = RuntimeError("boom")

    with pytest.raises(RuntimeError):
        repositorio.buscar_por_texto_normalizado("hola")


# --- buscar_mas_parecida -----------------------------------------------------


def test_buscar_mas_parecida_sobre_base_vacia_devuelve_none_rn09() -> None:
    repositorio = RepositorioEnMemoria()

    assert repositorio.buscar_mas_parecida([1.0, 0.0]) is None


def test_buscar_mas_parecida_devuelve_la_de_mayor_coseno() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.sembrar("lejos", [0.0, 1.0])
    cercana = repositorio.sembrar("cerca", [1.0, 0.0])

    resultado = repositorio.buscar_mas_parecida([1.0, 0.0])

    assert resultado is not None
    frase, puntaje = resultado
    assert frase.id == cercana.id
    assert puntaje == pytest.approx(1.0)


def test_buscar_mas_parecida_en_empate_devuelve_la_de_id_menor_rn08() -> None:
    repositorio = RepositorioEnMemoria()
    primera = repositorio.sembrar("primera", [1.0, 0.0])
    repositorio.sembrar("segunda", [1.0, 0.0])

    resultado = repositorio.buscar_mas_parecida([1.0, 0.0])

    assert resultado is not None
    frase, _ = resultado
    assert frase.id == primera.id


def test_buscar_mas_parecida_no_recorta_un_puntaje_negativo() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.sembrar("opuesta", [-1.0, 0.0])

    resultado = repositorio.buscar_mas_parecida([1.0, 0.0])

    assert resultado is not None
    _, puntaje = resultado
    assert puntaje == pytest.approx(-1.0)


def test_buscar_mas_parecida_es_independiente_de_la_norma_de_los_vectores() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.sembrar("misma dirección, otra magnitud", [5.0, 0.0])

    resultado = repositorio.buscar_mas_parecida([0.2, 0.0])

    assert resultado is not None
    _, puntaje = resultado
    assert puntaje == pytest.approx(1.0)


def test_con_fallo_configurado_buscar_mas_parecida_lanza() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.fallo = ErrorRepositorio("caída")

    with pytest.raises(ErrorRepositorio):
        repositorio.buscar_mas_parecida([1.0, 0.0])


def test_con_fallo_generico_configurado_buscar_mas_parecida_lanza() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.fallo = RuntimeError("boom")

    with pytest.raises(RuntimeError):
        repositorio.buscar_mas_parecida([1.0, 0.0])


# --- guardar con fallo -------------------------------------------------------


def test_con_fallo_configurado_guardar_lanza_y_no_registra_nada() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.fallo = ErrorRepositorio("caída")

    with pytest.raises(ErrorRepositorio):
        repositorio.guardar(_frase_nueva("Hola", "hola", [1.0]))

    assert repositorio.guardadas == []


def test_con_fallo_generico_configurado_guardar_lanza() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.fallo = RuntimeError("boom")

    with pytest.raises(RuntimeError):
        repositorio.guardar(_frase_nueva("Hola", "hola", [1.0]))


# --- listar ------------------------------------------------------------------


def test_listar_devuelve_la_pagina_pedida_y_el_total() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.sembrar("una", [1.0])
    repositorio.sembrar("dos", [1.0])
    repositorio.sembrar("tres", [1.0])

    items, total = repositorio.listar(limite=2, desplazamiento=0)

    assert total == 3
    assert len(items) == 2


def test_listar_ordena_por_fecha_de_creacion_descendente_rn17() -> None:
    fechas = iter(
        [
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 2, tzinfo=UTC),
            datetime(2026, 1, 3, tzinfo=UTC),
        ]
    )
    repositorio = RepositorioEnMemoria(reloj=lambda: next(fechas))
    primera = repositorio.guardar(_frase_nueva("una", "una", [1.0]))
    segunda = repositorio.guardar(_frase_nueva("dos", "dos", [1.0]))
    tercera = repositorio.guardar(_frase_nueva("tres", "tres", [1.0]))

    items, _ = repositorio.listar(limite=10, desplazamiento=0)

    assert [item.id for item in items] == [tercera.id, segunda.id, primera.id]


def test_listar_con_fechas_iguales_ordena_por_id_descendente_rn17() -> None:
    repositorio = RepositorioEnMemoria()
    primera = repositorio.guardar(_frase_nueva("una", "una", [1.0]))
    segunda = repositorio.guardar(_frase_nueva("dos", "dos", [1.0]))
    tercera = repositorio.guardar(_frase_nueva("tres", "tres", [1.0]))

    items, _ = repositorio.listar(limite=10, desplazamiento=0)

    assert [item.id for item in items] == [tercera.id, segunda.id, primera.id]


def test_listar_respeta_limite_y_desplazamiento_juntos() -> None:
    fechas = iter(datetime(2026, 1, dia, tzinfo=UTC) for dia in range(1, 6))
    repositorio = RepositorioEnMemoria(reloj=lambda: next(fechas))
    ids = [repositorio.guardar(_frase_nueva(str(n), str(n), [1.0])).id for n in range(1, 6)]
    # Orden esperado, más reciente primero: [5, 4, 3, 2, 1] (por id, ya que sus ids).

    items, total = repositorio.listar(limite=2, desplazamiento=2)

    assert total == 5
    assert [item.id for item in items] == [ids[2], ids[1]]


def test_listar_con_desplazamiento_mayor_que_el_total_devuelve_lista_vacia_con_total_correcto() -> (
    None
):
    repositorio = RepositorioEnMemoria()
    repositorio.sembrar("una", [1.0])
    repositorio.sembrar("dos", [1.0])

    items, total = repositorio.listar(limite=10, desplazamiento=5)

    assert items == []
    assert total == 2


def test_listar_sobre_base_vacia_devuelve_lista_vacia_y_total_cero() -> None:
    repositorio = RepositorioEnMemoria()

    items, total = repositorio.listar(limite=10, desplazamiento=0)

    assert items == []
    assert total == 0


def test_con_fallo_configurado_listar_lanza() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.fallo = ErrorRepositorio("caída")

    with pytest.raises(ErrorRepositorio):
        repositorio.listar(limite=10, desplazamiento=0)


def test_con_fallo_generico_configurado_listar_lanza() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.fallo = RuntimeError("boom")

    with pytest.raises(RuntimeError):
        repositorio.listar(limite=10, desplazamiento=0)


# --- esta_disponible ----------------------------------------------------------


def test_esta_disponible_es_verdadero_sin_fallo_configurado() -> None:
    repositorio = RepositorioEnMemoria()

    assert repositorio.esta_disponible() is True


def test_esta_disponible_es_falso_con_fallo_configurado() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.fallo = ErrorRepositorio("caída")

    assert repositorio.esta_disponible() is False


def test_esta_disponible_no_lanza_aunque_haya_un_fallo_generico_configurado() -> None:
    repositorio = RepositorioEnMemoria()
    repositorio.fallo = RuntimeError("boom")

    assert repositorio.esta_disponible() is False
