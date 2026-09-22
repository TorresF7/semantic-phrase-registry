"""`FakeEmbedder`: implementación determinista de `ProveedorEmbeddings`.

No carga ningún modelo. El vector de cada texto sale de una de tres fuentes:

1. `fijar_similitud`: puntajes exactos entre pares de frases (AC-04 a AC-06).
2. `fijar_vector`: un vector concreto, incluso sin normalizar o de ceros (AC-17).
3. Sin nada fijado: un vector derivado de un hash del texto normalizado.

Todo vector sale multiplicado por `factor_escala`, para probar que la
normalización es del negocio y no del proveedor (RN-19). Las claves pasan por
`normalizar`, igual que el texto que el caso de uso embebe (RN-05).
"""

import hashlib
import math
import random
from typing import TYPE_CHECKING

from app.domain.normalizacion import normalizar

if TYPE_CHECKING:
    from app.ports.embeddings import ProveedorEmbeddings


class FakeEmbedder:
    def __init__(
        self,
        nombre_modelo: str = "modelo-falso",
        dimension: int = 384,
        factor_escala: float = 1.0,
    ) -> None:
        self._nombre_modelo = nombre_modelo
        self._dimension = dimension
        self._factor_escala = factor_escala
        self._vectores: dict[str, list[float]] = {}
        # Anclas de `fijar_similitud` y el eje de la base canónica que ocupa cada una.
        self._ejes_de_anclas: dict[str, int] = {}
        self._siguiente_eje = 0
        self.textos_recibidos: list[str] = []
        self.fallo: Exception | None = None

    @property
    def nombre_modelo(self) -> str:
        return self._nombre_modelo

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def llamadas(self) -> int:
        return len(self.textos_recibidos)

    def generar(self, texto: str) -> list[float]:
        self.textos_recibidos.append(texto)
        if self.fallo is not None:
            raise self.fallo
        clave = normalizar(texto)
        vector = self._vectores.get(clave) or self._vector_por_hash(clave)
        return [componente * self._factor_escala for componente in vector]

    def fijar_vector(self, texto: str, vector: list[float]) -> None:
        self._vectores[normalizar(texto)] = list(vector)

    def fijar_similitud(self, ancla: str, otra: str, puntaje: float) -> None:
        """Hace que el coseno entre `ancla` y `otra` sea exactamente `puntaje`.

        La ancla ocupa un eje propio; cada `otra` se construye como
        `puntaje * eje_ancla + sqrt(1 - puntaje**2) * eje_nuevo`, con un eje nuevo
        por cada una. Así una misma ancla admite varias `otra`, y dos `otra`
        con el mismo puntaje empatan de forma exacta (AC-06).
        """
        if not -1.0 <= puntaje <= 1.0:
            raise ValueError(f"El puntaje debe estar en [-1, 1]: {puntaje}")
        clave_ancla = normalizar(ancla)
        clave_otra = normalizar(otra)
        if clave_otra == clave_ancla or clave_otra in self._vectores:
            raise ValueError(f"'{otra}' ya tiene un vector fijado")
        if clave_ancla not in self._ejes_de_anclas:
            if clave_ancla in self._vectores:
                raise ValueError(f"'{ancla}' ya tiene un vector fijado y no puede ser ancla")
            eje = self._reservar_eje()
            self._ejes_de_anclas[clave_ancla] = eje
            self._vectores[clave_ancla] = self._vector_unitario(eje)

        vector = [0.0] * self._dimension
        vector[self._ejes_de_anclas[clave_ancla]] = puntaje
        vector[self._reservar_eje()] = math.sqrt(1.0 - puntaje * puntaje)
        self._vectores[clave_otra] = vector

    def _reservar_eje(self) -> int:
        if self._siguiente_eje >= self._dimension:
            raise ValueError("No quedan ejes libres: aumenta la dimensión del embedder falso")
        eje = self._siguiente_eje
        self._siguiente_eje += 1
        return eje

    def _vector_unitario(self, eje: int) -> list[float]:
        vector = [0.0] * self._dimension
        vector[eje] = 1.0
        return vector

    def _vector_por_hash(self, clave: str) -> list[float]:
        # Semilla estable entre procesos: `hash()` de Python no lo es.
        generador = random.Random(hashlib.sha256(clave.encode("utf-8")).digest())
        vector = [generador.gauss(0.0, 1.0) for _ in range(self._dimension)]
        norma = math.sqrt(sum(componente * componente for componente in vector))
        return [componente / norma for componente in vector]


if TYPE_CHECKING:
    # mypy comprueba aquí que el doble implementa el puerto.
    _conforme: ProveedorEmbeddings = FakeEmbedder()
