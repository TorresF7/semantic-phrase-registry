# Banco de Frases

Registro de frases cortas que evita duplicados **por significado**, no solo por
coincidencia exacta de texto.

Una persona escribe "El pago fue rechazado por el banco" y presiona
**Comprobar similitud**. Si ya existe "La entidad bancaria rechazó la
transacción", la aplicación avisa: *"Ya existe una frase con el mismo
significado"*, con las dos frases lado a lado y un 87 % de similitud. La
persona elige entre **Editar frase** (no guarda nada y le devuelve el texto
para corregirlo) y **Guardar de todos modos**. Las dos frases no comparten casi
ninguna palabra: la comparación se hace con un modelo de lenguaje que
convierte cada frase en un vector que representa su significado.

![Aviso de duplicado: «Recibirás tu compra en un plazo de tres días» frente a «El pedido llegará en tres días», 85 % de similitud, con los botones Editar frase y Guardar de todos modos](docs/capturas/aviso-duplicado.png)

Si la frase no se parece a ninguna, el botón pasa a **Guardar frase**. Tras
guardar, la frase aparece arriba de la lista sin recargar la página; si se
guardó pese al aviso, queda como *Duplicado confirmado* junto a la frase a la
que se parece:

![Guardado confirmado: mensaje «Frase guardada como duplicado confirmado» y la frase nueva al principio de la lista, con 85 % y un enlace a la más parecida](docs/capturas/guardado-confirmado.png)

El botón se deshabilita con menos de 3 o más de 280 caracteres, y el pie del
campo dice por qué, con el mismo mensaje que daría el servidor.

El problema, el alcance y los usuarios están en
[`docs/context/product.md`](docs/context/product.md). Las reglas de negocio, en
[`docs/context/business-rules.md`](docs/context/business-rules.md).

---

## Arranque rápido con Docker

Requisitos: Docker con Docker Compose v2. Nada más.

```bash
git clone https://github.com/TorresF7/semantic-phrase-registry.git
cd semantic-phrase-registry
docker compose up --build
```

Abre <http://localhost:8080>.

- No hace falta crear un `.env`: cada variable tiene un valor por defecto de
  desarrollo. Si existe un `.env` en la raíz, sus valores prevalecen, salvo
  `DATABASE_URL`: dentro de Compose el backend siempre usa el servicio `db`.
- **La primera vez tarda varios minutos.** Se construyen las imágenes y el
  backend descarga el modelo (unos 470 MB) en el volumen `cache_modelo`. En los
  arranques siguientes el modelo ya está en caché y carga en segundos.
- El backend aplica las migraciones al arrancar. No hay pasos manuales.
- Para comprobar que todo está listo:

  ```bash
  curl http://localhost:8080/api/v1/salud
  # {"estado":"ok","modelo_cargado":true,"base_datos":"ok"}
  ```

  **Mientras el backend carga el modelo, nginx responde `502 Bad Gateway`**,
  tanto a la API como a las peticiones de la interfaz, que muestra «No se pudo
  cargar la lista»: el backend no acepta conexiones hasta tener el modelo en
  memoria. Espera a que `salud` responda y recarga la página. Lo mismo ocurre
  unos segundos tras cada `docker compose up -d --build`.

  Si el modelo no llega a cargar, el backend arranca igualmente en modo
  degradado: `modelo_cargado` vale `false` y validar o guardar una frase nueva
  responde `503`. Una frase idéntica a una ya guardada se detecta igual,
  porque para eso no hace falta el modelo.

Para detenerlo: `docker compose down`. Para borrar también las frases y el
modelo descargado: `docker compose down -v`.

### Qué levanta Compose

| Servicio | Imagen | Puerto en el host | Para qué |
|---|---|---|---|
| `db` | `pgvector/pgvector:pg16` | ninguno (`5432` solo con `-f docker-compose.dev.yml`, ver abajo) | PostgreSQL con la extensión `pgvector` |
| `backend` | `./backend` | ninguno | API FastAPI en el puerto 8000 de la red interna |
| `frontend` | `./frontend` | `8080` | nginx: sirve la aplicación y reenvía `/api/` al backend |

---

## Arranque sin Docker (desarrollo)

Útil para trabajar en el código con recarga en caliente. Requisitos:
Python 3.11, Node.js 24 y un PostgreSQL 16 con la extensión `pgvector`.

La forma más sencilla de tener PostgreSQL es usar solo ese servicio de Compose,
añadiendo `docker-compose.dev.yml`, que publica el puerto 5432 en el host:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
```

`docker compose up` a secas no publica el 5432, así que no choca con un
PostgreSQL que ya tengas instalado. Con este archivo sí: si tu 5432 está
ocupado, usa ese PostgreSQL propio, como se explica a continuación.

Si prefieres un PostgreSQL propio, instala `pgvector`, crea el usuario y la base
de `DATABASE_URL`, y dale permiso para `CREATE EXTENSION` (la primera migración
crea la extensión `vector`).

### 1. Configuración

```bash
cp .env.example .env
```

El backend lee el `.env` de la raíz. Los valores de ejemplo ya apuntan a
`localhost`.

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

# torch primero y desde el índice de CPU: el de PyPI arrastra CUDA y pesa varios GB.
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.0
pip install -e ".[dev]"

alembic upgrade head
uvicorn app.main:app --reload
```

La API queda en <http://localhost:8000/api/v1> y la documentación interactiva,
con ejemplos de cada respuesta, en <http://localhost:8000/api/v1/docs>. En
Compose está en <http://localhost:8080/api/v1/docs>, y el esquema OpenAPI en
`/api/v1/openapi.json`.

Si el puerto 8000 ya está ocupado, arranca con `uvicorn app.main:app --reload
--port 8001` y usa ese puerto en `VITE_API_URL` (paso 3).

La primera vez, el arranque descarga el modelo en la caché de Hugging Face del
usuario (`~/.cache/huggingface`, o la ruta de `HF_HOME` si está definida en el
entorno).

### 3. Frontend

En otra terminal:

```bash
cd frontend
npm ci
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```

Abre <http://localhost:5173>.

Vite lee sus variables de `frontend/`, no del `.env` de la raíz. Sin
`VITE_API_URL`, el cliente pide a `/api/v1` en el mismo origen, que en
desarrollo no existe. `.env.local` está en `.gitignore`.

---

## Datos de ejemplo

`scripts/sembrar_frases.py` guarda 10 frases de ejemplo pasando por la misma
validación que la API, con su vector y sus metadatos. Con `docker compose up`
en marcha, desde la raíz:

```bash
docker compose cp scripts/sembrar_frases.py backend:/tmp/sembrar_frases.py
docker compose exec -e PYTHONPATH=/srv backend python /tmp/sembrar_frases.py
```

Sin Docker, con el entorno del backend activado: `python scripts/sembrar_frases.py`.

Ejecutarlo dos veces no duplica nada: la segunda vez todas se omiten. Después,
escribe "El pago fue rechazado por el banco" en la interfaz y presiona
**Comprobar similitud**: aparece el aviso contra "La entidad bancaria rechazó la
transacción".

> En Git Bash para Windows, antepón `MSYS_NO_PATHCONV=1` al segundo comando:
> si no, Git Bash reescribe la ruta `/tmp/...`.

---

## Probar la API con `curl`

Con la aplicación levantada en Compose y la base vacía. Primero se guarda una
frase:

```bash
curl -X POST http://localhost:8080/api/v1/frases \
  -H "Content-Type: application/json" \
  -d '{"texto": "La entidad bancaria rechazó la transacción"}'
```

```json
{
  "id": 1,
  "texto": "La entidad bancaria rechazó la transacción",
  "estado": "UNICA",
  "puntaje_similitud": null,
  "id_mas_parecida": null,
  "umbral_aplicado": 0.75,
  "modelo": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
  "creada_en": "2026-09-22T17:33:37.421907Z"
}
```

Después se valida la otra, sin guardarla:

```bash
curl -X POST http://localhost:8080/api/v1/frases/validar \
  -H "Content-Type: application/json" \
  -d '{"texto": "El pago fue rechazado por el banco"}'
```

```json
{
  "es_posible_duplicado": true,
  "motivo": "SEMANTICO",
  "puntaje": 0.8735,
  "umbral_aplicado": 0.75,
  "mas_parecida": {
    "id": 1,
    "texto": "La entidad bancaria rechazó la transacción"
  },
  "modelo": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
}
```

> **En Windows**, la consola puede enviar las tildes en una codificación que no
> es UTF-8 y la API rechaza el cuerpo. Si pasa, guarda el JSON en un archivo con
> codificación UTF-8 y envíalo con `--data-binary @archivo.json`.

**0.8735** es el puntaje real de este par con el modelo por defecto, medido en
T-00 y confirmado en la calibración (D-20). La interfaz lo muestra como "87% de
similitud".

Si ahora se intenta guardar sin confirmar, la API responde `409` con el mismo
detalle. Para guardarla igualmente:

```bash
curl -X POST http://localhost:8080/api/v1/frases \
  -H "Content-Type: application/json" \
  -d '{"texto": "El pago fue rechazado por el banco", "confirmar_duplicado": true}'
```

La frase queda con estado `DUPLICADO_CONFIRMADO`. El listado paginado está en
`GET /api/v1/frases?limite=20&desplazamiento=0`. El contrato completo, con
todos los errores, está en el
[plan técnico, §1](docs/specs/001-validacion-semantica/plan.md).

---

## Variables de entorno

Todas tienen un valor por defecto de desarrollo. La lista comentada está en
[`.env.example`](.env.example).

### Backend

| Variable | Por defecto | Para qué |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://banco:banco@localhost:5432/banco_frases` | Conexión a PostgreSQL. En Compose se sustituye por la del servicio `db` |
| `TEST_DATABASE_URL` | `postgresql+psycopg://banco:banco@localhost:5432/banco_frases_test` | Base **separada** para los tests de integración, que vacían la tabla |
| `SIMILARITY_THRESHOLD` | `0.75` | Umbral de posible duplicado, entre 0 y 1. Fuera de ese rango, el backend no arranca. Ver [calibración](#calibración-del-umbral) |
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Modelo de embeddings. ⚠️ **No lo cambies si ya hay frases guardadas** (ver abajo) |
| `EMBEDDING_DIMENSION` | `384` | Dimensión del vector. Se comprueba contra el modelo al arrancar: si no coincide, el backend no arranca |
| `MAX_PHRASE_LENGTH` | `280` | Longitud máxima de una frase, en caracteres, una vez normalizada |
| `CORS_ORIGINS` | `http://localhost:5173` | Orígenes permitidos, separados por comas. Solo hace falta sin Docker: en Compose todo va por el mismo origen |
| `HF_HOME` | `/home/app/.cache/huggingface` en la imagen | Dónde se guarda el modelo descargado. La lee Hugging Face del entorno del proceso, no del `.env` |
| `LOG_LEVEL` | `INFO` | Nivel de log |

> ⚠️ **`EMBEDDING_MODEL_NAME` y las frases ya guardadas.** Los vectores de
> modelos distintos no son comparables: si se cambia el modelo con frases en la
> base, los puntajes dejan de tener sentido y la detección de duplicados falla
> sin avisar. No está soportado (caso borde B-13). Cada frase guarda el nombre
> del modelo con que se validó, lo que permite detectar la mezcla, pero volver a
> generar los vectores está fuera del alcance. Si hay que cambiar de modelo,
> empieza con una base vacía y ajusta también `EMBEDDING_DIMENSION`.

### Compose

| Variable | Por defecto | Para qué |
|---|---|---|
| `POSTGRES_USER` | `banco` | Usuario del servicio `db` |
| `POSTGRES_PASSWORD` | `banco` | Contraseña del servicio `db`. Cámbiala fuera de desarrollo |
| `POSTGRES_DB` | `banco_frases` | Base de datos del servicio `db` |

### Frontend

Se incrustan en el paquete JavaScript al construirlo y son públicas: nunca
pongas un secreto en una variable `VITE_*`.

| Variable | Por defecto | Para qué |
|---|---|---|
| `VITE_API_URL` | `/api/v1` | Dirección de la API. Sin Docker: `http://localhost:8000/api/v1` |
| `VITE_MAX_PHRASE_LENGTH` | `280` | Máximo del contador de caracteres. Solo informativo: el límite real lo aplica el servidor |

---

## Arquitectura

Arquitectura hexagonal ligera: el dominio y los casos de uso no conocen
FastAPI, ni SQLAlchemy, ni `sentence-transformers`. Hablan con puertos
(`typing.Protocol`) cuyas implementaciones se inyectan desde `app/main.py`, el
único módulo que importa adaptadores concretos. Por eso toda la lógica de
validación se prueba en milisegundos, sin base de datos y sin descargar el
modelo.

```mermaid
flowchart TB
    UI["React + TypeScript<br/>registro · veredicto · listado"]

    subgraph API["Adaptador HTTP — FastAPI"]
        R["Routers · Schemas Pydantic<br/>Manejador de errores"]
    end

    subgraph APP["Aplicación — casos de uso"]
        UC1["ValidarFrase"]
        UC2["GuardarFrase"]
    end

    subgraph DOM["Dominio"]
        E["Frase · ResultadoValidacion<br/>Normalización · Política de umbral"]
    end

    subgraph PORTS["Puertos (Protocol)"]
        P1["ProveedorEmbeddings"]
        P2["RepositorioFrases"]
    end

    subgraph ADP["Adaptadores de salida"]
        A1["HuggingFaceEmbedder"]
        A2["FakeEmbedder (tests)"]
        A3["RepositorioPostgres"]
    end

    DB[("PostgreSQL 16<br/>+ pgvector")]

    UI -->|HTTP JSON| R
    R --> UC1 & UC2
    UC1 & UC2 --> E
    UC1 & UC2 --> P1 & P2
    P1 -.implementa.-> A1
    P1 -.implementa.-> A2
    P2 -.implementa.-> A3
    A3 --> DB
```

Cómo se decide si una frase es un duplicado:

1. Se **normaliza** el texto: Unicode NFKC, recorte, espacios colapsados y
   minúsculas.
2. Si el texto normalizado ya existe, es un **duplicado exacto**. No hace falta
   el modelo.
3. Si no, se genera el vector del texto normalizado, se normaliza a longitud 1
   y PostgreSQL busca el **vecino más cercano por similitud coseno** con un
   índice HNSW. Nunca se cargan todas las frases en memoria.
4. Si el puntaje es **mayor o igual** al umbral, es un posible duplicado.
5. Al guardar, el servidor **vuelve a validar desde cero**: entre validar y
   guardar otra persona pudo registrar una frase parecida.

El detalle está en [`docs/context/architecture.md`](docs/context/architecture.md)
y los patrones aplicados, cada uno con el problema que resuelve, en
[`docs/context/patterns.md`](docs/context/patterns.md).

### Estructura

```
backend/
  app/
    domain/          entidades y reglas puras
    application/     casos de uso
    ports/           interfaces (typing.Protocol)
    adapters/
      api/           capa HTTP (FastAPI)
      persistence/   PostgreSQL + pgvector
      embeddings/    proveedor de embeddings real y falso
    main.py          raíz de composición
  migrations/        Alembic
  tests/
frontend/
  src/
    api/             cliente HTTP y tipos
    components/
    hooks/
    estilos/
datos/               pares etiquetados para calibrar el umbral
docs/                producto, reglas de negocio, arquitectura, specs y decisiones
scripts/
```

---

## Decisiones principales

Cada decisión, con su justificación y las alternativas descartadas, está en
[`docs/decisions.md`](docs/decisions.md). Las que más condicionan el sistema:

| # | Decisión | Por qué |
|---|---|---|
| D-01 | La búsqueda de similitud vive en PostgreSQL con `pgvector` | Con un índice HNSW el tiempo no crece con cada frase nueva y la API no guarda estado entre réplicas |
| D-02 | Modelo `paraphrase-multilingual-MiniLM-L12-v2` | Entrenado para detectar paráfrasis, funciona en español, corre en CPU y pesa poco |
| D-03 | Arquitectura hexagonal ligera | La lógica se prueba sin base ni modelo, y cambiar de proveedor de IA no toca el negocio |
| D-04 | El servidor revalida al guardar | El resultado que tiene el cliente puede estar desactualizado |
| D-05, D-06 | Sin autenticación y sin colas | Fuera de alcance: repositorio compartido y validación síncrona porque la persona espera la respuesta |
| D-09 | Vectores normalizados por el dominio, no por el proveedor | Todos los vectores guardados son homogéneos, venga de donde venga el modelo |
| D-10 | Backend síncrono de punta a punta | FastAPI ejecuta los endpoints síncronos en un grupo de hilos: el modelo no bloquea nada y el código es más simple |
| D-20 | Umbral por defecto 0.75, calibrado con datos | Ver la sección siguiente |

---

## Calibración del umbral

El umbral por defecto no se eligió a ojo. `scripts/calibrar_umbral.py` mide el
modelo sobre [`datos/pares_etiquetados.csv`](datos/pares_etiquetados.csv): 32
pares en español, 14 de ellos equivalentes, que incluyen paráfrasis del
dominio, negaciones, antónimos, pares del mismo tema con distinto significado y
pares sin relación.

| Umbral | Precisión | Exhaustividad | F1 | Falsos positivos | Falsos negativos |
|---|---|---|---|---|---|
| 0.60 | 0.500 | 0.714 | 0.588 | 10 | 4 |
| 0.65 | 0.556 | 0.714 | 0.625 | 8 | 4 |
| 0.70 | 0.562 | 0.643 | 0.600 | 7 | 5 |
| **0.75** | 0.727 | 0.571 | **0.640** | 3 | 6 |
| 0.80 | 0.727 | 0.571 | 0.640 | 3 | 6 |
| 0.85 | 0.600 | 0.214 | 0.316 | 2 | 11 |
| 0.90 | 0.333 | 0.071 | 0.118 | 2 | 13 |
| 0.95 | 0.000 | 0.000 | 0.000 | 1 | 14 |

0.75 y 0.80 empatan en F1, y se eligió 0.75. Da margen a cuatro paráfrasis
verdaderas que quedan entre 0.81 y 0.83. Además, un falso positivo solo pide a
la persona que confirme, mientras que un falso negativo deja entrar un
duplicado sin aviso.

Límites conocidos del modelo, que ningún umbral corrige:

- **No distingue cambios de lugar, número o dirección.** "El envío sale desde
  Madrid" y "El envío llega a Madrid" puntúan 0.9659, más que el par del
  ejemplo. En esos casos la alerta aparece y la persona decide.
- **Pierde paráfrasis que cambian casi todas las palabras.** "El producto está
  agotado" y "No quedan unidades disponibles de este artículo" puntúan 0.4039.
- **Las negaciones quedan cerca del umbral** (0.65 a 0.70). Si se baja
  `SIMILARITY_THRESHOLD` a 0.70 o menos, empiezan a marcarse como duplicados.

Para recalibrar, amplía el CSV con frases reales y ejecuta, con el entorno del
backend activado y desde la raíz:

```bash
python scripts/calibrar_umbral.py
```

El análisis completo está en [D-20](docs/decisions.md).

---

## Pruebas

```bash
# Backend, dentro de backend/ con el entorno activado
pytest -m "not slow and not integration"   # suite rápida: sin base ni modelo, unos segundos
pytest -m integration                      # contra PostgreSQL real (ver abajo)
pytest -m slow                             # con el modelo real: lo descarga si no está en caché
ruff check . && ruff format --check .
mypy app

# Frontend, dentro de frontend/
npm run test
npm run build
```

Los tests de integración usan una base **separada**, `banco_frases_test`, porque
vacían la tabla. Para crearla y migrarla, con la base de desarrollo en marcha
(`docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db`):

```bash
bash scripts/preparar_base_test.sh
```

El script es idempotente. La integración continua
([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) ejecuta lint, tipos, la
suite rápida, la de integración y las comprobaciones del frontend en cada push
a `main` y en cada pull request.

---

## Documentación

- [`docs/README.md`](docs/README.md) — mapa de toda la documentación.
- [`docs/specs/001-validacion-semantica/`](docs/specs/001-validacion-semantica/) —
  especificación, plan técnico y tareas.
- [`docs/constitution.md`](docs/constitution.md) — principios del proyecto.
- [`docs/STATUS.md`](docs/STATUS.md) — estado actual del trabajo.

## Licencia

[MIT](LICENSE).
