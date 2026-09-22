"""Datos de ejemplo: 10 frases en español para probar la aplicación (T-18).

Cada frase se guarda con el caso de uso `GuardarFrase`, igual que desde la
API: pasa por la validación completa y queda con su embedding y sus metadatos
(RN-13, RN-14). Nunca se confirma un duplicado, así que ejecutar el script dos
veces no duplica nada: la segunda vez todas se omiten como duplicado exacto.

Las frases son distintas entre sí y todas quedan por debajo del umbral por
defecto. Tras sembrar, escribir "El pago fue rechazado por el banco" en la
interfaz muestra la alerta contra "La entidad bancaria rechazó la transacción"
con un 87 % de similitud.

Uso con Docker, con `docker compose up` en marcha y desde la raíz:

    docker compose run --rm -v ./scripts:/srv/scripts -e PYTHONPATH=/srv \
        backend python scripts/sembrar_frases.py

Uso sin Docker, con el entorno del backend activado y desde la raíz:

    python scripts/sembrar_frases.py

Escribe en la base de DATABASE_URL. El modelo es el de EMBEDDING_MODEL_NAME.
"""

import sys
from pathlib import Path

# Sin Docker, el paquete `app` está en backend/. En el contenedor lo aporta
# PYTHONPATH=/srv.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.adapters.embeddings.huggingface import HuggingFaceEmbedder
from app.adapters.persistence.repositorio import RepositorioPostgres
from app.adapters.persistence.sesion import crear_fabrica_sesiones
from app.application.guardar_frase import GuardarFrase
from app.config import obtener_configuracion
from app.domain.errores import ErrorInfraestructura, PosibleDuplicado

FRASES = [
    "La entidad bancaria rechazó la transacción",
    "Tu pedido ya está en camino",
    "La factura se envió a tu correo electrónico",
    "El producto está agotado",
    "Tu contraseña se cambió correctamente",
    "Cliente con pago pendiente",
    "Se aceptan devoluciones hasta 30 días después de la compra",
    "Atención al cliente de lunes a viernes, de 9:00 a 18:00",
    "Tu suscripción se renovará automáticamente el próximo mes",
    "Oferta válida solo para compras en línea",
]


def main() -> int:
    configuracion = obtener_configuracion()
    print(f"Cargando el modelo {configuracion.nombre_modelo}…")
    guardar_frase = GuardarFrase(
        RepositorioPostgres(crear_fabrica_sesiones(configuracion.url_base_datos)),
        HuggingFaceEmbedder(configuracion.nombre_modelo),
        configuracion.umbral_similitud,
        configuracion.longitud_maxima_frase,
    )

    guardadas = 0
    for texto in FRASES:
        try:
            frase = guardar_frase.guardar(texto)
        except PosibleDuplicado as duplicado:
            parecida = duplicado.resultado.mas_parecida
            existente = parecida.texto_original if parecida else "?"
            print(f"  omitida   {texto!r} (se parece a {existente!r})")
        except ErrorInfraestructura as error:
            # Base o modelo no disponibles: no tiene sentido seguir (RN-15).
            print(f"No se pudo sembrar: {error}", file=sys.stderr)
            return 1
        else:
            guardadas += 1
            print(f"  guardada  {texto!r} (id {frase.id})")

    print(f"{guardadas} frases guardadas, {len(FRASES) - guardadas} omitidas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
