from fastapi import APIRouter

router = APIRouter(tags=["salud"])


# Versión provisional (T-02): el estado real del modelo llega en T-10 y la
# comprobación de la base en T-12b (plan §1.4).
@router.get("/salud")
def consultar_salud() -> dict[str, str | bool]:
    return {"estado": "ok", "modelo_cargado": False, "base_datos": "sin verificar"}
