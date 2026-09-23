---
name: react-frontend
description: Convenciones de React, TypeScript y experiencia de uso de este proyecto. Se aplica al escribir o revisar cualquier código del frontend.
---

# Convenciones del frontend

## Stack

React 18 + TypeScript estricto + Vite. Sin librería de estado global: el estado
cabe en dos hooks. Sin librería de componentes: la interfaz es una pantalla.

Para todo lo visual (color, espaciado, tipografía, forma de cada componente)
manda la skill `ui-design`. Aquí solo está la estructura del código.

## Patrones que se usan, y por qué

El catálogo completo, con los patrones del backend y los descartados, está en
`docs/context/patterns.md`. Aquí solo el resumen del frontend.

Cinco patrones, cada uno resolviendo un problema concreto. No hay más.

| Patrón | Dónde | Qué problema resuelve |
|---|---|---|
| **Máquina de estados con unión discriminada** | `EstadoFormulario` | Hace imposible representar estados contradictorios, como "cargando y con error a la vez" |
| **Adaptador de API** | `api/cliente.ts` | Ningún componente conoce `fetch`, URLs ni códigos HTTP. Cambiar el transporte toca un solo archivo |
| **Hooks personalizados** | `useFrases`, `useValidacion` | Separan la lógica de estado del renderizado, y se pueden probar sin montar la interfaz |
| **Presentacional / contenedor** | `App` orquesta; `FormularioFrase`, `ListaFrases`, `Veredicto` solo reciben props y emiten eventos | Los componentes de presentación se prueban con props, sin red ni contexto |
| **Elevación del estado** | El estado del formulario vive en `App` | Guardar una frase tiene que refrescar la lista. Si cada componente guardara su estado, harían falta trucos para sincronizarlos |

Patrones que **no** se usan y por qué: Redux o Zustand (el estado cabe en dos
hooks y no se comparte entre rutas, porque no hay rutas), Context (no hay prop
drilling: el árbol tiene dos niveles), render props y componentes de orden
superior (los hooks ya lo resuelven), y componentes compuestos (hay un solo
componente compuesto y no se reutiliza).

## TypeScript

`strict: true`, y además `noUncheckedIndexedAccess`.

Los tipos de la API viven en `api/tipos.ts` y son **espejo literal del contrato**
de `plan.md`. Los campos que el contrato permite nulos se tipan nulos:

```ts
export type ResultadoValidacion = {
  es_posible_duplicado: boolean;
  motivo: "EXACTO" | "SEMANTICO" | null;
  puntaje: number | null;
  umbral_aplicado: number;
  mas_parecida: { id: number; texto: string } | null;
  modelo: string;
};
```

Nada de `any`. Nada de `as` para callar al compilador: si hace falta, el tipo
está mal.

## Estados, no banderas

Prohibido `const [cargando, setCargando] = useState(false)` junto a
`const [error, setError] = useState(...)` junto a `const [resultado, ...]`. Eso
permite estados imposibles, como cargando y con error a la vez.

Se usa un tipo discriminado:

```ts
type EstadoFormulario =
  | { tipo: "inactivo" }
  | { tipo: "validando" }
  | { tipo: "unica"; resultado: ResultadoValidacion }
  | { tipo: "posible_duplicado"; resultado: ResultadoValidacion }
  | { tipo: "guardando" }
  | { tipo: "guardada"; frase: Frase }
  | { tipo: "conflicto"; resultado: DatosDuplicado }
  | { tipo: "error"; codigo: string; mensaje: string };
```

`conflicto` es el `409` al guardar: el servidor revalidó y la base había
cambiado mientras la persona revisaba (RN-11). Se muestra distinto de
`posible_duplicado`. `DatosDuplicado` es el tipo que entrega el cliente para
el `409` (plan §5).

Las transiciones fuera del camino feliz están en la tabla de `plan.md` §5. Las
dos que más se olvidan: **editar el texto** desde cualquier estado vuelve a
`inactivo` (el resultado caduca, AC-16b), y **Editar frase** vuelve a
`inactivo` conservando el texto y devolviendo el foco al campo.

La lista tiene su propia máquina, también discriminada:

```ts
type EstadoLista =
  | { tipo: "cargando" }
  | { tipo: "ok"; pagina: PaginaFrases }
  | { tipo: "cambiando"; pagina: PaginaFrases }
  | { tipo: "vacia" }
  | { tipo: "error" };
```

Cambiar de página con una página a la vista pasa a `cambiando`, que conserva
la anterior (D-37). Pulsar Reintentar vuelve a `cargando`.

## Cliente de API

Un solo módulo `api/cliente.ts`. Ningún componente llama a `fetch` directamente.

El cliente traduce la respuesta de error de la API a un tipo propio. Un `409` no
es una excepción inesperada: es una respuesta prevista del contrato y se maneja
como tal.

## Reglas de experiencia de uso

- **Nada de jerga.** Sigue la tabla del glosario. Se dice "87% de similitud", no
  "puntaje 0.8734". No aparece la palabra "embedding" en ningún lado.
- Un solo botón principal que avanza por pasos. Está deshabilitado mientras no
  exista un resultado de validación para el texto actual, y el veredicto junto
  a él explica por qué.
- El veredicto de duplicado muestra la frase existente completa, el porcentaje
  y dos acciones sin ambigüedad: **Editar frase** (la destacada) y **Guardar de
  todos modos** (secundaria). No existe "Cancelar".
- En `unica` también se muestra la frase más cercana con su medidor; con la
  base vacía, "Es la primera frase del catálogo."
- Si el servidor responde `409` al guardar, se pasa a `conflicto` con el dato
  nuevo. Esto es visible y deliberado: el servidor revalidó.
- Tras guardar, el campo se limpia y recupera el foco.
- Toda operación en curso tiene indicador visible. Ningún botón se puede
  presionar dos veces: mientras carga lleva `aria-disabled` e ignora el clic,
  no `disabled`, para no perder el foco (D-36).
- Al llegar el veredicto, el foco va a "Guardar frase" si es único y a
  "Editar frase" si es un duplicado o un conflicto (D-36).
- Los errores se muestran en lenguaje claro, con una acción posible cuando la
  hay ("Reintentar").

## La lista

Es una **tabla** de cinco columnas (Frase, Estado, Similitud, Más parecida al
registrar, Registrada) que hasta 900 px se muestra en fichas, con la
misma semántica HTML y los encabezados ocultos pero accesibles. Tiene cuatro
estados, cada uno como lo especifica la skill `ui-design` v2 (AC-20):

| Estado | Qué se ve |
|---|---|
| `cargando` | Filas de esqueleto con las mismas columnas que una fila real; `aria-busy="true"` en el `tbody` |
| `ok` | Las filas. La paginación solo aparece si `total` es mayor que el tamaño de página |
| `cambiando` | Las filas de la página anterior, atenuadas y con `aria-busy="true"` en la tabla; la paginación sigue montada (D-37) |
| `vacia` | Texto útil que dice qué hacer, no una lista en blanco |
| `error` | Mensaje en lenguaje claro y botón "Reintentar" que vuelve a pedir la lista |

"Más parecida al registrar" usa `mas_parecida` del contrato (AC-19). Nunca se
resuelve con una petición por fila.

## Seguridad

- Nunca `dangerouslySetInnerHTML`. React escapa el contenido por defecto y las
  frases las escribe una persona: es la superficie obvia de XSS.
- Las variables `VITE_*` se incrustan en el paquete y son públicas. Ningún
  secreto ahí. Son tres: `VITE_API_URL`, `VITE_MAX_PHRASE_LENGTH` y
  `VITE_API_TIMEOUT_MS`.
- Toda petición lleva `AbortSignal.timeout(VITE_API_TIMEOUT_MS)`, por defecto
  15000 ms. Agotado el tiempo, el cliente devuelve `SIN_CONEXION`, igual que
  sin red (D-38).
- La validación de longitud en el cliente es para la experiencia de uso. La que
  manda es la del servidor (Artículo 8). El contador cuenta puntos de código
  (`[...texto].length`), no `texto.length`: un emoji es 1 carácter para el
  servidor y 2 unidades UTF-16 para JavaScript.
- El máximo del contador sale de `VITE_MAX_PHRASE_LENGTH`, no está escrito en
  el código.

## Accesibilidad mínima

Etiquetas asociadas a sus campos. La alerta de duplicado con `role="alert"`.
Foco visible. Navegable con teclado. Sin transmitir información solo por color.

## Estructura

```
src/
  api/          cliente.ts · tipos.ts
  hooks/        useFrases.ts · useValidacion.ts
  components/   un componente por archivo, en PascalCase
  estilos/      tokens.css
  App.tsx
```

## Tests

Vitest + Testing Library. Cada test de un AC lo nombra:
`it("ac16: tras guardar como única muestra 'Frase guardada.' y vacía el campo")`.
Los detalles están en la skill `testing`.

Componentes de función. Sin clases. Sin `useEffect` para cosas que puedan
calcularse durante el renderizado.
