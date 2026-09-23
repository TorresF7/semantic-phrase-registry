# Banco de Frases — Guía del proyecto

Producto interno que permite registrar frases cortas y **evitar duplicados por significado**,
no solo por coincidencia exacta de texto.

## Documentos que debes conocer

Lee estos archivos antes de proponer o escribir código. Son la fuente de verdad.

@docs/context/product.md
@docs/context/business-rules.md
@docs/context/architecture.md
@docs/context/patterns.md
@docs/context/glossary.md
@docs/constitution.md
@docs/STATUS.md

Otros documentos, léelos cuando corresponda:

- `docs/README.md` — mapa de toda la documentación.
- `docs/decisions.md` — decisiones técnicas tomadas y su justificación.
- `docs/CHANGELOG.md` — historial de cambios.
- `docs/specs/<id>-<slug>/spec.md` — qué debe hacer una funcionalidad.
- `docs/specs/<id>-<slug>/plan.md` — cómo se construye.
- `docs/specs/<id>-<slug>/tasks.md` — tareas atómicas y su estado.
- `docs/changes/` — propuestas de cambio sobre specs ya aprobadas.

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | React 18 + TypeScript + Vite |
| Backend | Python 3.11 + FastAPI + Pydantic v2 |
| Persistencia | PostgreSQL 16 + extensión `pgvector` |
| ORM / migraciones | SQLAlchemy 2.0 + Alembic |
| Embeddings | `sentence-transformers`, modelo multilingüe local |
| Tests | pytest (backend), Vitest + Testing Library (frontend) |
| Entorno | Docker Compose |

Todo el backend es **síncrono** (D-10): nada de `async def`, `asyncpg` ni
`pytest-asyncio`. La lista cerrada de dependencias está en
`docs/specs/001-validacion-semantica/plan.md`, sección 9b.

## Estructura del repositorio

```
backend/
  app/
    domain/          entidades y reglas puras (sin FastAPI, sin SQL)
    application/     casos de uso
    ports/           interfaces (typing.Protocol)
    adapters/
      api/           routers, schemas, manejo de errores
      persistence/   SQLAlchemy + pgvector
      embeddings/    proveedor real y proveedor falso
    config.py        configuración por variables de entorno
    main.py          raíz de composición: único módulo que importa adaptadores concretos
  migrations/        Alembic
  tests/
    dobles/          FakeEmbedder, RepositorioEnMemoria
    unit/            domain/ y application/, sin base de datos
    integration/     repositorio contra PostgreSQL real (marcador `integration`)
    api/             TestClient con dependencias sustituidas
frontend/
  src/
    api/             cliente HTTP y tipos
    components/
    hooks/
    estilos/         tokens.css
docs/
scripts/
docker-compose.yml
```

## Comandos

```bash
# Levantar todo
docker compose up --build

# Backend (dentro de backend/)
uvicorn app.main:app --reload
pytest -m "not slow and not integration"   # suite rápida, sin nada levantado
pytest -m integration                      # requiere: docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
pytest                                     # todo, incluido el modelo real
ruff check . && ruff format --check .
mypy app

# Frontend (dentro de frontend/)
npm run dev
npm run test
npm run build

# Migraciones
alembic upgrade head
alembic revision --autogenerate -m "mensaje"
```

## Cómo trabajamos

1. **Nada se implementa sin spec aprobada.** Si te piden código para algo que no
   está en una spec, detente y propón primero la spec o una propuesta de cambio
   en `docs/changes/`.
2. **Una tarea a la vez.** Trabaja únicamente sobre la tarea indicada de
   `tasks.md`. No adelantes trabajo de otras tareas.
3. **Tests primero.** Cada criterio de aceptación (AC) tiene un test que se
   escribe antes de la implementación y que debe fallar al inicio.
4. **Trazabilidad.** Cada test nombra el AC que cubre:
   `test_ac03_frase_vacia_devuelve_422`. Cada commit menciona la tarea: `(T05)`.
5. **Commits atómicos** en formato Conventional Commits, en español:
   `feat(validacion): calcular similitud coseno contra frases guardadas (T05)`.
   Tipos: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`, `ci`.
6. **Sin sorpresas.** No agregues dependencias, servicios ni capas que no estén
   en el plan (sección 9b). Si crees que falta algo, dilo y espera confirmación.
7. **Fin de sesión.** Al terminar, ejecuta `/handoff` para dejar actualizados
   `STATUS.md`, `decisions.md` y `CHANGELOG.md`.
8. **Los commits los confirma una persona.** `git commit` no está en la lista
   de permisos a propósito: cada commit pide confirmación, y así se revisa el
   mensaje y el alcance antes de que entre al historial.

## Límites explícitos

No implementes, aunque parezca útil: autenticación de usuarios, colas o workers
asíncronos, caché distribuido, multi-tenencia, WebSockets, Kubernetes,
microservicios separados. Están fuera de alcance por decisión registrada en
`docs/decisions.md`.
