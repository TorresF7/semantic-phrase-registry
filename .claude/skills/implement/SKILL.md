---
name: implement
description: Implementa UNA tarea de tasks.md siguiendo el ciclo test primero. Úsala con el identificador de la tarea, por ejemplo /implement T-07.
---

# Implementar una tarea

**Uso:** `/implement T-07`

Trabajas sobre **una sola tarea**. No adelantas trabajo de otras, aunque sea
tentador y aunque "ya que estamos".

## Paso 0 — Cargar contexto

Lee, en este orden:

1. `docs/STATUS.md` — dónde quedó el trabajo.
2. `docs/specs/<spec>/tasks.md` — la tarea concreta, su DoD y sus dependencias.
3. `docs/specs/<spec>/spec.md` — los criterios de aceptación que cubre la tarea.
4. `docs/specs/<spec>/plan.md` — el contrato, el DDL, las firmas de los puertos,
   la lista de dependencias (§9b) y la sección que corresponda a la tarea.
5. `docs/context/business-rules.md` — las reglas que esos AC implementan.
6. `docs/constitution.md`.
7. La skill de convenciones que toque: `python-backend`, `react-frontend`,
   `ui-design` o `testing`.

**Verifica las dependencias.** Si la tarea depende de otra que no está marcada
como hecha, detente y dilo.

Si algo en la tarea es ambiguo, **pregunta antes de escribir código**. Una
suposición silenciosa cuesta más que una pregunta.

**Tareas sin criterios de aceptación** (andamiaje, Docker, migración, CI,
README, semillas): no tienen fase roja. Salta el paso 1, implementa contra el
DoD de la tarea y usa `chore`, `ci` o `docs` como tipo de commit.

## Paso 1 — Tests primero

Invoca al subagente `test-writer` con los criterios de aceptación de la tarea.
Revisa los tests que devuelve: ¿cubren cada AC?, ¿están nombrados con el AC?,
¿prueban comportamiento observable y no detalles de implementación?

Ejecuta la suite. **Los tests nuevos deben fallar.** Si alguno pasa sin haber
escrito la implementación, está mal escrito: o no prueba nada, o el
comportamiento ya existía.

Commit: `test(<ámbito>): criterios AC-xx a AC-yy (T-nn)`.

El hook de cierre sabe que tras un commit `test(...)` los tests están en rojo a
propósito y no bloquea. Es el único momento en que se permite parar con la
suite en rojo.

## Paso 2 — Implementar

Escribe el mínimo código que hace pasar los tests.

Respeta la dirección de las dependencias (Artículo 2). Si para que el test pase
necesitas importar un adaptador desde el dominio, la solución es un puerto, no
el import.

No agregues librerías que no estén en el plan (§9b). Si crees que hace falta
una, detente y pregunta.

Ejecuta lint, tipos y la suite rápida (`pytest -m "not slow and not
integration"`) hasta tener todo en verde. Si la tarea toca el repositorio real,
también `pytest -m integration` con la base levantada.

Commit: `feat(<ámbito>): <qué hace> (T-nn)`. El `[x]` en `tasks.md` va en
este mismo commit.

## Paso 3 — Revisar

Invoca al subagente `code-reviewer` sobre el diff de la tarea.

Clasifica cada hallazgo:
- **Bloqueante**: incumple un artículo de la constitución, una regla de negocio
  o un criterio de aceptación. Se corrige ahora.
- **Menor**: legibilidad, nombres, duplicación pequeña. Se corrige si cuesta
  poco; si no, se anota en `STATUS.md`.
- **Fuera de alcance**: pertenece a otra tarea. Se anota, no se hace.

Si la tarea toca entrada de datos, respuestas HTTP o renderizado de contenido
que escribe una persona, invoca también `security-review`.

## Paso 4 — Cerrar

Verifica el Definition of Done de la tarea, uno por uno.

Si el comportamiento cambió respecto a lo documentado, actualiza la spec y
`CHANGELOG.md` en el mismo commit (Artículo 11).

Comprueba que la tarea quedó marcada `[x]` en `tasks.md`.

Informa al humano en este formato, sin florituras:

```
T-07 terminada.
Tests: 6 nuevos (AC-03 a AC-08), 31 en total, todos en verde.
Commits: 2.
Hallazgos menores anotados: 1 (nombre de variable en politica.py).
Siguiente: T-08.
```

## Reglas duras

- Nunca marques una tarea como hecha con tests en rojo.
- Nunca desactives, saltees ni relajes un test para que pase. Si un test es
  incorrecto, se corrige explicándolo, no se silencia.
- Nunca toques archivos fuera del alcance de la tarea sin decirlo.
- Nunca implementes dos tareas en un mismo commit.
