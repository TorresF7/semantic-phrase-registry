# CH-04 — Caracteres invisibles (`Cf`) en la normalización

**Fecha:** 2026-09-23
**Estado:** aplicada (a la spec; el código, en T-26)
**Afecta a:** RN-02 (o RN-01, según la alternativa), RN-04 (datos ya
guardados), spec 001 (AC-01, AC-03, B-05, B-28 y B-29 nuevos), plan §4 (docstring de
`normalizar`), glosario («Texto normalizado»), D-28 (réplica de la
normalización en el cliente), D-32. Las skills `ui-design` y `react-frontend`
no cambian: hablan del «texto normalizado» sin enumerar sus pasos

## Qué se propone cambiar

Eliminar los caracteres de formato Unicode (categoría `Cf`: U+200B, U+200D,
U+FEFF, U+00AD, los controles bidireccionales…) al calcular el texto
normalizado (RN-02). También en la réplica del cliente que mide la longitud
(D-28). El texto original se sigue guardando y mostrando tal como llegó.

## Por qué

D-32 rechaza los caracteres de control (`Cc`), pero los de formato (`Cf`) no
son espacio para `str.split()` ni los quita NFKC. Así que hoy llegan intactos
al texto normalizado. Lo comprobé con `normalizar_y_validar` sobre el código
actual (Unicode 15.1):

| Texto que llega | Texto normalizado hoy | Efecto |
|---|---|---|
| `"​​​"` | `"​​​"` | **Se acepta**: 3 caracteres ≥ mínimo. Se guarda una frase que en pantalla se ve vacía |
| `"El pago fue rechazado﻿"` | `"el pago fue rechazado﻿"` | No es duplicado exacto de «El pago fue rechazado» (RN-04). Solo lo detecta el embedding, y con puntaje menor que 1.0 |
| `"pago­rechazado"` | `"pago­rechazado"` | Un guion discreto, pegado desde un procesador de textos, cambia el texto normalizado |
| `"‮odazahcer ogap"` | igual | Un control bidireccional hace que el texto original se vea al revés en la tabla |

El primer caso va contra la intención de RN-01 y RN-03: la regla no dice
«con contenido», pero una frase que se ve vacía no es una frase. El segundo, la intención de RN-02: dos
escrituras de la misma frase deben dar el mismo texto normalizado. Estos
caracteres llegan sin querer al copiar desde el navegador, un PDF o una hoja
de cálculo; no hace falta un atacante.

La base de desarrollo no tiene ninguna frase con `Cf` (0 de 20).

## Impacto

- **Reglas de negocio afectadas.** RN-02 añade un paso tras NFKC: «eliminación
  de los caracteres de formato (categoría Unicode `Cf`)». El orden queda: NFKC,
  eliminación de `Cf`, recorte, colapso de espacios y minúsculas. RN-01 no
  cambia: la longitud ya se mide sobre el texto normalizado, así que
  `"​​​"` pasa a medir 0 y se rechaza por RN-03.
- **Criterios de aceptación.**
  - AC-01 añade un «Y»: un texto formado solo por caracteres `Cf`, o que tras
    quitarlos queda por debajo de 3, se rechaza con `422 FRASE_INVALIDA` y el
    mensaje de longitud mínima.
  - Casos borde nuevos **B-28** y **B-29**, y **B-05** se precisa:

    | # | Situación | Comportamiento esperado |
    |---|---|---|
    | B-28 | Texto con caracteres de formato (`Cf`: U+200B, U+200D, U+FEFF, U+00AD, U+202E…) | Se eliminan del texto normalizado. Se comparan, se miden y se embeben sin ellos. El texto original los conserva. Si tras quitarlos quedan menos de 3 caracteres, `422 FRASE_INVALIDA` (AC-01) |
    | B-29 | Cambian las reglas de normalización con frases ya guardadas | Las frases guardadas conservan el texto normalizado calculado al guardarlas; no se recalcula ni hay migración. El duplicado exacto (RN-04) compara contra ese texto. Igual que B-13 con el modelo |
    | B-05 (precisión) | Texto con emojis | Se sigue aceptando. Un emoji compuesto con U+200D (👨‍👩‍👧) llega al modelo como sus emojis sueltos (👨👩👧) |

- **Tareas afectadas.** Una tarea nueva al final del bloque G, la siguiente
  libre (T-26, o T-27 si CH-05 se aplica antes). Incluye:
  - `normalizacion.py` quita los `Cf` con `unicodedata.category(c) == "Cf"`.
  - `longitudNormalizada` en `FormularioFrase.tsx` añade
    `.replace(/\p{Cf}/gu, "")` tras `normalize("NFKC")`.
  - Actualizar la definición de «Texto normalizado» en el glosario y el
    docstring de `normalizar` en plan §3.
  - Una comprobación de datos, sin migración (B-29): una consulta SQL de una
    sola vez, anotada en la tarea, que cuenta las frases guardadas con algún
    `Cf` en `texto_original`. No es un script ni lleva test: solo informa de
    cuántas quedan con el normalizado antiguo.
- **Tests que hay que reescribir.** Ninguno: los actuales no usan `Cf`. Se
  añaden:
  - en `tests/unit/domain/test_normalizacion.py`, los cuatro casos de la tabla
    de «Por qué»;
  - en `tests/api/test_validacion_entrada.py`, un 422 con
    `"​​​"`;
  - en el caso de uso, un duplicado exacto entre `"El pago fue rechazado"` y
    la misma frase con U+FEFF;
  - en `App.test.tsx`, el contador marca 0 con `"​​​"` y el
    botón queda deshabilitado.

**Consecuencias que acepta esta alternativa:**
- Las frases ya guardadas con `Cf` no pasan a coincidir como duplicado exacto
  con su versión limpia (B-29). Siguen detectándose por el embedding. Hoy no
  hay ninguna en desarrollo; en otro entorno se sabría con la consulta de la
  tarea. Ninguna regla dice hoy qué pasa con el texto normalizado guardado
  cuando cambia la normalización: B-29 lo fija. RN-13 no lo cubre, porque no
  lo cuenta entre los metadatos de la validación.
- El texto original sigue mostrando los `Cf`, incluidos los controles
  bidireccionales. React los escapa, pero pueden alterar el orden visual. Si
  se quiere evitar, es la alternativa (b), o (a) + (b) solo para los
  bidireccionales.
- U+200D dentro de un emoji compuesto (👨‍👩‍👧) desaparece del texto
  normalizado. No se ve, porque el normalizado nunca se muestra, pero sí llega
  así al modelo (RN-05): la familia se embebe como tres personas sueltas y el
  puntaje de esa frase puede cambiar un poco (B-05). Si se quiere saber
  cuánto antes de decidir, se puede medir con el modelo real, como se hizo
  con el umbral (D-20). Es raro en frases de negocio.
- La réplica del cliente sigue siendo una aproximación (D-28): el navegador
  puede usar una versión de Unicode distinta de la de Python 3.11.

## Alternativas consideradas

### (a) Eliminarlos al normalizar (la que se propone)

La descrita arriba. Es coherente con cómo RN-02 trata los espacios: no se
rechazan, se normalizan. La persona no ve estos caracteres y no puede
corregirlos, así que rechazarle la frase por ellos sería un error
incomprensible («caracteres no permitidos» en un texto que se ve bien).

### (b) Rechazarlos con `422 FRASE_INVALIDA`

Como hizo D-32 con los `Cc`: RN-01 añade los `Cf` a los caracteres que hacen
inválida una frase, con el mensaje «La frase contiene caracteres no
permitidos.».
- **A favor:** el texto original nunca los contiene, lo que también resuelve
  el orden visual de los bidireccionales.
- **En contra:**
  - Rechaza frases que se ven perfectamente, sin que la persona pueda ver
    qué corregir.
  - Rechaza los emojis compuestos, que llevan U+200D, y las banderas de
    subdivisión, que llevan caracteres de etiqueta de categoría `Cf`.
  - Obliga a que el aviso del cliente (D-33) detecte y explique los `Cf`.

### (a) + (b) solo para los bidireccionales

Se eliminan todos los `Cf` del normalizado y, además, se rechazan los
controles bidireccionales (U+202A–U+202E, U+2066–U+2069, U+061C, U+200E,
U+200F), porque son los únicos que cambian cómo se ve el texto original.
Tiene más reglas que mantener, y a cambio cubre un riesgo que hoy es
teórico: la aplicación es interna y sin autenticación (fuera de alcance).

### No hacer nada

Se acepta que:
- una frase «vacía» a la vista se pueda guardar;
- dos escrituras de la misma frase que solo difieren en un `Cf` no sean
  duplicado exacto, aunque el embedding casi no cambie y lo más probable es
  que se detecten como posible duplicado semántico.

Es el menor costo, y deja RN-01 incumplida en el primer caso.

## Decisión

**Aceptada por Franklin el 2026-09-23: alternativa (a)**, eliminar los
caracteres `Cf` al normalizar. Queda registrada como **D-41**.

- **Emojis compuestos (Q-10):** no se mide antes con el modelo real cuánto
  cambia el puntaje de un emoji con U+200D. B-05 lo recoge.
- **Frases ya guardadas (Q-10):** se acepta B-29. Su texto normalizado no se
  recalcula nunca.
- **Aplicación a la documentación:** RN-02, AC-01, AC-03, B-05, B-28, B-29,
  plan §4, glosario, README y la tarea **T-26** en el bloque H nuevo.
