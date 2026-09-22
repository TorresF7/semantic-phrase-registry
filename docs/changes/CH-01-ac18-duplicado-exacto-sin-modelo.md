# CH-01 — AC-18: el duplicado exacto se valida aunque el modelo no haya cargado

**Fecha:** 2026-09-22
**Estado:** propuesta
**Afecta a:** spec 001, AC-18 y B-09 (redacción). Sin cambio en RN-15, RN-12 ni B-20.

## Qué se propone cambiar
Precisar la segunda cláusula de AC-18 y la fila B-09, que dicen que, con el
modelo sin cargar, "validar y guardar responden `503`". Ese `503` solo aparece
cuando la operación necesita generar un vector. Con un duplicado exacto hay
dos casos que no lo necesitan.

Redacción propuesta para AC-18, en lugar de su segunda cláusula:

> **Y** validar una frase que no es duplicado exacto responde `503` con código
> `SERVICIO_IA_NO_DISPONIBLE`, y guardarla también
> **Y** con un duplicado exacto, que no necesita el modelo (RN-04, RN-15, igual
> que en AC-13): validar responde `200`; guardar sin confirmar responde `409`
> (AC-10); y guardar confirmando responde `503`, porque hay que generar su
> vector (AC-11b, B-20)

Redacción propuesta para B-09:

> El proceso arranca igual. `/salud` responde degradado. Lo que necesita
> generar un vector responde `503`; un duplicado exacto se sigue validando
> (AC-18, B-20). El listado funciona

## Por qué
AC-18 contradice a la regla que dice cubrir. RN-15 dice: "La validación de un
duplicado exacto no necesita al proveedor (RN-04) y por eso responde con
normalidad aunque esté caído". B-20 lo repite para el caso del proveedor caído.
AC-18, leído al pie de la letra, exige `503` también para ese caso.

La revisión de T-12a lo detectó al encontrar el problema en el código: la
primera implementación seguía el plan §4, respondía `503` y rompía RN-15. Se
corrigió con D-21. Si AC-18 se queda como está, alguien que lo lea sin conocer
D-21 puede "corregir" el código de vuelta y romper RN-15, con los tests de
AC-18 en verde, porque estos solo prueban frases nuevas.

## Impacto
- **Reglas de negocio:** ninguna. RN-15 y RN-12 ya dicen lo correcto; el
  cambio alinea el criterio y el caso borde con ellas.
- **Criterios de aceptación y casos borde:** se modifica la redacción de la
  segunda cláusula de AC-18 y la de B-09. No se agrega ni se elimina ninguno.
- **Tareas:** ninguna reabierta. T-12a y T-12b ya implementan el comportamiento
  propuesto (D-21); los tests nuevos se añaden al aplicar este cambio.
- **Tests:**
  - Renombrar
    `test_b20_modelo_sin_cargar_validar_un_duplicado_exacto_sigue_respondiendo_200`
    (`backend/tests/api/test_disponibilidad_proveedor.py`) a
    `test_ac18_modelo_sin_cargar_validar_un_duplicado_exacto_responde_200`, para
    que el comportamiento quede trazado al AC (Artículo 4).
  - Añadir, con el modelo sin cargar (`cliente_con_arranque_degradado`), dos
    tests de guardado por HTTP de un duplicado exacto que hoy no existen:
    - `test_ac18_modelo_sin_cargar_guardar_duplicado_exacto_sin_confirmar_responde_409`
    - `test_ac18_modelo_sin_cargar_guardar_duplicado_exacto_confirmado_responde_503_y_no_persiste`

    El comportamiento ya existe (D-21) y ambos deberían pasar al escribirse.
    Fijan el contrato para que nadie lo "corrija" más adelante.
  - Ningún test existente cambia de aserción.

## Alternativas consideradas
- **No hacer nada.** D-21 ya documenta la excepción. Pero la spec es la fuente
  de verdad (Artículo 1) y quedaría contradiciendo a RN-15.
- **Cambiar RN-15 para que el modelo sin cargar dé siempre `503`.** Es más
  simple de explicar, pero peor para la persona usuaria: el duplicado exacto no
  depende del modelo, y rechazarlo no protege nada. Además obligaría a deshacer
  D-21.
- **Mover el caso a la tabla de casos borde como B-27.** B-20 ya lo cubre en
  parte. El problema no es que falte el caso: es que AC-18 lo contradice.
- **Remitir a AC-10 y AC-11b sin listar los tres desenlaces en AC-18.** Es más
  corto, pero es justo la omisión que causó el problema. Tres desenlaces
  explícitos, con referencia a los AC que los detallan, son verificables al
  leerlos.
- **Corregir B-09 en una propuesta aparte.** Tiene el mismo defecto, en la
  misma frase. Separarlo solo alarga el proceso.

## Decisión
Pendiente. La decisión es humana (ver el flujo en `README.md`).
