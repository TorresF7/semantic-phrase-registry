# Tareas 001 — Validación semántica de frases

Una tarea = un commit (o dos: `test:` y luego `feat:`). Si una tarea necesita
más, estaba mal dividida.

Marca `[x]` solo cuando se cumpla el Definition of Done de la tarea. La marca
va en el mismo commit que cierra la tarea.

Las tareas que no cubren ningún AC (andamiaje, Docker, migración, CI, README)
no pasan por el ciclo test-primero; su commit es `chore`, `ci` o `docs`.

**Leyenda de tamaño:** S ≈ 20 min · M ≈ 45 min · L ≈ 90 min

---

## Bloque A — Base (lunes)

### [x] T-00 · Comprobación del modelo con frases reales · S
Antes de escribir nada: un script desechable (no se commitea) que carga
`paraphrase-multilingual-MiniLM-L12-v2` y mide el coseno de seis pares en
español, empezando por el par estrella de `product.md` ("El pago fue rechazado
por el banco" / "La entidad bancaria rechazó la transacción"), dos paráfrasis
más, dos pares sin relación y una negación.
**DoD:** los seis puntajes anotados en `STATUS.md`. Si el par estrella no
supera 0.80, se cambia el ejemplo de `product.md`, AC-04 y el README por uno
que sí lo haga, **antes** de T-01. Si el modelo tarda en descargar, se deja
descargando mientras se hace T-01.
*No depende de nada.*

### [x] T-01 · Andamiaje del repositorio · M
Crear la estructura de carpetas del backend y del frontend, `pyproject.toml`
con ruff, mypy y los marcadores `slow` e `integration` de pytest, `.gitignore`,
`.gitattributes` con `*.sh text eol=lf` (en Windows `autocrlf` convertiría los
hooks a CRLF y `bash` no los ejecutaría), `.env.example` con todas las
variables de `architecture.md`, `frontend/package.json`
con las dependencias de desarrollo del plan §9b (incluido `prettier`), y
`README.md` inicial con solo el título y la estructura.
Incluye el esqueleto mínimo de Vite (`tsconfig.json` estricto, `vite.config.ts`
con Vitest en jsdom, `index.html`, `main.tsx` y un `App.tsx` que solo pinta el
título): T-02 necesita `npm run build` y T-13b da por hecho `main.tsx`.
**DoD:** `ruff check .` pasa sobre un proyecto vacío; `pytest` no falla con la
carpeta de tests vacía; `.env` está ignorado.
*Depende de T-00.*

### [x] T-02 · Docker Compose funcional · M
`docker-compose.yml` con `db` (pgvector/pgvector:pg16, healthcheck, sin puerto
publicado), `backend` y `frontend` con nginx haciendo proxy de `/api`.
`docker-compose.override.yml` para desarrollo que publica 5432. Dockerfiles
multietapa con usuario sin privilegios, `HF_HOME` y el directorio del caché con
el dueño correcto. `torch` desde el índice de CPU.
Incluye un `app/main.py` mínimo con `GET /api/v1/salud` que responde
`{"estado": "ok", "modelo_cargado": false, "base_datos": "sin verificar"}`. El
modelo y la comprobación de la base llegan en T-10 y T-12b.
**DoD:** `docker compose up --build` levanta los tres servicios;
`curl localhost:8080/api/v1/salud` responde a través de nginx.
*Depende de T-01.*

### [x] T-03 · Configuración por entorno · S
`app/config.py` con `pydantic-settings`. Todas las variables de
`architecture.md`, con sus valores por defecto y validación de rango para el
umbral (entre 0 y 1 inclusive).
**Tests:** existe un valor por defecto para el umbral y está dentro de [0, 1];
un umbral de 1.5 y uno de -0.1 hacen fallar la construcción. **No** se afirma
el valor concreto 0.80: cambia en T-11.
**DoD:** los tests pasan.
*Depende de T-01.*

### [x] T-04 · Migración inicial con pgvector · M
Alembic configurado con el tipo `Vector` del paquete `pgvector`. Primera y
única migración: extensión `vector`, tipo enum, tabla `frases`, los tres índices
del plan §2 (incluido HNSW). El `downgrade` elimina el tipo enum. El servicio
`backend` de Compose pasa a ejecutar `alembic upgrade head` antes de `uvicorn`.
**DoD:** `alembic upgrade head`, `alembic downgrade base` y de nuevo
`alembic upgrade head` funcionan en secuencia sobre una base limpia.
*Depende de T-02, T-03.*

---

## Bloque B — Dominio y casos de uso (lunes noche / martes mañana)

### [x] T-05 · Dominio: normalización, vectores y política · S
`domain/normalizacion.py`, `domain/vectores.py`, `domain/politica.py`,
`domain/errores.py`. Entidades `Frase` y `FraseNueva`, objeto de valor
`ResultadoValidacion`.
**Tests primero:** `test_ac01_*`, `test_ac02_*` (longitud sobre el texto
normalizado), normalización de RN-02 con tabulaciones y saltos de línea (B-17),
comparación `>=` del umbral (B-08), puntaje sin redondear (B-16), recorte a
[0, 1] (B-15), `normalizar_vector` y norma cero.
**DoD:** funciones puras, sin importar nada de `adapters` ni de `config`.
*Depende de T-01.*

### [x] T-06 · Puertos y dobles de prueba · S
`ports/embeddings.py`, `ports/repositorio.py` con `Protocol`. `FakeEmbedder`
determinista (puede devolver vectores sin normalizar a propósito, para AC-17) y
`RepositorioEnMemoria` con los mismos desempates que el SQL.
**DoD:** el embedder falso produce el mismo vector para el mismo texto y permite
fijar puntajes concretos entre pares de frases. `mypy` acepta los dobles como
implementaciones de los puertos.
*Depende de T-05.*

### [x] T-07 · Caso de uso ValidarFrase · L
Implementa los 5 pasos del plan §4.
**Tests primero:** `test_ac03_*` (incluye verificar que el embedder **no** fue
llamado y el desempate del exacto de AC-06), `test_ac04_*`, `test_ac05_*`,
`test_ac06_*`, `test_ac07_*`, `test_ac08_*`, `test_ac17_*` (el embedder falso
devuelve norma 5; lo que se compara tiene norma 1).
**DoD:** los tests pasan con el embedder falso, sin base de datos y en menos de
un segundo. Cubre AC-03 a AC-08 y AC-17.
*Depende de T-06.*

### [x] T-08 · Caso de uso GuardarFrase · M
Revalidación completa, decisión sobre `confirmar_duplicado`, generación del
embedding cuando el resultado no lo trae, construcción de metadatos.
**Tests primero:** `test_ac09_*`, `test_ac10_*`, `test_ac11_*`,
`test_ac11b_*` (exacto confirmado: se genera y persiste el embedding; si el
proveedor falla, no se guarda), `test_ac12_*` (los metadatos de `FraseNueva`
que llegan al repositorio: puntaje, id de la más parecida, estado, modelo,
umbral; la cláusula del vector en la base se prueba en T-09), `test_ac12b_*`.
**DoD:** los tests pasan. `test_ac12b` es el que demuestra RN-11. Cubre AC-09 a
AC-12b.
*Depende de T-07.*

---

## Bloque C — Adaptadores (martes)

### [x] T-09 · Repositorio PostgreSQL con pgvector · L
Modelos SQLAlchemy y el repositorio concreto, síncrono, con `psycopg` 3. Las
tres consultas del plan §2. Traducción de errores de conexión a
`ErrorRepositorio`. `esta_disponible()`.
**Tests de integración** (marcador `integration`, base `banco_frases_test`):
`test_ac12_*` (la fila guardada contiene el vector del embedding y todos los
metadatos, leídos con SQL directo porque `Frase` no transporta el vector),
vecino más cercano correcto, desempate por `id` en el semántico y en el exacto
(B-18), paginación con fechas iguales (AC-15, última cláusula),
`esta_disponible()` en verde.
**DoD:** los tests de integración pasan con `docker compose up -d db`.
`EXPLAIN` sobre la consulta del vecino muestra el índice HNSW; si no, aplicar
la alternativa del plan §2 y anotarlo en `decisions.md`.
*Depende de T-04, T-06.*

### [x] T-10 · Adaptador de Hugging Face · M
`HuggingFaceEmbedder` sobre `SentenceTransformer`, con import perezoso. Carga
en el `lifespan` a través de la fábrica sustituible, guardado en `app.state`;
si la carga falla, el proceso arranca degradado (B-09). Comprobación de
dimensión (B-14). Traducción de excepciones a `ErrorProveedorEmbeddings`.
Llama a `encode` con `normalize_embeddings=True`.
**Tests:** uno marcado `slow` que carga el modelo real y comprueba que dos
paráfrasis en español superan 0.80 y dos frases sin relación no llegan a 0.50
(los umbrales van en el test, no salen de la configuración). Uno rápido que
simula el fallo del proveedor y comprueba la traducción de la excepción. Uno
rápido que comprueba que el arranque con fábrica que falla deja
`app.state.embedder` en `None`.
**DoD:** `pytest -m "not slow and not integration"` sigue corriendo en segundos
y sin `torch` importado.
*Depende de T-06.*

### [x] T-11 · Calibración del umbral · M
`scripts/calibrar_umbral.py` y `datos/pares_etiquetados.csv` con al menos 20
pares en español, incluyendo negaciones y los seis pares de T-00.
**DoD:** el script imprime la tabla de precisión/exhaustividad/F1 por umbral y
recomienda uno. El valor recomendado se fija como valor por defecto en
`config.py`, en la tabla de `architecture.md` y en el ejemplo de RN-06, y se
registra en `decisions.md` (cierra Q-01). Ningún test cambia: todos inyectan su
umbral.
*Depende de T-03. Solo necesita el modelo descargado; se puede hacer en cuanto
haya tiempo muerto.*

---

## Bloque D — API (martes tarde)

### [x] T-12a · Capa HTTP: errores, validar y guardar · L
`adapters/api/errores.py` con el manejador global y la sustitución de los tres
manejadores por defecto de FastAPI (plan §1.5). `adapters/api/dependencias.py`.
Schemas Pydantic de entrada (con el tope defensivo, no con 280) y de salida.
Routers de `POST /frases/validar` y `POST /frases`. CORS desde `CORS_ORIGINS`.
**Tests (`tests/api/`):** `test_ac01_*`, `test_ac02_*`, `test_ac02b_*`,
`test_ac13_*` (503 del proveedor; exacto sigue en 200), `test_ac14_*` (forma
uniforme en 404, 405, 409, 422, 500, 503), y el guardado extremo a extremo con
`TestClient` y la fábrica de embedder sustituida.
**DoD:** los tests pasan. Ningún cuerpo de error tiene la forma `{"detail": ...}`.
*Depende de T-08, T-09, T-10.*

### [ ] T-12b · Capa HTTP: listado, salud y OpenAPI · M
Router de `GET /frases` con validación de `limite` y `desplazamiento`.
`GET /salud` completo: estado del modelo y `esta_disponible()` de la base.
Ejemplos en `/docs` para cada endpoint y cada código de error.
**Tests:** `test_ac15_*` (incluida la página vacía y los 422 de rango),
`test_ac18_*` (degradado sin modelo, listado en 200 con modelo caído, 503
`BASE_DATOS_NO_DISPONIBLE` con repositorio que lanza `ErrorRepositorio`).
**DoD:** los 20 AC del backend tienen al menos un test que los nombra y pasa.
`/docs` muestra ejemplos en cada endpoint.
*Depende de T-12a.*

---

## Bloque E — Frontend (miércoles mañana)

### [ ] T-13 · Cliente de API tipado · S
`api/tipos.ts` espejo del contrato (incluido `modelo`) y `api/cliente.ts` que
traduce las respuestas de error de la API a un tipo discriminado y el `409` a
un resultado de validación.
**DoD:** `tsc --noEmit` en modo estricto sin errores. Los campos que pueden ser
nulos están tipados como tales.
*Depende de T-12b.*

### [ ] T-13b · Tokens de diseño y estilos base · S
`src/estilos/tokens.css` con los tokens de la skill `ui-design`, importado en
`main.tsx`. Reinicio de estilos mínimo y layout de una columna.
**DoD:** los tokens están definidos y ningún otro archivo CSS contiene un valor
de color o espaciado escrito a mano.
*Depende de T-01. Se puede hacer en paralelo al backend.*

### [ ] T-14 · Formulario con validación y alerta · L
`FormularioFrase`, `AlertaDuplicado`, `useValidacion` con la máquina de estados
y la tabla de transiciones del plan §5. Incluye el manejo del `409` al guardar,
la caducidad del resultado al editar, Cancelar conservando el texto, y la
confirmación de guardado con sus dos variantes. Sigue `ui-design`.
**Tests (Vitest):** `ac16: ...` para las dos confirmaciones y el campo vacío;
`ac16b: ...` para la caducidad al editar y para Cancelar; transición a
`posible_duplicado` al validar; el `409` del guardado vuelve a mostrar la
alerta.
**DoD:** el flujo completo funciona contra el backend real. El botón Guardar
está deshabilitado sin validación previa. Cubre AC-16 y AC-16b.
*Depende de T-13, T-13b.*

### [ ] T-15 · Listado y estados de la interfaz · M
`ListaFrases` con paginación por botones, `useFrases`, `EstadoVacio`,
indicadores de carga y de error con reintento. Distintivo con texto para las
frases en estado `DUPLICADO_CONFIRMADO`. Tras guardar, vuelve a la primera
página (AC-16).
**DoD:** con la base vacía se ve el estado vacío, no una lista en blanco. Los
textos siguen el glosario: nada de jerga técnica. La lista de verificación final
de `ui-design` pasa completa.
*Depende de T-14.*

---

## Bloque F — Cierre (miércoles tarde)

### [ ] T-16 · Integración continua · S
GitHub Actions: `ruff`, `mypy`, `pytest -m "not slow and not integration"` sin
servicios, `pytest -m integration` con un servicio `pgvector/pgvector:pg16`,
`tsc --noEmit`, `vitest run` y `npm run build`. `torch` desde el índice de CPU
también aquí, o el trabajo tarda diez minutos solo instalando.
**DoD:** el workflow pasa en verde en GitHub.
*Depende de T-12b, T-15.*

### [ ] T-17 · README completo · M
Instalación, ejecución con Docker y sin Docker, tabla de variables de entorno
(con la advertencia de B-13 junto a `EMBEDDING_MODEL_NAME`), diagrama Mermaid,
resumen de decisiones con enlace a `decisions.md`, ejemplo `curl` con las dos
frases de T-00 y su puntaje real, y la tabla de calibración del umbral si T-11
se hizo; si no, una nota de que el umbral es el valor inicial y Q-01 sigue
abierta.
**DoD:** una persona que no conoce el proyecto lo levanta siguiendo solo el
README.
*Depende de T-16. Usa T-11 si está hecha.*

### [ ] T-18 · Semillas y revisión final · M
Script de datos de ejemplo con 10 frases en español que demuestran el caso de
uso, insertadas a través del caso de uso `GuardarFrase` para que lleven
embedding y metadatos. Ejecutar el subagente `code-reviewer` sobre todo el
diff. Verificar el Definition of Done de la spec.
**DoD:** sin hallazgos bloqueantes. `docker compose up` en una máquina limpia
deja todo funcionando.
*Depende de T-17.*

### [ ] T-19 · Despliegue (opcional) · M
Solo si sobra tiempo. Proxy con HTTPS automático, límite de peticiones y
cabeceras de seguridad en el proxy (D-11), `.env` de producción en el servidor,
únicamente los puertos 80 y 443 expuestos.
**DoD:** la URL responde y el flujo completo funciona desde internet.
*Depende de T-18. Si el tiempo aprieta, se descarta sin afectar la entrega.*

---

## Ruta crítica

```
T-00 → T-01 → T-02 → T-04 ─────────────┐
         ├──→ T-03 ──→ T-11 ───────────┼──────────────────────────→ T-17
         ├──→ T-13b ───────────────────┼─────────────┐              ↑
         └──→ T-05 → T-06 → T-07 → T-08 → T-12a → T-12b → T-13 → T-14 → T-15 → T-16
                       ├──→ T-09 ─────────↑
                       └──→ T-10 ─────────↑
```

Si el tiempo se acorta, lo que se sacrifica en este orden: T-19, el test
`slow` de T-10, la paginación por botones de T-15 (queda la primera página), y
T-11 (el umbral se queda en 0.80 y Q-01 sigue abierta). **Nunca** se sacrifican
T-07, T-08, T-12a ni los tests de Vitest de T-14: AC-16 y AC-16b solo se
prueban ahí, y sin ellos el Definition of Done de la spec no se cumple.
