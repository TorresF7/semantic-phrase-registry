# Arquitectura

## Principio rector

Arquitectura hexagonal ligera: el dominio y los casos de uso no conocen FastAPI,
ni SQLAlchemy, ni `sentence-transformers`. Hablan con interfaces (*puertos*);
las implementaciones concretas (*adaptadores*) se inyectan desde afuera.

La consecuencia práctica es que la lógica de validación se prueba en
milisegundos con un embedder falso y sin base de datos, y que cambiar el modelo
o el proveedor de IA no obliga a tocar una sola línea de negocio.

## Diagrama

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

Las flechas de dependencia apuntan siempre **hacia adentro**. `domain` no
importa nada de `adapters`. `application` importa `domain` y `ports`, nunca
`adapters`.

## Las cuatro capas

La separación es explícita y cada capa tiene una única responsabilidad:

| Capa | Dónde vive | Responsabilidad |
|---|---|---|
| **Interfaz de usuario** | `frontend/src/` y `backend/app/adapters/api/` | Presentar y recoger información. Traducir entre HTTP y los casos de uso. No contiene ninguna regla de negocio |
| **Negocio** | `backend/app/domain/` y `backend/app/application/` | Normalización, política de umbral, decisión de duplicado, orquestación de los casos de uso. No sabe que existe HTTP, ni SQL, ni Hugging Face |
| **Datos** | `backend/app/adapters/persistence/` | Persistencia y recuperación. Traduce entre modelos ORM y entidades de dominio. No decide nada |
| **Integración de IA** | `backend/app/adapters/embeddings/` | Generación de vectores. Aislada tras el puerto `ProveedorEmbeddings`, intercambiable sin tocar el negocio |

Las capas de datos e integración de IA se comunican con la de negocio
**únicamente a través de puertos**. Por eso la de negocio se prueba entera sin
base de datos y sin descargar ningún modelo.

## Detalle por carpeta

| Carpeta | Contiene | No puede importar |
|---|---|---|
| `app/domain` | Entidades, objetos de valor, normalización de texto, política de umbral | Nada externo salvo la librería estándar y Pydantic |
| `app/application` | Casos de uso `ValidarFrase` y `GuardarFrase` | `adapters` |
| `app/ports` | `ProveedorEmbeddings`, `RepositorioFrases` como `typing.Protocol` | `adapters`, `application` |
| `app/adapters/api` | Routers, schemas de entrada/salida, manejador global de errores, funciones para `Depends` | `adapters/persistence`, `adapters/embeddings` |
| `app/adapters/persistence` | Modelos SQLAlchemy, repositorio concreto, consultas pgvector | `application` |
| `app/adapters/embeddings` | Implementación real y falsa del proveedor | `application` |
| `app/main.py` | **Raíz de composición**: el único módulo que importa adaptadores concretos y los cablea en el `lifespan` | — |

## Flujo: validar y guardar

```mermaid
sequenceDiagram
    participant U as Persona
    participant F as Frontend
    participant A as API
    participant V as ValidarFrase
    participant G as GuardarFrase
    participant E as Embeddings
    participant D as PostgreSQL

    U->>F: escribe la frase y presiona «Comprobar similitud»
    F->>A: POST /api/v1/frases/validar
    A->>V: validar(texto)
    V->>V: normalizar (RN-02)
    V->>D: ¿existe texto normalizado? (RN-04)
    alt duplicado exacto
        D-->>V: sí
    else
        V->>E: generar embedding del texto normalizado
        E-->>V: vector (se normaliza a norma 1, RN-19)
        V->>D: vecino más cercano por coseno (RN-05)
        D-->>V: frase e índice de similitud
    end
    V-->>A: resultado
    A-->>F: 200 {es_posible_duplicado, puntaje, mas_parecida}
    F-->>U: muestra el aviso de duplicado o «Guardar frase»

    U->>F: presiona «Guardar frase» o «Guardar de todos modos»
    F->>A: POST /api/v1/frases {texto, confirmar_duplicado}
    A->>G: guardar(...)
    G->>V: revalida desde cero (RN-11)
    V-->>G: resultado
    alt posible duplicado y no confirmado
        G-->>A: conflicto
        A-->>F: 409 con el duplicado encontrado
    else
        opt el resultado fue EXACTO y no trae embedding
            G->>E: generar embedding (RN-14)
        end
        G->>D: INSERT frase + embedding + metadatos
        A-->>F: 201 con la frase creada
    end
```

## Decisión clave: la búsqueda vive en la base de datos

La alternativa ingenua es traer todas las frases a memoria y calcular coseno en
Python con NumPy. Funciona con mil frases y se rompe con cien mil: el tiempo y la
memoria crecen de forma lineal con cada petición, y varias réplicas de la API
duplican el problema.

Usamos `pgvector`. El vector se almacena en una columna `vector(384)` y la
consulta del vecino más cercano es:

```sql
SELECT id, texto_original, 1 - (embedding <=> :consulta) AS puntaje
FROM frases
ORDER BY embedding <=> :consulta ASC, id ASC
LIMIT 1;
```

El operador `<=>` es distancia coseno. La similitud es `1 - distancia`. El
segundo criterio `id ASC` es el desempate de RN-08. Con un índice HNSW la
búsqueda es sublineal y el motor hace el trabajo pesado.

```sql
CREATE INDEX ON frases USING hnsw (embedding vector_cosine_ops);
```

HNSW es un índice **aproximado**: puede, en casos raros, no devolver el vecino
exacto. Para detectar duplicados es un compromiso aceptable y es el estándar de
la industria. Si el requisito fuera exactitud absoluta se usaría búsqueda
secuencial, mucho más lenta. El índice se crea en la primera migración; con
pocos registros PostgreSQL lo ignora y hace la búsqueda secuencial, que a ese
volumen es igual de rápida.

## Ejecución síncrona

Toda la aplicación es síncrona (D-10): puertos con `def`, endpoints con `def`,
sesión de SQLAlchemy síncrona con `psycopg` 3. FastAPI ejecuta los endpoints
`def` en un grupo de hilos, así que varias peticiones se atienden a la vez sin
que la generación del embedding —trabajo de CPU— bloquee nada.

## Modelo de embeddings

`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, 384 dimensiones.

Razones: las frases son en español y los modelos entrenados solo en inglés
producen resultados pobres con textos en castellano. Este está entrenado
específicamente para detectar paráfrasis, que es exactamente el problema. Pesa
poco y corre en CPU sin GPU.

Se carga **una sola vez** en el `lifespan` de FastAPI y se reutiliza. Cargarlo
por petición añadiría segundos a cada llamada.

## Configuración

Todo por variables de entorno, leídas con `pydantic-settings`. Sin valores
mágicos dispersos en el código.

**Backend**

| Variable | Por defecto | Para qué |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://banco:banco@localhost:5432/banco_frases` | Cadena de conexión a PostgreSQL. El valor por defecto es solo para desarrollo local |
| `TEST_DATABASE_URL` | `postgresql+psycopg://banco:banco@localhost:5432/banco_frases_test` | Base **separada** para los tests de integración, que truncan la tabla |
| `SIMILARITY_THRESHOLD` | `0.75` (calibrado en T-11, D-20) | Umbral de posible duplicado (RN-06). Entre 0 y 1 |
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Modelo a cargar. No cambiarlo con frases guardadas (B-13) |
| `EMBEDDING_DIMENSION` | `384` | Dimensión del vector. Se comprueba contra el modelo al arrancar (B-14) |
| `MAX_PHRASE_LENGTH` | `280` | Longitud máxima del texto normalizado (RN-01) |
| `CORS_ORIGINS` | `http://localhost:5173` | Orígenes permitidos, lista separada por comas. Solo hace falta en desarrollo sin Docker: en Compose todo va por el mismo origen |
| `HF_HOME` | `/home/app/.cache/huggingface` (en la imagen) | Dónde se cachea el modelo descargado |
| `LOG_LEVEL` | `INFO` | Nivel de log |

**Compose**: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` para el
servicio `db`, con los mismos valores que `DATABASE_URL`.

**Frontend**: `VITE_API_URL` (`/api/v1` en la imagen, `http://localhost:8000/api/v1`
en desarrollo), `VITE_MAX_PHRASE_LENGTH` (`280`, solo para el contador) y
`VITE_API_TIMEOUT_MS` (`15000`, milisegundos sin respuesta antes de abortar una
petición, D-38).
Las variables `VITE_*` se incrustan en el paquete público.

## Escalabilidad

| Dimensión | Enfoque |
|---|---|
| Volumen de frases | Índice HNSW en pgvector; la complejidad de búsqueda no crece linealmente |
| Concurrencia | API sin estado, varias réplicas detrás de un balanceador |
| Carga del modelo | Una carga por proceso, cacheada en volumen para no descargar en cada arranque |
| Lecturas | El listado es paginado y tiene índice por fecha de creación e id |
| Cambio de modelo | El campo `modelo` por frase permite re-embeber por lotes sin perder el histórico; sería el único caso donde una cola tendría sentido |
