"""Caso de uso `ValidarFrase` (plan §4). Solo lectura: no persiste nada (RN-10)."""

from app.domain.entidades import Frase, MotivoDuplicado, ResultadoValidacion
from app.domain.normalizacion import normalizar_y_validar
from app.domain.politica import es_posible_duplicado, recortar_puntaje
from app.domain.vectores import normalizar_vector
from app.ports.embeddings import ProveedorEmbeddings
from app.ports.repositorio import RepositorioFrases


class ValidarFrase:
    def __init__(
        self,
        repositorio: RepositorioFrases,
        embedder: ProveedorEmbeddings,
        umbral: float,
        longitud_maxima: int,
    ) -> None:
        self._repositorio = repositorio
        self._embedder = embedder
        self._umbral = umbral
        self._longitud_maxima = longitud_maxima

    def validar(self, texto: str) -> ResultadoValidacion:
        # 1. Normalizar y validar longitud antes de tocar nada (RN-01 a RN-03).
        texto_normalizado = normalizar_y_validar(texto, self._longitud_maxima)

        # 2. Duplicado exacto: más barato, sin llamar al proveedor (RN-04, RN-08).
        exacta = self._repositorio.buscar_por_texto_normalizado(texto_normalizado)
        if exacta is not None:
            return self._resultado(
                texto_normalizado,
                embedding=None,
                es_duplicado=True,
                motivo=MotivoDuplicado.EXACTO,
                puntaje=1.0,
                mas_parecida=exacta,
            )

        # 3. Embedding del texto normalizado, llevado a norma 1 (RN-05, RN-19).
        embedding = normalizar_vector(self._embedder.generar(texto_normalizado))

        # 4. Vecino más cercano; base vacía, frase única (RN-09).
        vecino = self._repositorio.buscar_mas_parecida(embedding)
        if vecino is None:
            return self._resultado(
                texto_normalizado,
                embedding=embedding,
                es_duplicado=False,
                motivo=None,
                puntaje=None,
                mas_parecida=None,
            )

        # 5. Recortar y aplicar la política sobre el puntaje sin redondear (RN-05, RN-06).
        mas_parecida, coseno = vecino
        puntaje = recortar_puntaje(coseno)
        es_duplicado = es_posible_duplicado(puntaje, self._umbral)
        return self._resultado(
            texto_normalizado,
            embedding=embedding,
            es_duplicado=es_duplicado,
            motivo=MotivoDuplicado.SEMANTICO if es_duplicado else None,
            puntaje=puntaje,
            mas_parecida=mas_parecida,
        )

    def _resultado(
        self,
        texto_normalizado: str,
        *,
        embedding: list[float] | None,
        es_duplicado: bool,
        motivo: MotivoDuplicado | None,
        puntaje: float | None,
        mas_parecida: Frase | None,
    ) -> ResultadoValidacion:
        return ResultadoValidacion(
            es_posible_duplicado=es_duplicado,
            motivo=motivo,
            puntaje=puntaje,
            mas_parecida=mas_parecida,
            umbral_aplicado=self._umbral,
            modelo=self._embedder.nombre_modelo,
            texto_normalizado=texto_normalizado,
            embedding=embedding,
        )
