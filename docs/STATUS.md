# Estado actual

> Este archivo es el punto de entrada de cada sesión nueva. Se actualiza con
> `/handoff` al cerrar cada sesión. Si lo que dice aquí no coincide con el
> repositorio, gana el repositorio y hay que corregir este archivo.

**Última actualización:** 2026-09-23 — sesión 7 (fix del cuerpo no UTF-8)

---

## Dónde estamos

Fase: **bloque G (CH-02) cerrado; CH-03 propuesta y pendiente de decisión.**

Sesión 7: corregido el `400 ERROR_INTERNO` de un cuerpo que no es JSON UTF-8
legible, que ahora responde `422 PARAMETROS_INVALIDOS` (ver «Hecho»). La tabla
de T-24 que sigue es de la sesión 6 y no ha cambiado.

T-24 está cerrada, pero **su lista de verificación no pasa entera**: el
propietario decidió cerrarla así y dejar el punto que falla documentado.

| Punto de la lista de `ui-design` | Resultado |
|---|---|
| `grep` de colores, `px`, `999px`/`box-shadow`/fuentes web | pasa |
| Contraste AA en todo texto visible | pasa (mínimo medido 5.01:1) |
| Recorrido con Tab, foco visible | pasa (contorno de 2 px en todo elemento enfocable) |
| 390 y 360 px sin desplazamiento horizontal, tabla en fichas | pasa |
| 1080 px con cinco columnas sin truncar | pasa |
| **Nada salta al aparecer el veredicto ni al pasar del esqueleto a los datos** | **NO pasa.** El veredicto no desplaza nada, pero al pasar del esqueleto a los datos las columnas se mueven entre **15 y 50 px a 1080 px**, y a **721 px la columna Frase se queda en 62 px**. El fallo es anterior a T-24. Propuesta: CH-03 |
| 8 estados del registro y 4 de la lista frente al prototipo | pasa (reales y con respuestas simuladas por `page.route`) |

Todo en verde al cerrar:

| Comprobación | Resultado |
|---|---|
| `ruff check . && ruff format --check .` | limpio |
| `mypy app tests/dobles` | limpio |
| `pytest -m "not slow and not integration"` | 210 en verde (4 nuevos del fix) |
| `pytest -m integration` (con `db` levantada) | 16 en verde |
| `npx prettier --check src` | limpio |
| `npx tsc --noEmit` y `npm run build` | limpio |
| `npx vitest run` | 39 en verde (4 nuevos de T-24) |
| CI en GitHub | en verde hasta el cierre de la sesión 6; los 2 commits del fix y este cierre aún no están subidos |

## Hecho

- [x] Sesiones 0 a 5: funcionalidad 001 completa (T-00 a T-18, CH-01) y
  rediseño CH-02 (T-20 a T-23).
- [x] T-24: el contenedor del veredicto ya no lleva `aria-live` (antes se
  anidaba con `alert`/`status`). La lista gana una región viva de cortesía
  siempre montada. La tabla y el esqueleto declaran roles explícitos, que
  conservan la semántica en fichas (comprobado en el árbol de accesibilidad
  de Chromium a 360 px). Se precisó la skill `ui-design`. `code-reviewer` no
  dejó bloqueantes y sus menores se aplicaron o están en «Notas». D-29.
- [x] CH-03 redactada con las alternativas (a) `table-layout: fixed` con
  tres tokens de ancho y (b) punto de corte en ~900 px. Pasó por
  `spec-reviewer`: se corrigieron los dos bloqueantes (regla
  `.colFrase { width: 40% }` y relación con T-24) y los importantes. **No se
  ha implementado nada de CH-03.**
- [x] `fix(api)` (sesión 7): un cuerpo con bytes que no son UTF-8, o con un
  anidamiento que agota la recursión, respondía `400 ERROR_INTERNO`. FastAPI
  solo traduce a `422` el `JSONDecodeError`; el resto lo lanza como
  `HTTPException(400)`. Ahora responde `422 PARAMETROS_INVALIDOS` con
  `{"cuerpo": "El cuerpo no es JSON válido."}`, igual que un JSON mal formado
  (AC-02b). Se reprodujo contra Compose antes de corregir. D-22 corregida.
  `code-reviewer` y `security-review` sin bloqueantes. El OpenAPI no cambia:
  ya documentaba el `422`.

## En curso

Nada. El árbol está limpio salvo `.playwright-mcp/` (ver notas).

**Sin subir:** `main` va 3 commits por delante de `origin`, contando este
cierre (test y fix del cuerpo no UTF-8).

**El contenedor `backend` de Compose sigue con la imagen anterior al fix.**
Para verlo corregido en el puerto 8080:
`docker compose up -d --build --no-deps backend`.

## Siguiente

1. **Decidir CH-03** (`docs/changes/CH-03-columnas-estables-tabla.md`): (a),
   (b), (a)+(b) o no hacer nada. Si se acepta, se crea T-25 como indica la
   propuesta y se aplica con el flujo de `docs/changes/README.md`.
2. **Decidir si se aceptan cuerpos en UTF-16/UTF-32.** Hoy un JSON en UTF-16
   con BOM responde `200`, porque `json.loads` detecta la codificación. El
   plan §1 dice «todo el cuerpo es JSON UTF-8». No es un riesgo de
   seguridad: el texto se decodifica bien y pasa por NFKC. Pero es una
   desviación del contrato. Si se corrige, va por `docs/changes/` o como
   `fix` con test primero; hay que decidirlo antes. Se reproduce con:
   `printf '{"texto":"hola mundo"}' | iconv -f utf-8 -t utf-16 > u16.json`
   y `curl -X POST localhost:8080/api/v1/frases/validar
   -H "Content-Type: application/json" --data-binary @u16.json`.
3. `T-19` (opcional): despliegue. Depende de Q-02.

## Dudas abiertas

| # | Duda | Quién decide | Estado |
|---|---|---|---|
| Q-01 | Valor definitivo del umbral por defecto | Calibración de T-11 | **cerrada**: 0.75 (D-20) |
| Q-02 | Si se despliega en un servidor público, ¿hace falta autenticación básica en el proxy? | Franklin | abierta, bloquea T-19 |
| Q-03 | Resumen de la tabla "26 frases": ¿solo la cifra en mono, como el prototipo? Hoy va entero en mono; cambiarlo obliga a otra consulta en el test que busca "26 frases" | Franklin | abierta, menor |
| Q-04 | Micro-medidor sin marca de umbral | Franklin | **cerrada**: sin marca, color por estado (D-27, skill) |
| Q-05 | Duraciones de animación sin token | Franklin | **cerrada**: tokens de movimiento (D-28) |
| Q-06 | CH-03: (a), (b), (a)+(b) o no hacer nada; con (a), cómo se reparten Frase y Más parecida | Franklin | abierta |
| Q-07 | ¿Se rechazan los cuerpos JSON que no están en UTF-8 (UTF-16/32 hoy dan `200`)? | Franklin | abierta, menor |

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
- **`rm -rf` está denegado por permisos.** `.playwright-mcp/` (registros de
  consola de las pruebas en el navegador, incluidas las de esta sesión) sigue
  sin trackear. Bórrala a mano o añádela a `.gitignore`.
- **Medir el salto del esqueleto** (T-24, CH-03): con Playwright, retener
  `GET /frases?…` con `page.route` hasta leer los anchos de `thead th` y
  soltarla después; así se comparan esqueleto y datos en el mismo ancho.
- **La base de desarrollo `banco_frases` tiene frases de prueba**, incluida
  "La reunión de mañana se pospone al jueves", guardada al probar T-22.
- **Tu `.env` local** puede seguir con `SIMILARITY_THRESHOLD=0.80` si se copió
  de un `.env.example` antiguo: cámbialo a 0.75.
- **mypy:** `mypy tests` entero tiene un único error heredado de T-07 en
  `tests/unit/application/test_validar_frase.py:230`.
- Menores pendientes:
  - **Frontend:**
    - No hay `ErrorBoundary`.
    - `favicon.ico` responde 404 en desarrollo (solo ruido en la consola; la
      skill prohíbe logos, así que no se añade sin decidirlo).
    - Los tests de T-24 llevan prefijo `ac16`/`ac19`/`ac20`, pero lo que
      prueban (roles, regiones vivas) sale del DoD de T-24, no del texto
      literal de esos AC (hallazgo menor de `code-reviewer`).
    - La normalización del cliente (D-28) es una aproximación: en casos raros
      de NFKC puede habilitar el botón y el servidor responder `422`.
  - **CI (D-25):** acciones sobre Node 20 (deprecado), Node 24 sin fijar en
    `.nvmrc`/`engines`, y `format:check` no corre.
  - **Backend y despliegue:**
    - La tabla de casos borde de la spec no tiene una fila B-nn para «cuerpo
      no UTF-8 o anidamiento excesivo»: lo cubre la redacción general de
      AC-02b. Añadirla exige una propuesta en `docs/changes/` (menor de
      `code-reviewer`).
    - Sin despliegue, no hay tope de tamaño del cuerpo si uvicorn se expone
      directamente; tras nginx rige el límite por defecto de 1 MB (T-19).
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
2. Decidir CH-03 (Q-06).
3. Decidir Q-07 (cuerpos en UTF-16/32).
4. Al terminar la sesión, ejecuta `/handoff`.
