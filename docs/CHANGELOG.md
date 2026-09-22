# Historial de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Se registra lo que cambia el comportamiento observable o las decisiones, no cada
commit.

---

## [No publicado]

### Agregado
- Documentación de contexto: producto, reglas de negocio, arquitectura, glosario.
- Constitución del proyecto con 12 artículos.
- Especificación `001-validacion-semantica` con 19 reglas de negocio, 22
  criterios de aceptación y 26 casos borde.
- Harness de trabajo con agentes: skills de spec, plan, implementación y cierre
  de sesión; subagentes revisores de spec y plan, tests y código; hooks de
  verificación.
- Decisiones D-01 a D-11 registradas.
- Andamiaje del repositorio: backend con `pyproject.toml` (ruff, mypy estricto,
  marcadores `slow` e `integration`), esqueleto de Vite con TypeScript estricto,
  `.env.example`, `.gitignore` y `.gitattributes` (T-01).
- Docker Compose con `db` (pgvector), `backend` y `frontend` (nginx sin
  privilegios, proxy de `/api`), imágenes multietapa y `GET /api/v1/salud`
  provisional (T-02).
- Configuración por entorno en `app/config.py`; un umbral fuera de [0, 1] o no
  numérico impide el arranque (RN-06, B-24, T-03).
- Migración inicial con Alembic: extensión `vector`, tipo `estado_frase`, tabla
  `frases` e índices del plan §2, incluido HNSW. El backend migra al arrancar
  (T-04).
- D-12: `@types/react`, `@types/react-dom` y Testing Library 15 en el frontend.
- D-13 a D-15: Compose sin `.env` obligatorio y migración al arrancar;
  configuración con nombres en español; migración inicial escrita a mano.
- Dominio: normalización y validación de longitud, política de umbral con
  `>=` sin redondear, recorte a [0, 1], normalización de vectores y jerarquía
  de errores (T-05).
- Puertos `ProveedorEmbeddings` y `RepositorioFrases`; dobles `FakeEmbedder` y
  `RepositorioEnMemoria` con los mismos desempates que el SQL (T-06).
- Caso de uso `ValidarFrase`: duplicado exacto sin llamar al proveedor,
  semántico con vector normalizado, base vacía y desempate determinista (T-07).
- Caso de uso `GuardarFrase`: revalidación completa, confirmación explícita,
  embedding del duplicado exacto generado al guardar y metadatos inmutables
  (T-08).
- D-16 a D-18: ruff sin N818; conformidad de los dobles comprobada por mypy;
  contratos del dominio y de los casos de uso.
- Repositorio PostgreSQL síncrono con pgvector: duplicado exacto, vecino más
  cercano con desempate por id sobre los 5 candidatos del índice HNSW, listado
  paginado, `esta_disponible()` y traducción de fallos a `ErrorRepositorio`
  (T-09).
- `scripts/preparar_base_test.sh` crea y migra `banco_frases_test` (T-09).
- D-19: el desempate por id del vecino más cercano se resuelve fuera del
  índice; mypy no analiza los stubs de numpy.
- Adaptador `HuggingFaceEmbedder` con import perezoso y traducción de fallos
  a `ErrorProveedorEmbeddings`. El `lifespan` carga el modelo una vez desde
  `app.state.fabrica_embedder`: si no carga, arranca degradado (B-09); si su
  dimensión no coincide con `EMBEDDING_DIMENSION`, el arranque falla (B-14)
  (T-10).

### Cambiado (auditoría previa al primer commit)
- Se embebe el texto normalizado, no el original (RN-02, RN-05).
- El duplicado exacto confirmado genera su embedding al guardar (RN-14, AC-11b).
- Aplicación síncrona de punta a punta (D-10); sin límite de peticiones en la
  aplicación (D-11).
- Puntaje recortado a [0, 1] y comparado sin redondear (RN-05, B-15, B-16).
- Desempate por identificador también en el duplicado exacto y en el listado
  (RN-08, RN-17).
- La normalización de vectores es del dominio, no del proveedor (RN-19, D-09).
- Longitud medida sobre el texto normalizado, en el dominio (RN-01, AC-02).

---

<!--
Plantilla para nuevas entradas:

## [0.1.0] - AAAA-MM-DD

### Agregado
- ...

### Cambiado
- ...

### Corregido
- ...

### Eliminado
- ...
-->
