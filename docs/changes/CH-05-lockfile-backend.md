# CH-05 — Lockfile de las dependencias del backend

**Fecha:** 2026-09-23
**Estado:** propuesta
**Afecta a:** NF-07, plan §9 (entorno Docker) y §9b (dependencias),
`backend/Dockerfile`, `.github/workflows/ci.yml`, README, `decisions.md`
(decisión nueva que precisa D-25), `scripts/`. No afecta a reglas de negocio
ni a criterios de aceptación.

## Qué se propone cambiar

Fijar también las dependencias **transitivas** del backend, de ejecución y de
desarrollo, en un solo archivo versionado, `backend/requirements.lock`. Se usa
como restricción (`pip install -c`) al construir la imagen, en CI y en la
instalación local. Se genera con `pip freeze` en un contenedor Linux amd64
con Python 3.11, sin herramientas nuevas.

## Por qué

`pyproject.toml` fija con `==` las dependencias directas, pero no las que
estas arrastran: `transformers`, `tokenizers`, `huggingface-hub`, `numpy`,
`starlette`, `anyio`, `scikit-learn`… Cada `pip install` resuelve la última
versión compatible del día. Por eso dos `docker compose up --build` hechos en
fechas distintas pueden instalar versiones distintas, con dos riesgos:

- NF-07 podría dejar de cumplirse: `docker compose up` debe dejar la
  aplicación funcionando en una máquina limpia. Hoy se cumple, pero una
  versión nueva de una dependencia transitiva podría romper el arranque, por
  ejemplo al cargar el modelo, sin que haya cambiado ninguna línea del
  repositorio.
- Los puntajes pueden variar: la calibración del umbral (T-11, D-20) se hizo
  con unas versiones concretas de `transformers` y `tokenizers`, y los
  cambios de tokenización alteran el embedding.

Ya hay un indicio de esta deriva: la suite de pruebas avisa de dos
deprecaciones (`httpx` en `starlette.testclient` y `anyio.abc.BlockingPortal`)
que vienen de versiones de `starlette` y `anyio` que el repositorio no fija.
`httpx` es de desarrollo; por eso el lockfile cubre las dos listas. El
frontend no tiene el problema, porque `package-lock.json` está versionado y CI
usa `npm ci`.

## Impacto

- **Reglas de negocio afectadas:** ninguna.
- **Criterios de aceptación a agregar, modificar o eliminar:** ninguno.
- **Tareas afectadas.** Una tarea nueva al final del bloque G, la siguiente
  libre (T-26, o T-27 si CH-04 se aplica antes). La tarea hace esto:
  1. Añade `scripts/congelar_dependencias.sh`. El script ejecuta
     `docker run --platform linux/amd64 python:3.11-slim` con `backend/`
     montado. Dentro instala `torch` desde el índice de CPU, luego
     `pip install -e ".[dev]"`, y escribe
     `pip freeze --exclude-editable` en `backend/requirements.lock`.
     - La plataforma coincide con la de la imagen y la de CI (`ubuntu-latest`,
       amd64), también si se regenera desde un Mac con Apple Silicon.
     - No toca la etapa `dependencias` del Dockerfile, que no copia `app/` y
       no podría instalar `.[dev]`.
  2. Cambia `backend/Dockerfile`: `COPY pyproject.toml requirements.lock .`, y
     los dos `pip install` de la etapa `dependencias` llevan
     `-c requirements.lock`. La imagen solo instala lo de ejecución: las
     líneas de desarrollo del lockfile no la afectan, porque una restricción
     no obliga a instalar nada.
  3. Cambia el trabajo `backend` de CI y el de integración:
     - `pip install -c requirements.lock -e ".[dev]"`;
     - el `torch` con `-c requirements.lock` también;
     - `cache-dependency-path` con `backend/pyproject.toml` y
       `backend/requirements.lock`.
  4. Cambia la instalación local del README para usar los mismos
     `-c requirements.lock`. En Windows, pip puede instalar paquetes que en
     Linux no hacen falta, como `colorama`; quedan sin fijar, pero la
     restricción no falla por ellos.
  5. Añade a plan §9 y al README cuándo regenerarlo:
     - al cambiar cualquier versión en `pyproject.toml`;
     - cuando un paquete fijado deje de estar disponible (ver «Costo» abajo).

     Nunca se edita a mano.
  6. Añade a plan §9b que el lockfile existe y cómo se genera, y registra una
     decisión D-nn que **precisa D-25**: CI instala con el lockfile. D-25 no
     se edita, porque `decisions.md` solo admite añadir entradas.
- **Tests que hay que reescribir:** ninguno. La verificación de la tarea se
  hace el mismo día, y comprueba que las versiones dependen del lockfile:
  - dos construcciones de la imagen sin caché dan el mismo `pip freeze`, y
    coincide con las líneas de ejecución de `requirements.lock`;
  - se baja a mano en el lockfile la versión de una dependencia transitiva
    (por ejemplo `anyio`), se construye, y el `pip freeze` de la imagen
    muestra esa versión; después se revierte;
  - pasan las suites rápida, de integración y `slow`.

**A verificar en la tarea:**
- `torch` viene del índice de CPU con la versión local `+cpu`. `pip freeze`
  escribe `torch==2.14.0+cpu`, y el requisito de `pyproject.toml` es
  `torch==2.14.0`. PEP 440 dice que un `==` sin segmento local acepta el
  `+cpu`, pero la combinación de requisito y restricción no está probada con
  esta versión de pip. Si falla en una construcción limpia, se fija
  `torch==2.14.0+cpu` también en `pyproject.toml`.

**Costo que se acepta:** con versiones exactas, el riesgo cambia de forma.
Hoy es que se instale algo distinto. Con el lockfile, es que no se pueda
instalar nada si una versión fijada se retira del índice (yanked) o el índice
de CPU de PyTorch deja de publicar esa combinación. El fallo es inmediato y
evidente, y se arregla regenerando el lockfile con el script.

## Alternativas consideradas

### (a) `pip freeze` como archivo de restricciones (la que se propone)

- **A favor:**
  - no añade ninguna dependencia ni herramienta, así que plan §9b no cambia
    de lista;
  - el Dockerfile y CI siguen usando `pip`;
  - `-c` es un mecanismo estándar.
- **En contra:**
  - sin hashes: fija versiones, pero no protege contra un paquete
    sustituido en el índice;
  - la regeneración es un paso manual que alguien tiene que acordarse de
    hacer.

### (b) `pip-tools` (`pip-compile --generate-hashes`)

- **A favor:**
  - lockfile con hashes, generado desde `pyproject.toml`;
  - `pip-sync` deja el entorno exactamente igual al lockfile.
- **En contra:**
  - es una dependencia de desarrollo nueva, fuera de §9b;
  - `--generate-hashes` calcula los hashes de lo que resuelve, pero `torch`
    viene de otro índice: resolverlo en la misma pasada que el resto obliga a
    mezclar índices (`--extra-index-url`), y con eso pip puede tomar un
    paquete del índice equivocado.

### (c) `uv` (`uv lock` o `uv pip compile`)

- **A favor:**
  - es rápido y admite un índice por paquete (`[tool.uv.sources]`), lo que
    resuelve `torch` de forma declarativa;
  - un solo lockfile para todas las plataformas.
- **En contra:**
  - es una herramienta nueva que sustituye a `pip` en el Dockerfile, en CI y
    en las instrucciones del README;
  - es el cambio más grande de los tres, y cambia el flujo de trabajo local.

### No hacer nada

Se acepta que la imagen pueda cambiar sin que cambie el repositorio. Es
tolerable mientras el proyecto no se despliegue (T-19 sigue pendiente de
Q-02), pero deja NF-07 a merced de versiones publicadas por terceros. Además, un fallo de arranque causado por una
dependencia transitiva es difícil de diagnosticar: el historial de git no lo
muestra.

## Decisión

Pendiente. La decide Franklin (Q-09).
