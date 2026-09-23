# Estado actual

> Este archivo es el punto de entrada de cada sesión nueva. Se actualiza con
> `/handoff` al cerrar cada sesión. Si lo que dice aquí no coincide con el
> repositorio, gana el repositorio y hay que corregir este archivo.

**Última actualización:** 2026-09-23 — sesión 11 (CH-04 y CH-05 decididas e
implementadas: T-26 y T-27)

---

## Dónde estamos

Fase: **funcionalidad 001, bloque G y bloque H completos (T-00 a T-27, sin
T-19). Auditoría previa a la entrega cerrada.** Solo queda T-19 (despliegue),
opcional y pendiente de Q-02.

Todo en verde al cerrar:

| Comprobación | Resultado |
|---|---|
| `ruff check . && ruff format --check .` | limpio |
| `mypy app tests/dobles` | limpio |
| `pytest -m "not slow and not integration"` | 247 en verde |
| `pytest -m integration` (con `db` publicada por `docker-compose.dev.yml`) | 19 en verde |
| `pytest -m slow` (`HF_HOME=C:/t00/hf HF_HUB_OFFLINE=1`) | 4 en verde |
| `npx prettier --check src` | limpio |
| `npx tsc --noEmit` y `npm run build` | limpio |
| `npx vitest run` | 66 en verde |
| `docker compose up -d --build` y repaso en 8080 | bien (ver sesión 11) |
| CI en GitHub | los commits de las sesiones 10 y 11 aún no están subidos; los trabajos `arquitectura` y `prettier`, y la instalación con `-c requirements.lock`, no han corrido nunca en GitHub |

## Hecho

- [x] Sesiones 0 a 6: funcionalidad 001 completa (T-00 a T-18, CH-01),
  rediseño CH-02 (T-20 a T-24, D-29) y propuesta CH-03.
- [x] Sesiones 7 y 8: AC-02b (cuerpo no UTF-8), D-30, CH-03 aplicada (D-31) y
  T-25.
- [x] Sesión 9, auditoría bloque A: U+0000 da `422` (D-32), Swagger bajo
  `/api/v1` (D-34), `LOG_LEVEL`, `docker-compose.dev.yml` (D-35), aviso de
  longitud sobre el normalizado (D-33), tests del cliente y de HTTP contra
  PostgreSQL, y README al día.
- [x] Sesión 10, auditoría bloque B: foco al comprobar (D-36), paginación sin
  esqueleto (D-37), tiempo límite del cliente (D-38), 413 en JSON (D-39),
  cabeceras de seguridad y CSP (D-40), textos de error por operación,
  glosario, CI con `format:check` y `arquitectura`, y las propuestas CH-04 y
  CH-05.
- [x] **Sesión 11:**
  - **Decisiones del propietario:** CH-04 (a) y CH-05 (a), que cierran Q-09,
    Q-10 y Q-11. Aplicadas a la documentación, una propuesta por commit y
    las dos revisadas con `spec-reviewer`: RN-02, AC-01, AC-03, B-05, B-28,
    B-29, plan §4, §9 y §9b, glosario, README, D-41, D-42 y el bloque H nuevo
    con T-26 y T-27. `spec-reviewer` también encontró que el plan §9 decía
    `--extra-index-url` para `torch`; se corrigió.
  - **T-26 (CH-04, D-41):** `normalizar` elimina los caracteres `Cf` tras NFKC
    y antes de colapsar; el contador del cliente hace lo mismo con
    `\p{Cf}`. 10 tests en rojo primero (`c1b923c`) y la implementación
    después (`904f468`). La consulta de B-29 da 0 de 21 frases con `Cf`.
    `code-reviewer` y `security-review` no encontraron bloqueantes.
  - **T-27 (CH-05, D-42, D-43):** `backend/requirements.lock`, generado por
    `scripts/congelar_dependencias.sh`, se usa con `-c` en el Dockerfile, en
    los trabajos `backend` e `integracion` de CI y en el README. Desviación
    **D-43**, decidida por el propietario: `torch` no va al lockfile, porque
    en Windows se publica sin `+cpu` y rompía la instalación local.
    `code-reviewer` encontró un bloqueante, ya corregido: el script ya no
    confía en una tubería bajo `dash`. Verificación, en la nota de T-27 en
    `tasks.md`:
    - dos construcciones sin caché con el mismo `pip freeze`;
    - `torch==2.14.0+cpu` sin CUDA;
    - 455 MB, igual que antes;
    - una versión bajada a mano en el lockfile se respeta;
    - el `.venv` local, alineado: tenía 7 paquetes desviados.
  - **Repaso en 8080** tras `docker compose up -d --build`:
    - salud 200;
    - tres U+200B dan `422 FRASE_INVALIDA` con el mensaje de longitud mínima;
    - «El pago fue rechazado por el banco» más U+FEFF da `EXACTO` 1.0;
    - las cabeceras de seguridad siguen;
    - el contador de Chrome marca 0 con tres U+200B y 3 con `abc` más U+FEFF,
      sin errores en la consola.

## En curso

Nada. El árbol está limpio salvo `.playwright-mcp/` (ver notas).

**Sin subir:** según la referencia local, `main` va 17 commits por delante de
`origin/main`, contando este cierre.

**Compose:** el último `docker compose up -d --build` se hizo sin
`docker-compose.dev.yml`, así que `db` no publica el 5432. Para los tests de
integración desde el host, levántala otra vez con el `-f` (ver «Cómo
retomar»).

## Siguiente

1. Subir a GitHub y comprobar que CI pasa: sobre todo los trabajos
   `arquitectura` y `prettier`, y la instalación con `-c requirements.lock`
   en los dos trabajos de backend.
2. Medir los tokens de ancho de columna con las fuentes de macOS y Android
   (D-31, costo aceptado).
3. `T-19` (opcional): despliegue. Depende de Q-02.

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

- **Memoria.** Claude Code corta los comandos en segundo plano cuando el
  sistema va justo de memoria (le pasó a la primera generación del lockfile).
  Antes de construir la imagen del backend o de ejecutar
  `scripts/congelar_dependencias.sh`, para el backend de Compose
  (`docker compose stop backend`), que tiene el modelo cargado. Si el comando
  queda en segundo plano y lo cortan, el contenedor de `docker run` puede
  seguir vivo: búscalo con `docker ps` y detenlo.
- **Construir sin caché tarda.** La imagen del backend tarda unos 4 minutos;
  a veces `download-r2.pytorch.org` corta la descarga (`Read timed out`) y
  basta con reintentar.
- **Regenerar el lockfile:** `bash scripts/congelar_dependencias.sh`, con
  Docker arriba. Tarda unos minutos y nunca se edita a mano (D-42). La línea
  de `torch` no va en él (D-43).
- **El `.venv` local es Python 3.13 en Windows**, no 3.11 como la imagen y
  CI. Con `-c requirements.lock` queda alineado con la imagen salvo `torch`
  (2.14.0 sin `+cpu`) y `uvloop` (no existe en Windows).
- **Versión de Unicode:** Node 24 trae Unicode 17.0 y Python 3.11 la 15.1.0.
  Un carácter reclasificado dentro o fuera de `Cf` entre esas versiones haría
  discrepar el contador del cliente y el servidor. Es el riesgo que acepta
  D-28, y manda el servidor.
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
- **La base de desarrollo `banco_frases` tiene 21 frases de prueba**, ninguna
  con `Cf`. La 21.ª es «Las oficinas cierran a las seis de la tarde los
  viernes», guardada en la sesión 10 para que apareciera la paginación.
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
    - No hay un test explícito de que el texto original conserva los `Cf` al
      guardar (B-28). Hoy lo garantiza la estructura: `texto_original` no se
      transforma en ningún punto (menor de `code-reviewer`, T-26).
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
    - La suite avisa de una deprecación de `anyio`
      (`anyio.abc.BlockingPortal`). La de `httpx` desapareció con
      `starlette` 1.7.0, la versión fijada en el lockfile.

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
