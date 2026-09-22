"""`HuggingFaceEmbedder`: implementación de `ProveedorEmbeddings` con `sentence-transformers`.

El import de `sentence_transformers` es perezoso, dentro del constructor: así
la aplicación y la suite rápida se importan sin cargar `torch` (plan §3).
Cualquier fallo de la librería se traduce a `ErrorProveedorEmbeddings` (RN-15).
"""

from typing import TYPE_CHECKING

from app.domain.errores import ErrorProveedorEmbeddings

if TYPE_CHECKING:
    from app.ports.embeddings import ProveedorEmbeddings


class HuggingFaceEmbedder:
    def __init__(self, nombre_modelo: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            self._modelo = SentenceTransformer(nombre_modelo)
            dimension = self._modelo.get_embedding_dimension()
        except Exception as error:
            raise ErrorProveedorEmbeddings(
                f"No se pudo cargar el modelo {nombre_modelo}."
            ) from error
        if dimension is None:
            raise ErrorProveedorEmbeddings(f"El modelo {nombre_modelo} no declara su dimensión.")
        self._nombre_modelo = nombre_modelo
        self._dimension: int = dimension

    @property
    def nombre_modelo(self) -> str:
        return self._nombre_modelo

    @property
    def dimension(self) -> int:
        return self._dimension

    def generar(self, texto: str) -> list[float]:
        try:
            # La normalización a norma 1 es del negocio (RN-19); pedirla aquí
            # solo ahorra trabajo, el caso de uso la aplica igualmente.
            vector = self._modelo.encode(texto, normalize_embeddings=True)
            componentes = vector.tolist() if hasattr(vector, "tolist") else vector
            return [float(componente) for componente in componentes]
        except Exception as error:
            raise ErrorProveedorEmbeddings("No se pudo generar el embedding.") from error


if TYPE_CHECKING:
    # mypy comprueba aquí que el adaptador implementa el puerto.
    _conforme: ProveedorEmbeddings = HuggingFaceEmbedder("")
