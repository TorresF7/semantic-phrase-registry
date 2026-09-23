# Estado actual

> Este archivo es el punto de entrada de cada sesión nueva. Se actualiza con
> `/handoff` al cerrar cada sesión. Si lo que dice aquí no coincide con el
> repositorio, gana el repositorio y hay que corregir este archivo.

**Última actualización:** 2026-09-23 — sesión 10 (auditoría previa a la
entrega, bloque B)

---

## Dónde estamos

Fase: **funcionalidad 001 y bloque G completos (T-00 a T-25, sin T-19). Los
bloques A y B de la auditoría previa a la entrega están aplicados.** Quedan:
- T-19 (despliegue), opcional y pendiente de Q-02;
- implementar T-26 (CH-04, D-41) y T-27 (CH-05, D-42), ya aceptadas.

Todo en verde al cerrar:

| Comprobación | Resultado |
|---|---|
| `ruff check . && ruff format --check .` | limpio |
| `mypy app tests/dobles` | limpio |
| `pytest -m "not slow and not integration"` | 238 en verde |
| `pytest -m integration` (con `db` publicada por `docker-compose.dev.yml`) | 19 en verde |
| `pytest -m slow` (`HF_HOME=C:/t00/hf HF_HUB_OFFLINE=1`) | 4 en verde |
| `npx prettier --check src` | limpio |
| `npx tsc --noEmit` y `npm run build` | limpio |
| `npx vitest run` | 65 en verde |
| `docker compose up -d --build` y repaso en 8080 | bien (ver sesión 10) |
| CI en GitHub | los commits de la sesión 10 aún no están subidos; el trabajo `arquitectura` nuevo no ha corrido nunca en GitHub |

## Hecho

- [x] Sesiones 0 a 6: funcionalidad 001 completa (T-00 a T-18, CH-01),
  rediseño CH-02 (T-20 a T-24, D-29) y propuesta CH-03.
- [x] Sesiones 7 y 8: AC-02b (cuerpo no UTF-8), D-30, CH-03 aplicada (D-31) y
  T-25.
- [x] Sesión 9, auditoría bloque A: U+0000 da `422` (D-32), Swagger bajo
  `/api/v1` (D-34), `LOG_LEVEL`, `docker-compose.dev.yml` (D-35), aviso de
  longitud sobre el normalizado (D-33), tests del cliente y de HTTP contra
  PostgreSQL, y README al día.
- [x] **Sesión 10, auditoría bloque B**, un commit por punto, cada uno con su
  test en rojo antes del código:
  1. **`fix(registro)`, D-36.** Mientras carga, el botón usa `aria-disabled`
     en lugar de `disabled` y conserva el foco. Al llegar el veredicto, el
     foco va a «Guardar frase» (única) o a «Editar frase» (duplicado o 409).
     Lo mismo para «Guardar de todos modos».
  2. **`fix(listado)`, D-37.** Estado nuevo `cambiando`: al paginar, la
     página anterior sigue atenuada (`--opacidad-cambiando`) y con
     `aria-busy`, y la paginación no se desmonta. Sus botones usan
     `aria-disabled`, también en los extremos.
  3. **`fix(api-cliente)`, D-38.** `AbortSignal.timeout` con
     `VITE_API_TIMEOUT_MS` (15000 por defecto). Agotado el tiempo, el
     cliente devuelve `SIN_CONEXION`, también si se agota mientras llega el
     cuerpo.
  4. **`fix(nginx)`, D-39.** `client_max_body_size 16k` y `413` en JSON con
     el código nuevo `CUERPO_DEMASIADO_GRANDE`: en el catálogo del plan §1.5,
     en OpenAPI y con un test que compara `nginx.conf` con la documentación.
  5. **`fix(nginx)`, D-40.** `server_tokens off`, `X-Content-Type-Options`,
     `Referrer-Policy`, `X-Frame-Options` y CSP por ruta con `map`: estricta
     en la app, con jsDelivr y `'unsafe-inline'` solo en `/api/v1/docs`.
  6. **`fix(veredicto)`.** Cabecera y texto de error según la operación que
     falló: el estado `error` guarda `operacion`.
  7. **`docs(glosario)`.** Excepción de «umbral» en el medidor (D-27).
  8. **`ci`.** `npm run format:check` y trabajo `arquitectura` con los `grep`
     del hook. Cierra el menor de D-25 sobre `format:check`.
  9. **`docs(cambios)`.** CH-04 (caracteres `Cf`) y CH-05 (lockfile del
     backend) como **propuestas**, revisadas con `spec-reviewer` y con sus
     hallazgos aplicados. Sin implementar.
  - **Repaso en 8080** tras `docker compose up -d --build`:
    - cabeceras presentes en `/`, en la API y en el 413, y `Server: nginx`
      sin versión;
    - un cuerpo de 20 KB da `413 application/json`;
    - la app y Swagger cargan sin violaciones de CSP en la consola;
    - flujo completo con el foco en Chrome real: «Comprobando…» → «Guardar
      frase» → «Guardando…» → campo;
    - «Siguientes» deja 20 filas atenuadas con el foco y sin mover el scroll;
    - con el backend parado, el veredicto dice «No se pudo comparar la
      frase» y «El servicio no responde. Reintenta en unos segundos.».

## En curso

**Sesión 11, abierta.** CH-04 (alternativa (a), D-41) y CH-05 (alternativa
(a), D-42) están aceptadas y aplicadas a la documentación, con sus tareas T-26
y T-27. El código de ninguna de las dos se ha tocado todavía. Este archivo se reescribe entero con
`/handoff` al cerrar la sesión 11.

**Sin subir:** según la referencia local, `main` va 11 commits por delante de
`origin/main`, contando este cierre.

**Compose:** el último `docker compose up -d --build` se hizo sin
`docker-compose.dev.yml`, así que `db` no publica el 5432. Para los tests de
integración desde el host, levántala otra vez con el `-f` (ver «Cómo
retomar»).

## Siguiente

1. Implementar **T-26** (CH-04) y después **T-27** (CH-05), bloque H.
2. Subir a GitHub y comprobar que CI pasa, sobre todo el trabajo nuevo
   `arquitectura` y el paso `prettier`.
3. Medir los tokens de ancho de columna con las fuentes de macOS y Android
   (D-31, costo aceptado).
4. `T-19` (opcional): despliegue. Depende de Q-02.

## Dudas abiertas

| # | Duda | Quién decide | Estado |
|---|---|---|---|
| Q-01 | Valor definitivo del umbral por defecto | Calibración de T-11 | **cerrada**: 0.75 (D-20) |
| Q-02 | Si se despliega en un servidor público, ¿hace falta autenticación básica en el proxy? | Franklin | abierta, bloquea T-19 |
| Q-03 | Resumen de la tabla "26 frases": ¿solo la cifra en mono, como el prototipo? Hoy va entero en mono; cambiarlo obliga a otra consulta en el test que busca "26 frases" | Franklin | abierta, menor |
| Q-04 | Micro-medidor sin marca de umbral | Franklin | **cerrada**: sin marca, color por estado (D-27, skill) |
| Q-05 | Duraciones de animación sin token | Franklin | **cerrada**: tokens de movimiento (D-28) |
| Q-06 | CH-03: (a), (b), (a)+(b) o no hacer nada | Franklin | **cerrada**: (a)+(b), 900 px (D-31) |
| Q-07 | ¿Se rechazan los cuerpos JSON que no están en UTF-8? | Franklin | **cerrada**: UTF-8, se toleran UTF-16/32 (D-30) |
| Q-08 | Aviso de longitud: ¿con el campo vacío? ¿Sobre crudo o normalizado? | Franklin | **cerrada**: solo con texto; normalizado (D-33) |
| Q-09 | Caracteres invisibles (`Cf`) y lockfile del backend | Franklin | **cerrada**: CH-04 (a) (D-41, T-26) y CH-05 (a) (D-42, T-27) |
| Q-10 | CH-04: ¿medir con el modelo real cuánto cambia el puntaje de un emoji con U+200D antes de decidir? ¿Se acepta que el normalizado guardado no se recalcule nunca (B-29)? | Franklin | **cerrada**: no se mide; se acepta B-29 (D-41) |
| Q-11 | CH-05: ¿fijar `torch==2.14.0+cpu` en `pyproject.toml` desde el principio, o solo si la restricción falla? | Franklin | **cerrada**: solo si falla en la construcción limpia (D-42) |

## Notas para la siguiente sesión

- **Arrancar el entorno.** Docker Desktop no arranca solo en esta máquina. Con
  el motor arriba:
  `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db`, y
  la primera vez
  `bash scripts/preparar_base_test.sh`, que es idempotente. Activa
  `backend/.venv` antes de cualquier comando del backend.
- **`localhost` falla con `curl` en esta máquina** (resuelve a IPv6 y el
  puerto 8080 no responde ahí). Usa `http://127.0.0.1:8080`.
- **Con el backend parado, nginx tarda unos segundos en dar el 502** (no
  resuelve `backend`). El veredicto de error llega tarde, pero llega.
- **Heredocs en la herramienta Bash:** `\\` dentro de un heredoc con comillas
  llega como `\`, así que un `\uXXXX` en un script de Python rompe con
  `unicodeescape`. En los scripts que editan archivos, usa `chr(92)` para la
  barra invertida.
- **Fin de línea:** varios archivos del árbol de trabajo están en CRLF
  (`* text=auto`). Los scripts de edición deben leer con `newline=''` y
  conservar el fin de línea que encuentren; si no, el `assert` de búsqueda
  falla con `\r\n`.
- **jsdom no quita el foco a un botón que se deshabilita.** Por eso un test
  de foco que parte del propio botón pasa aunque en Chrome se pierda. Los
  tests de D-36 parten del campo con Ctrl+Enter o comprueban `aria-disabled`.
- **Un `add_header` en cualquier `location` de `nginx.conf`** anula todas las
  cabeceras de seguridad de `server` en esa ruta (D-40).
- **El mensaje del 413 está en `nginx.conf` y en `documentacion.py`.**
  `test_el_413_documentado_es_el_que_devuelve_nginx` los compara.
- **Probar la interfaz contra el backend real sin Docker** (lo que se hizo en
  T-21 a T-23): en `backend/`,
  `HF_HOME=C:/t00/hf HF_HUB_OFFLINE=1 uvicorn app.main:app --port 8001`; en
  `frontend/`, `VITE_API_URL=http://localhost:8001/api/v1 npx vite --port 5173`.
  El puerto 8000 del host lo ocupa otro proceso ajeno al proyecto.
- **`docker compose up -d --build frontend` recrea también el backend**, que
  tarda en cargar el modelo; mientras, nginx responde 502. Para reconstruir
  solo el frontend: `docker compose build frontend && docker compose up -d
  --no-deps frontend`.
- **Tests `slow` y scripts sin descargar el modelo:**
  `HF_HOME=C:/t00/hf HF_HUB_OFFLINE=1 pytest -m slow`. **No borrar
  `C:\t00\hf`**.
- **Testing Library y textos partidos:** `getByText` solo mira los nodos de
  texto directos de un elemento. Un texto repartido en varios nodos
  (`<span>26</span> frases`) no se encuentra con una cadena; y un texto que
  aparece como celda y como enlace de otra fila exige `{ selector: "td" }`.
- **Los comandos rechazados pueden haberse ejecutado.** Tras un rechazo,
  revisa `git diff` antes de repetir.
- **Git Bash en Windows:** `curl -d` con tildes no envía UTF-8 (usa
  `--data-binary @archivo`); antepón `MSYS_NO_PATHCONV=1` en
  `docker compose exec` con rutas `/tmp/...`.
- **`rm -rf` está denegado por permisos.** `.playwright-mcp/` sigue sin
  trackear. Bórrala a mano o añádela a `.gitignore`.
- **Navegador:** en la sesión 10 se usó Chrome DevTools MCP con
  `isolatedContext`. Playwright MCP puede quedar bloqueado («Browser is
  already in use»).
- **Python en Git Bash lee `stdin` como cp1252.** Un script que recibe texto
  con tildes por un heredoc debe leer `sys.stdin.buffer` y decodificar
  UTF-8.
- **Probar B-27 con `curl`:** el cuerpo debe llevar el escape JSON literal
  `\u0000` (seis caracteres), no un NUL.
- **Procesos huérfanos de Vite y uvicorn.** Antes de arrancar,
  `netstat -ano | grep :5173` y, si hace falta, `taskkill //PID <pid> //F`.
  `CORS_ORIGINS` solo admite `localhost:5173`.
- **`calc()` con porcentaje en columnas de tabla** se trata como `auto` en
  Chromium, también en `<col>` (D-31).
- **La base de desarrollo `banco_frases` tiene 21 frases de prueba.** La 21.ª
  es «Las oficinas cierran a las seis de la tarde los viernes», guardada en la
  sesión 10 para que apareciera la paginación.
- **Tu `.env` local** puede seguir con `SIMILARITY_THRESHOLD=0.80` si se copió
  de un `.env.example` antiguo: cámbialo a 0.75. `.env.example` tiene ahora
  `VITE_API_TIMEOUT_MS`.
- **mypy:** `mypy tests` entero tiene un único error heredado de T-07 en
  `tests/unit/application/test_validar_frase.py:230`.
- Menores pendientes:
  - **Frontend:**
    - No hay `ErrorBoundary`.
    - `favicon.ico` responde 404 (solo ruido en la consola).
    - Los tests de T-24 llevan prefijo `ac16`/`ac19`/`ac20` aunque prueban el
      DoD de T-24.
    - La normalización del cliente (D-28) es una aproximación.
    - Un `413` mostraría «Reintentar», que no sirve de nada. No se puede
      provocar desde la interfaz: el máximo son 280 caracteres.
  - **CI (D-25):** acciones sobre Node 20 (deprecado) y Node 24 sin fijar en
    `.nvmrc`/`engines`.
  - **Backend y despliegue:**
    - La spec no tiene fila B-nn para «cuerpo no UTF-8 o anidamiento
      excesivo» (lo cubre AC-02b).
    - El 502 de nginx mientras carga el modelo sigue siendo HTML. El cliente
      lo trata como `RESPUESTA_INESPERADA`.
    - Sin nginx, uvicorn no tiene límite de tamaño del cuerpo (T-19).
    - `documentacion.py` escribe «280 caracteres» a mano en el ejemplo de
      `FRASE_INVALIDA`.
    - `RepositorioPostgres.esta_disponible()` solo atrapa `ErrorRepositorio`.
    - Con `"a\u0000"` gana el mensaje de caracteres no permitidos sobre el de
      longitud mínima.
    - `ItemListado.desde_frase` descarta `mas_parecida` si falta el texto
      (inalcanzable).
    - Imágenes base fijadas por versión menor, no por digest (NF-07; CH-05
      trata las dependencias de Python, no las imágenes).
    - `RepositorioEnMemoria.sembrar` fija `modelo="modelo-falso"` y
      `umbral_aplicado=0.80`.
    - La suite avisa de dos deprecaciones de `starlette` y `anyio` (ver
      CH-05).

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
