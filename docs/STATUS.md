# Estado actual

> Este archivo es el punto de entrada de cada sesión nueva. Se actualiza con
> `/handoff` al cerrar cada sesión. Si lo que dice aquí no coincide con el
> repositorio, gana el repositorio y hay que corregir este archivo.

**Última actualización:** 2026-09-22 — sesión 4 (frontend, CI, README y semillas: T-13b a T-18)

---

## Dónde estamos

Fase: **funcionalidad 001 completa. Solo queda T-19 (despliegue), que es
opcional.**

El Definition of Done de la spec (§6) se cumple entero. Los 22 AC tienen un test
que los nombra y pasa. El historial sigue test → feat en cada tarea con AC. El
flujo completo funciona desde la interfaz con `docker compose up`, probado
también en un clon limpio sin `.env`. La revisión final de `code-reviewer` no
encontró nada bloqueante.

Todo en verde al cerrar:

| Comprobación | Resultado |
|---|---|
| `ruff check . && ruff format --check .` | limpio |
| `mypy app tests/dobles` | limpio |
| `pytest -m "not slow and not integration"` | 204 en verde, ~8 s |
| `pytest -m integration` (con `db` levantada) | 14 en verde |
| `npx vitest run` | 23 en verde |
| `npx tsc --noEmit` y `npm run build` | limpio |
| CI en GitHub | verde (run 35765448389, commit `f0af615`) |

## Hecho

- [x] Sesiones 0 a 3: contexto, spec, plan, harness, backend completo y cliente
  de API (T-00 a T-13, CH-01).
- [x] T-13b: tokens de diseño, reinicio y layout. Se añadieron tokens que la
  skill exigía y no tenía (D-23).
- [x] T-14: formulario, alerta, confirmación y máquina de estados de
  `useValidacion` (D-24). 14 tests de Vitest.
- [x] T-15: listado paginado con `useFrases`, estado vacío, carga, error con
  Reintentar y etiqueta de duplicado confirmado. 9 tests de Vitest.
- [x] T-16: `.github/workflows/ci.yml`, verde en GitHub (D-25).
- [x] T-17: README completo, revisado contra el código.
- [x] T-18: `scripts/sembrar_frases.py` (D-26) y revisión final sin
  bloqueantes.

## En curso

Nada. El árbol de trabajo está limpio salvo `.playwright-mcp/` (ver notas).

**Sin subir:** `main` va por delante de `origin` con los commits de T-16 (cierre),
T-17, T-18 y este cierre de sesión. El push necesita el inicio de sesión del
Git Credential Manager: en la sesión 4 se quedó esperando la ventana.

## Siguiente

1. **`fix(api)`: cuerpo que no es UTF-8.** Hoy responde `400` con código
   `ERROR_INTERNO` y el mensaje "Ocurrió un error inesperado". D-22 debería
   haberlo evitado: un JSON mal formado se informa con el campo `cuerpo`. La
   causa está en la propia D-22: "una `HTTPException` con un estado distinto de
   404 o 405 conserva su estado y responde `ERROR_INTERNO`. Hoy la aplicación
   no genera ninguna." Es falso. FastAPI lanza `HTTPException(400)` cuando no
   puede decodificar el cuerpo. Primero va el test que falle, luego la
   corrección en `adapters/api/errores.py`, y hay que actualizar D-22.
   Reproducción:
   `printf '{"texto":"rechaz\xf3"}' > c.json && curl -X POST
   localhost:8080/api/v1/frases/validar -H "Content-Type: application/json"
   --data-binary @c.json`.
2. `T-19` (opcional): despliegue. Depende de Q-02.

## Dudas abiertas

| # | Duda | Quién decide | Estado |
|---|---|---|---|
| Q-01 | Valor definitivo del umbral por defecto | Calibración de T-11 | **cerrada**: 0.75 (D-20) |
| Q-02 | Si se despliega en un servidor público, ¿hace falta autenticación básica en el proxy? | Franklin | abierta, bloquea T-19 |

## Notas para la siguiente sesión

- **Arrancar el entorno.** Docker Desktop no arranca solo en esta máquina. Con
  el motor arriba: `docker compose up -d db`, y la primera vez
  `bash scripts/preparar_base_test.sh`, que es idempotente. Activa
  `backend/.venv` antes de cualquier comando del backend.
- **`docker compose up -d --build frontend` recrea también el backend**, que
  tarda unos segundos en cargar el modelo. Mientras tanto nginx responde 502.
  Para reconstruir solo el frontend: `--no-deps`.
- **El puerto 8000 del host lo ocupa otro proceso** que no es de este proyecto
  (PID 13688 en la sesión 4). Responde incluso a `127.0.0.1`. Para probar el
  backend sin Docker usa `--port 8001` (está en el README).
- **Tests `slow` y scripts sin descargar el modelo:**
  `HF_HOME=C:/t00/hf HF_HUB_OFFLINE=1 pytest -m slow`. Usa la caché de T-00:
  **no borrar `C:\t00\hf`**. Lo mismo vale para `scripts/calibrar_umbral.py` y
  `scripts/sembrar_frases.py`.
- **Git Bash en Windows:**
  - `curl -d '{"texto":"…ó…"}'` envía las tildes sin codificar en UTF-8 y se
    tropieza con el defecto de arriba. Usa un archivo con `--data-binary @`.
  - Reescribe las rutas `/tmp/...` en `docker compose exec`: antepón
    `MSYS_NO_PATHCONV=1`.
- **`rm -rf` está denegado por permisos.** `.playwright-mcp/` (capturas y
  registros de las pruebas en el navegador) sigue en la raíz, sin trackear.
  Bórrala a mano o añádela a `.gitignore`.
- **La base de desarrollo `banco_frases` tiene frases de prueba**: las de las
  sesiones 3 y 4 y las que escribió Franklin. Las semillas se probaron solo
  contra `banco_frases_test` y un clon limpio.
- **Tu `.env` local** no se puede leer desde aquí. Si se copió de
  `.env.example` cuando valía 0.80, seguirá fijando
  `SIMILARITY_THRESHOLD=0.80`: cámbialo a 0.75.
- **mypy:** `mypy tests` entero tiene un único error heredado de T-07 en
  `tests/unit/application/test_validar_frase.py:230` (`Frase | None` sin
  comprobar). Si se arregla, el hook y CI pueden pasar a `mypy app tests`.
- **Warnings de `TestClient`**: `httpx` deprecado y un alias de `anyio`.
  Vienen de Starlette. `httpx` está en el plan §9b.
- Menores pendientes:
  - **Frontend:**
    - Si una página del listado ya cargada falla al cambiar de página, la caja
      de error la sustituye de golpe (D-24).
    - El error del listado usa un mensaje fijo y el del formulario usa el del
      servidor (D-24).
    - Mientras se ve la alerta, el botón Guardar del formulario sigue visible
      y deshabilitado junto a "Guardar de todos modos".
    - `ui-design` no especifica el aviso de "frase única". Se usó
      `--color-acento-suave`.
    - No hay `ErrorBoundary`. El único caso conocido que tumbaba la pantalla,
      una fecha ilegible, ya está protegido.
    - La reserva de alto de la zona de resultado deja un hueco visible en
      reposo. Es intencionado (ui-design), pero es mucho espacio.
  - **CI (D-25):**
    - Las acciones apuntan a Node 20, deprecado: subirlas a la versión mayor
      siguiente.
    - Node 24 no está fijado con `.nvmrc` ni `engines`.
    - `format:check` no corre.
  - **Backend y despliegue:**
    - `documentacion.py` escribe "280 caracteres" a mano en el ejemplo de
      `FRASE_INVALIDA`.
    - `RepositorioPostgres.esta_disponible()` solo atrapa `SQLAlchemyError`.
    - Las imágenes base están fijadas por versión menor, no por digest (NF-07).
    - `RepositorioEnMemoria.sembrar` fija `modelo="modelo-falso"` y
      `umbral_aplicado=0.80`.

---

## Cómo retomar

1. Lee este archivo.
2. Empieza por el `fix(api)` del cuerpo no UTF-8 (sección Siguiente). Después,
   si Q-02 está resuelta, `/implement T-19`.
3. Al terminar la sesión, ejecuta `/handoff`.
