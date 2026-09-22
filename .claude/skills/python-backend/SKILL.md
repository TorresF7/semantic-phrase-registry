---
name: python-backend
description: Convenciones de Python, FastAPI, SQLAlchemy y arquitectura hexagonal de este proyecto. Se aplica al escribir o revisar cualquier código del backend.
---

# Convenciones del backend

## Regla de dependencias

```
adapters  →  application  →  domain
              ports  ←  adapters
```

- `domain/` importa solo la librería estándar y Pydantic. Nada más. Nunca
  FastAPI, nunca SQLAlchemy, nunca `sentence_transformers`, nunca `config`.
- `application/` importa `domain` y `ports`. Nunca `adapters` ni `config`: los
  valores de configuración que necesita (umbral, longitud máxima) le llegan
  por constructor como datos simples.
- `adapters/` importa lo que necesite, pero un adaptador no importa a otro.
- `main.py` es la **raíz de composición**: el único módulo que importa
  adaptadores concretos. Los cablea en el `lifespan` y los deja en `app.state`.
  `adapters/api/dependencias.py` los lee de ahí para `Depends`.

Si un test de `application` necesita una base de datos o descargar un modelo, la
capa está mal diseñada: falta un puerto.

## Todo síncrono

Puertos, casos de uso, repositorio y endpoints son `def`, nunca `async def`
(D-10). FastAPI ejecuta los endpoints `def` en un grupo de hilos. La sesión de
SQLAlchemy es la síncrona con `psycopg` 3. Si escribes `await`, algo va mal.

## Puertos

Se declaran con `typing.Protocol`, no con `ABC`. No hay herencia: un adaptador
es compatible por su forma. Las firmas completas y vigentes están en `plan.md`
§3; esto es solo la forma:

```python
from typing import Protocol

class ProveedorEmbeddings(Protocol):
    @property
    def nombre_modelo(self) -> str: ...
    @property
    def dimension(self) -> int: ...
    def generar(self, texto: str) -> list[float]: ...
```

## Tipado

- Anotaciones de tipo en todas las funciones públicas. `mypy` en modo estricto.
- Sintaxis moderna: `str | None`, `list[float]`, no `Optional` ni `List`.
- Nada de `Any` sin un comentario que lo justifique.

## Errores

Jerarquía propia en `domain/errores.py`:

```python
class ErrorDominio(Exception): ...
class FraseInvalida(ErrorDominio): ...          # → 422 FRASE_INVALIDA
class PosibleDuplicado(ErrorDominio): ...       # → 409 POSIBLE_DUPLICADO
class ErrorInfraestructura(Exception): ...
class ErrorProveedorEmbeddings(ErrorInfraestructura): ...  # → 503 SERVICIO_IA_NO_DISPONIBLE
class ErrorRepositorio(ErrorInfraestructura): ...          # → 503 BASE_DATOS_NO_DISPONIBLE
```

El dominio y la aplicación **lanzan excepciones de dominio**. Los adaptadores
traducen cualquier excepción de su librería a la de infraestructura que les
corresponde, en su frontera. Solo la capa HTTP traduce a códigos de estado, en
manejadores registrados con `app.exception_handler`. Ningún caso de uso
devuelve un `JSONResponse` ni conoce el número 409.

Para cumplir AC-14 hay que registrar también manejadores para
`RequestValidationError`, `StarletteHTTPException` y `Exception`: sin eso,
FastAPI responde `{"detail": ...}` en 422, 404 y 500.

Nunca uses `except Exception: pass`. Nunca dejes que una traza llegue al
cliente. El manejador de `Exception` registra la traza en el log y responde
`ERROR_INTERNO` con un mensaje genérico.

## FastAPI

- Un router por recurso, en `adapters/api/routers/`.
- Los schemas de entrada y salida viven en `adapters/api/schemas.py` y son
  distintos de las entidades del dominio. No se expone el modelo interno.
- Las dependencias se inyectan con `Depends`, apuntando a funciones que
  devuelven el adaptador configurado. Eso permite sustituirlas en los tests con
  `app.dependency_overrides`.
- Recursos costosos (el modelo) se cargan en el `lifespan` y viven en
  `app.state`. Nunca a nivel de módulo, nunca por petición. El `lifespan` pide
  el embedder a `app.state.fabrica_embedder`, que los tests reemplazan antes de
  crear el `TestClient`; así la suite rápida nunca carga el modelo real.
- Si el modelo no carga, se registra el error y `app.state.embedder` queda en
  `None`: el proceso arranca degradado (B-09). No se propaga la excepción.
- El import de `sentence_transformers` va dentro del constructor de
  `HuggingFaceEmbedder`, no en la cabecera del módulo.
- Cada endpoint declara `response_model`, `status_code` y `responses` con los
  códigos de error documentados.
- Los schemas de entrada no ponen `max_length=280`: la regla de longitud es del
  dominio y se mide sobre el texto normalizado. Solo un tope defensivo (2000).

## Configuración

`pydantic-settings`, una sola clase `Configuracion`, cacheada con
`functools.lru_cache`. Ningún `os.getenv` disperso por el código.

Todo valor configurable tiene validación de rango. Un umbral de 1.5 debe hacer
fallar el arranque, no producirse resultados raros en producción.

## SQLAlchemy

- Estilo 2.0: `select()`, `session.execute()`. Nada de `Query` heredada.
- Los modelos ORM viven en `adapters/persistence/modelos.py` y no salen de ahí.
  El repositorio traduce entre modelo ORM y entidad de dominio.
- La columna vectorial usa `Vector(384)` del paquete `pgvector.sqlalchemy`, y
  la consulta del vecino, su comparador `.cosine_distance()`. Si hiciera falta
  `text()`, el parámetro se convierte con `CAST(:v AS vector)`, nunca con
  `:v::vector`.
- Fechas siempre `TIMESTAMPTZ` en UTC, asignadas por la base (`server_default`).
  Nunca fechas ingenuas.
- Consultas parametrizadas siempre. Ningún f-string dentro de un `text()`.
- Todo error de `sqlalchemy.exc` se captura en el repositorio y se relanza
  como `ErrorRepositorio`.

## Nombres

- Código, funciones y variables en **español**, coherentes con el glosario:
  `puntaje`, `umbral`, `texto_normalizado`, `es_posible_duplicado`.
- Booleanos con prefijo `es_`, `tiene_`, `debe_`.
- Sin abreviaturas inventadas: `frase`, no `fr`.

## Formato

`ruff` para lint y formato, línea de 100 caracteres. Se ejecuta con el hook
después de cada edición: no hace falta pedirlo.

## Lo que no se hace

Sin patrón repositorio genérico con `TypeVar`. Sin fábrica abstracta. Sin
contenedor de inyección de dependencias. Sin capa de "servicios" además de los
casos de uso. Sin `utils.py` cajón de sastre.
