---
name: spec
description: Convierte un requerimiento en una especificación completa (reglas de negocio, criterios de aceptación, casos borde). Úsala antes de cualquier diseño técnico o implementación.
---

# Escribir una especificación

Tu trabajo aquí es definir **qué** debe hacer el sistema. No decides tecnología,
no escribes código y no propones estructura de carpetas. Eso viene después, en
`/plan`.

## Antes de escribir

Lee `docs/context/product.md`, `docs/context/business-rules.md`,
`docs/context/glossary.md` y `docs/constitution.md`.

Si el requerimiento entra en conflicto con una regla de negocio existente,
detente y dilo. No inventes una excepción.

## Procedimiento

1. **Reformula el requerimiento** en dos o tres frases, con el vocabulario del
   glosario. Si tuviste que inventar un término, agrégalo al glosario en el
   mismo cambio.

2. **Identifica las reglas de negocio.** Si el requerimiento introduce reglas
   nuevas, propónlas numeradas como `RN-nn` continuando la numeración de
   `business-rules.md`. Nunca renumeres reglas existentes.

3. **Escribe las historias de usuario** en formato "Como… quiero… para…".

4. **Deriva los criterios de aceptación.** Uno por comportamiento observable,
   en formato Dado / Cuando / Entonces, numerados `AC-nn`. Cada uno debe ser
   verificable con un test automatizado. Si no sabes cómo probarlo, está mal
   escrito.

5. **Enumera los casos borde** de forma explícita, con la decisión ya tomada
   para cada uno. Recorre esta lista mentalmente:
   - colección vacía
   - un solo elemento
   - empates y valores exactamente iguales al límite
   - entradas vacías, solo espacios, longitud mínima y máxima
   - caracteres especiales, acentos, emojis
   - dependencia externa caída
   - concurrencia: ¿qué pasa si dos peticiones hacen lo mismo a la vez?
   - cambios de configuración después de que hay datos guardados

6. **Escribe qué queda fuera de alcance**, con el motivo. Esta sección protege
   el trabajo tanto como la de dentro.

7. **Completa la tabla de trazabilidad** RN → AC.

8. **Marca el Definition of Ready** y señala qué falta para cumplirlo.

## Salida

Crea `docs/specs/<nnn>-<slug>/spec.md` siguiendo la estructura de
`docs/specs/001-validacion-semantica/spec.md`.

## Después

1. Invoca al subagente `spec-reviewer` sobre la spec recién escrita.
2. Presenta al humano los hallazgos y **las preguntas abiertas que no puedas
   resolver solo**. No las resuelvas por tu cuenta con una suposición.
3. Espera la aprobación explícita. Sin aprobación no se pasa a `/plan`.
4. Con la aprobación, haz el commit: `docs(spec): especificación de <slug>`.

## Prohibido en este paso

Nombrar librerías, elegir base de datos, definir estructura de carpetas,
escribir código o pseudocódigo de implementación. Si sientes la tentación,
anótalo en una lista de "temas para el plan" al final y sigue.
