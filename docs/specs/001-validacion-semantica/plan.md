# Plan 001 — Validación semántica de frases

**Estado:** aprobado · **Fecha:** 2026-09-21

Este documento describe **cómo** se construye lo definido en `spec.md`.

---

## 1. Contrato de la API

Base: `/api/v1`. Todo el cuerpo es JSON UTF-8. Las fechas son ISO-8601 en UTC.

### 1.1 `POST /frases/validar`

Compara una frase contra las registradas. **No persiste nada** (RN-10).

**Petición**
```json
{ "texto": "La entidad bancaria rechazó la transacción" }
```

**Respuesta `200`**
```json
{
  "es_posible_duplicado": true,
  "motivo": "SEMANTICO",
  "puntaje": 0.8912,
  "umbral_aplicado": 0.80,
  "mas_parecida": {
    "id": 42,
    "texto": "El pago fue rechazado por el banco"
  },
  "modelo": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
}
```

- `motivo`: `"EXACTO"` | `"SEMANTICO"` | `null` cuando no hay duplicado.
- `puntaje`: número en [0, 1] (recortado, RN-05), o `null` si la base está vacía
  (AC-07). Se redondea a 4 decimales **solo al serializar**: la política de
  umbral compara el valor sin redondear (B-16). Los schemas de respuesta no
  declaran `ge`/`le` sobre el puntaje: el recorte es del dominio.
- `mas_parecida`: objeto o `null`. Presente también cuando el motivo es `EXACTO`
  y cuando no hay duplicado (AC-05).
- `modelo`: el valor exacto de `EMBEDDING_MODEL_NAME`, con su prefijo.

### 1.2 `POST /frases`

Revalida y, si corresponde, persiste (RN-11, RN-12).

**Petición**
```json
{ "texto": "La entidad bancaria rechazó la transacción", "confirmar_duplicado": false }
```

**Respuesta `201`**
```json
{
  "id": 43,
  "texto": "La entidad bancaria rechazó la transacción",
  "estado": "UNICA",
  "puntaje_similitud": 0.42,
  "id_mas_parecida": 42,
  "umbral_aplicado": 0.80,
  "modelo": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
  "creada_en": "2026-09-21T17:04:33Z"
}
```

`texto` es siempre el texto original. El texto normalizado y el embedding nunca
salen por la API.

**Respuesta `409`** cuando hay posible duplicado sin confirmar (AC-10)
```json
{
  "codigo": "POSIBLE_DUPLICADO",
  "mensaje": "Ya existe una frase muy parecida a la que intentas guardar.",
  "detalles": {
    "puntaje": 0.8912,
    "umbral_aplicado": 0.80,
    "motivo": "SEMANTICO",
    "mas_parecida": { "id": 42, "texto": "El pago fue rechazado por el banco" }
  }
}
```

### 1.3 `GET /frases`

**Parámetros:** `limite` (por defecto 20, entre 1 y 100), `desplazamiento` (por
defecto 0, mayor o igual a 0). Fuera de rango: `422 PARAMETROS_INVALIDOS`. Un
desplazamiento mayor que el total devuelve `200` con `items: []`.

**Respuesta `200`**
```json
{
  "total": 25,
  "limite": 20,
  "desplazamiento": 0,
  "items": [
    {
      "id": 43,
      "texto": "La entidad bancaria rechazó la transacción",
      "estado": "UNICA",
      "puntaje_similitud": 0.42,
      "creada_en": "2026-09-21T17:04:33Z"
    }
  ]
}
```

### 1.4 `GET /salud`

Vive bajo la misma base: `/api/v1/salud`.

```json
{ "estado": "ok", "modelo_cargado": true, "base_datos": "ok" }
```

Responde `503` con `"estado": "degradado"` si el modelo no cargó o la base no
responde (B-09, AC-18). Es un informe de estado, no un error: es la única
respuesta no exitosa que no usa la forma de 1.5. La comprobación de la base usa
`RepositorioFrases.esta_disponible()`; si falla, `base_datos` vale
`"no_disponible"` (D-22).

### 1.5 Catálogo de errores (RN-16, AC-14)

Toda respuesta de error tiene la misma forma:

```json
{ "codigo": "STRING_EN_MAYUSCULAS", "mensaje": "Texto para la persona usuaria.", "detalles": {} }
```

| HTTP | `codigo` | Cuándo |
|---|---|---|
| 422 | `FRASE_INVALIDA` | Longitud del texto normalizado fuera de rango, o vacío tras normalizar. Lo decide el dominio |
| 422 | `PARAMETROS_INVALIDOS` | Cuerpo mal formado, campo ausente o de tipo incorrecto, `limite` o `desplazamiento` fuera de rango. Lo decide el schema |
| 409 | `POSIBLE_DUPLICADO` | Duplicado detectado sin confirmación |
| 404 | `NO_ENCONTRADO` | Ruta inexistente |
| 405 | `METODO_NO_PERMITIDO` | Método HTTP no admitido en la ruta |
| 503 | `SERVICIO_IA_NO_DISPONIBLE` | El proveedor de embeddings falló o no cargó (RN-15) |
| 503 | `BASE_DATOS_NO_DISPONIBLE` | Sin conexión a PostgreSQL (`ErrorRepositorio`) |
| 500 | `ERROR_INTERNO` | Cualquier otro fallo. Sin traza en la respuesta |

El cliente del frontend (`api/cliente.ts`) añade dos códigos propios, que el
servidor nunca emite: `SIN_CONEXION` (la petición no llegó al servidor;
`estado_http` es `null`) y `RESPUESTA_INESPERADA` (la respuesta no tiene la
forma del contrato; por ejemplo, un `502` de nginx en HTML).

Para que AC-14 se cumpla hay que sustituir tres manejadores por defecto de
FastAPI: `RequestValidationError`, `StarletteHTTPException` y `Exception`. Sin
eso el framework responde `{"detail": ...}`.

**Dónde se valida la longitud.** El schema Pydantic de entrada solo exige que
`texto` sea una cadena y le pone un tope defensivo de 2000 caracteres crudos,
para no normalizar entradas gigantes. La regla de 3 a 280 (RN-01) se aplica en
el dominio sobre el texto **normalizado**. Poner `max_length=280` en el schema
sería un error: rechazaría un texto de 300 caracteres que normaliza a 250.

---

## 2. Modelo de datos

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TYPE estado_frase AS ENUM ('UNICA', 'DUPLICADO_CONFIRMADO');

CREATE TABLE frases (
    id                BIGSERIAL PRIMARY KEY,
    texto_original    TEXT        NOT NULL,
    texto_normalizado TEXT        NOT NULL,
    embedding         vector(384) NOT NULL,
    estado            estado_frase NOT NULL,
    puntaje_similitud DOUBLE PRECISION,
    id_mas_parecida   BIGINT      REFERENCES frases(id),
    modelo            TEXT        NOT NULL,
    umbral_aplicado   DOUBLE PRECISION NOT NULL,
    creada_en         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_frases_texto_normalizado ON frases (texto_normalizado, id);
CREATE INDEX idx_frases_creada_en         ON frases (creada_en DESC, id DESC);
CREATE INDEX idx_frases_embedding ON frases
    USING hnsw (embedding vector_cosine_ops);
```

Todo esto va en **la primera y única migración**, incluido el índice HNSW.

**Notas de diseño**

- No hay restricción `UNIQUE` sobre `texto_normalizado`: RN-12 permite guardar un
  duplicado exacto si la persona lo confirma. La unicidad es una decisión de
  negocio, no una restricción de la base.
- `puntaje_similitud` e `id_mas_parecida` son nulos cuando la base estaba vacía
  (RN-09).
- `umbral_aplicado` y `modelo` se guardan por fila para que los metadatos
  históricos no cambien al cambiar la configuración (AC-12).
- El índice HNSW sobre pocas filas no aporta y PostgreSQL puede ignorarlo. Se
  crea igualmente desde la primera migración porque es lo que cumple NF-02, y a
  diferencia de IVFFlat no necesita datos previos para construirse.
- `puntaje_similitud` y `umbral_aplicado` son `DOUBLE PRECISION`, no `REAL`: con
  4 bytes, un umbral de 0.80 se lee de vuelta como 0.800000011920929 y dejaría
  de ser igual al valor configurado (AC-12).
- `id_mas_parecida` no declara `ON DELETE`: no existe el borrado de frases y los
  metadatos son inmutables (RN-13).
- `creada_en` la asigna la base. `now()` devuelve la hora de inicio de la
  transacción, así que varias filas insertadas juntas comparten fecha: por eso
  el listado desempata por `id` (RN-17).
- El `downgrade` de la migración hace `DROP TYPE estado_frase` de forma
  explícita; `drop_table` no elimina el tipo y un `upgrade` posterior fallaría.

**Consulta del duplicado exacto** (RN-04, RN-08):

```sql
SELECT id, texto_original FROM frases
WHERE texto_normalizado = :texto
ORDER BY id ASC
LIMIT 1;
```

**Consulta del vecino más cercano** (RN-05, RN-08):

```sql
SELECT id, texto_original, 1 - (embedding <=> :consulta) AS puntaje
FROM frases
ORDER BY embedding <=> :consulta ASC, id ASC
LIMIT 1;
```

El segundo criterio de orden `id ASC` es lo que implementa el desempate
determinista de RN-08. En T-09 se comprueba con `EXPLAIN` que, con el índice
HNSW presente, el plan sigue usándolo pese al segundo criterio; si no lo usa, se
piden los 5 más cercanos ordenando solo por distancia y el desempate se resuelve
sobre esos 5.

En SQLAlchemy la consulta se escribe con el tipo `Vector` del paquete `pgvector`
y su comparador `cosine_distance()`. Si se usara `text()`, el parámetro se
convierte con `CAST(:consulta AS vector)`; la forma `:consulta::vector` choca con
la sintaxis de parámetros de SQLAlchemy.

**Listado** (RN-17): `ORDER BY creada_en DESC, id DESC LIMIT :limite OFFSET :desplazamiento`.

Como los vectores están normalizados (RN-19), el operador de producto interno
`<#>` daría exactamente el mismo orden y sería algo más rápido. Se mantiene
`<=>` porque expresa la intención de forma directa y la diferencia es
despreciable a este volumen. La justificación completa está en D-09.

---

## 3. Puertos y adaptadores

```python
# app/ports/embeddings.py
class ProveedorEmbeddings(Protocol):
    @property
    def nombre_modelo(self) -> str: ...
    @property
    def dimension(self) -> int: ...
    def generar(self, texto: str) -> list[float]: ...

# app/ports/repositorio.py
class RepositorioFrases(Protocol):
    def buscar_por_texto_normalizado(self, texto: str) -> Frase | None: ...
    def buscar_mas_parecida(self, embedding: list[float]) -> tuple[Frase, float] | None: ...
    def guardar(self, frase: FraseNueva) -> Frase: ...
    def listar(self, limite: int, desplazamiento: int) -> tuple[list[Frase], int]: ...
    def esta_disponible(self) -> bool: ...
```

**Todo es síncrono** (D-10): los puertos son `def`, los endpoints son `def` y
FastAPI los ejecuta en su grupo de hilos. `encode()` es trabajo de CPU
bloqueante; dentro de un `async def` congelaría el bucle de eventos. La sesión de
SQLAlchemy es la síncrona, con el driver `psycopg` 3
(`postgresql+psycopg://...`).

- `buscar_por_texto_normalizado` devuelve la de **identificador menor** si hay
  varias (RN-08).
- `Frase` es la entidad ya persistida: tiene `id` y `creada_en`. `FraseNueva` es
  lo que se va a guardar: texto original, texto normalizado, embedding y
  metadatos, sin `id` ni fecha. `Frase` no transporta el embedding: nadie lo lee
  de vuelta.
- `dimension` se usa una sola vez, al arrancar, para comprobar que coincide con
  `EMBEDDING_DIMENSION` (B-14).
- Cualquier fallo de conexión o de SQL se traduce dentro del adaptador a
  `ErrorRepositorio`, que el manejador convierte en `503`.

**Adaptadores de `ProveedorEmbeddings`:**

- `HuggingFaceEmbedder`: envuelve `SentenceTransformer`. Se instancia una vez en
  el `lifespan` de FastAPI (NF-03) y se guarda en `app.state`. Llama a
  `encode(texto, normalize_embeddings=True)`. El import de
  `sentence_transformers` es **perezoso**, dentro del constructor: así el resto
  de la aplicación y toda la suite rápida se importan sin tener `torch`
  instalado. Cualquier excepción se traduce a `ErrorProveedorEmbeddings`, que el
  manejador convierte en `503`.
- `FakeEmbedder`: determinista, sin dependencias pesadas. Genera el vector a
  partir de un hash del texto normalizado, o devuelve vectores preprogramados
  para pares concretos de frases. Permite escribir tests que fijan el puntaje
  exacto (AC-04, AC-05, AC-06) sin depender del modelo real.

---

## 4. Lógica del dominio

```python
# app/domain/normalizacion.py
def normalizar(texto: str) -> str:
    """NFKC, recorte, colapso de espacios, minúsculas. RN-02."""

# app/domain/politica.py
def es_posible_duplicado(puntaje: float | None, umbral: float) -> bool:
    """Comparación >= sobre el puntaje sin redondear. Nulo es falso. RN-06, B-08, B-16."""

def recortar_puntaje(puntaje: float) -> float:
    """Lleva el coseno a [0, 1]. RN-05, B-15."""

# app/domain/vectores.py
def normalizar_vector(vector: list[float]) -> list[float]:
    """Devuelve el vector con norma 1. Norma cero lanza ErrorProveedorEmbeddings. RN-19."""
```

Funciones puras, sin entrada/salida y sin NumPy (`math.sqrt` basta para 384
números). Se prueban directamente, sin mocks.

`normalizar` usa `unicodedata.normalize("NFKC", ...)`, `" ".join(texto.split())`
—que recorta y colapsa **todo** espacio en blanco Unicode en un paso— y
`str.lower()`. La longitud se mide con `len()` sobre el resultado.

`ResultadoValidacion` lleva: `es_posible_duplicado`, `motivo`, `puntaje`,
`mas_parecida`, `umbral_aplicado`, `modelo`, `texto_normalizado` y `embedding`
(`list[float] | None`; es `None` cuando el motivo es `EXACTO`). Los dos últimos
son de uso interno entre casos de uso y no se serializan.

Los casos de uso reciben por constructor sus puertos y los valores de
configuración que necesitan (`umbral`, `longitud_maxima`) como datos simples.
`application/` no importa `config.py`.

**Caso de uso `ValidarFrase`:**
1. Normalizar y validar longitud → si falla, `FraseInvalida` (AC-01, AC-02).
2. Buscar duplicado exacto por texto normalizado → si existe, devolver puntaje
   1.0 y motivo `EXACTO`, **sin llamar al proveedor de embeddings** (AC-03).
3. Generar el embedding **del texto normalizado** (RN-05) y pasarlo por
   `normalizar_vector` (RN-19, AC-17).
4. Buscar el vecino más cercano → si no hay, devolver puntaje nulo (AC-07).
5. Recortar el puntaje, aplicar la política de umbral y devolver el resultado.

**Caso de uso `GuardarFrase`:**
1. Ejecutar `ValidarFrase` completo (RN-11, AC-12b).
2. Si es posible duplicado y no está confirmado → `PosibleDuplicado` → `409`.
3. Si el resultado no trae embedding —duplicado exacto confirmado—, generarlo y
   normalizarlo ahora. Si el proveedor falla → `503` y no se guarda (AC-11b).
4. Construir `FraseNueva` con todos los metadatos y persistir en una transacción.

**Raíz de composición.** `app/main.py` es el **único** módulo que importa
adaptadores concretos. Crea la aplicación, y en el `lifespan` construye el
embedder y la fábrica de sesiones y los deja en `app.state`.
`adapters/api/dependencias.py` expone funciones para `Depends` que leen de
`app.state` y arman los casos de uso, sin importar `persistence` ni `embeddings`.

**Arranque (`lifespan`).** El embedder se obtiene de una fábrica sustituible, de
modo que `TestClient` nunca carga el modelo real. Si la carga falla, el error
se registra en el log, `app.state.embedder` queda en `None` y el proceso
**arranca igual** (B-09, AC-18): cuando es `None`, la dependencia que entrega
el embedder devuelve un `EmbedderNoDisponible` cuyo `generar` lanza
`ErrorProveedorEmbeddings`. Así un duplicado exacto se sigue validando (RN-15,
B-20) y todo lo que necesita un vector responde `503` (D-21). Si carga, se comprueba que su
`dimension` coincida con `EMBEDDING_DIMENSION`; si no, el arranque falla (B-14).

---

## 5. Frontend

**Estructura**

```
src/
  api/cliente.ts        fetch tipado, traduce errores de la API a un tipo propio
  api/tipos.ts          tipos espejo del contrato
  hooks/useFrases.ts    listado y paginación
  hooks/useValidacion.ts  estado de la validación
  components/
    FormularioFrase.tsx
    ListaFrases.tsx
    AlertaDuplicado.tsx
    BotonCarga.tsx      botón con estado de carga que no cambia de ancho (ui-design)
    EstadoVacio.tsx
  App.tsx
```

**Máquina de estados del formulario** (evita los estados imposibles):

`inactivo` → `validando` → (`unica` | `posible_duplicado` | `error`) → `guardando` → `guardada`

Transiciones que no son el camino feliz:

| Desde | Evento | Hacia |
|---|---|---|
| `unica`, `posible_duplicado`, `error`, `guardada` | La persona modifica el texto | `inactivo` (AC-16b) |
| `posible_duplicado` | Cancelar | `inactivo`, **conservando** el texto |
| `guardando` | `409` | `posible_duplicado` con los datos del `409` |
| `guardando` | `422`, `503`, fallo de red | `error` |
| `error` | Reintentar | repite la última operación (`validando` o `guardando`) |
| `guardada` | — | El campo ya está vacío; el mensaje se queda hasta que se escribe |

El `409` trae en `detalles` lo mismo que un resultado de validación salvo
`es_posible_duplicado` y `modelo` (§1.2). El cliente lo entrega como
`DatosDuplicado`, un tipo que también cumple cualquier resultado de validación.
El estado `posible_duplicado` usa ese tipo, porque la alerta no muestra el
modelo.

Reglas de interfaz:
- El botón Guardar está deshabilitado hasta que exista un resultado de
  validación **para el texto actual**.
- En estado `unica` se muestra solo "No encontramos frases parecidas. Puedes
  guardarla." No se muestra la más cercana ni su porcentaje: un 42 % no ayuda a
  decidir y confunde.
- En `unica`, Guardar envía `confirmar_duplicado: false`. En
  `posible_duplicado`, **Guardar de todos modos** envía `true`.
- Tras guardar, el listado vuelve a la primera página y se vuelve a pedir
  (AC-16). La paginación son dos botones, **Anteriores** y **Siguientes**.
- El máximo de caracteres del contador sale de `VITE_MAX_PHRASE_LENGTH` (por
  defecto 280). El contador cuenta puntos de código (`[...texto].length`), igual
  que el servidor, no unidades UTF-16: un emoji cuenta 1, no 2.
- Si el estado es `posible_duplicado`, se muestra la frase existente y el
  porcentaje, con dos acciones claras: **Guardar de todos modos** y **Cancelar**.
- Si el servidor responde `409` al guardar (porque revalidó), se vuelve al
  estado `posible_duplicado` con el nuevo dato. Este caso se prueba: es la
  evidencia visible de RN-11.
- El contador de caracteres avisa a partir de 280. La validación real es del
  servidor (Artículo 8).
- Nunca se usa `dangerouslySetInnerHTML`.

---

## 6. Seguridad

| Medida | Dónde |
|---|---|
| CORS restringido a `CORS_ORIGINS`, nunca `*` | Backend |
| Validación de tipo y tope defensivo de tamaño con Pydantic; la longitud de negocio, en el dominio (ver 1.5) | Backend |
| Consultas parametrizadas vía SQLAlchemy | Backend |
| Sin trazas internas en las respuestas de error | Backend |
| Secretos solo por variables de entorno, `.env` fuera del repositorio | Ambos |
| Escapado automático de React, sin `dangerouslySetInnerHTML` | Frontend |
| Sin secretos en variables `VITE_*` | Frontend |
| Usuario sin privilegios en las imágenes Docker | Infraestructura |
| Postgres sin puerto publicado hacia afuera | Infraestructura |
| Límite de peticiones por IP, HTTPS y cabeceras `X-Content-Type-Options`, `X-Frame-Options`, CSP básica | Proxy inverso, **solo** si hay despliegue público (T-19, D-11) |

El límite de peticiones no vive en la aplicación (D-11): ninguna regla lo pide,
detrás de un proxy todas las peticiones llegan con la misma IP, y un contador en
memoria por proceso contradice NF-04.

---

## 7. Estrategia de pruebas

| Nivel | Qué cubre | Con qué |
|---|---|---|
| Unitario dominio | Normalización de texto y de vectores, política de umbral, recorte | Sin dependencias |
| Unitario aplicación | Los dos casos de uso completos, AC-03 a AC-12b y AC-17 | `FakeEmbedder` + `RepositorioEnMemoria` |
| Integración (marcados `integration`) | Repositorio contra PostgreSQL con pgvector, migración ida y vuelta, consulta del vecino, desempates, paginación, y la cláusula del vector persistido de AC-12 | El servicio `db` de Compose, con una base **separada** `banco_frases_test` |
| API | AC-01, AC-02, AC-02b, AC-13, AC-14, AC-15, AC-18 y el flujo de guardado por HTTP | `TestClient` con `app.dependency_overrides` y la fábrica de embedder sustituida |
| Marcados `slow` | Un test con el modelo real: dos paráfrasis en español superan 0.80 y dos frases sin relación no llegan a 0.50 | `sentence-transformers` de verdad |
| Frontend | AC-16 y AC-16b: máquina de estados, alerta, confirmación y `409` | Vitest + Testing Library |

**Marcadores:** `slow` e `integration`, declarados en `pyproject.toml`. La suite
rápida es `pytest -m "not slow and not integration"` y no necesita nada
levantado. CI y el hook de cierre corren esa. `pytest -m integration` exige
`docker compose up -d db` y usa `TEST_DATABASE_URL`, nunca la base de
desarrollo: los tests truncan la tabla al empezar.

**`TestClient` y el modelo.** `TestClient(app)` ejecuta el `lifespan`. Para que
la suite rápida no descargue nada, el `lifespan` obtiene el embedder llamando a
`app.state.fabrica_embedder`, que los tests reemplazan por una que devuelve el
`FakeEmbedder` antes de crear el cliente.

**Convención de nombres:** `test_ac04_duplicado_semantico_sobre_umbral`.
Un AC sin test que lo nombre es un AC no cubierto.

---

## 8. Calibración del umbral (D-07)

`scripts/calibrar_umbral.py` recibe `datos/pares_etiquetados.csv` con columnas
`frase_a`, `frase_b`, `equivalentes` (1 o 0) y, opcional, `tipo`
(paráfrasis, negación, antónimo, mismo tema, sin relación), que solo se muestra. Mínimo 20 pares en español,
incluidos casos difíciles: negaciones ("el pago fue aprobado" vs "el pago fue
rechazado") y frases del mismo tema pero distinto significado.

Salida: tabla con umbral, precisión, exhaustividad y F1 para valores de 0.60 a
0.95 en pasos de 0.05, más el umbral recomendado. El resultado se pega en el
README y sustenta el valor por defecto.

---

## 9. Entorno Docker

```
docker-compose.yml
  db        pgvector/pgvector:pg16, volumen de datos, healthcheck con pg_isready,
            sin puerto publicado (para desarrollo local se usa un
            docker-compose.override.yml que publica 5432)
  backend   depende de db sana, ejecuta alembic upgrade head y luego uvicorn.
            Solo expuesto a la red interna de Compose
  frontend  build de Vite servido por nginx en el puerto 8080 del host.
            nginx hace proxy de /api hacia backend:8000
```

**Mismo origen.** El navegador solo habla con nginx: la interfaz se sirve en
`/` y la API en `/api`, así que en Compose no hay CORS que configurar. `CORS_ORIGINS`
existe únicamente para el desarrollo sin Docker (`npm run dev` en 5173 contra
`uvicorn` en 8000). `VITE_API_URL` vale `/api/v1` en la imagen y
`http://localhost:8000/api/v1` en desarrollo.

**Caché del modelo.** `HF_HOME=/home/app/.cache/huggingface` y un volumen con
nombre montado ahí. El `Dockerfile` crea el directorio y lo asigna al usuario
`app` **antes** de declarar `USER app`; si no, el volumen nace con dueño `root`,
la descarga falla con `PermissionError` y la API queda en `503` para siempre.

**Tamaño de imagen.** `torch` se instala desde el índice de CPU
(`--extra-index-url https://download.pytorch.org/whl/cpu`). Con el índice por
defecto la imagen supera los 5 GB por las librerías de CUDA.

Las imágenes usan construcción multietapa y un usuario sin privilegios.

---

## 9b. Dependencias

Lista cerrada. Agregar cualquier otra exige actualizar esta sección y
`decisions.md` en el mismo commit (CLAUDE.md, regla 6). Versiones fijadas en
`pyproject.toml` y `package.json`.

**Backend, ejecución:** `fastapi`, `uvicorn[standard]`, `pydantic` v2,
`pydantic-settings`, `sqlalchemy` 2.x, `psycopg[binary]` 3, `pgvector` (el
paquete Python: aporta el tipo `Vector` para SQLAlchemy y para Alembic),
`alembic`, `sentence-transformers`, `torch` (índice CPU).

**Backend, desarrollo:** `pytest`, `httpx` (lo exige `TestClient`), `ruff`,
`mypy`. No hay `pytest-asyncio`: nada es asíncrono (D-10). No hay
`testcontainers`: la integración usa el `db` de Compose. No hay `slowapi` (D-11).

**Frontend, ejecución:** `react`, `react-dom`.
**Frontend, desarrollo:** `vite`, `typescript`, `@vitejs/plugin-react`,
`vitest`, `@testing-library/react`, `@testing-library/user-event`,
`@testing-library/jest-dom`, `jsdom`, `prettier`, `@types/react` y
`@types/react-dom` (D-12). `@testing-library/react` en la rama 15, que
incluye `@testing-library/dom` y no obliga a declararla aparte (D-12).

---

## 10. Orden de construcción

El detalle está en `tasks.md`. La secuencia es: comprobación del modelo con las
frases de ejemplo → andamiaje y Docker → migración y modelo de datos → dominio →
puertos y adaptadores falsos → casos de uso con tests → adaptador de persistencia
real → adaptador de Hugging Face → API → frontend → calibración → CI y README.

El backend se completa y se prueba **antes** de tocar el frontend. Así, si el
tiempo se acorta, lo que queda incompleto es lo más superficial.
