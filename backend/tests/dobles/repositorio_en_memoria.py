"""`RepositorioEnMemoria`: implementación de `RepositorioFrases` con una lista.

Respeta los mismos desempates que las consultas SQL del plan §2 (RN-08,
RN-17); si no, los tests de AC-06 no probarían lo que creen probar. Con
`fallo` configurado simula la caída de la base (AC-14, AC-18).
"""

import math
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.domain.entidades import EstadoFrase, Frase, FraseNueva
from app.domain.normalizacion import normalizar

if TYPE_CHECKING:
    from app.ports.repositorio import RepositorioFrases

# Sin reloj inyectado, todas las frases comparten fecha, como las insertadas
# en una misma transacción (plan §2): el listado desempata por id.
_FECHA_FIJA = datetime(2026, 1, 1, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class _Registro:
    frase: Frase
    texto_normalizado: str
    embedding: list[float]


class RepositorioEnMemoria:
    def __init__(self, reloj: Callable[[], datetime] | None = None) -> None:
        self._reloj = reloj or (lambda: _FECHA_FIJA)
        self._registros: list[_Registro] = []
        self.guardadas: list[FraseNueva] = []
        self.fallo: Exception | None = None

    def sembrar(self, texto_original: str, embedding: list[float]) -> Frase:
        """Atajo de preparación de los tests. Ignora `fallo` y no cuenta en `guardadas`."""
        return self._insertar(
            FraseNueva(
                texto_original=texto_original,
                texto_normalizado=normalizar(texto_original),
                embedding=embedding,
                estado=EstadoFrase.UNICA,
                puntaje_similitud=None,
                id_mas_parecida=None,
                modelo="modelo-falso",
                umbral_aplicado=0.80,
            )
        )

    def buscar_por_texto_normalizado(self, texto: str) -> Frase | None:
        self._fallar_si_corresponde()
        for registro in self._registros:  # en orden de id ascendente
            if registro.texto_normalizado == texto:
                return registro.frase
        return None

    def buscar_mas_parecida(self, embedding: list[float]) -> tuple[Frase, float] | None:
        self._fallar_si_corresponde()
        candidatas = [
            (registro.frase, _coseno(embedding, registro.embedding)) for registro in self._registros
        ]
        if not candidatas:
            return None
        return max(candidatas, key=lambda candidata: (candidata[1], -candidata[0].id))

    def guardar(self, frase: FraseNueva) -> Frase:
        self._fallar_si_corresponde()
        self.guardadas.append(frase)
        return self._insertar(frase)

    def listar(self, limite: int, desplazamiento: int) -> tuple[list[Frase], int]:
        self._fallar_si_corresponde()
        ordenadas = sorted(
            (registro.frase for registro in self._registros),
            key=lambda frase: (frase.creada_en, frase.id),
            reverse=True,
        )
        return ordenadas[desplazamiento : desplazamiento + limite], len(ordenadas)

    def esta_disponible(self) -> bool:
        return self.fallo is None

    def _fallar_si_corresponde(self) -> None:
        if self.fallo is not None:
            raise self.fallo

    def _insertar(self, nueva: FraseNueva) -> Frase:
        frase = Frase(
            id=len(self._registros) + 1,
            texto_original=nueva.texto_original,
            estado=nueva.estado,
            puntaje_similitud=nueva.puntaje_similitud,
            id_mas_parecida=nueva.id_mas_parecida,
            modelo=nueva.modelo,
            umbral_aplicado=nueva.umbral_aplicado,
            creada_en=self._reloj(),
        )
        self._registros.append(_Registro(frase, nueva.texto_normalizado, list(nueva.embedding)))
        return frase


def _coseno(a: list[float], b: list[float]) -> float:
    """Similitud coseno sin recortar: `1 - (a <=> b)` en pgvector."""
    producto = sum(x * y for x, y in zip(a, b, strict=True))
    return producto / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


if TYPE_CHECKING:
    # mypy comprueba aquí que el doble implementa el puerto.
    _conforme: RepositorioFrases = RepositorioEnMemoria()
