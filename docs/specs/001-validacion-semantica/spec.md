# Spec 001 — Validación semántica de frases

**Estado:** aprobada · **Fecha:** 2026-09-21
**Reglas de negocio cubiertas:** RN-01 a RN-19

Este documento describe **qué** debe hacer el sistema. El **cómo** está en
`plan.md`. Si algo aquí es ambiguo, se aclara antes de implementar.

---

## 1. Historias de usuario

**HU-01.** Como persona del equipo de negocio, quiero registrar una frase nueva
para que quede disponible en el repositorio compartido.

**HU-02.** Como persona del equipo de negocio, quiero que el sistema me avise
antes de guardar si ya existe una frase que significa lo mismo, aunque esté
redactada distinto, para no llenar el catálogo de repeticiones.

**HU-03.** Como persona del equipo de negocio, quiero decidir yo si guardo o no
una frase que el sistema marcó como parecida, porque a veces el matiz importa.

**HU-04.** Como persona del equipo de negocio, quiero ver las frases ya
registradas y saber cuáles se guardaron pese a una alerta.

---

## 2. Criterios de aceptación

Formato Dado / Cuando / Entonces. Cada uno debe tener al menos un test
automatizado cuyo nombre lo referencie: `test_ac04_...` en el backend,
`it("ac16: ...")` en el frontend. AC-16, AC-16b, AC-20 y AC-21 son de interfaz
y se prueban con Vitest; el resto, en el backend. La última cláusula de AC-19 se
prueba en integración, contra PostgreSQL.

Todos los puntajes y umbrales de estos criterios se fijan explícitamente en el
test. Ningún test depende del valor por defecto de `SIMILARITY_THRESHOLD`, que
puede cambiar tras la calibración (D-07).

---

### Validación de entrada

**AC-01 — Frase demasiado corta o vacía**
> **Dado** que el campo de frase contiene `"  "` o `"ab"`
> **Cuando** se solicita validar o guardar
> **Entonces** la API responde `422` con código `FRASE_INVALIDA` y el detalle
> indica el campo `texto`
> **Y** no se genera ningún embedding ni se consulta la base de datos

*Cubre RN-01, RN-03.*

**AC-02 — Frase demasiado larga**
> **Dado** que el texto normalizado de la frase tiene 281 caracteres
> **Cuando** se solicita validar o guardar
> **Entonces** la API responde `422` con código `FRASE_INVALIDA`
> **Y** el mensaje indica el máximo permitido
> **Y** un texto de 300 caracteres que tras normalizar queda en 250 **se acepta**:
> la longitud se mide sobre el texto normalizado

*Cubre RN-01, RN-02.*

**AC-02b — Cuerpo de la petición mal formado**
> **Dado** un cuerpo sin el campo `texto`, con `texto` que no es una cadena, o
> que no es JSON válido
> **Cuando** se solicita validar o guardar
> **Entonces** la API responde `422` con código `PARAMETROS_INVALIDOS` y la
> estructura uniforme de error
> **Y** al guardar con `confirmar_duplicado` que no es booleano, también `422`
> **Y** los campos desconocidos se ignoran: validar con un `confirmar_duplicado`
> de más responde `200`

*Cubre RN-16.*

---

### Detección

**AC-03 — Duplicado exacto ignorando mayúsculas y espacios**
> **Dado** que existe registrada la frase `"El pago fue rechazado"`
> **Cuando** se valida `"  el PAGO   fue rechazado "`
> **Entonces** la respuesta indica `es_posible_duplicado: true`, `puntaje: 1.0`,
> `motivo: "EXACTO"` y `mas_parecida` con el id y el texto original de la frase
> existente
> **Y** el proveedor de embeddings no fue invocado
> **Y** lo mismo ocurre al validar `"el pago\tfue\nrechazado"` y
> `"el pago fue rechazado"`: tabulaciones, saltos de línea y
> cualquier espacio Unicode (espacio duro, espacio de ancho fijo) cuentan como
> espacios

*Cubre RN-02, RN-04.*

**AC-04 — Duplicado semántico por encima del umbral**
> **Dado** que existe registrada la frase `"El pago fue rechazado por el banco"`
> **Y** que el umbral configurado es `0.80`
> **Cuando** se valida `"La entidad bancaria rechazó la transacción"` y la
> similitud calculada es `0.89`
> **Entonces** la respuesta indica `es_posible_duplicado: true`, `motivo: "SEMANTICO"`,
> `puntaje: 0.89` y `mas_parecida` con el id y el texto original de la frase existente
> **Y** devuelve el `umbral_aplicado: 0.80`

*Cubre RN-05, RN-06, RN-07.*

**AC-05 — Frase distinta por debajo del umbral**
> **Dado** que existen frases registradas
> **Y** que el umbral configurado es `0.80`
> **Cuando** se valida una frase cuya mayor similitud es `0.42`
> **Entonces** la respuesta indica `es_posible_duplicado: false`, `puntaje: 0.42`
> **Y** `mas_parecida` contiene igualmente la frase más cercana encontrada

*Cubre RN-05, RN-06, RN-07.*

**AC-06 — Empate resuelto de forma determinista**
> **Dado** que dos frases registradas producen exactamente el mismo puntaje
> **Cuando** se valida la frase nueva dos veces seguidas
> **Entonces** ambas respuestas señalan la misma frase: la de identificador menor
> **Y** si dos frases registradas comparten el mismo texto normalizado, el
> duplicado exacto señala también la de identificador menor

*Cubre RN-08.*

**AC-07 — Base de datos vacía**
> **Dado** que no hay ninguna frase registrada
> **Cuando** se valida cualquier frase válida
> **Entonces** la respuesta indica `es_posible_duplicado: false`, `puntaje: null`
> y `mas_parecida: null`

*Cubre RN-09.*

---

### Guardado

**AC-08 — Validar no persiste**
> **Dado** que la base tiene N frases
> **Cuando** se valida una frase, sea o no duplicada
> **Entonces** la base sigue teniendo N frases

*Cubre RN-10.*

**AC-09 — Guardado de frase única**
> **Dado** que la frase nueva no supera el umbral contra ninguna existente
> **Cuando** se solicita guardarla con `confirmar_duplicado: false`
> **Entonces** la API responde `201` con la frase creada en estado `UNICA`
> **Y** la frase aparece en el listado
> **Y** si se solicita guardar otra frase única con `confirmar_duplicado: true`,
> también queda en estado `UNICA`: el indicador no fuerza el estado, solo
> autoriza guardar cuando hay posible duplicado

*Cubre RN-11, RN-12.*

**AC-10 — Guardado bloqueado por posible duplicado**
> **Dado** que la frase nueva supera el umbral contra una existente
> **Cuando** se solicita guardarla con `confirmar_duplicado: false`
> **Entonces** la API responde `409` con código `POSIBLE_DUPLICADO` y el detalle
> de la frase más parecida y su puntaje
> **Y** la frase **no** queda registrada

*Cubre RN-11, RN-12.*

**AC-11 — Guardado confirmado pese a la alerta**
> **Dado** el mismo escenario anterior
> **Cuando** se solicita guardarla con `confirmar_duplicado: true`
> **Entonces** la API responde `201` y la frase queda en estado
> `DUPLICADO_CONFIRMADO`

*Cubre RN-12.*

**AC-11b — Duplicado exacto confirmado se guarda con su embedding**
> **Dado** que existe registrada la frase `"Hola mundo"`
> **Cuando** se solicita guardar `"hola mundo"` con `confirmar_duplicado: true`
> **Entonces** la API responde `201` con estado `DUPLICADO_CONFIRMADO` y
> `puntaje_similitud: 1.0`
> **Y** el registro nuevo tiene su embedding, generado al guardar porque la
> validación no lo necesitó
> **Y** si el proveedor de embeddings falla en ese momento, la API responde `503`
> y la frase no queda registrada

*Cubre RN-14, RN-15.*

**AC-12 — Metadatos persistidos**
> **Dado** un guardado exitoso
> **Cuando** se consulta el registro en la base
> **Entonces** contiene puntaje de similitud, identificador de la frase más
> parecida, estado, nombre del modelo, umbral aplicado, fecha de creación en UTC
> y el vector del embedding
> **Y** al cambiar después el umbral por variable de entorno, los metadatos del
> registro anterior **no** cambian

*Cubre RN-13, RN-14. Los metadatos escalares se prueban en el caso de uso con
el repositorio en memoria; la presencia del vector en la fila se prueba en
integración contra PostgreSQL, con SQL directo.*

**AC-12b — Revalidación del servidor con base modificada**
> **Dado** que se validó una frase y el resultado fue único
> **Y** que antes de guardarla se registró otra frase muy parecida
> **Cuando** se solicita guardar con `confirmar_duplicado: false`
> **Entonces** la API responde `409`, porque revalidó con el estado actual de la base

*Cubre RN-11.*

---

### Errores y disponibilidad

**AC-13 — Proveedor de embeddings caído**
> **Dado** que el proveedor de embeddings lanza una excepción
> **Cuando** se solicita validar o guardar una frase válida que no es duplicado
> exacto de ninguna registrada
> **Entonces** la API responde `503` con código `SERVICIO_IA_NO_DISPONIBLE`
> **Y** ninguna frase queda registrada
> **Y** la respuesta no contiene trazas internas ni nombres de clases
> **Y** validar un duplicado exacto sigue respondiendo `200`, porque no necesita
> al proveedor

*Cubre RN-15, RN-16.*

**AC-14 — Estructura uniforme de error**
> **Dado** cualquier error de la API (`404`, `405`, `409`, `422`, `500`, `503`)
> **Cuando** el cliente recibe la respuesta
> **Entonces** el cuerpo tiene siempre la misma forma: `codigo`, `mensaje` y
> `detalles` opcional
> **Y** el `500` se provoca en el test con un repositorio doble que lanza una
> excepción genérica (`RuntimeError`), y su cuerpo no contiene el texto de esa
> excepción
> **Y** esto incluye los errores que el framework genera por su cuenta (ruta
> inexistente, método no permitido, cuerpo mal formado)

*Cubre RN-16.*

**AC-18 — Salud y degradación controlada**
> **Dado** que el modelo de embeddings no pudo cargarse al arrancar
> **Cuando** se consulta `GET /api/v1/salud`
> **Entonces** responde `503` con `estado: "degradado"` y `modelo_cargado: false`
> **Y** validar una frase que no es duplicado exacto responde `503` con código
> `SERVICIO_IA_NO_DISPONIBLE`, y guardarla también
> **Y** con un duplicado exacto, que no necesita el modelo (RN-04, RN-15, igual
> que en AC-13): validar responde `200`; guardar sin confirmar responde `409`
> (AC-10); y guardar confirmando responde `503`, porque hay que generar su
> vector (AC-11b, B-20)
> **Y** el listado sigue respondiendo `200`, porque no necesita el modelo
> **Y** con el modelo cargado y la base disponible, `/salud` responde `200` con
> `estado: "ok"`
> **Y** con la base de datos caída, validar, guardar y listar responden `503`
> con código `BASE_DATOS_NO_DISPONIBLE`

*Cubre RN-15, RN-16. Segunda cláusula precisada por CH-01 (2026-09-22). El
cuerpo de `/salud` es un informe de estado, no un error:
es la única respuesta no exitosa que no usa la estructura de AC-14.*

---

### Consulta

**AC-15 — Listado paginado y ordenado**
> **Dado** que hay 25 frases registradas
> **Cuando** se consulta el listado sin parámetros
> **Entonces** devuelve 20 elementos ordenados por fecha de creación
> descendente y, a igual fecha, por identificador descendente, junto con el total
> **Y** al pedir `limite=100&desplazamiento=20` devuelve las 5 restantes
> **Y** al pedir `desplazamiento=1000` devuelve `200` con la lista vacía y el total
> **Y** al pedir `limite=500`, `limite=0` o `desplazamiento=-1` responde `422`
> con código `PARAMETROS_INVALIDOS`
> **Y** ninguna frase aparece en dos páginas ni falta en todas, aunque varias
> compartan la misma fecha de creación

*Cubre RN-17.*

**AC-19 — El listado incluye la frase más parecida**
> **Dado** que existe «Compré un auto» con id 4
> **Y** que «Compré un carro» se guardó como duplicado confirmado con
> `id_mas_parecida = 4`
> **Cuando** se consulta el listado
> **Entonces** el elemento de «Compré un carro» incluye
> `mas_parecida: { id: 4, texto: "Compré un auto" }`
> **Y** el elemento de la primera frase registrada incluye `mas_parecida: null`
> **Y** el número de sentencias SQL que ejecuta el listado es el mismo con una
> frase que con veinte

*Cubre RN-17. La última cláusula se prueba en integración contando las
sentencias con el evento `before_cursor_execute` de SQLAlchemy. Agregado por
CH-02 (2026-09-22).*

---

### Retroalimentación

**AC-16 — Confirmación tras guardar**
> **Dado** que se guardó una frase correctamente
> **Cuando** la interfaz recibe el `201`
> **Entonces** muestra un mensaje de confirmación que distingue si quedó como
> única o como duplicado confirmado
> **Y** el campo de texto queda vacío
> **Y** el listado vuelve a la primera página y la frase nueva aparece en él sin
> recargar la página

*Cubre RN-18.*

**AC-16b — El resultado de validación caduca al editar**
> **Dado** que se validó una frase y hay un resultado en pantalla
> **Cuando** la persona modifica el texto del campo
> **Entonces** el resultado desaparece y el botón principal vuelve a
> "Comprobar similitud": no se puede guardar hasta validar de nuevo
> **Y** al presionar **Editar frase** en el veredicto de duplicado, el
> veredicto desaparece, el texto escrito **se conserva** para poder corregirlo
> y el foco vuelve al campo

*Cubre RN-10, RN-12 (la decisión de confirmar se toma sobre el texto validado).
Modificado por CH-02 (2026-09-22): "Cancelar" pasa a llamarse "Editar frase".*

**AC-20 — Estados de la lista en la interfaz**
> **Dado** que el listado está cargando
> **Entonces** se muestran filas de esqueleto con las mismas columnas que una
> fila real y el cuerpo de la tabla tiene `aria-busy="true"`
>
> **Dado** que el listado respondió con cero frases
> **Entonces** se muestra el estado vacío con una indicación de qué hacer
>
> **Dado** que el listado falló
> **Entonces** se muestra un mensaje de error con un botón "Reintentar" que
> vuelve a pedir la lista
>
> **Dado** que el total es menor o igual que el tamaño de página
> **Entonces** no se muestran controles de paginación

*Cubre RN-18 en su parte de interfaz. Se verifica con Vitest. Agregado por
CH-02 (2026-09-22).*

**AC-21 — Conflicto al guardar**
> **Dado** que se validó una frase y el resultado fue única
> **Y** que entre la validación y el guardado otra persona registró una frase parecida
> **Cuando** se presiona Guardar y el servidor responde `409`
> **Entonces** la interfaz pasa al estado `conflicto`, distinto de `posible_duplicado`: explica que la base cambió mientras la persona revisaba y que la frase no se guardó
> **Y** muestra la frase encontrada y su porcentaje, con las acciones Editar frase y Guardar de todos modos
> **Y** Guardar de todos modos envía `confirmar_duplicado: true` y, si el servidor acepta, la frase queda como duplicado confirmado

*Cubre RN-11, RN-12 en la interfaz (AC-12b cubre el lado del servidor). Introducido por la adenda de CH-02.*

---

### Vectores

**AC-17 — Vectores normalizados**
> **Dado** un proveedor de embeddings que devuelve un vector sin normalizar, por
> ejemplo de norma 5
> **Cuando** se valida o se guarda una frase
> **Entonces** el vector que se compara y el que se persiste tienen norma 1, con
> una tolerancia de 1e-6
> **Y** un vector de norma cero se trata como fallo del proveedor (`503`)

*Cubre RN-19. Se prueba con el embedder falso: la normalización es del negocio,
no del proveedor.*

---

## 3. Casos borde acordados

| # | Situación | Comportamiento esperado |
|---|---|---|
| B-01 | Base de datos vacía | AC-07: puntaje nulo, frase única |
| B-02 | Una sola frase registrada, idéntica a la nueva | Duplicado exacto, puntaje 1.0 |
| B-03 | Empate de puntaje entre dos frases | Gana la de id menor (AC-06) |
| B-04 | Texto solo con espacios o saltos de línea | `422` (AC-01) |
| B-05 | Texto con emojis o caracteres no latinos | Se acepta; NFKC no los elimina; el modelo los procesa |
| B-06 | Texto de exactamente 280 caracteres | Se acepta. 281, se rechaza |
| B-07 | Texto de exactamente 3 caracteres | Se acepta. 2, se rechaza |
| B-08 | Puntaje exactamente igual al umbral | Es posible duplicado. La comparación es `>=` |
| B-09 | El modelo no pudo cargarse al arrancar | El proceso arranca igual. `/salud` responde degradado. Lo que necesita generar un vector responde `503`; un duplicado exacto se sigue validando (AC-18, B-20). El listado funciona |
| B-10 | Dos peticiones simultáneas con la misma frase | Ambas revalidan (RN-11). La segunda verá la primera si ya se confirmó la transacción; si no, pueden quedar dos frases idénticas en estado `UNICA`. No se exige bloqueo distribuido. El desempate de RN-08 mantiene determinista la validación posterior |
| B-11 | Frase con distinta acentuación (`"telefono"` vs `"teléfono"`) | No son duplicado exacto. El modelo decide la similitud semántica |
| B-12 | Se cambia `SIMILARITY_THRESHOLD` y se reinicia | Aplica a las validaciones nuevas. Los metadatos históricos no se recalculan (AC-12) |
| B-13 | Se cambia `EMBEDDING_MODEL_NAME` cuando ya hay frases guardadas | No soportado: los vectores de modelos distintos no son comparables y los puntajes dejarían de tener sentido. Se advierte en el README junto a la variable. El campo `modelo` por frase permite detectarlo; el re-embebido masivo está fuera de alcance |
| B-14 | `EMBEDDING_DIMENSION` no coincide con la dimensión real del modelo cargado | El arranque falla con un mensaje claro. No se llega a insertar nada |
| B-15 | Puntaje negativo, o mayor que 1 por redondeo de coma flotante | Se recorta a [0, 1] (RN-05) |
| B-16 | Puntaje que redondeado alcanza el umbral pero sin redondear no (0.79996 con umbral 0.80) | No es posible duplicado. Se compara sin redondear |
| B-17 | Texto con tabulaciones, saltos de línea o espacios Unicode (U+00A0, U+2003) internos | Cuentan como espacios y se colapsan (AC-03). `str.split()` sin argumentos ya separa por todo espacio Unicode |
| B-18 | Varias frases registradas con el mismo texto normalizado | El duplicado exacto devuelve la de identificador menor (AC-06) |
| B-19 | Se confirma un duplicado exacto | Se genera el embedding al guardar (AC-11b) |
| B-20 | Proveedor caído y la frase es duplicado exacto | Validar responde `200`. Guardar con confirmación responde `503` |
| B-21 | Base de datos caída | `503` con `BASE_DATOS_NO_DISPONIBLE` (AC-18) |
| B-22 | `desplazamiento` mayor que el total | `200` con lista vacía (AC-15) |
| B-23 | Proveedor de embeddings lento | No aplica: el modelo es local y no hay llamada de red. Sin tiempo límite propio |
| B-24 | `SIMILARITY_THRESHOLD` fuera de [0, 1], o no numérico | El arranque falla con un mensaje claro, igual que B-14. No se recorta ni se sustituye por el valor por defecto |
| B-25 | Frase única guardada con `confirmar_duplicado: true` | Queda en `UNICA`. El indicador no fuerza el estado (AC-09) |
| B-26 | Campos desconocidos en el cuerpo | Se ignoran (AC-02b) |

---

## 4. Fuera de alcance de esta spec

Autenticación, edición y borrado de frases, búsqueda por texto libre,
categorías, exportación, notificaciones, re-embebido masivo al cambiar de
modelo, y devolución de un top-N de frases parecidas (se devuelve solo la más
parecida).

---

## 5. Definition of Ready

Esta spec está lista porque:

- [x] Las reglas de negocio están numeradas y son la fuente única de verdad.
- [x] Cada criterio de aceptación está en formato Dado/Cuando/Entonces y es
      verificable con un test automatizado.
- [x] Los casos borde están enumerados y decididos, no pendientes.
- [x] El contrato de la API está definido en `plan.md`, incluidos los errores.
- [x] Existe una sección de "fuera de alcance" explícita.
- [x] Los requisitos no funcionales tienen objetivos medibles en `product.md`.
- [x] Fue revisada y aprobada por una persona.

## 6. Definition of Done de la funcionalidad

- [ ] Todos los AC tienen al menos un test que los referencia por nombre y pasa.
- [ ] `ruff`, `mypy` y `pytest` en verde; `tsc` y `vitest` en verde.
- [ ] El flujo completo funciona desde la interfaz con `docker compose up`.
- [ ] El README documenta instalación, variables de entorno, arquitectura y
      decisiones.
- [ ] El historial de commits refleja spec → tests → implementación.
- [ ] Ningún hallazgo bloqueante del subagente `code-reviewer`.
