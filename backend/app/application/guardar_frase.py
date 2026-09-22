"""Caso de uso `GuardarFrase` (plan §4): revalida y, si corresponde, persiste."""

from app.application.validar_frase import ValidarFrase
from app.domain.entidades import EstadoFrase, Frase, FraseNueva
from app.domain.errores import PosibleDuplicado
from app.domain.vectores import normalizar_vector
from app.ports.embeddings import ProveedorEmbeddings
from app.ports.repositorio import RepositorioFrases


class GuardarFrase:
    def __init__(
        self,
        repositorio: RepositorioFrases,
        embedder: ProveedorEmbeddings,
        umbral: float,
        longitud_maxima: int,
    ) -> None:
        self._repositorio = repositorio
        self._embedder = embedder
        self._validar_frase = ValidarFrase(repositorio, embedder, umbral, longitud_maxima)

    def guardar(self, texto: str, confirmar_duplicado: bool = False) -> Frase:
        # 1. Revalidar desde cero: lo que el cliente vio antes no es prueba (RN-11).
        resultado = self._validar_frase.validar(texto)

        # 2. Un posible duplicado solo se guarda con confirmación explícita (RN-12).
        if resultado.es_posible_duplicado and not confirmar_duplicado:
            raise PosibleDuplicado(resultado)

        # 3. El duplicado exacto no llegó a generar embedding: se genera ahora (RN-14).
        #    Si el proveedor falla, la excepción impide guardar (RN-15).
        embedding = resultado.embedding
        if embedding is None:
            embedding = normalizar_vector(self._embedder.generar(resultado.texto_normalizado))

        # 4. Persistir con los metadatos de este momento (RN-13).
        return self._repositorio.guardar(
            FraseNueva(
                texto_original=texto,
                texto_normalizado=resultado.texto_normalizado,
                embedding=embedding,
                estado=(
                    EstadoFrase.DUPLICADO_CONFIRMADO
                    if resultado.es_posible_duplicado
                    else EstadoFrase.UNICA
                ),
                puntaje_similitud=resultado.puntaje,
                id_mas_parecida=resultado.mas_parecida.id if resultado.mas_parecida else None,
                modelo=resultado.modelo,
                umbral_aplicado=resultado.umbral_aplicado,
            )
        )
