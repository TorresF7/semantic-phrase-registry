---
name: ui-design
description: Sistema de diseño visual del proyecto — tokens de color, tipografía, espaciado y especificación de cada componente de la interfaz. Úsala antes de escribir cualquier CSS o componente visual.
---

# Sistema de diseño

La interfaz es **una sola pantalla**. El objetivo es que se vea deliberada. Una
interfaz sin estilo parece inacabada; una sobrecargada distrae de lo que
importa. El punto medio se consigue con pocas decisiones aplicadas de forma
consistente.

**Regla principal:** ningún valor se escribe a mano. Todo color, espacio, tamaño
y radio sale de un token. Si necesitas un valor que no está aquí, el diseño está
mal o falta un token: dilo, no improvises.

---

## Tokens

Van en `src/estilos/tokens.css`, importado una sola vez en `main.tsx`.

```css
:root {
  /* --- Color: superficie y texto --- */
  --color-fondo:              #FFFFFF;
  --color-superficie:         #F7F8FA;
  --color-borde:              #E3E6EA;
  --color-borde-fuerte:       #C9CFD6;

  --color-texto:              #16191D;  /* 17.6:1 sobre fondo */
  --color-texto-secundario:   #59616B;  /*  6.3:1 */
  --color-texto-sutil:        #6E7680;  /*  4.6:1 — mínimo permitido */

  /* --- Color: acento --- */
  --color-acento:             #1F5FA8;  /*  6.4:1 sobre blanco */
  --color-acento-hover:       #194E8A;
  --color-acento-suave:       #EDF3FA;

  /* --- Color: semántico --- */
  --color-alerta-fondo:       #FFF6E8;
  --color-alerta-borde:       #B87514;
  --color-alerta-texto:       #7A4A00;  /*  7.0:1 sobre su fondo */

  --color-exito-fondo:        #E9F7F1;
  --color-exito-texto:        #0E6B49;  /*  5.9:1 */

  --color-peligro-fondo:      #FDECEA;
  --color-peligro-texto:      #A5231A;  /*  6.4:1 */

  /* --- Tipografía --- */
  --fuente: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto,
            "Helvetica Neue", Arial, sans-serif;
  --fuente-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace;

  --texto-xs:   0.75rem;   /* 12px — metadatos */
  --texto-sm:   0.875rem;  /* 14px — secundario, etiquetas */
  --texto-base: 1rem;      /* 16px — cuerpo, campos */
  --texto-lg:   1.125rem;  /* 18px — la frase en la alerta */
  --texto-xl:   1.5rem;    /* 24px — título de la página */

  --peso-normal:  400;
  --peso-medio:   500;
  --peso-fuerte:  600;

  --interlineado-ajustado: 1.25;
  --interlineado-normal:   1.55;

  /* --- Espaciado: escala de 4px --- */
  --esp-1:  0.25rem;   /*  4px */
  --esp-2:  0.5rem;    /*  8px */
  --esp-3:  0.75rem;   /* 12px */
  --esp-4:  1rem;      /* 16px */
  --esp-6:  1.5rem;    /* 24px */
  --esp-8:  2rem;      /* 32px */
  --esp-12: 3rem;      /* 48px */

  /* --- Forma --- */
  --radio-sm:  4px;
  --radio-md:  8px;
  --radio-lg: 12px;

  --foco-grosor:     2px;
  --foco-separacion: 2px;
  --borde-fino:     1px;
  --borde-grueso:   3px;

  --sombra-sutil:  0 1px 2px rgba(22, 25, 29, 0.06);
  --sombra-tarjeta: 0 1px 3px rgba(22, 25, 29, 0.08),
                    0 1px 2px rgba(22, 25, 29, 0.04);

  /* --- Movimiento --- */
  --transicion: 150ms ease;

  /* --- Layout --- */
  --ancho-contenido: 720px;
  --alto-tactil: 44px;          /* objetivo táctil mínimo */
  --alto-zona-resultado: 13rem; /* reserva el hueco de la alerta: la lista no salta */
  --alto-tarjeta: 4.5rem;       /* una tarjeta del listado; reserva el hueco al cargar */
}

@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
```

Los ratios de contraste anotados están verificados y todos cumplen WCAG AA.
Si cambias un color, vuelve a verificarlo antes de commitearlo.

---

## Layout

Una columna centrada, `max-width: var(--ancho-contenido)`, con
`padding: var(--esp-8) var(--esp-4)`. Nada de barras laterales ni cabeceras
elaboradas: la pantalla tiene un formulario y una lista.

Orden vertical:

```
Título + una línea explicando qué hace la aplicación
Formulario (campo + contador + botones)
Zona de resultado (alerta o confirmación) — aparece debajo del formulario
Separador
Lista de frases
```

La zona de resultado **reserva su espacio** o usa `min-height`, para que la
lista no salte cuando aparece la alerta.

Responsivo: por debajo de 640px los botones pasan a ancho completo y se apilan.
No hay más puntos de corte: no hacen falta.

---

## Componentes

### Campo de texto

- `width: 100%`, `padding: var(--esp-3)`, `border: 1px solid var(--color-borde-fuerte)`,
  `border-radius: var(--radio-md)`, `font-size: var(--texto-base)`.
- Foco: `outline: var(--foco-grosor) solid var(--color-acento); outline-offset: var(--foco-separacion)`.
  **Nunca `outline: none` sin reemplazo.**
- Deshabilitado: fondo `--color-superficie`, cursor `not-allowed`, opacidad 1
  (no atenúes el texto, empeora el contraste).
- Etiqueta visible arriba, `<label for>` asociado. Nada de usar solo el
  `placeholder` como etiqueta.
- Contador de caracteres abajo a la derecha, `--texto-xs`,
  `--color-texto-sutil`, con el formato `123 / 280`. Pasa a
  `--color-peligro-texto` al superar el máximo. Cuenta puntos de código, no
  unidades UTF-16 (ver `react-frontend`).

### Botones

| Variante | Uso | Estilo |
|---|---|---|
| Primario | Validar; Guardar cuando la frase resultó única | Fondo `--color-acento`, texto blanco |
| Secundario | Guardar de todos modos | Fondo blanco, borde `--color-borde-fuerte`, texto `--color-texto` |
| Discreto | Cancelar | Sin fondo ni borde, texto `--color-texto-secundario`, subrayado al pasar el cursor |

Validar y Guardar van juntos bajo el campo. Guardar es primario solo cuando
está habilitado; mientras está deshabilitado, se ve como tal (abajo).

Comunes: `padding: var(--esp-3) var(--esp-6)`, `border-radius: var(--radio-md)`,
`font-weight: var(--peso-medio)`, `min-height: 44px` (objetivo táctil),
`transition: var(--transicion)`.

Estado de carga: el texto cambia ("Validando…"), el botón se deshabilita, y se
muestra un indicador. **El ancho no cambia** entre estados: reserva el espacio
del texto más largo o fija `min-width`.

Nunca deshabilites un botón sin que se vea por qué. Si Guardar está bloqueado,
debajo hay un texto en `--texto-sm` que dice "Valida la frase antes de guardar".

### Alerta de posible duplicado

Es el componente central de toda la aplicación. Si algo se ve cuidado, que sea
esto.

```
┌─────────────────────────────────────────────────┐
│ ⚠  Esta frase se parece mucho a una existente   │  ← peso fuerte, texto-base
│                                                 │
│    "El pago fue rechazado por el banco"         │  ← texto-lg, cursiva
│                                                 │
│    87% de similitud                             │  ← texto-sm, secundario
│                                                 │
│    [ Guardar de todos modos ]  Cancelar         │
└─────────────────────────────────────────────────┘
```

- Fondo `--color-alerta-fondo`, borde izquierdo de 3px en
  `--color-alerta-borde`, resto del borde 1px `--color-borde`.
- `border-radius: var(--radio-md)`, `padding: var(--esp-4)`.
- `role="alert"` para que los lectores de pantalla la anuncien.
- El icono es decorativo: `aria-hidden="true"`.
- La frase existente se muestra **completa**, nunca truncada. Es la información
  que la persona necesita para decidir.
- El porcentaje se calcula `Math.round(puntaje * 100)`. Nunca se muestra el
  decimal crudo.

Para el duplicado exacto, el mismo componente con el texto "Esta frase ya existe
tal cual" y sin porcentaje: decir "100% de similitud" suena a cálculo cuando en
realidad es una coincidencia literal.

### Confirmación de guardado

Ocupa el mismo lugar que la alerta, para que la persona mire siempre al mismo
sitio esperando el veredicto.

- Fondo `--color-exito-fondo`, texto `--color-exito-texto`, borde izquierdo de
  3px en el mismo color del texto.
- Dos mensajes distintos según el estado (RN-18):
  - Única: "Frase guardada."
  - Duplicado confirmado: "Frase guardada como duplicado confirmado."
- Lleva `role="status"`, no `role="alert"`: es información, no una advertencia
  que interrumpa.
- Desaparece al empezar a escribir una frase nueva. **No se desvanece sola por
  tiempo**: quien lee despacio o usa un lector de pantalla se lo perdería.

### Lista de frases

Tarjetas apiladas con `gap: var(--esp-2)`, no una tabla: el contenido es una
frase larga, no columnas.

Cada elemento:
- Texto de la frase en `--texto-base`, color `--color-texto`.
- Línea de metadatos en `--texto-xs`, `--color-texto-sutil`: fecha y hora
  locales con `Intl.DateTimeFormat` (por ejemplo "21 sept 2026, 14:04") y, si
  aplica, la marca de duplicado confirmado. Fecha absoluta, no relativa: no
  hay que recalcularla ni mantenerla actualizada.
- Las frases en estado `DUPLICADO_CONFIRMADO` llevan una etiqueta pequeña con
  fondo `--color-alerta-fondo` y texto `--color-alerta-texto`.
  **No basta con un color de fondo distinto**: la etiqueta lleva texto, porque
  la información nunca se transmite solo por color.

### Estado vacío

Centrado, `padding: var(--esp-12) var(--esp-4)`, texto en
`--color-texto-secundario`. Dice qué pasa y qué hacer: "Todavía no hay frases
registradas. Escribe la primera arriba." Sin ilustraciones.

### Estados de carga y error

- Carga del listado: el texto "Cargando frases…" en `--color-texto-secundario`,
  dentro de un contenedor con `min-height` igual a tres tarjetas para que no
  salte el contenido, y `aria-busy="true"` en la lista.
- Error de red: caja con `--color-peligro-fondo` y un botón de reintentar. El
  mensaje dice qué falló en lenguaje llano, nunca el código HTTP.
- Paginación: dos botones secundarios, **Anteriores** y **Siguientes**, bajo la
  lista, deshabilitados cuando no hay más páginas, con el texto "1–20 de 25"
  entre ellos.

---

## Accesibilidad — mínimos obligatorios

- Todo texto cumple contraste AA (4.5:1 normal, 3:1 grande).
- Foco visible en todo elemento interactivo. Prohibido `outline: none` a secas.
- Objetivos táctiles de al menos 44×44px.
- Toda la pantalla es operable con teclado, en orden lógico.
- La alerta usa `role="alert"`; el estado de carga, `aria-busy`.
- Ninguna información se transmite solo por color.
- `prefers-reduced-motion` respetado.

---

## Lo que NO se hace

- Nada de librerías de componentes: ni Material, ni Chakra, ni shadcn. Para una
  pantalla es más peso que beneficio.
- Nada de Tailwind. CSS Modules o CSS plano con los tokens.
- Nada de modo oscuro. No aporta aquí y duplica el trabajo de verificar
  contrastes.
- Nada de animaciones de entrada, degradados, sombras marcadas, esquinas muy
  redondeadas ni iconos decorativos de relleno.
- Ningún valor de color, espacio o tamaño escrito a mano fuera de `tokens.css`.

## Verificación antes de dar por cerrada la interfaz

- [ ] `grep -rn "#[0-9a-fA-F]\{3,6\}" src/ --include="*.css"` no devuelve nada
      fuera de `tokens.css`
- [ ] Recorriste toda la pantalla con Tab y el foco siempre se ve
- [ ] La alerta se entiende sin saber nada de IA
- [ ] Nada salta de posición al aparecer la alerta o al cargar la lista
- [ ] A 375px de ancho no hay desbordamiento horizontal
