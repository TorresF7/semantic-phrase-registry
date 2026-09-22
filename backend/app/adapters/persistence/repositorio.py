"""`RepositorioPostgres`: implementación de `RepositorioFrases` con pgvector (plan §2).

Toda excepción de SQLAlchemy o del driver se traduce aquí a `ErrorRepositorio`
(RN-15): los casos de uso nunca ven un tipo de error de la librería.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased, sessionmaker

from app.adapters.persistence.modelos import ModeloFrase
from app.domain.entidades import Frase, FraseNueva
from app.domain.errores import ErrorRepositorio

if TYPE_CHECKING:
    from app.ports.repositorio import RepositorioFrases

_T = TypeVar("_T")

# HNSW no se usa si el ORDER BY lleva `id` además de la distancia: se piden
# las más cercanas solo por distancia y el desempate de RN-08 se resuelve
# sobre ellas (plan §2, D-19).
_CANDIDATAS_DESEMPATE = 5


class RepositorioPostgres:
    def __init__(self, fabrica_sesiones: sessionmaker[Session]) -> None:
        self._fabrica_sesiones = fabrica_sesiones

    def buscar_por_texto_normalizado(self, texto: str) -> Frase | None:
        consulta = (
            select(ModeloFrase)
            .where(ModeloFrase.texto_normalizado == texto)
            .order_by(ModeloFrase.id.asc())
            .limit(1)
        )
        return self._ejecutar(lambda sesion: _a_frase_o_nada(sesion.scalars(consulta).first()))

    def buscar_mas_parecida(self, embedding: list[float]) -> tuple[Frase, float] | None:
        distancia = ModeloFrase.embedding.cosine_distance(embedding).label("distancia")
        candidatas = (
            select(ModeloFrase, distancia)
            .order_by(distancia)
            .limit(_CANDIDATAS_DESEMPATE)
            .subquery()
        )
        candidata = aliased(ModeloFrase, candidatas)
        consulta = (
            select(candidata, candidatas.c.distancia)
            .order_by(candidatas.c.distancia.asc(), candidata.id.asc())
            .limit(1)
        )

        def buscar(sesion: Session) -> tuple[Frase, float] | None:
            fila = sesion.execute(consulta).first()
            if fila is None:
                return None
            modelo, distancia_coseno = fila
            return _a_frase(modelo), 1.0 - distancia_coseno

        return self._ejecutar(buscar)

    def guardar(self, frase: FraseNueva) -> Frase:
        def insertar(sesion: Session) -> Frase:
            modelo = ModeloFrase(
                texto_original=frase.texto_original,
                texto_normalizado=frase.texto_normalizado,
                embedding=frase.embedding,
                estado=frase.estado,
                puntaje_similitud=frase.puntaje_similitud,
                id_mas_parecida=frase.id_mas_parecida,
                modelo=frase.modelo,
                umbral_aplicado=frase.umbral_aplicado,
            )
            sesion.add(modelo)
            sesion.commit()
            # `id` y `creada_en` los asigna la base; el refresco los trae.
            sesion.refresh(modelo)
            return _a_frase(modelo)

        return self._ejecutar(insertar)

    def listar(self, limite: int, desplazamiento: int) -> tuple[list[Frase], int]:
        consulta = (
            select(ModeloFrase)
            .order_by(ModeloFrase.creada_en.desc(), ModeloFrase.id.desc())
            .limit(limite)
            .offset(desplazamiento)
        )
        contar = select(func.count()).select_from(ModeloFrase)

        def paginar(sesion: Session) -> tuple[list[Frase], int]:
            frases = [_a_frase(modelo) for modelo in sesion.scalars(consulta)]
            return frases, sesion.scalar(contar) or 0

        return self._ejecutar(paginar)

    def esta_disponible(self) -> bool:
        try:
            self._ejecutar(lambda sesion: sesion.execute(text("SELECT 1")))
        except ErrorRepositorio:
            return False
        return True

    def _ejecutar(self, operacion: Callable[[Session], _T]) -> _T:
        try:
            with self._fabrica_sesiones() as sesion:
                return operacion(sesion)
        except SQLAlchemyError as error:
            raise ErrorRepositorio("La base de datos no está disponible.") from error


def _a_frase(modelo: ModeloFrase) -> Frase:
    return Frase(
        id=modelo.id,
        texto_original=modelo.texto_original,
        estado=modelo.estado,
        puntaje_similitud=modelo.puntaje_similitud,
        id_mas_parecida=modelo.id_mas_parecida,
        modelo=modelo.modelo,
        umbral_aplicado=modelo.umbral_aplicado,
        creada_en=modelo.creada_en,
    )


def _a_frase_o_nada(modelo: ModeloFrase | None) -> Frase | None:
    return None if modelo is None else _a_frase(modelo)


if TYPE_CHECKING:
    # mypy comprueba aquí que el adaptador implementa el puerto.
    _conforme: RepositorioFrases = RepositorioPostgres(sessionmaker())
