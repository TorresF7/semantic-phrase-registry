"""Puerto del repositorio de frases (plan §3).

Cualquier fallo de conexión o de SQL se traduce, dentro del adaptador, a
`ErrorRepositorio` (RN-15).
"""

from typing import Protocol

from app.domain.entidades import Frase, FraseNueva


class RepositorioFrases(Protocol):
    def buscar_por_texto_normalizado(self, texto: str) -> Frase | None:
        """La frase con ese texto normalizado; si hay varias, la de id menor (RN-04, RN-08)."""
        ...

    def buscar_mas_parecida(self, embedding: list[float]) -> tuple[Frase, float] | None:
        """La frase de mayor similitud coseno, sin recortar; empate por id menor (RN-05, RN-08).

        `None` si no hay frases registradas (RN-09).
        """
        ...

    def guardar(self, frase: FraseNueva) -> Frase:
        """Persiste la frase con su embedding; la base asigna `id` y fecha (RN-13, RN-14)."""
        ...

    def listar(self, limite: int, desplazamiento: int) -> tuple[list[Frase], int]:
        """Una página por fecha descendente y, a igual fecha, id descendente, y el total (RN-17)."""
        ...

    def esta_disponible(self) -> bool: ...
