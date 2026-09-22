"""Calibración del umbral de similitud con pares etiquetados (plan §8, D-07).

Genera los embeddings con el mismo adaptador y la misma normalización que la
aplicación (RN-02, RN-19), calcula el coseno de cada par y, para cada umbral
de 0.60 a 0.95 en pasos de 0.05, informa precisión, exhaustividad y F1 de la
regla "posible duplicado si puntaje >= umbral" (RN-06).

Uso, con el entorno del backend activado y desde la raíz del repositorio:

    python scripts/calibrar_umbral.py [datos/pares_etiquetados.csv]

El modelo es el de EMBEDDING_MODEL_NAME; la primera ejecución lo descarga.
"""

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_RAIZ / "backend"))

from app.adapters.embeddings.huggingface import HuggingFaceEmbedder  # noqa: E402
from app.config import obtener_configuracion  # noqa: E402
from app.domain.normalizacion import normalizar  # noqa: E402
from app.domain.politica import es_posible_duplicado, recortar_puntaje  # noqa: E402
from app.domain.vectores import normalizar_vector  # noqa: E402

_ARCHIVO_POR_DEFECTO = _RAIZ / "datos" / "pares_etiquetados.csv"
_UMBRALES = [round(0.60 + 0.05 * paso, 2) for paso in range(8)]


@dataclass(frozen=True)
class Par:
    frase_a: str
    frase_b: str
    equivalentes: bool
    tipo: str
    puntaje: float


@dataclass(frozen=True)
class Metricas:
    umbral: float
    precision: float
    exhaustividad: float
    f1: float
    falsos_positivos: int
    falsos_negativos: int


def leer_pares(ruta: Path, embedder: HuggingFaceEmbedder) -> list[Par]:
    pares = []
    with ruta.open(encoding="utf-8", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            vector_a = normalizar_vector(embedder.generar(normalizar(fila["frase_a"])))
            vector_b = normalizar_vector(embedder.generar(normalizar(fila["frase_b"])))
            coseno = sum(x * y for x, y in zip(vector_a, vector_b, strict=True))
            pares.append(
                Par(
                    frase_a=fila["frase_a"],
                    frase_b=fila["frase_b"],
                    equivalentes=fila["equivalentes"] == "1",
                    tipo=fila.get("tipo", ""),
                    puntaje=recortar_puntaje(coseno),
                )
            )
    return pares


def evaluar(pares: list[Par], umbral: float) -> Metricas:
    verdaderos_positivos = falsos_positivos = falsos_negativos = 0
    for par in pares:
        predicho = es_posible_duplicado(par.puntaje, umbral)
        if predicho and par.equivalentes:
            verdaderos_positivos += 1
        elif predicho:
            falsos_positivos += 1
        elif par.equivalentes:
            falsos_negativos += 1
    predichos = verdaderos_positivos + falsos_positivos
    reales = verdaderos_positivos + falsos_negativos
    precision = verdaderos_positivos / predichos if predichos else 1.0
    exhaustividad = verdaderos_positivos / reales if reales else 1.0
    suma = precision + exhaustividad
    f1 = 2 * precision * exhaustividad / suma if suma else 0.0
    return Metricas(umbral, precision, exhaustividad, f1, falsos_positivos, falsos_negativos)


def recomendar(metricas: list[Metricas]) -> Metricas:
    """El de mayor F1; ante empate, el más bajo (D-20).

    Un falso positivo solo le pide a la persona que confirme (RN-12); un falso
    negativo deja entrar un duplicado sin aviso. Por eso se prefiere exhaustividad.
    """
    mejor_f1 = max(metrica.f1 for metrica in metricas)
    return min(
        (metrica for metrica in metricas if metrica.f1 == mejor_f1),
        key=lambda metrica: metrica.umbral,
    )


def main() -> None:
    # La consola de Windows no usa UTF-8 por defecto y rompe los acentos.
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else _ARCHIVO_POR_DEFECTO
    configuracion = obtener_configuracion()
    embedder = HuggingFaceEmbedder(configuracion.nombre_modelo)
    pares = leer_pares(ruta, embedder)

    total_equivalentes = sum(par.equivalentes for par in pares)
    print(f"Modelo: {embedder.nombre_modelo}")
    print(f"Pares: {len(pares)} ({total_equivalentes} equivalentes)\n")

    print("| Puntaje | Esperado | Tipo | Frase A | Frase B |")
    print("|---|---|---|---|---|")
    for par in sorted(pares, key=lambda par: par.puntaje, reverse=True):
        esperado = "sí" if par.equivalentes else "no"
        print(f"| {par.puntaje:.4f} | {esperado} | {par.tipo} | {par.frase_a} | {par.frase_b} |")

    metricas = [evaluar(pares, umbral) for umbral in _UMBRALES]
    print("\n| Umbral | Precisión | Exhaustividad | F1 | Falsos positivos | Falsos negativos |")
    print("|---|---|---|---|---|---|")
    for metrica in metricas:
        print(
            f"| {metrica.umbral:.2f} | {metrica.precision:.3f} | {metrica.exhaustividad:.3f} "
            f"| {metrica.f1:.3f} | {metrica.falsos_positivos} | {metrica.falsos_negativos} |"
        )

    recomendado = recomendar(metricas)
    print(f"\nUmbral recomendado: {recomendado.umbral:.2f} (F1 {recomendado.f1:.3f})")


if __name__ == "__main__":
    main()
