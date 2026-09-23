---
name: ui-design
description: Sistema de diseño visual del proyecto — tokens, estructura de la pantalla y especificación de cada componente y estado. Úsala antes de escribir cualquier CSS o componente visual.
---

# Sistema de diseño (v2, CH-02)

**Referencia visual:** `docs/design/prototipo.html`. Ábrela antes de maquetar.
Todo lo que está aquí describe ese prototipo; si algo no queda claro, el
prototipo decide.

**No copies del prototipo:** la función de similitud simulada (`sim`,
`validar`, `SYN`, `STOP`), el selector "Prototipo · estado", los datos de
ejemplo ni las constantes `UMBRAL`, `MAX` y `MENSAJE_API`. En el proyecto, los
datos y la comparación vienen de la API; el umbral es `umbral_aplicado` de la
respuesta de validar y el máximo es `VITE_MAX_PHRASE_LENGTH`.

## Carácter

Herramienta interna empresarial: sobria, densa y legible. Se ve profesional
por lo que **no** tiene. Una sola pantalla, una tabla, un color de acento
usado solo en la acción principal.

**Regla principal:** ningún valor se escribe a mano. Todo color, fuente,
tamaño de texto, espacio y radio sale de un token de `src/estilos/tokens.css`.
El prototipo usa valores literales porque es un archivo suelto; al portarlo,
cada valor se sustituye por el token equivalente de abajo.

---

## Tokens

```css
:root {
  /* --- Color: fondo y texto --- */
  --color-fondo: #F3F5F8;
  --color-superficie: #FFFFFF;
  --color-superficie-alt: #F7F8FA;
  --color-borde: #E2E6EC;
  --color-borde-fuerte: #C8CFD9;
  --color-texto: #17202C;            /* 16.4:1 sobre superficie */
  --color-texto-secundario: #56616F; /*  6.3:1 */
  --color-texto-sutil: #667080;      /*  5.0:1 sobre superficie, 4.7:1 sobre alt — mínimo permitido */

  /* --- Color: estructura y acento --- */
  --color-enlace: #1D3A66;           /* enlaces y foco, 11.4:1 */
  --color-resaltado: #E8EDF5;        /* fila resaltada */
  --color-acento: #B53A22;           /* solo la acción principal; blanco encima 5.8:1 */
  --color-acento-hover: #962F1B;
  --color-sobre-acento: #FFFFFF;

  /* --- Color: semántico --- */
  --color-duplicado-fondo: #FBEFD7;
  --color-duplicado-borde: #E7CFA0;
  --color-duplicado-texto: #7A4800;  /* 6.7:1 sobre su fondo */
  --color-duplicado-barra: #B87514;  /* 3.1:1 sobre la pista */
  --color-exito-fondo: #E4F1E9;
  --color-exito-texto: #1F5E3F;      /* 6.6:1 sobre su fondo */
  --color-exito-barra: #3C8A62;      /* 3.5:1 sobre la pista */
  --color-error-fondo: #FCECEA;
  --color-error-texto: #9B2418;      /* 6.9:1 sobre su fondo, 7.9:1 sobre superficie */
  --color-barra-pista: #E6E9EE;
  --color-barra-apagada: #A3ACB9;

  /* --- Tipografía --- */
  --fuente: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --fuente-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
  --texto-xs: 10.5px;   /* escala del medidor */
  --texto-sm: 11.5px;   /* etiquetas del par de frases, kbd */
  --texto-md: 12px;     /* encabezados de columna, etiquetas de estado, pie del campo */
  --texto-md2: 12.5px;  /* fechas, resumen, fila del medidor, pie de la lista */
  --texto-base: 13px;   /* texto secundario, cuerpo del veredicto */
  --texto-base2: 13.5px;/* cabecera del veredicto */
  --texto-lg: 14px;     /* cuerpo, botones, frases */
  --texto-xl: 15px;     /* campo, nombre del producto, frase en ficha móvil */
  --texto-cifra: 18px;  /* cifra del medidor */
  --peso-normal: 400;
  --peso-medio: 500;
  --peso-fuerte: 600;
  --interlineado: 1.5;

  /* --- Espacio --- */
  --espacio-1: 4px;
  --espacio-2: 8px;
  --espacio-3: 12px;
  --espacio-4: 16px;
  --espacio-5: 20px;
  --espacio-6: 40px;   /* padding vertical de los estados vacío y error */

  /* --- Forma y medidas --- */
  --radio: 4px;
  --radio-sm: 3px;
  --grosor-borde: 1px;
  --alto-control: 44px;      /* botones, campo, objetivo táctil */
  --alto-control-sm: 36px;   /* paginación */
  --alto-campo-max: 160px;
  --ancho-boton-principal: 168px;
  --ancho-pagina: 1080px;
  --ancho-micro-barra: 64px;
  --grosor-barra: 6px;
  --grosor-micro-barra: 4px;
  --punto-corte: 720px;      /* documental: las media queries no aceptan var() */

  /* --- Movimiento: se anulan con prefers-reduced-motion --- */
  --duracion-spinner: 800ms; /* una vuelta del indicador de carga */
  --duracion-brillo: 1.2s;   /* una pasada del brillo del esqueleto */
}
```

Fuentes: **las del sistema**, sin dependencias ni descargas. La pila de arriba
da Segoe UI en Windows, San Francisco en macOS/iOS y Roboto en Android; la
mono, la equivalente de cada sistema. Ninguna fuente web, ni autoalojada ni
de un tercero (CH-02).

**Escala tipográfica:** la de los tokens. No hay títulos más grandes que 15 px;
la única cifra grande es la del medidor (18 px).

**Números** (porcentajes, fechas, contadores): siempre `--fuente-mono` con
`font-variant-numeric: tabular-nums`.

---

## Estructura de la pantalla

```
┌ Barra superior ───────────────────────────────────────────────┐
│ Banco de Frases                     Comparación por significado │
└───────────────────────────────────────────────────────────────┘
┌ Registrar frase ──────────────────────────────────────────────┐
│ [ campo de texto                          ] [ Comprobar similitud ] │
│ Ctrl + Enter para continuar                           24 / 280 │
│ ┌ veredicto (solo si hay uno) ────────────────────────────┐   │
│ └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
┌ Frases registradas                                  26 frases ┐
│ Frase │ Estado │ Similitud │ Más parecida al registrar │ Registrada │
└───────────────────────────────────────────────────────────────┘
```

- Contenedor de una columna, `max-width: var(--ancho-pagina)`, centrado,
  gutter de `--espacio-4`.
- La barra superior es una sola línea sobre `--color-superficie`. **Sin logo,
  sin monograma, sin migas de pan, sin título grande, sin datos que la API no
  da** (el umbral no se muestra aquí: se ve en el medidor de cada veredicto).
- Separación vertical entre bloques: `--espacio-4`. Sin barras laterales ni
  modales.

---

## Componentes

### Registro

- Etiqueta visible "Registrar frase" asociada al campo.
- Campo de texto de una línea que **crece** con el contenido (hasta
  `--alto-campo-max`) y sin tirador de redimensión. Altura mínima
  `--alto-control`.
- A la derecha, el botón principal (en móvil, debajo y a ancho completo). Su
  texto sigue el paso:

| Estado | Botón principal |
|---|---|
| `inactivo`, `guardada` | "Comprobar similitud" (deshabilitado si hay menos de 3 caracteres o más del máximo) |
| `validando` | "Comprobando…" con indicador, deshabilitado |
| `unica` | "Guardar frase" |
| `guardando` | "Guardando…" con indicador, deshabilitado |
| `posible_duplicado`, `conflicto` | "Guardar frase" deshabilitado; las acciones van en el veredicto, justo debajo, que explica por qué |
| `error` | "Reintentar": repite la última operación (validar o guardar), como dice `plan.md` §5. Con un `422` no hay Reintentar (D-24): el botón vuelve a "Comprobar similitud" y la persona corrige el texto |

- Debajo del campo: "Ctrl + Enter para continuar" a la izquierda y el contador
  `24 / 280` a la derecha. El contador pasa a `--color-error-texto` al superar
  el máximo. Cuenta puntos de código, igual que el servidor.
- **Cualquier edición del texto vuelve a `inactivo`.**
- Tras guardar: se limpia el campo y se le devuelve el foco.

### Veredicto

Aparece dentro de la tarjeta de registro, debajo del campo, **solo cuando hay
uno**. Nunca se reserva espacio vacío para él.

Estructura: recuadro con borde de `--grosor-borde`, cabecera de una línea con
color semántico, y cuerpo.

| Estado | Cabecera | Cuerpo |
|---|---|---|
| `unica` | verde: "No hay otra frase con el mismo significado" | "La más cercana es «…»" + medidor. Con la base vacía (puntaje nulo): "Es la primera frase del catálogo." |
| `posible_duplicado` semántico | ámbar: "Ya existe una frase con el mismo significado" | Par de frases + medidor + acciones |
| `posible_duplicado` exacto | ámbar: "Esta frase ya existe tal cual" | Par de frases (etiqueta "Registrada (idéntica)"), **sin medidor** + acciones |
| `conflicto` (409 al guardar) | ámbar: "Alguien registró una frase parecida mientras revisabas" | "Al guardar volvimos a comparar y el resultado cambió. La frase no se guardó." + par + medidor + acciones |
| `error` | rojo: "No se pudo comparar la frase" | El `mensaje` de la respuesta de error de la API (`422`, `503`). Solo con `SIN_CONEXION` o `RESPUESTA_INESPERADA`: "El servicio no responde. La frase no se guardó; reintenta en unos segundos." |
| `guardada` | — | Línea verde con punto: "Frase guardada." o "Frase guardada como duplicado confirmado." + "Ya aparece en la lista." |

**Acciones ante un duplicado o conflicto:** "Editar frase" (botón con borde,
destacado) y "Guardar de todos modos" (botón de texto subrayado, secundario).
La acción segura siempre pesa más. "Editar frase" vuelve a `inactivo`,
conserva el texto y devuelve el foco al campo (AC-16b). No existe "Cancelar".

En escritorio, el par de frases y el medidor van en dos columnas (1.4 : 1).
En móvil se apilan.

`role="alert"` para duplicado, conflicto y error; `role="status"` para única y
guardada.

### Par de frases

Lista de definición con dos filas separadas por una línea de `--grosor-borde`:
"Tu frase" y "Registrada". Etiquetas en `--texto-sm` `--color-texto-sutil`,
frases en `--texto-lg` `--color-texto`. Las frases largas se parten en varias
líneas; nunca se truncan.

### Medidor

- Fila superior: "Similitud de significado" a la izquierda y la cifra en mono
  `--texto-cifra` a la derecha (`91 %`).
- Barra de `--grosor-barra`, relleno `--color-duplicado-barra` si alcanza el
  umbral y `--color-exito-barra` si no.
- Marca vertical de 2 px en la posición del umbral.
- Escala debajo en mono `--texto-xs`: `0`, `umbral 75`, `100`. El número del
  umbral es `Math.round(umbral_aplicado * 100)`, nunca una constante.
- `role="img"` con `aria-label="Similitud 91 %, umbral 75 %"`.
- El porcentaje es `Math.round(puntaje * 100)`. Nunca decimales crudos.

### Tabla

- Cabecera con "Frases registradas" y el resumen "26 frases" (el `total` de la
  respuesta, en mono). No se cuenta nada más: el contrato no lo da.
- Columnas: **Frase** (40 %), **Estado**, **Similitud**, **Más parecida al
  registrar**, **Registrada**.
- Encabezados de columna en `--texto-md` `--color-texto-secundario` sobre
  `--color-superficie-alt`.
- Filas separadas por `--grosor-borde`, padding 11 px × `--espacio-4`, fondo
  `--color-superficie-alt` al pasar el cursor.
- **Estado:** etiqueta rectangular (`--radio-sm`): "Única" en verde o
  "Duplicado confirmado" en ámbar. Siempre con texto, nunca solo color.
- **Similitud:** micro-medidor: cifra en mono + barra de `--ancho-micro-barra`
  × `--grosor-micro-barra` sin marca de umbral: el listado no trae
  `umbral_aplicado` y cada frase se guardó con el suyo (RN-13); el color sale
  del estado. Es una desviación deliberada del prototipo. `—` si el puntaje es
  nulo.
- **Más parecida:** el texto de `mas_parecida.texto`, solo en duplicados
  confirmados; en las demás, `—`. Si la frase referida **está en la página
  actual**, es un botón con aspecto de enlace (`--color-enlace`, subrayado
  tenue) que la desplaza a la vista y la resalta con `--color-resaltado`
  durante ~1 s. Si está en otra página, es texto plano: no se navega a otra
  página por un enlace de la tabla.
- **Registrada:** `22 sept · 14:45` en mono.
- Tras guardar, la fila nueva se resalta igual.

### Estados de la lista

| Estado | Comportamiento |
|---|---|
| `cargando` | 5 filas de esqueleto con las **mismas columnas** que una fila real (barras grises de 10 px con brillo). `aria-busy="true"` en el `tbody` y texto oculto "Cargando frases…". El resumen también es un esqueleto |
| `vacia` | Sin encabezados de columna. "Todavía no hay frases" + "Escribe la primera en el campo de arriba. Como no habrá nada con qué compararla, se guardará como única." |
| `error` | Sin encabezados. "No se pudo cargar la lista" en `--color-error-texto` + "El servidor no respondió. Las frases guardadas no se han perdido." + botón "Reintentar" |
| Paginación | Solo si `total` es mayor que el tamaño de página. Pie con "1–20 de 26" y botones "Anteriores" / "Siguientes" (deshabilitados en los extremos). Cambiar de página vuelve a `cargando` |

### Botones

| Variante | Uso | Estilo |
|---|---|---|
| Acento | La acción principal del registro | `--color-acento`, texto `--color-sobre-acento`, `min-width: var(--ancho-boton-principal)` |
| Con borde | Editar frase, Reintentar, paginación | `--color-superficie`, borde `--color-borde-fuerte` |
| Texto | Guardar de todos modos | Sin fondo, subrayado con `--color-borde-fuerte` |

Altura mínima `--alto-control` (`--alto-control-sm` en paginación), `--radio`,
`--peso-medio`. El ancho no cambia entre "Comprobar similitud" y
"Comprobando…".

---

## Diseño adaptable — obligatorio

Una sola maqueta para todos los anchos. **Un solo punto de corte: 720 px**
(`@media (max-width: 720px)`; el token `--punto-corte` solo documenta el valor,
porque las media queries no aceptan `var()`).

| Bloque | Más de 720 px | Hasta 720 px |
|---|---|---|
| Barra superior | Nombre a la izquierda, subtítulo a la derecha | Se envuelve en dos líneas si no cabe |
| Registro | Campo y botón en una fila | Botón bajo el campo, a ancho completo |
| Veredicto | Par de frases y medidor en dos columnas | Una columna, en ese orden |
| Tabla | Cinco columnas | **Fichas**: encabezados ocultos pero accesibles (no `display: none`); cada fila es una rejilla con la frase arriba a todo el ancho (`--texto-xl`), estado a la izquierda y similitud a la derecha, "Parecida a: …" solo en duplicados, fecha al final |
| Paginación | Pie en una línea | Igual; los botones conservan `--alto-control-sm` |
| Selector del prototipo | — | Solo el `select`, sin etiqueta |

Reglas:
- Rango soportado: **360 px a 1080 px** de ancho. En todo el rango, **cero
  desplazamiento horizontal**: se verifica a 390 px y a 360 px.
- Ningún texto se trunca con puntos suspensivos. Las frases largas se parten
  en varias líneas, en la tabla, en las fichas y en el par de frases.
- Objetivos táctiles de al menos `--alto-control` (44 px), incluidos el enlace
  de "Parecida a" en las fichas (padding vertical) y los botones del veredicto.
- Sin `position: fixed` salvo el selector del prototipo, que no existe en el
  proyecto.
- El `textarea` no usa `font-size` menor de 15 px: por debajo, iOS amplía la
  página al enfocar.
- Nada cambia de sitio al aparecer el veredicto ni al pasar del esqueleto a
  los datos, en ningún ancho.

---

## Accesibilidad — obligatorio

- Contraste AA (4.5:1) en todo texto, incluido el auxiliar. Los valores de los
  tokens ya están verificados; si cambias un color, vuelve a verificarlo.
- Foco visible: `outline: 2px solid var(--color-enlace)`. Prohibido
  `outline: none` a secas.
- Toda la pantalla operable con teclado; `Ctrl/Cmd + Enter` en el campo.
- `aria-live="polite"` en el veredicto y en la lista.
- `prefers-reduced-motion`: sin brillo del esqueleto ni desplazamiento suave.

---

## Prohibido

Estos rasgos hacen que la interfaz parezca genérica o generada:

- Sombras en tarjetas. Solo bordes de `--grosor-borde`.
- Radios grandes. Máximo `--radio`.
- Etiquetas en forma de píldora (`border-radius: 999px`).
- Tipografía serif, Inter, IBM Plex o degradados.
- Listas de tarjetas para datos tabulares en escritorio (en móvil las fichas
  **son** la tabla, con la misma semántica HTML).
- Modales o paneles laterales para registrar.
- Logos, monogramas, iconos decorativos o emojis.
- Filas de estadísticas grandes o números gigantes.
- Datos inventados en la interfaz: todo número que se muestra viene de una
  respuesta de la API.
- Librerías de componentes o frameworks CSS (Tailwind, Bootstrap, MUI).
- Fuentes web: ni paquetes `@fontsource` ni Google Fonts. Solo la pila del sistema.
- Modo oscuro (fuera de alcance).

---

## Verificación antes de cerrar una tarea visual

- [ ] `grep -rnE "#[0-9a-fA-F]{3,6}" src/ --include="*.css" --include="*.tsx"` no devuelve nada fuera de `tokens.css`
- [ ] `grep -rnE "[0-9]+px" src/ --include="*.css" --include="*.tsx"` no devuelve nada fuera de `tokens.css`, salvo la media query de 720 px y los 2 px de la marca del umbral
- [ ] `grep -rn "999px\|box-shadow\|fonts.googleapis" src/` no devuelve nada
- [ ] Recorrí la pantalla con Tab; el foco siempre se ve
- [ ] A 390 px y a 360 px de ancho no hay desplazamiento horizontal y la tabla se ve en fichas
- [ ] A 1080 px la tabla muestra las cinco columnas y nada se trunca
- [ ] Nada salta al aparecer el veredicto ni al pasar del esqueleto a los datos
- [ ] Los 8 estados del registro (`inactivo`, `validando`, `unica`, `posible_duplicado`, `conflicto`, `error`, `guardando`, `guardada`) y los 4 de la lista se ven como en el prototipo
