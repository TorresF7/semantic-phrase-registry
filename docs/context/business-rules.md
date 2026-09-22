# Reglas de negocio

Fuente única de verdad del comportamiento. Toda spec, test y decisión de
implementación debe poder rastrearse hasta una de estas reglas.

Formato del identificador: `RN-nn`. Las reglas no se renumeran; si una regla
queda obsoleta se marca como DEROGADA y se conserva.

---

## Frase

**RN-01 — Definición.**
Una frase es un texto plano de entre 3 y 280 caracteres, una vez normalizado.
Fuera de ese rango, la frase es inválida. La longitud se mide **sobre el texto
normalizado**, en puntos de código Unicode, nunca sobre el texto tal como llegó.

**RN-02 — Normalización.**
Antes de cualquier comparación se calcula un *texto normalizado*, aplicando en
este orden: normalización Unicode NFKC, recorte al inicio y al final, colapso de
toda secuencia de espacios en blanco (espacios, tabulaciones, saltos de línea y
cualquier otro espacio Unicode) en un solo espacio, y conversión a minúsculas.
El *texto original* tal como lo escribió la persona se conserva y es el que se
muestra en la interfaz. El texto normalizado se usa para comparar y para generar
el embedding (RN-05); nunca se muestra.

**RN-03 — Frase vacía.**
Un texto que tras normalizar queda vacío o con menos de 3 caracteres se rechaza
con error de validación. No se genera embedding ni se consulta la base.

---

## Detección de duplicados

**RN-04 — Duplicado exacto.**
Si el texto normalizado de la frase nueva coincide exactamente con el de una
frase ya registrada, se considera duplicado con puntaje 1.0 y motivo `EXACTO`.
Esta comprobación se hace **antes** de generar el embedding, por ser más barata.

**RN-05 — Similitud semántica.**
Si no hay duplicado exacto, se genera el embedding **del texto normalizado** de
la frase nueva y se calcula la **similitud coseno** contra los embeddings de las
frases registradas. Embeber siempre el texto normalizado garantiza que dos
escrituras de la misma frase produzcan el mismo vector.
El coseno está matemáticamente en [-1, 1]. El puntaje se recorta al rango
[0, 1]: un valor negativo se trata como 0 y un exceso por redondeo de coma
flotante como 1. La comparación contra el umbral se hace con el puntaje sin
redondear; el redondeo es solo de presentación.

**RN-06 — Umbral configurable.**
Existe un umbral `SIMILARITY_THRESHOLD`, configurable por variable de entorno,
entre 0 y 1 inclusive; un valor fuera de ese rango impide el arranque. Su valor
por defecto es 0.75, fijado por la calibración con datos (D-07, D-20). Si el
puntaje más alto encontrado es **mayor o igual** al umbral, la frase se marca
como *posible duplicado*. El umbral aplicado
se registra junto con la validación.

**RN-07 — Frase más parecida.**
La validación devuelve la frase con mayor puntaje: su identificador, su texto
original y el puntaje obtenido.

**RN-08 — Desempate determinista.**
Si dos o más frases empatan en el puntaje más alto, gana la de identificador
menor, es decir, la registrada primero. Lo mismo aplica al duplicado exacto
(RN-04): si varias frases registradas comparten el texto normalizado, se
devuelve la de identificador menor. El resultado de validar dos veces la misma
frase sobre la misma base debe ser idéntico.

**RN-09 — Base vacía.**
Si no hay frases registradas, no existe frase más parecida. El puntaje es nulo y
la frase se considera única.

---

## Validación y guardado

**RN-10 — Validar no persiste.**
La operación de validación es de solo lectura. No crea ni modifica registros, ni
siquiera cuando la frase resulta única.

**RN-11 — El servidor revalida al guardar.**
La operación de guardado ejecuta de nuevo la validación completa. El resultado
que el cliente recibió antes no se acepta como prueba: entre la validación y el
guardado otra persona pudo registrar una frase parecida.

**RN-12 — Confirmación explícita.**
El guardado recibe un indicador `confirmar_duplicado` (falso por defecto).
- Si la revalidación **no** detecta posible duplicado: la frase se guarda con
  estado `UNICA`, sin importar el valor del indicador.
- Si detecta posible duplicado y el indicador es falso: la frase **no** se guarda
  y la API responde 409 con el detalle del duplicado encontrado.
- Si detecta posible duplicado y el indicador es verdadero: la frase se guarda
  con estado `DUPLICADO_CONFIRMADO`.

**RN-13 — Metadatos de la validación.**
Toda frase guardada registra: puntaje de similitud obtenido (nulo si la base
estaba vacía), identificador de la frase más parecida (nulo si no hubo),
estado, nombre del modelo utilizado (el valor exacto de `EMBEDDING_MODEL_NAME`),
umbral aplicado y fecha de creación en UTC, asignada por la base de datos.
Estos metadatos son inmutables: reflejan las condiciones del momento del
guardado, no las actuales.

**RN-14 — Persistencia del embedding.**
El embedding de cada frase se guarda junto a ella, **siempre**: también cuando la
frase se guarda como duplicado exacto confirmado, caso en el que la validación
no llegó a generarlo (RN-04) y se genera en el momento de guardar. Validar una
frase nueva nunca recalcula los embeddings de las frases existentes.

---

## Errores y disponibilidad

**RN-15 — Fallo del modelo.**
Si el proveedor de embeddings no está disponible o falla cuando hace falta, la
API responde 503 y la frase **no** se guarda. Nunca se persiste una frase sin
validar ni sin embedding. La validación de un duplicado exacto no necesita al
proveedor (RN-04) y por eso responde con normalidad aunque esté caído. Si la
base de datos no está disponible, la API responde también 503.

**RN-16 — Estructura de error uniforme.**
Toda respuesta de error usa la misma estructura: código interno legible, mensaje
para la persona usuaria y detalle opcional por campo. Las trazas internas nunca
se exponen al cliente.

---

## Consulta

**RN-17 — Listado paginado.**
El listado devuelve las frases ordenadas por fecha de creación descendente y,
ante fechas iguales, por identificador descendente, con paginación por
desplazamiento. Tamaño de página por defecto 20, mínimo 1, máximo 100. El
desplazamiento es mayor o igual a 0; si supera el total, la página llega vacía.
Cada elemento incluye su texto original, estado, puntaje y fecha.

---

## Retroalimentación al usuario

**RN-18 — Confirmación de guardado.**
Tras un guardado exitoso la interfaz muestra un mensaje de confirmación
explícito, distinto según el estado con el que quedó registrada la frase: única,
o duplicado confirmado. El campo se limpia y la frase nueva aparece en el
listado sin necesidad de recargar la página.

**RN-19 — Normalización de vectores.**
Todo embedding se normaliza a longitud 1 antes de persistirse y antes de
compararse. La similitud coseno no depende de la magnitud, de modo que
normalizar no cambia el puntaje; se hace para que todos los vectores guardados
sean homogéneos sin importar qué proveedor los generó, y para que coseno y
producto interno sean intercambiables (D-09). La normalización es una regla del
negocio y no se delega en el proveedor. Un vector de norma cero no se puede
normalizar y se trata como fallo del proveedor (RN-15).

---

## Trazabilidad

| Regla | Spec | Criterios de aceptación |
|---|---|---|
| RN-01, RN-02, RN-03 | 001 | AC-01, AC-02, AC-03 |
| RN-04 | 001 | AC-03 |
| RN-05, RN-06, RN-07 | 001 | AC-04, AC-05 |
| RN-08 | 001 | AC-06 |
| RN-09 | 001 | AC-07 |
| RN-10 | 001 | AC-08, AC-16b |
| RN-11, RN-12 | 001 | AC-09, AC-10, AC-11, AC-12b, AC-16b |
| RN-13, RN-14 | 001 | AC-11b, AC-12 |
| RN-15, RN-16 | 001 | AC-02b, AC-13, AC-14, AC-18 |
| RN-17 | 001 | AC-15 |
| RN-18 | 001 | AC-16 |
| RN-19 | 001 | AC-17 |
