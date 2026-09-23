# Estado actual

> Este archivo es el punto de entrada de cada sesión nueva. Se actualiza con
> `/handoff` al cerrar cada sesión. Si lo que dice aquí no coincide con el
> repositorio, gana el repositorio y hay que corregir este archivo.

**Última actualización:** 2026-09-23 — sesión 9 (auditoría previa a la entrega)

---

## Dónde estamos

Fase: **funcionalidad 001 y bloque G completos (T-00 a T-25, sin T-19), con la
auditoría previa a la entrega aplicada.** Queda T-19 (despliegue), opcional y
pendiente de Q-02, y dos temas que necesitan propuesta (Q-09).

Todo en verde al cerrar:

| Comprobación | Resultado |
|---|---|
| `ruff check . && ruff format --check .` | limpio |
| `mypy app tests/dobles` | limpio |
| `pytest -m "not slow and not integration"` | 236 en verde |
| `pytest -m integration` (con `db` publicada por `docker-compose.dev.yml`) | 19 en verde |
| `pytest -m slow` (`HF_HOME=C:/t00/hf HF_HUB_OFFLINE=1`) | 4 en verde |
| `npx prettier --check src` | limpio |
| `npx tsc --noEmit` y `npm run build` | limpio |
| `npx vitest run` | 50 en verde |
| `docker compose up -d --build` y repaso en 8080 | bien (ver sesión 9) |
| CI en GitHub | en verde hasta el cierre de la sesión 6; los commits posteriores a `e5e24fc` aún no están subidos |

## Hecho

- [x] Sesiones 0 a 6: funcionalidad 001 completa (T-00 a T-18, CH-01),
  rediseño CH-02 (T-20 a T-24, D-29) y propuesta CH-03.
- [x] Sesión 7: un cuerpo que no es JSON UTF-8 legible responde
  `422 PARAMETROS_INVALIDOS` (AC-02b; D-22 corregida).
- [x] Sesión 8: D-30 (JSON UTF-8, se toleran UTF-16/32), CH-03 aplicada
  (D-31) y T-25 (punto de corte en 900 px y columnas estables; la lista de
  verificación de `ui-design` pasa entera).
- [x] Sesión 9, auditoría previa a la entrega, un commit por punto:
  1. **`fix(api)`:** un texto con U+0000 respondía `503`. El dominio rechaza
     ahora todo carácter de control `Cc` que no sea espacio con
     `422 FRASE_INVALIDA` (RN-01, B-27, D-32), y el repositorio ya no traduce
     `DataError` a base caída.
  2. **`fix(api)`:** Swagger en `/api/v1/docs` y OpenAPI en
     `/api/v1/openapi.json`, accesibles tras nginx; ReDoc desactivado (D-34).
  3. **`fix(config)`:** `LOG_LEVEL` se aplica al registro raíz en el arranque.
  4. **`fix(compose)`:** `docker-compose.override.yml` pasa a
     `docker-compose.dev.yml` y solo se aplica con `-f` (NF-07, D-35).
  5. **`feat(registro)`:** aviso en `#pie-frase` con los textos del servidor
     cuando el normalizado tiene menos de 3 o más de 280 caracteres; contador
     y máximo miden el normalizado (D-33, skill `ui-design`).
  6. **`test`:** `cliente.test.ts` (409, forma inválida, HTML, red caída) y
     `tests/integration/test_api_postgres.py` (flujo completo por HTTP contra
     PostgreSQL con el embedder falso). Pasaron desde el primer momento porque
     cubren código existente; con mutaciones se comprobó que detectan
     regresiones.
  7. **`docs`:** README con la interfaz actual, el 502 durante la carga del
     modelo, Swagger y dos capturas en `docs/capturas/`; `product.md`,
     `architecture.md`, `docs/README.md` (25 AC, 27 casos borde, 28 tareas) y
     plan §1 (ejemplos con 0.75).
  - Además: arreglo de E501 en el docstring de `tests/integration/conftest.py`,
    y la fila de `FRASE_INVALIDA` del catálogo de errores del plan (menor de
    `code-reviewer`, que no encontró bloqueantes).
  - Repaso en 8080 tras `docker compose up -d --build`: 502 unos segundos
    mientras carga el modelo; luego `salud` 200, `/api/v1/docs` y
    `/api/v1/openapi.json` 200, `/api/v1/redoc` 404, `\u0000` → 422
    `FRASE_INVALIDA`, aviso del pie visible en rojo, y el flujo «Comprobar
    similitud» → 85 % → «Guardar de todos modos» completo. `db` ya no publica
    el 5432.
  - D-29 no se tocó: no afirma pruebas con lector de pantalla real, y así lo
    decidió el propietario.

## En curso

Nada. El árbol está limpio salvo `.playwright-mcp/` (ver notas).

**Sin subir:** `main` va 10 commits por delante de `origin`, contando este
cierre.

**Compose:** el último `docker compose up -d --build` se hizo sin
`docker-compose.dev.yml`, así que `db` no publica el 5432. Para los tests de
integración desde el host, levántala otra vez con el `-f` (ver «Cómo
retomar»).

## Siguiente

1. Decidir Q-09: si se escriben las propuestas de caracteres invisibles y de
   lockfile del backend (ver notas).
2. Medir los tokens de ancho de columna con las fuentes de macOS y Android
   (D-31, costo aceptado): llevan margen sobre Segoe UI, pero no se han
   comprobado con otras fuentes del sistema.
3. `T-19` (opcional): despliegue. Depende de Q-02.

## Dudas abiertas

| # | Duda | Quién decide | Estado |
|---|---|---|---|
| Q-01 | Valor definitivo del umbral por defecto | Calibración de T-11 | **cerrada**: 0.75 (D-20) |
| Q-02 | Si se despliega en un servidor público, ¿hace falta autenticación básica en el proxy? | Franklin | abierta, bloquea T-19 |
| Q-03 | Resumen de la tabla "26 frases": ¿solo la cifra en mono, como el prototipo? Hoy va entero en mono; cambiarlo obliga a otra consulta en el test que busca "26 frases" | Franklin | abierta, menor |
| Q-04 | Micro-medidor sin marca de umbral | Franklin | **cerrada**: sin marca, color por estado (D-27, skill) |
| Q-05 | Duraciones de animación sin token | Franklin | **cerrada**: tokens de movimiento (D-28) |
| Q-06 | CH-03: (a), (b), (a)+(b) o no hacer nada; con (a), cómo se reparten Frase y Más parecida | Franklin | **cerrada**: (a)+(b), 900 px, Frase con el espacio restante (D-31) |
| Q-07 | ¿Se rechazan los cuerpos JSON que no están en UTF-8 (UTF-16/32 hoy dan `200`)? | Franklin | **cerrada**: se exige UTF-8 y se toleran UTF-16/32 (D-30, plan §1) |
| Q-08 | Aviso de longitud: ¿también con el campo vacío? ¿Contador sobre crudo o normalizado? | Franklin | **cerrada**: solo con texto escrito; todo sobre el normalizado (D-33) |
| Q-09 | ¿Propuestas para caracteres invisibles (`Cf`) y para un lockfile del backend? | Franklin | abierta |

## Notas para la siguiente sesión

- **Arrancar el entorno.** Docker Desktop no arranca solo en esta máquina. Con
  el motor arriba:
  `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db`, y
  la primera vez
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
  consola de las pruebas en el navegador) sigue sin trackear. Bórrala a mano
  o añádela a `.gitignore`.
- **Playwright MCP puede quedar bloqueado** («Browser is already in use»)
  por una instancia anterior. Las capturas de la sesión 9 se hicieron con
  Chrome DevTools MCP y `isolatedContext`, a 1080 × 760.
- **Python en Git Bash lee `stdin` como cp1252.** Un script que recibe texto
  con tildes por un heredoc debe leer `sys.stdin.buffer` y decodificar
  UTF-8; si no, escribe mojibake. Y un `\\u0000` dentro de un heredoc
  pasado a Python puede acabar como un byte NUL real en el archivo: revisa
  con `grep -a` antes de dar por bueno un test con caracteres de control.
- **Probar B-27 con `curl`:** el cuerpo debe llevar el escape JSON literal
  `\u0000` (seis caracteres), no un NUL; si no, responde
  `422 PARAMETROS_INVALIDOS` por JSON inválido, no `FRASE_INVALIDA`.
- **Medir el salto del esqueleto** (T-24, T-25): con Playwright, retener
  `GET /frases?…` con `page.route` hasta leer los anchos de `thead th` y
  soltarla después; así se comparan esqueleto y datos en el mismo ancho.
- **Procesos huérfanos de Vite y uvicorn.** Un Vite lanzado en segundo plano
  puede sobrevivir a su tarea y seguir ocupando el 5173 con un
  `VITE_API_URL` viejo: la lista falla sin error en la consola. Antes de
  arrancar, `netstat -ano | grep :5173` y, si hace falta,
  `taskkill //PID <pid> //F`. `CORS_ORIGINS` solo admite `localhost:5173`,
  así que otro puerto no sirve contra el backend.
- **`calc()` con porcentaje en columnas de tabla** se trata como `auto` en
  Chromium, también en `<col>` (D-31). Para repartir, usa anchos fijos y deja
  una columna sin ancho.
- **La base de desarrollo `banco_frases` tiene frases de prueba**, incluida
  "La reunión de mañana se pospone al jueves", guardada al probar T-22.
- **Tu `.env` local** puede seguir con `SIMILARITY_THRESHOLD=0.80` si se copió
  de un `.env.example` antiguo: cámbialo a 0.75.
- **mypy:** `mypy tests` entero tiene un único error heredado de T-07 en
  `tests/unit/application/test_validar_frase.py:230`.
- **Necesitan propuesta en `docs/changes/`** (el propietario las dejó fuera
  de la auditoría de la sesión 9; Q-09):
  - **Caracteres invisibles.** D-32 rechaza los de control (`Cc`), pero los de
    formato (`Cf`: U+200B de ancho cero, U+200D, U+FEFF…) se aceptan y se
    guardan. Dos frases que solo difieren en uno de ellos no son duplicado
    exacto, aunque el embedding casi no cambie. Decidir si se eliminan al
    normalizar (cambia RN-02) o se rechazan (cambia RN-01).
  - **Lockfile del backend.** `pyproject.toml` fija con `==` las
    dependencias directas, pero no las transitivas (`torch`, `transformers`,
    `starlette`…), y no hay lockfile: dos `docker compose up --build` en días
    distintos pueden instalar versiones distintas (NF-07). El frontend sí
    tiene `package-lock.json`. Elegir herramienta (`pip-tools`, `uv`) es una
    dependencia nueva fuera del plan §9b.
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
    - `RepositorioPostgres.esta_disponible()` solo atrapa `ErrorRepositorio`:
      desde D-32, un `DataError` en `SELECT 1` se propagaría en lugar de dar
      `False`. Inalcanzable con una consulta fija (menor de `code-reviewer`).
    - Con un texto que incumple a la vez el mínimo y B-27 (`"a\u0000"`),
      gana el mensaje de caracteres no permitidos: la comprobación de `Cc` va
      antes que la de longitud. La spec no fija prioridad; ambos son `422`.
    - `ItemListado.desde_frase` descarta `mas_parecida` si falta el texto; es
      inalcanzable (no hay borrado) pero `mypy` necesita la comprobación.
    - Imágenes base fijadas por versión menor, no por digest (NF-07).
    - `RepositorioEnMemoria.sembrar` fija `modelo="modelo-falso"` y
      `umbral_aplicado=0.80`.

---

## Cómo retomar

1. Lee este archivo.
2. Si cambió el código desde la última reconstrucción:
   `docker compose up -d --build`. Mientras el backend carga el modelo, nginx
   responde 502.
3. Para los tests de integración:
   `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db`.
4. Sigue con «Siguiente».
5. Al terminar la sesión, ejecuta `/handoff`.
