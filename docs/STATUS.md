# Estado actual

> Este archivo es el punto de entrada de cada sesión nueva. Se actualiza con
> `/handoff` al cerrar cada sesión. Si lo que dice aquí no coincide con el
> repositorio, gana el repositorio y hay que corregir este archivo.

**Última actualización:** 2026-09-22 — sesión 5 (rediseño CH-02: T-20 a T-23)

---

## Dónde estamos

Fase: **rediseño CH-02 implementado salvo la revisión final (T-24).**

La funcionalidad 001 seguía completa al empezar. En esta sesión se aplicó
CH-02: el listado trae la frase más parecida (T-20) y la interfaz pasa a la v2
de la skill `ui-design`, con registro en línea y tabla (T-21 a T-23). Cada tarea
con AC siguió test → feat y pasó por `code-reviewer` sin bloqueantes; T-22 y
T-23 pasaron además `security-review` sin hallazgos. El flujo completo se probó
en el navegador contra el backend real a 1080, 390 y 360 px.

Todo en verde al cerrar:

| Comprobación | Resultado |
|---|---|
| `ruff check . && ruff format --check .` | limpio |
| `mypy app tests/dobles` | limpio |
| `pytest -m "not slow and not integration"` | 206 en verde, ~3 s |
| `pytest -m integration` (con `db` levantada) | 16 en verde |
| `npx prettier --check src` | limpio |
| `npx tsc --noEmit` y `npm run build` | limpio |
| `npx vitest run` | 35 en verde |
| CI en GitHub | no ejecutado: los commits de esta sesión no están subidos |

## Hecho

- [x] Sesiones 0 a 4: funcionalidad 001 completa (T-00 a T-18, CH-01) y
  propuesta CH-02 aplicada a la spec.
- [x] T-20: `FraseListada` y `mas_parecida` en `GET /frases`, con `LEFT JOIN`;
  el número de sentencias no depende de las filas (AC-19).
- [x] T-21: tokens v2, `base.css` y `botones.css` migrados, barra superior.
- [x] T-22: registro en línea, `Veredicto` (sustituye a `AlertaDuplicado`),
  estado `conflicto` para el `409`, Editar frase (AC-16, AC-16b, AC-21). Con
  un `fix` posterior: el mínimo de 3 caracteres se mide sobre el texto
  normalizado (D-28).
- [x] T-23: tabla de cinco columnas, esqueleto, vacío, error, paginación
  condicional, fichas bajo 720 px (AC-19, AC-20). Alias temporales eliminados;
  tokens de movimiento `--duracion-spinner` y `--duracion-brillo`.
- [x] Decisiones: D-24 generalizada, D-27 precisada (micro-medidor sin marca de
  umbral), D-28 nueva. Skill `ui-design` actualizada en esos dos puntos.

## En curso

Nada. El árbol está limpio salvo `.playwright-mcp/` (ver notas).

**Sin subir:** `main` va 13 commits por delante de `origin` (desde la
propuesta CH-02). El push necesita el inicio de sesión del Git Credential
Manager.

## Siguiente

1. `/implement T-24`: revisión visual y accesibilidad del bloque G. Además de
   su lista, llevar allí:
   - **`aria-live`**: el veredicto lo tiene en el contenedor con `role="alert"`
     o `role="status"` dentro (posibles anuncios dobles; la solución prevista
     está en `tasks.md`), y la lista **no** lo tiene, aunque la skill lo exige.
     Resolver ambos juntos: el error de la lista ya usa `role="alert"`.
   - **Fichas móviles**: `display: block` en `table`/`tr`/`td` puede hacer que
     algunos lectores de pantalla dejen de exponer filas y celdas; añadir
     `role="row"`/`"cell"`.
2. `fix(api)`: cuerpo que no es UTF-8. Responde `400 ERROR_INTERNO` en vez de
   informar el campo `cuerpo`; D-22 afirma algo falso ("hoy la aplicación no
   genera ninguna" `HTTPException` distinta de 404/405: FastAPI lanza
   `HTTPException(400)` al no poder decodificar). Test primero, corrección en
   `adapters/api/errores.py` y actualizar D-22. Reproducción:
   `printf '{"texto":"rechaz\xf3"}' > c.json && curl -X POST
   localhost:8080/api/v1/frases/validar -H "Content-Type: application/json"
   --data-binary @c.json`.
3. `T-19` (opcional): despliegue. Depende de Q-02.

## Dudas abiertas

| # | Duda | Quién decide | Estado |
|---|---|---|---|
| Q-01 | Valor definitivo del umbral por defecto | Calibración de T-11 | **cerrada**: 0.75 (D-20) |
| Q-02 | Si se despliega en un servidor público, ¿hace falta autenticación básica en el proxy? | Franklin | abierta, bloquea T-19 |
| Q-03 | Resumen de la tabla "26 frases": ¿solo la cifra en mono, como el prototipo? Hoy va entero en mono; cambiarlo obliga a otra consulta en el test que busca "26 frases" | Franklin | abierta, menor |
| Q-04 | Micro-medidor sin marca de umbral | Franklin | **cerrada**: sin marca, color por estado (D-27, skill) |
| Q-05 | Duraciones de animación sin token | Franklin | **cerrada**: tokens de movimiento (D-28) |

## Notas para la siguiente sesión

- **Arrancar el entorno.** Docker Desktop no arranca solo en esta máquina. Con
  el motor arriba: `docker compose up -d db`, y la primera vez
  `bash scripts/preparar_base_test.sh`, que es idempotente. Activa
  `backend/.venv` antes de cualquier comando del backend.
- **Probar la interfaz contra el backend real sin Docker** (lo que se hizo en
  T-21 a T-23): en `backend/`,
  `HF_HOME=C:/t00/hf HF_HUB_OFFLINE=1 uvicorn app.main:app --port 8001`; en
  `frontend/`, `VITE_API_URL=http://localhost:8001/api/v1 npx vite --port 5173`.
  El puerto 8000 del host lo ocupa otro proceso ajeno al proyecto.
- **`docker compose up -d --build frontend` recrea también el backend**, que
  tarda en cargar el modelo; mientras, nginx responde 502. Para reconstruir
  solo el frontend: `--no-deps`.
- **Tests `slow` y scripts sin descargar el modelo:**
  `HF_HOME=C:/t00/hf HF_HUB_OFFLINE=1 pytest -m slow`. **No borrar
  `C:\t00\hf`**.
- **Testing Library y textos partidos:** `getByText` solo mira los nodos de
  texto directos de un elemento. Un texto repartido en varios nodos
  (`<span>26</span> frases`) no se encuentra con una cadena; y un texto que
  aparece como celda y como enlace de otra fila exige `{ selector: "td" }`.
- **Los comandos rechazados pueden haberse ejecutado.** En esta sesión, un
  script que el propietario rechazó ya había aplicado sus cambios; el `Edit`
  siguiente los duplicó. Tras un rechazo, revisa `git diff` antes de repetir.
- **Git Bash en Windows:** `curl -d` con tildes no envía UTF-8 (usa
  `--data-binary @archivo`); antepón `MSYS_NO_PATHCONV=1` en
  `docker compose exec` con rutas `/tmp/...`.
- **`rm -rf` está denegado por permisos.** `.playwright-mcp/` (capturas de las
  pruebas en el navegador, incluidas las de esta sesión) sigue sin trackear.
  Bórrala a mano o añádela a `.gitignore`.
- **La base de desarrollo `banco_frases` tiene frases de prueba**, incluida
  "La reunión de mañana se pospone al jueves", guardada al probar T-22.
- **Tu `.env` local** puede seguir con `SIMILARITY_THRESHOLD=0.80` si se copió
  de un `.env.example` antiguo: cámbialo a 0.75.
- **mypy:** `mypy tests` entero tiene un único error heredado de T-07 en
  `tests/unit/application/test_validar_frase.py:230`.
- Menores pendientes:
  - **Frontend:**
    - No hay `ErrorBoundary`.
    - La normalización del cliente (D-28) es una aproximación: en casos raros
      de NFKC puede habilitar el botón y el servidor responder `422`.
  - **CI (D-25):** acciones sobre Node 20 (deprecado), Node 24 sin fijar en
    `.nvmrc`/`engines`, y `format:check` no corre.
  - **Backend y despliegue:**
    - `documentacion.py` escribe "280 caracteres" a mano en el ejemplo de
      `FRASE_INVALIDA`.
    - `RepositorioPostgres.esta_disponible()` solo atrapa `SQLAlchemyError`.
    - `ItemListado.desde_frase` descarta `mas_parecida` si falta el texto; es
      inalcanzable (no hay borrado) pero `mypy` necesita la comprobación.
    - Imágenes base fijadas por versión menor, no por digest (NF-07).
    - `RepositorioEnMemoria.sembrar` fija `modelo="modelo-falso"` y
      `umbral_aplicado=0.80`.

---

## Cómo retomar

1. Lee este archivo.
2. `/implement T-24`, con los dos puntos de accesibilidad de "Siguiente".
3. Después, el `fix(api)` del cuerpo no UTF-8.
4. Al terminar la sesión, ejecuta `/handoff`.
