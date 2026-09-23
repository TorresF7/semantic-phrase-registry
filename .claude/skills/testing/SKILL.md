---
name: testing
description: Convenciones de pruebas de este proyecto: nomenclatura ligada a criterios de aceptación, dobles de prueba y niveles. Úsala al escribir o revisar cualquier test.
---

# Convenciones de pruebas

## Nomenclatura

Un test que cubre un criterio de aceptación lo nombra:

```python
def test_ac04_duplicado_semantico_sobre_umbral_devuelve_mas_parecida(): ...
def test_ac13_proveedor_caido_devuelve_503_y_no_persiste(): ...
```

El nombre dice **qué situación** y **qué se espera**, no qué función se llama.
`test_validar_frase` no dice nada.

Un criterio de aceptación sin un test que lo nombre está sin cubrir. Se puede
verificar con
`grep -rhoE "test_ac[0-9]+b?" backend/tests | sort -u`
contra la lista de AC de la spec: un AC que no aparece es un AC sin test.

Los tests que no cubren un AC (utilidades, regresiones) se nombran
descriptivamente, sin prefijo `ac`.

## Niveles

| Carpeta | Qué prueba | Dependencias | Velocidad |
|---|---|---|---|
| `tests/unit/domain/` | Funciones puras: normalizar texto y vectores, política de umbral, recorte | Ninguna | instantáneo |
| `tests/unit/application/` | Los casos de uso completos | `FakeEmbedder` y `RepositorioEnMemoria` | milisegundos |
| `tests/integration/`, marcados `integration` | Repositorio real, migración ida y vuelta, consulta vectorial | PostgreSQL con pgvector, base `banco_frases_test` | segundos |
| `tests/api/` | Los AC extremo a extremo por HTTP | `TestClient` con dependencias sustituidas | rápido |
| marcados `slow` | El modelo real de Hugging Face | Descarga el modelo | lento |
| `tests/dobles/` | Los dobles de prueba compartidos | — | — |

Los marcadores `slow` e `integration` se declaran en `pyproject.toml`
(`[tool.pytest.ini_options] markers`), o pytest los rechaza en modo estricto.

`pytest -m "not slow and not integration"` es la suite rápida: la que corre el
hook de cierre, la que corre en integración continua sin servicios, y la que se
ejecuta a cada rato. No necesita nada levantado y debe seguir siendo cuestión
de segundos. `pytest -m integration` necesita
`docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db`.

**Los tests de integración nunca tocan la base de desarrollo.** Leen
`TEST_DATABASE_URL`, que apunta a `banco_frases_test`, y truncan la tabla al
empezar cada test. Si la variable no está definida, el fixture de conexión
llama a `pytest.skip("Define TEST_DATABASE_URL")` en tiempo de ejecución. Es la
única forma de salto permitida: es por falta de entorno, no por un test que
estorba, y no usa el decorador `pytest.mark.skip`, que el hook de cierre
rechaza.

**`TestClient` y el `lifespan`.** Crear `TestClient(app)` ejecuta el `lifespan`
y cargaría el modelo. Los tests de API reemplazan `app.state.fabrica_embedder`
por una que devuelve el `FakeEmbedder` **antes** de crear el cliente, y
sustituyen el repositorio con `app.dependency_overrides`.

## Dobles de prueba

**`FakeEmbedder`**: determinista y sin dependencias pesadas. Dos modos:
1. Vector derivado de un hash del texto normalizado, para tests que no
   dependen del puntaje.
2. Puntajes preprogramados entre pares de frases, para fijar exactamente el
   valor que necesita el AC.

El segundo modo es lo que permite probar AC-04 con un puntaje de 0.89 exacto,
sin depender de lo que devuelva el modelo real ese día. Además cuenta sus
invocaciones (AC-03), puede configurarse para lanzar `ErrorProveedorEmbeddings`
(AC-13, AC-11b) y para devolver vectores **sin** normalizar (AC-17).

**`RepositorioEnMemoria`**: implementa `RepositorioFrases` con una lista. Debe
respetar el desempate por identificador menor en el vecino más cercano **y en
el duplicado exacto**, igual que las consultas SQL, o los tests de AC-06 no
prueban lo que creen probar. Puede configurarse para lanzar `ErrorRepositorio`
(AC-18).

**Umbrales en los tests.** Cada test que dependa del umbral lo pasa
explícitamente al caso de uso o a la configuración de prueba. Ningún test
afirma que el valor por defecto sea 0.80: ese valor cambia en T-11.

Los dobles implementan el mismo `Protocol` que los adaptadores reales. Si el
protocolo cambia, `mypy` hace fallar los dobles. Eso es deseado.

## Qué se prueba y qué no

**Sí:** comportamiento observable, contratos, casos borde de la spec, el camino
de error tanto como el feliz.

**No:** detalles de implementación. Un test no debe romperse porque renombraste
una variable privada o extrajiste una función. Si eso pasa, el test estaba
acoplado a la implementación.

**No se prueban** librerías de terceros. No verificamos que SQLAlchemy sabe
insertar.

## Reglas duras

- Un test nuevo debe **fallar** antes de la implementación. Si pasa desde el
  principio, no prueba nada.
- Nunca se marca un test como `skip` ni `xfail` para que la suite pase. Si un
  test estorba, o el código está mal o el test está mal, y ambos casos se
  arreglan, no se silencian.
- Nada de `time.sleep` en los tests.
- Cada test es independiente: no depende del orden ni del estado que dejó otro.
  Los tests de integración limpian la base o usan transacciones que se revierten.
- Un test, una aserción conceptual. Varias aserciones sobre el mismo hecho están
  bien; probar tres comportamientos distintos en un test, no.

## Frontend

Vitest + Testing Library. Se prueba lo que ve la persona, no el estado interno:
consultas por rol y por texto, nunca por clase CSS ni por `data-testid` salvo
que no haya alternativa. El cliente de API se sustituye con `vi.mock`; ningún
test del frontend hace peticiones reales.

Los tests de un AC lo nombran igual que en el backend:
`it("ac16: tras guardar como única muestra 'Frase guardada.' y vacía el campo")`,
`it("ac16b: editar el texto oculta el resultado y deshabilita Guardar")`.

Mínimo obligatorio, y **no se sacrifica** aunque falte tiempo: AC-16, AC-16b,
la transición a `posible_duplicado` tras validar, y que un `409` al guardar
vuelva a mostrar la alerta. Son los únicos tests que cubren AC-16 y AC-16b.
