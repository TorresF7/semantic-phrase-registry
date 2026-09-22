"""Puerto del proveedor de embeddings (plan §3, NF-08)."""

from typing import Protocol


class ProveedorEmbeddings(Protocol):
    """Convierte un texto en un vector que representa su significado.

    Cualquier fallo se traduce, dentro del adaptador, a
    `ErrorProveedorEmbeddings` (RN-15). La normalización del vector no es
    responsabilidad del proveedor (RN-19).
    """

    @property
    def nombre_modelo(self) -> str: ...

    @property
    def dimension(self) -> int: ...

    def generar(self, texto: str) -> list[float]: ...
