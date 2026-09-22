# Estado actual

> Este archivo es el punto de entrada de cada sesión nueva. Se actualiza con
> `/handoff` al cerrar cada sesión. Si lo que dice aquí no coincide con el
> repositorio, gana el repositorio y hay que corregir este archivo.

**Última actualización:** 2026-09-21 — sesión 2 (bloque B: T-05 a T-08)

---

## Dónde estamos

Fase: **bloque B (dominio y casos de uso) completo; empiezan los adaptadores.**

El negocio completo está escrito y probado sin infraestructura: dominio,
puertos, dobles y los casos de uso `ValidarFrase` y `GuardarFrase`. Todavía no
hay repositorio PostgreSQL, adaptador de Hugging Face ni endpoints de frases.
Ruff, `mypy app tests/dobles` y la suite rápida (134 tests, <1 s) están en
verde.

## Hecho

- [x] Contexto, reglas de negocio, constitución, spec, plan y harness (sesión 0)
- [x] T-00 a T-04 — Bloque A: puntajes del modelo, andamiaje, Compose,
  configuración y migración inicial (sesión 1)
- [x] T-05 — Dominio: `normalizacion.py`, `politica.py`, `vectores.py`,
  `errores.py` y `entidades.py` (31 tests)
- [x] T-06 — Puertos `ProveedorEmbeddings` y `RepositorioFrases`; dobles
  `FakeEmbedder` y `RepositorioEnMemoria` (69 tests del contrato de los dobles)
- [x] T-07 — `ValidarFrase`: AC-03 a AC-08 y AC-17 (14 tests)
- [x] T-08 — `GuardarFrase`: AC-09 a AC-12b y la persistencia de AC-17 (12 tests)

## En curso

Nada en curso. El árbol de trabajo está limpio.

## Siguiente

`T-09` — Repositorio PostgreSQL con pgvector. Antes de escribir los tests de
integración hay que crear y migrar la base `banco_frases_test` (ver notas).
T-10 (adaptador de Hugging Face) no depende de T-09 y puede ir en paralelo.

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
- **mypy:** usar `mypy app tests/dobles`, que también comprueba que los dobles
  cumplen los puertos (D-17). `mypy tests` entero falla en local por los stubs
  de numpy 2 que arrastra `pytest`. El hook de cierre solo ejecuta `mypy app`:
  valorar ampliarlo en T-16.
- **Contratos ya fijados (D-18):** `ValidarFrase(repositorio, embedder, umbral,
  longitud_maxima).validar(texto)`, `GuardarFrase(...).guardar(texto,
  confirmar_duplicado)`, y `PosibleDuplicado.resultado` para los `detalles` del
  409. `buscar_por_texto_normalizado` recibe el texto **ya normalizado**: el
  adaptador PostgreSQL no debe normalizar.
- **Convención de los tests de aplicación:** para sembrar una frase se genera
  su vector con el mismo `FakeEmbedder` y después se hace
  `embedder.textos_recibidos.clear()`, para que el espía solo registre lo que
  hace el caso de uso.
- `ruff` excluye `migrations/`. La plantilla `script.py.mako` ya genera
  migraciones con la sintaxis de tipos moderna.
- `docker compose up --build -d` deja todo en http://localhost:8080. El
  override publica 5432 para `alembic` y los tests desde el host. Un 502 justo
  después de recrear el backend es uvicorn arrancando, no un error.
- Pendientes menores:
  - **La base `banco_frases_test` no existe todavía.** Nadie la crea ni la
    migra; es el primer paso de T-09.
  - `routers/salud.py` es provisional y no declara `response_model` ni
    `responses`. En T-12b sí es obligatorio: no tomarlo como plantilla.
  - Las imágenes base están fijadas por versión menor, no por digest. Si NF-07
    exige builds idénticos en el tiempo, fijarlas por digest.
  - `ResultadoValidacion.mas_parecida` es una `Frase` completa, como devuelven
    los puertos, aunque la API solo expone `{id, texto}`. En T-09 el
    repositorio ya lee la fila entera, así que no debería obligar a inventar
    campos; si lo hace, valorar un tipo más pequeño (revisión de T-05).
  - `RepositorioEnMemoria.sembrar` fija `modelo="modelo-falso"` y
    `umbral_aplicado=0.80`. Ningún test lo relee; si alguno llega a afirmar
    algo sobre los metadatos de una frase sembrada, que los fije de forma
    explícita (revisión de T-06).
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
