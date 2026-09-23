# CH-03 — Columnas estables en la tabla de frases

**Fecha:** 2026-09-23
**Estado:** aplicada
**Afecta a:** skill `ui-design` (tokens, «Tabla», «Diseño adaptable»), skill
`react-frontend` («La lista»), `decisions.md` (D-31),
`plan.md` §5 (punto de corte de 720 px), `docs/design/prototipo.html` (tiene
la misma regla `.c-frase { width: 40% }` y el mismo `@media (max-width: 720px)`,
y la skill lo declara referencia que decide),
`frontend/src/components/ListaFrases.module.css`
y, según la alternativa, `frontend/src/estilos/tokens.css` y las media queries
de `FormularioFrase.module.css`, `Veredicto.module.css` y `botones.css`. No
afecta a reglas de negocio ni a criterios de aceptación.

## Qué se propone cambiar

Que las columnas de la tabla no cambien de sitio al pasar del esqueleto a los
datos, y que la columna Frase no se quede estrecha en los anchos de escritorio
más bajos.

## Por qué

La revisión de T-24 (2026-09-23), medida en Chromium contra el backend real
(18 frases, 3 de ellas duplicados confirmados), deja sin cumplir el punto
«Nada salta al aparecer el veredicto ni al pasar del esqueleto a los datos» de
la skill `ui-design`. Los dos problemas ya existían antes de T-24:

1. **Salto del esqueleto a los datos.** La tabla usa el reparto automático
   (`table-layout: auto`) y solo Frase tiene ancho (40 %). El reparto depende
   del contenido: las barras del esqueleto no ocupan lo mismo que la etiqueta
   «Duplicado confirmado», la cifra con su barra o la fecha. Anchos de columna
   medidos (Frase, Estado, Similitud, Más parecida, Registrada):

   | Ancho de ventana | Esqueleto | Datos |
   |---|---|---|
   | 1080 px | 418 · 118 · 158 · 204 · 148 | 412 · 170 · 140 · 174 · 135 |
   | 900 px | 346 · 98 · 130 · 169 · 122 | 241 · 170 · 140 · 166 · 135 |
   | 721 px | 177 · 96 · 128 · 166 · 120 | 62 · 170 · 140 · 166 · 135 |

   A 1080 px, los bordes de las columnas se desplazan entre 15 y 50 px.

2. **Columna Frase estrecha.** Estado, Similitud y Registrada no se parten
   (`white-space: nowrap`) y entre las tres necesitan unos 445 px. Por
   encima del punto de corte, lo que queda se lo reparten Frase y Más
   parecida. A 721 px, Frase se queda en **62 px**, y las frases se parten
   en dos o tres palabras por línea.

## Impacto

- Reglas de negocio afectadas: ninguna.
- Criterios de aceptación a agregar, modificar o eliminar: ninguno. AC-20 pide
  las mismas columnas en el esqueleto que en una fila real, y eso ya se
  cumple. La estabilidad de las columnas es un criterio visual de la skill
  y se verifica en la lista de comprobación, no con Vitest: jsdom no calcula
  el diseño.
- Tareas afectadas: T-24 ya está cerrada (2026-09-23). El propietario decidió
  cerrarla con este punto marcado como no superado en `tasks.md` y
  `STATUS.md`, así que no espera a CH-03. Si se acepta, se añade **T-25** al
  final del bloque G (depende de T-24; en la ruta crítica: `T-24 ──→ T-25`),
  sin AC. La definición exacta de T-25 está en `tasks.md`.
- Tests que hay que reescribir: ninguno. Con la alternativa (b) hay que
  comprobar que ningún test de Vitest dependa del ancho de 720 px (hoy
  ninguno lo hace).

## Alternativas consideradas

### (a) `table-layout: fixed` con tres tokens de ancho

- `.tabla { table-layout: fixed; }` por encima del punto de corte, dentro de
  un `@media (min-width: 721px)`. La skill hoy solo usa `max-width: 720px`, así
  que la forma de escribirlo también se documenta.
- Tres tokens nuevos en `tokens.css`, con el valor que necesita el contenido
  más ancho de cada columna más el padding horizontal: `--ancho-col-estado`
  (≈ 170 px, «Duplicado confirmado»), `--ancho-col-similitud` (≈ 140 px,
  «100 %» + micro-barra) y `--ancho-col-fecha` (≈ 135 px, «22 sept · 14:45»).
- **La regla actual `.colFrase { width: 40% }` se elimina.** Si se conserva,
  bajo `fixed` Frase ocupa siempre el 40 % de la tabla. A 721 px eso son
  ≈ 269 px, que con los 445 px fijos suman 714 px sobre ≈ 673 disponibles: no
  cabe.
- Frase y Más parecida se reparten el resto. Para un reparto distinto de todo
  a una columna, las dos necesitan ancho explícito: con `fixed`, una columna
  sin ancho se lleva todo el sobrante. Las opciones son Frase sin ancho (se
  lleva todo) o las dos con ancho relativo al sobrante (60/40 o 50/50,
  escrito con `calc()` sobre los tokens). Hay que decidirlo.

**Resuelve** el salto del esqueleto en todos los anchos: con `fixed`, el ancho
lo deciden las columnas, no el contenido.

**No resuelve del todo** la columna estrecha: a 721 px, el sobrante es de unos
227 px. Con el reparto 50/50 o 60/40, Frase recibiría entre 113 y 136 px:
más que los 62 px de hoy, pero sigue siendo estrecha. Si Frase se lleva todo
el sobrante, recibe 227 px, pero Más parecida desaparece en la práctica.

**Coste:** tres tokens nuevos, y la skill `ui-design` se actualiza (tokens y
sección «Tabla»). El `grep` de `px` sigue limpio porque los valores viven en
`tokens.css`.

### (b) Subir el punto de corte de las fichas de 720 px a ~900 px

- Las fichas se usan hasta ~900 px. Por encima, la tabla tiene al menos
  ~835 px útiles, y Frase recibe ~240 px o más.
- Hay que decidir si el punto de corte sube solo para la tabla o para toda la
  pantalla. La skill exige un solo punto de corte, así que lo coherente es
  subirlo en todos los bloques: registro, veredicto, botones y tabla. Al subir
  el global, entre 721 y 900 px el registro también pasa al diseño de una
  columna, y el veredicto pasa de dos columnas (par de frases y medidor) a
  una. Es el diseño móvil ya aprobado, pero en ventanas de escritorio de 721 a
  900 px no se ha revisado.

**Resuelve** la columna estrecha sin tokens de ancho nuevos.

**No resuelve** el salto del esqueleto: por encima del punto de corte el
reparto sigue siendo automático. A 1080 px seguiría habiendo entre 15 y 50 px
de desplazamiento.

**Coste:** cambiar `@media (max-width: 720px)` en cuatro hojas y en el
prototipo, el token documental `--punto-corte`, `plan.md` §5 y la skill. También hay que repetir
las comprobaciones a 390 y 360 px y añadir una a ~900 px.

### (a) + (b)

Juntas resuelven los dos problemas: `fixed` elimina el salto y el punto de
corte más alto da a Frase un ancho digno. Es la suma de los dos costes.

### No hacer nada

El salto es horizontal, pequeño a 1080 px y ocurre una sola vez por carga.
La columna estrecha solo afecta a ventanas de escritorio de 721 a ~900 px.
Pero entonces el punto de la skill queda incumplido y habría que acotarlo por
escrito. El requisito está en dos sitios de `ui-design`: la regla de «Diseño
adaptable» y el punto de la lista de verificación. La excepción se limitaría
a **las columnas de la tabla en horizontal**. La regla general se mantiene
para el veredicto y para cualquier otro salto.

## Decisión

**Aceptada por Franklin el 2026-09-23: (a) + (b)**, con una desviación
posterior que decidió él mismo (ver más abajo). Queda registrada como **D-31**.

- **Punto de corte único en 900 px** para toda la pantalla: registro,
  veredicto, botones y tabla. Se cambia también en el prototipo, en el token
  `--punto-corte`, en `plan.md` §5, en la skill `ui-design` y en la skill
  `react-frontend`.
- **`table-layout: fixed` por encima del punto de corte**, dentro de
  `@media (min-width: 901px)`. Se elimina `.colFrase { width: 40% }`.
- **Cuatro tokens de ancho de columna.** Los tres de la alternativa (a) y uno
  más para Más parecida:

  | Token | Valor | Contenido más ancho |
  |---|---|---|
  | `--ancho-col-estado` | 184px | «Duplicado confirmado», ≈ 170 px medidos con Segoe UI |
  | `--ancho-col-similitud` | 148px | «100 %» y la micro-barra, ≈ 140 px |
  | `--ancho-col-fecha` | 152px | «22 sept · 14:45» en mono, ≈ 135 px |
  | `--ancho-col-parecida` | 176px | Texto libre: se parte en varias líneas |

  Los valores incluyen el padding horizontal (2 × `--espacio-4`) y un margen
  sobre lo medido en Chromium con Segoe UI. San Francisco, Roboto y SF Mono
  son algo más anchas.
- **Frase no tiene ancho** y se queda con el espacio restante: con
  `table-layout: fixed`, la columna sin ancho recibe lo que dejan las demás.
  Ese comportamiento lo define la especificación de CSS y es igual en todos
  los navegadores. `--ancho-col-parecida` se eligió para que a 901 px Frase
  no quede más estrecha que Más parecida. A 901 px la tabla mide ≈ 852 px:
  901 − 15 (barra de desplazamiento de Chromium en Windows) − 2 × 16 (gutter)
  − 2 × 1 (borde de la tarjeta). Quedan 852 − 484 − 176 ≈ 192 px para Frase.
  A 1080 px, con la misma cuenta, la tabla mide 1031 px y Frase recibe
  1031 − 484 − 176 ≈ 371 px. T-25 mide los valores reales.

### Desviación de lo aceptado: sin reparto 60/40

La decisión inicial fue repartir el espacio restante entre Frase y Más
parecida al 60/40, con `calc()` sobre los tokens. Al prepararla se comprobó
en Chromium, con una página de prueba, que `calc()` con porcentaje en una
columna de tabla se trata como `auto`, igual en el `th` que en un `<col>`: el
reparto sale 50/50 (290 · 290 a 1080 px). Escribir `60%` y `40%` junto a los
px sí da 60/40 en Chromium (347 · 232), pero depende de cómo resuelve cada
navegador unas columnas que no caben, algo que la especificación no fija.
Franklin descartó las dos opciones y decidió el ancho fijo para Más parecida
con Frase sin ancho. Todo lo que decía 60/40 pasa a decir «Frase se queda con
el espacio restante».

### Qué no resuelve

A 1080 px, Frase recibe ≈ 371 px (≈ 36 % de la tabla, antes 40 %). Es el
precio de que ninguna columna dependa del contenido.
