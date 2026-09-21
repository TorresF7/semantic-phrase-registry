# Estado actual

> Este archivo es el punto de entrada de cada sesión nueva. Se actualiza con
> `/handoff` al cerrar cada sesión. Si lo que dice aquí no coincide con el
> repositorio, gana el repositorio y hay que corregir este archivo.

**Última actualización:** 2026-09-21 — sesión 0 (preparación del harness y
auditoría de la documentación)

---

## Dónde estamos

Fase: **spec aprobada y auditada, implementación no iniciada.**

El contexto, las reglas de negocio, la constitución y la spec de la
funcionalidad 001 están escritos y pasaron una auditoría de coherencia antes
del primer commit. No existe todavía código de aplicación.

## Hecho

- [x] Contexto del producto, reglas de negocio, arquitectura y glosario
- [x] Constitución del proyecto
- [x] Spec, plan y tareas de `001-validacion-semantica`
- [x] Skills, subagentes y hooks de Claude Code
- [x] Auditoría de la documentación y del harness (ver `CHANGELOG.md`)

## En curso

Nada en curso.

## Siguiente

`T-00` — Comprobación del modelo con frases reales. Ver
`docs/specs/001-validacion-semantica/tasks.md`. Sus puntajes se anotan aquí,
en "Notas para la siguiente sesión".

## Dudas abiertas

| # | Duda | Quién decide | Estado |
|---|---|---|---|
| Q-01 | Valor definitivo del umbral por defecto | Se resuelve con el script de calibración en T-11 | abierta |
| Q-02 | Si se despliega en un servidor público, ¿hace falta autenticación básica en el proxy? | Franklin | abierta |

## Notas para la siguiente sesión

- El hook `Stop` (`.claude/hooks/verificar.sh`) no bloquea cuando el último
  commit es `test(...)`: es la fase roja declarada del ciclo. En cualquier otro
  momento, tests en rojo bloquean el cierre.
- La suite rápida es `pytest -m "not slow and not integration"`. La de
  integración necesita `docker compose up -d db` y usa `TEST_DATABASE_URL`.
- Puntajes de T-00: pendientes.

---

## Cómo retomar

1. Lee este archivo.
2. Lee `docs/specs/001-validacion-semantica/tasks.md` y busca la primera tarea
   sin marcar.
3. Ejecuta `/implement T-XX` con esa tarea.
4. Al terminar la sesión, ejecuta `/handoff`.
