# Estado actual

> Este archivo es el punto de entrada de cada sesión nueva. Se actualiza con
> `/handoff` al cerrar cada sesión. Si lo que dice aquí no coincide con el
> repositorio, gana el repositorio y hay que corregir este archivo.

**Última actualización:** 2026-09-22 — sesión 3 (bloques C y D completos, T-09 a T-13)

---

## Dónde estamos

Fase: **backend terminado y probado; empieza el frontend.**

La API completa funciona sobre PostgreSQL real con el modelo real:
`POST /frases/validar`, `POST /frases`, `GET /frases` y `GET /salud`, con
errores uniformes y ejemplos en `/docs`. Los 20 AC del backend tienen un test
que los nombra y pasa. Del frontend existe el cliente de API tipado (T-13);
faltan los estilos, los hooks y los componentes.

Todo en verde al cerrar:

| Comprobación | Resultado |
|---|---|
| `ruff check . && ruff format --check .` | limpio |
| `mypy app tests/dobles` | limpio |
| `pytest -m "not slow and not integration"` | 204 en verde, ~4 s |
| `pytest -m integration` (con `db` levantada) | 14 en verde |
| `pytest -m slow` (modelo real, ver notas) | 4 en verde |
| `npx tsc --noEmit` y `npm run build` en `frontend/` | limpio |

## Hecho

- [x] Sesiones 0 a 2: contexto, spec, plan, harness, T-00 a T-08.
- [x] T-09: repositorio PostgreSQL con pgvector y `scripts/preparar_base_test.sh`.
  El desempate del vecino se resuelve sobre los 5 candidatos de HNSW (D-19).
- [x] T-10: `HuggingFaceEmbedder` y carga del modelo en el `lifespan`: si falla,
  arranque degradado (B-09); si la dimensión no cuadra, el arranque falla (B-14).
- [x] T-11: calibración con 32 pares. Umbral por defecto **0.75** (D-20, cierra
  Q-01). D-20 documenta los límites del modelo.
- [x] T-12a: validar y guardar por HTTP, errores uniformes y CORS. La revisión
  encontró que el duplicado exacto daba 503 con el modelo sin cargar, en contra
  de RN-15; se corrigió con D-21.
- [x] T-12b: listado paginado, `/salud` completo y ejemplos en OpenAPI.
  `security-review` detectó un `desplazamiento` sin tope que daba un 503 falso;
  se corrigió.
- [x] T-13: `api/tipos.ts` y `api/cliente.ts`, con guardas de tipo en tiempo de
  ejecución. El 409 llega como `DatosDuplicado` (sin `modelo`).
- [x] CH-01 aceptada y aplicada: AC-18 y B-09 precisan los tres desenlaces del
  duplicado exacto con el modelo sin cargar (200 al validar, 409 al guardar sin
  confirmar, 503 al confirmar).

## En curso

Nada. El árbol de trabajo está limpio.

## Siguiente

`T-13b` — tokens de diseño y estilos base. Después `T-14`, que es donde viven
los únicos tests de AC-16 y AC-16b: son obligatorios y no se sacrifican.

## Dudas abiertas

| # | Duda | Quién decide | Estado |
|---|---|---|---|
| Q-01 | Valor definitivo del umbral por defecto | Calibración de T-11 | **cerrada**: 0.75 (D-20) |
| Q-02 | Si se despliega en un servidor público, ¿hace falta autenticación básica en el proxy? | Franklin | abierta |

## Notas para la siguiente sesión

- **Arrancar el entorno.** Docker Desktop no arranca solo en esta máquina. Con
  el motor arriba: `docker compose up -d db`, y la primera vez
  `bash scripts/preparar_base_test.sh`, que es idempotente. Activa
  `backend/.venv` antes de cualquier comando del backend.
- **Tests `slow` sin descargar el modelo:**
  `HF_HOME=C:/t00/hf HF_HUB_OFFLINE=1 pytest -m slow`. Usa la caché de T-00:
  **no borrar `C:\t00\hf`**. Lo mismo vale para `scripts/calibrar_umbral.py`.
- **Tu `.env` local** no se puede leer desde aquí. Si se copió de
  `.env.example` cuando valía 0.80, seguirá fijando
  `SIMILARITY_THRESHOLD=0.80`: cámbialo a 0.75.
- **Frontend:**
  - Los componentes usan `api/cliente.ts` y nunca `fetch`.
  - El estado `posible_duplicado` se tipa con `DatosDuplicado`, no con
    `ResultadoValidacion` (plan §5).
  - `ErrorApi.estado_http` es `null` cuando no hubo conexión (`SIN_CONEXION`).
  - `npm run test` sigue saliendo con código 1 mientras no haya tests del
    frontend (llegan en T-14).
- **mypy:**
  - Desde D-19, mypy no analiza los stubs de numpy. `mypy tests` entero casi
    funciona: queda un único error en
    `tests/unit/application/test_validar_frase.py:230` (`Frase | None` sin
    comprobar), heredado de T-07. Si se arregla, el hook y CI (T-16) pueden
    pasar a `mypy app tests`.
  - El hook de cierre solo ejecuta `mypy app`.
- **Warnings de `TestClient`.** Aparecen dos: `httpx` deprecado en favor de
  `httpx2` y un alias de `anyio`. Vienen de Starlette, no del proyecto. No se
  cambió nada porque `httpx` está en el plan §9b; revisarlo si Starlette deja
  de admitirlo.
- **Prueba de humo con Compose.** Desde T-10, `docker compose up` carga el
  modelo al arrancar el backend (lo descarga la primera vez en el volumen
  `cache_modelo`). Todavía no se ha probado la pila completa en Compose; la
  prueba de humo se hizo con `TestClient` contra `banco_frases_test`.
- Pendientes menores:
  - `documentacion.py` escribe "280 caracteres" a mano en el ejemplo de
    `FRASE_INVALIDA`. Si cambia `MAX_PHRASE_LENGTH`, el ejemplo de `/docs` se
    queda atrás.
  - `RepositorioPostgres.esta_disponible()` solo atrapa `SQLAlchemyError`. Una
    excepción de otro tipo al abrir la sesión haría responder 500 a `/salud` en
    vez de 503. Es improbable (T-09).
  - Las imágenes base están fijadas por versión menor, no por digest (NF-07).
  - `RepositorioEnMemoria.sembrar` fija `modelo="modelo-falso"` y
    `umbral_aplicado=0.80`. Si un test llega a comprobar metadatos de una frase
    sembrada, que los fije de forma explícita.
  - La tabla de calibración para el README (T-17) está en D-20.
- Puntajes de T-00 y de la calibración: tabla completa en D-20. El par
  estrella da **0.8735**, que en el README aparece como 87 %.

---

## Cómo retomar

1. Lee este archivo.
2. Lee `docs/specs/001-validacion-semantica/tasks.md` y busca la primera tarea
   sin marcar.
3. Ejecuta `/implement T-XX` con esa tarea.
4. Al terminar la sesión, ejecuta `/handoff`.
