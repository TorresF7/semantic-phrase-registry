# CH-02 — Rediseño de la interfaz en una sola pantalla

**Fecha:** 2026-09-22
**Estado:** aplicada
**Afecta a:** RN-17, spec 001 (AC-16b modificado; AC-19 y AC-20 nuevos),
`plan.md` §1.3, §3 y §5, skill `ui-design` (v2) y skill `react-frontend`,
tareas nuevas T-20 a T-24.

**Referencia visual aprobada:** `docs/design/prototipo.html`. Ábrelo en el
navegador; el selector de la esquina inferior derecha recorre todos los estados.

> El prototipo **simula** la comparación con una heurística de palabras para
> poder navegarlo sin backend. Esa heurística **no se porta** al proyecto: la
> comparación real sigue siendo la del backend (embeddings + coseno). Del
> prototipo se toma solo la estructura visual, los textos y el comportamiento
> de la interfaz.

---

## Qué se propone cambiar

1. **Contrato de `GET /frases`.** Cada elemento incluye también la frase más
   parecida en el momento del registro: `mas_parecida: { id, texto } | null`.
   Es el único cambio de backend.
2. **Interfaz.** Pasa a una sola pantalla: barra superior mínima, registro en
   línea con el veredicto debajo del campo, y tabla de frases debajo. Sin
   modales ni paneles laterales.
3. **Estados de la lista.** Esqueleto de carga, lista vacía, error al cargar y
   paginación que solo aparece con más de una página.
4. **Textos y jerarquía de acciones.** Ante un posible duplicado la acción
   destacada es "Editar frase" y la secundaria "Guardar de todos modos".
   "Cancelar" desaparece como botón: "Editar frase" cumple su función
   (vuelve a `inactivo` conservando el texto y devuelve el foco al campo).
5. **Diseño adaptable.** Una sola maqueta que funciona de 360 px a 1080 px sin
   desplazamiento horizontal. Hasta 720 px el botón principal baja bajo el
   campo, el veredicto pasa a una columna y la tabla se convierte en fichas.
   La skill `ui-design` v2 fija los puntos de corte; T-24 lo verifica.

## Por qué

- La versión anterior dejaba un hueco reservado para la alerta que empujaba la
  lista fuera de la primera pantalla.
- Validar y Guardar tenían el mismo peso y uno aparecía deshabilitado sin
  explicación al lado: parecía un error. Ahora hay un solo botón principal que
  avanza por pasos y, cuando queda deshabilitado, el veredicto junto a él
  explica por qué y ofrece las acciones.
- La lista no explicaba los duplicados: se leía "Duplicado confirmado" sin
  saber a qué frase ni con cuánta similitud. Para mostrarlo hace falta el texto
  de la frase parecida, y hoy el contrato solo devuelve su id.
- La lista no tenía estados de carga, vacío ni error.
- La estética anterior se percibía genérica. La nueva sigue las convenciones de
  herramientas internas empresariales: tabla densa, bordes de 1 px, radios
  pequeños, sin sombras y un solo color de acento.

## Impacto

### Reglas de negocio

**RN-17 — Listado paginado** se amplía. El texto vigente se conserva entero y
se le añade al final esta oración:

> Cada elemento incluye además, si existe, la frase que resultó más parecida
> al registrarla: su identificador y su texto original.

No se crean reglas nuevas: los estados de la lista son comportamiento de
interfaz, no de negocio. En la tabla de trazabilidad, RN-17 pasa a cubrir
AC-15 y AC-19; RN-18 pasa a cubrir AC-16 y AC-20.

### Contrato — `plan.md` §1.3

Cada elemento de `items` pasa a ser:

```json
{
  "id": 10,
  "texto": "Compré un carro",
  "estado": "DUPLICADO_CONFIRMADO",
  "puntaje_similitud": 0.95,
  "mas_parecida": { "id": 4, "texto": "Compré un auto" },
  "creada_en": "2026-09-22T19:45:00Z"
}
```

`mas_parecida` es `null` cuando `id_mas_parecida` es nulo (base vacía al
registrar, RN-09).

**Implementación esperada:** un `LEFT JOIN` de la tabla consigo misma en el
repositorio, en la misma consulta que trae la página. El número de consultas
del listado no depende del número de filas: siguen siendo las dos de hoy (la
página y el `COUNT`). Nada de consultas por fila (N+1). No hace falta
migración: la columna `id_mas_parecida` ya existe.

### Puertos y dominio — `plan.md` §3

El texto de la frase parecida tiene que llegar desde el repositorio hasta el
schema sin que los modelos ORM salgan de `adapters/persistence/`. Cambian:

- `domain/entidades.py`: un modelo de lectura `FraseListada`, con los campos
  de `Frase` más `texto_mas_parecida: str | None`. `Frase` y `FraseNueva` no
  cambian, así que `ValidarFrase` y `GuardarFrase` tampoco.
- `ports/repositorio.py`: `listar` pasa a devolver
  `tuple[list[FraseListada], int]`.
- `adapters/persistence/repositorio.py`: `listar` con el `LEFT JOIN`.
- `tests/dobles/repositorio_en_memoria.py`: `listar` resuelve el texto en
  la lista en memoria.
- `adapters/api/schemas.py`: `mas_parecida` en el elemento del listado.

### Criterios de aceptación

AC-01 a AC-18 (con sus variantes `b`) ya existen. Se **modifica** AC-16b y se
**agregan** AC-19 y AC-20.

**AC-16b — El resultado de validación caduca al editar** (texto nuevo)
> **Dado** que se validó una frase y hay un resultado en pantalla
> **Cuando** la persona modifica el texto del campo
> **Entonces** el resultado desaparece y el botón principal vuelve a
> "Comprobar similitud": no se puede guardar hasta validar de nuevo
> **Y** al presionar **Editar frase** en el veredicto de duplicado, el
> veredicto desaparece, el texto escrito **se conserva** para poder corregirlo
> y el foco vuelve al campo

*Cubre RN-10, RN-12 (la decisión de confirmar se toma sobre el texto validado).
Modificado por CH-02 (2026-09-22): "Cancelar" pasa a llamarse "Editar frase".*

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
sentencias con el evento `before_cursor_execute` de SQLAlchemy.*

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

*Cubre RN-18 en su parte de interfaz. Se verifica con Vitest.*

### Plan — `plan.md` §5 (frontend)

La máquina de estados del registro queda así:

`inactivo` → `validando` → (`unica` | `posible_duplicado` | `error`)
→ `guardando` → (`guardada` | `conflicto` | `error`)

- `conflicto` es el 409 del guardado. Se muestra distinto de
  `posible_duplicado`: explica que la base cambió mientras la persona revisaba.
  Sustituye a la fila "`guardando` + `409` → `posible_duplicado`" de la tabla
  de transiciones.
- `error` muestra el mensaje que trae la respuesta de la API (`422`, `503`),
  como hoy (D-24). Solo con `SIN_CONEXION` o `RESPUESTA_INESPERADA` se usa el
  texto fijo "El servicio no responde. La frase no se guardó; reintenta en
  unos segundos." "Reintentar" repite la última operación, como hoy.
- Cualquier edición del texto vuelve a `inactivo`: el veredicto anterior
  correspondía a otro texto.
- "Editar frase" reemplaza a "Cancelar" en la tabla de transiciones, con el
  mismo destino: `inactivo` conservando el texto.
- Tras `guardada`, el campo se limpia y **el foco vuelve a él**.
- En `unica` **sí** se muestra la frase más cercana y su porcentaje, al
  contrario de lo que dice hoy §5. Con el medidor y la marca del umbral la
  cifra deja de ser un número suelto: la persona ve cuánto falta para que se
  considere duplicado. Si la base estaba vacía se muestra "Es la primera frase
  del catálogo."

Se añade una segunda máquina de estados para la lista:
`cargando` → (`ok` | `vacia` | `error`). Cambiar de página vuelve a `cargando`.

Reglas de diseño adaptable (se añaden a "Reglas de interfaz" de §5):
- Un solo punto de corte, **720 px**, definido en la skill `ui-design`. Por
  encima: campo y botón en una fila, veredicto en dos columnas, tabla de cinco
  columnas. Por debajo: botón bajo el campo a ancho completo, veredicto en una
  columna, tabla en fichas con los encabezados ocultos pero accesibles.
- Entre 360 px y 1080 px nunca hay desplazamiento horizontal. Ningún texto se
  trunca con puntos suspensivos: las frases se parten en varias líneas.
- Los objetivos táctiles miden al menos 44 px de alto, también en las fichas.
- No hay modo oscuro ni versión de escritorio distinta: es la misma maqueta.

Lo que **no** cambia: el botón principal se deshabilita mientras no exista un
resultado para el texto actual; `unica` guarda con `confirmar_duplicado:
false` y "Guardar de todos modos" con `true`; tras guardar, el listado vuelve a
la primera página; el contador cuenta puntos de código.

### Dependencias

Ninguna nueva. Las fuentes son las del sistema (`ui-sans-serif, system-ui,
…`), como hoy. `plan.md` §9b no cambia.

### Tareas

Se agregan al final de `tasks.md`, en un bloque nuevo:

**Bloque G — Rediseño (CH-02)**

| Tarea | Tamaño | Contenido | Depende de |
|---|---|---|---|
| **T-20** Contrato del listado | S | `FraseListada`, `listar` en el puerto y en el doble, `LEFT JOIN` en el repositorio y `mas_parecida` en el schema. Test primero: `test_ac19_*`, incluido el conteo de sentencias en integración | T-12b |
| **T-21** Tokens y estructura | S | Reemplazar `tokens.css` por los de la skill `ui-design` v2. Barra superior y contenedor de una columna | T-13b |
| **T-22** Registro en línea | L | Campo, botón que avanza por pasos, veredicto (par de frases + medidor), `conflicto`, error, confirmación, foco tras guardar. Tests de Vitest para la transición a `posible_duplicado`, el `conflicto`, AC-16 y el AC-16b modificado | T-21 |
| **T-23** Tabla y estados de la lista | M | Columnas, etiquetas, micro-medidor, enlace a la más parecida, esqueleto, vacío, error, paginación condicional y fichas en móvil. `test_ac20_*` | T-20, T-21 |
| **T-24** Revisión visual y accesibilidad | S | Lista de verificación de la skill `ui-design`; contrastes; teclado; 390 px sin desplazamiento horizontal; `code-reviewer` sobre el bloque | T-22, T-23 |

### Tests que hay que reescribir

- Los tests de frontend que buscaban el botón "Cancelar" pasan a buscar
  "Editar frase" (`App.test.tsx`, `ac16b`).
- Los tests que dependían de la tarjeta de lista anterior se reemplazan por los
  de T-23.
- **El único test existente que cambia es
  `test_ac15_item_del_listado_conserva_el_texto_original_sin_normalizar`**, que
  comprueba el conjunto exacto de claves del elemento y pasa a incluir
  `mas_parecida`; su intención (no filtrar campos internos) no cambia. `Frase`
  no cambia y el resto de tests del listado comparan campos, no la clase. Se
  agregan los de AC-19.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| No hacer nada | La lista no explicaba los duplicados y la pantalla desperdiciaba espacio |
| Panel lateral o modal para registrar | Oculta la lista mientras se escribe; se prefirió una sola pantalla |
| Dos columnas fijas (registro a la izquierda, lista a la derecha) | En pantallas medianas la tabla queda demasiado estrecha para cinco columnas |
| Plantilla administrativa comercial | Licencia incompatible con un repositorio público; añade Bootstrap y jQuery a un proyecto React sin librería de componentes (ver `patterns.md`) |
| Resolver `mas_parecida` en el frontend con una petición por fila | Genera N+1 peticiones; la relación ya existe en la base |
| Mostrar el umbral en la barra superior y el conteo de duplicados en el resumen | Ningún endpoint expone el umbral al cargar la página ni el total de duplicados; habría que ampliar el contrato solo para dos datos decorativos. El umbral ya se ve en el medidor de cada veredicto (`umbral_aplicado`) |
| Tipografía IBM Plex, autoalojada o desde Google Fonts | Autoalojarla añade dependencias npm fuera del plan §9b; cargarla de un tercero rompe NF-07. Se queda la pila del sistema |

## Decisión

Aceptada por Franklin el 2026-09-22, tras revisar el prototipo navegable.

Registrar en `docs/decisions.md` como **D-27 — Interfaz de una sola pantalla
con registro en línea**, con este resumen:

- **Decisión:** una sola pantalla; el registro y su veredicto van en línea
  sobre la tabla; sin modales. El listado devuelve el texto de la frase más
  parecida. Los tokens de diseño pasan a la v2 de la skill `ui-design`, que
  sustituye a los de D-23.
- **Por qué:** la persona compara su frase con el catálogo mientras decide.
  Ocultar la lista para registrar le quita justamente ese contexto.
- **Descartado:** modal o panel lateral, dos columnas fijas, plantilla
  comercial, umbral y conteo de duplicados fuera del contrato, fuentes web
  (motivos en la tabla de arriba).
- **Costo aceptado:** en móvil el veredicto empuja la lista hacia abajo.
  Se mitiga con el veredicto compacto y las filas en formato ficha.

## Adenda 2026-09-22, decidida al aplicar

La revisión de `spec-reviewer` al aplicar esta propuesta encontró que el estado
`conflicto` tenía comportamiento y textos propios pero ningún criterio de
aceptación que lo cubriera. Franklin decidió agregar AC-21 a la spec 001, en
Retroalimentación, después de AC-20:

**AC-21 — Conflicto al guardar**
> **Dado** que se validó una frase y el resultado fue única
> **Y** que entre la validación y el guardado otra persona registró una frase parecida
> **Cuando** se presiona Guardar y el servidor responde `409`
> **Entonces** la interfaz pasa al estado `conflicto`, distinto de `posible_duplicado`: explica que la base cambió mientras la persona revisaba y que la frase no se guardó
> **Y** muestra la frase encontrada y su porcentaje, con las acciones Editar frase y Guardar de todos modos
> **Y** Guardar de todos modos envía `confirmar_duplicado: true` y, si el servidor acepta, la frase queda como duplicado confirmado

*Cubre RN-11, RN-12 en la interfaz (AC-12b cubre el lado del servidor).*

Consecuencias: la trazabilidad de RN-11 y RN-12 añade AC-21; T-22 incluye el
test `ac21: ...`; D-27 lo menciona.

En la misma revisión se decidió también:
- D-24 no se sustituye: queda "vigente, precisada por D-27" (un solo botón
  principal; en `posible_duplicado` y `conflicto` se guarda desde el
  veredicto). Se conserva su excepción del `422`: sin Reintentar, el botón
  principal vuelve a "Comprobar similitud". Reflejado en `plan.md` §5 y en la
  skill `ui-design`.
- `AlertaDuplicado.tsx` pasa a ser `Veredicto.tsx`, un componente para
  `unica`, `posible_duplicado`, `conflicto`, `error` y `guardada`.
- AC-17 se mueve a una sección propia, "Vectores", sin renumerar.
