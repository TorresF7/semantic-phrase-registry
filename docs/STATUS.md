# Estado actual

> Este archivo es el punto de entrada de cada sesión nueva. Se actualiza con
> `/handoff` al cerrar cada sesión. Si lo que dice aquí no coincide con el
> repositorio, gana el repositorio y hay que corregir este archivo.

**Última actualización:** 2026-09-21 — sesión 1 (bloque A: T-00 a T-04)

---

## Dónde estamos

Fase: **bloque A (base) completo; empieza el dominio.**

Repositorio con andamiaje, Docker Compose funcional, configuración por entorno
y esquema de base migrado. Todavía no hay código de dominio ni casos de uso.
Lint, tipos, `tsc` y la suite rápida (8 tests) están en verde.

## Hecho

- [x] Contexto, reglas de negocio, constitución, spec, plan y harness (sesión 0)
- [x] T-00 — Puntajes del modelo con seis pares reales (tabla abajo)
- [x] T-01 — Andamiaje: `pyproject.toml`, esqueleto de Vite, `.env.example`,
  `.gitignore`, `.gitattributes`, README inicial
- [x] T-02 — Compose con `db`, `backend` y `frontend` (nginx); `GET /api/v1/salud`
  provisional
- [x] T-03 — `app/config.py` con validación de rango del umbral (8 tests)
- [x] T-04 — Migración `0001` con pgvector e índice HNSW; el backend migra al
  arrancar

## En curso

Nada en curso. El árbol de trabajo está limpio.

## Siguiente

`T-05` — Dominio: normalización, vectores y política. Ver
`docs/specs/001-validacion-semantica/tasks.md`.

## Dudas abiertas

| # | Duda | Quién decide | Estado |
|---|---|---|---|
| Q-01 | Valor definitivo del umbral por defecto | Se resuelve con el script de calibración en T-11 | abierta |
| Q-02 | Si se despliega en un servidor público, ¿hace falta autenticación básica en el proxy? | Franklin | abierta |

## Notas para la siguiente sesión

- **Entorno local.** Las herramientas del backend están en `backend/.venv`:
  actívalo, o el hook de cierre solo avisa y omite ruff, mypy y pytest. En
  Windows, `pip` falla con rutas largas: por eso el entorno de T-00 quedó en
  `C:\t00\` (se puede borrar, o conservarlo para reutilizar el modelo en T-11).
- **Node local 24.14.** jsdom 30 pide 24.15 o superior. Funciona, pero npm
  avisa. La imagen usa `node:24-alpine`.
- `npm run test` sale con código 1 mientras no haya tests del frontend
  (llegan en T-14). No se añadió `--passWithNoTests` a propósito.
- La suite rápida es `pytest -m "not slow and not integration"`. El hook
  `Stop` no bloquea cuando el último commit es `test(...)`: es la fase roja
  declarada.
- **Tests que construyan `Configuracion`:** siempre con `_env_file=None` (D-14).
- `ruff` excluye `migrations/`. La plantilla `script.py.mako` ya genera
  migraciones con la sintaxis de tipos moderna.
- `docker compose up --build -d` deja todo en http://localhost:8080. El
  override publica 5432 para `alembic` y los tests desde el host. Un 502 justo
  después de recrear el backend es uvicorn arrancando, no un error.
- Pendientes menores:
  - `routers/salud.py` es provisional y no declara `response_model` ni
    `responses`. En T-12b sí es obligatorio: no tomarlo como plantilla.
  - Las imágenes base están fijadas por versión menor, no por digest. Si NF-07
    exige builds idénticos en el tiempo, fijarlas por digest.
  - **La base `banco_frases_test` no existe todavía.** Nadie la crea ni la
    migra; hace falta antes de los tests de integración (T-08/T-09).
  - `ResultadoValidacion.mas_parecida` es una `Frase` completa, como devuelven
    los puertos del plan §3, aunque la API solo expone `{id, texto}`. Si en
    T-07 o T-09 construirla obliga a rellenar campos con valores ficticios,
    valorar un tipo más pequeño (revisión de T-05).
  - `RepositorioEnMemoria.sembrar` fija `modelo="modelo-falso"` y
    `umbral_aplicado=0.80` en las frases sembradas. Ningún test lo relee hoy;
    si T-07 o T-08 afirman algo sobre los metadatos de una frase sembrada,
    que lo hagan de forma explícita (revisión de T-06).
  - **`mypy tests` no funciona en local**: `pytest` arrastra los stubs de
    numpy 2, que usan sintaxis de 3.12, y el proyecto apunta a 3.11. La
    conformidad de los dobles con los puertos se comprueba con
    `mypy app tests/dobles`, pero el hook de cierre solo ejecuta `mypy app`,
    así que no la vigila. Valorar si se amplía el hook o CI (T-16).
- Puntajes de T-00 (`paraphrase-multilingual-MiniLM-L12-v2`, CPU, texto
  normalizado según RN-02, vectores de norma 1):

  | Tipo | Frase A | Frase B | Coseno |
  |---|---|---|---|
  | Estrella | El pago fue rechazado por el banco | La entidad bancaria rechazó la transacción | 0.8735 |
  | Paráfrasis | El pedido llegará en tres días | Recibirás tu compra en un plazo de tres días | 0.8512 |
  | Paráfrasis | No pudimos procesar su solicitud | Su petición no se ha podido tramitar | 0.8465 |
  | Sin relación | El pago fue rechazado por el banco | Mañana lloverá en la costa | -0.0330 |
  | Sin relación | Actualiza tu contraseña cada tres meses | El restaurante abre a las ocho | 0.0125 |
  | Negación | El pago fue aprobado | El pago no fue aprobado | 0.6458 |

  El par estrella supera 0.80: el ejemplo de `product.md` y AC-04 se quedan
  como están, y en el README aparece como **87%**. El coseno negativo del
  primer par sin relación confirma que el recorte a [0, 1] de RN-05 hace falta.
  La negación queda en 0.65, bajo el umbral inicial: el margen entre ella y la
  paráfrasis más baja (0.85) es el dato a vigilar en la calibración de T-11.
  La carga del modelo tardó ~23 s en frío (NF-03: una sola vez por proceso).

---

## Cómo retomar

1. Lee este archivo.
2. Lee `docs/specs/001-validacion-semantica/tasks.md` y busca la primera tarea
   sin marcar.
3. Ejecuta `/implement T-XX` con esa tarea.
4. Al terminar la sesión, ejecuta `/handoff`.
