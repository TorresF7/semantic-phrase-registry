# Banco de Frases

Registro de frases cortas que evita duplicados por significado, no solo por
coincidencia exacta de texto.

## Estructura

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
  migrations/        Alembic
  tests/
frontend/
  src/
    api/             cliente HTTP y tipos
    components/
    hooks/
    estilos/
docs/                producto, reglas de negocio, arquitectura, specs y decisiones
scripts/
```
