---
name: handoff
description: Cierra la sesión dejando el contexto listo para la siguiente. Actualiza STATUS.md, decisions.md y CHANGELOG.md. Úsala siempre al terminar de trabajar.
---

# Cerrar sesión

Esto existe para cumplir el Artículo 12: ninguna sesión debe depender de lo que
se conversó en otra. La siguiente sesión, tuya o de otra persona, arranca leyendo
`STATUS.md` y nada más.

## Procedimiento

### 1. Comprobar el estado real

```bash
git status --short
git log --oneline -10
```

Ejecuta lint y tests. Si algo está en rojo, eso va en `STATUS.md` como lo
primero a resolver. **No maquilles el estado.**

### 2. Actualizar `docs/STATUS.md`

Reescríbelo completo con:

- Fecha y número de sesión.
- Fase actual del proyecto, en una línea.
- **Hecho**: tareas completadas, con su identificador.
- **En curso**: si quedó algo a medias, qué archivos están tocados y cuál era la
  siguiente acción concreta. Sé específico: "falta el manejador de 503 en
  `adapters/api/errores.py`, el test `test_ac13` está escrito y en rojo".
- **Siguiente**: la tarea que toca, por identificador.
- **Dudas abiertas**: tabla con la duda, quién decide y su estado. Cierra las
  que se resolvieron durante la sesión.
- **Notas para la siguiente sesión**: trampas encontradas, comandos útiles,
  cosas que no funcionaron y por qué.

### 3. Actualizar `docs/decisions.md`

¿Se tomó alguna decisión técnica durante la sesión, aunque haya sido pequeña?
Agrégala como `D-nn` con: qué se decidió, por qué, qué se descartó y qué costo
se acepta.

Decisiones que suelen olvidarse: elegir una librería, cambiar la forma de una
respuesta, alterar un valor por defecto, resolver un caso borde de una manera
concreta.

### 4. Actualizar `docs/CHANGELOG.md`

Solo lo que cambia comportamiento observable o decisiones. No listes cada
commit.

### 5. Marcar tareas

Sincroniza `tasks.md` con la realidad. Una tarea a medias sigue sin marcar, y su
estado real se describe en `STATUS.md`.

### 6. Commit de cierre

```
docs(estado): cierre de sesión <n> — <resumen en pocas palabras>
```

### 7. Resumen al humano

Máximo seis líneas: qué se completó, qué quedó pendiente, qué decisiones se
tomaron y con qué comando retomar.

## Regla dura

Si los tests están en rojo o hay trabajo a medias, dilo con claridad en el
resumen y en `STATUS.md`. Una sesión que cierra fingiendo que todo está bien
cuesta el doble de tiempo a la siguiente.
