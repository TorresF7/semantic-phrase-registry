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

`T-01` — Andamiaje del repositorio. Ver
`docs/specs/001-validacion-semantica/tasks.md`.

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
- Puntajes de T-00 (`paraphrase-multilingual-MiniLM-L12-v2`, CPU, texto
  normalizado según RN-02, vectores de norma 1):

  | Tipo | Frase A | Frase B | Coseno |
  |---|---|---|---|
  | Estrella | El pago fue rechazado por el banco | La entidad bancaria rechazó la transacción | 0.8735 |
  | Paráfrasis | El pedido llegará en tres días | Recibirás tu compra en un plazo de tres días | 0.8512 |
  | Paráfrasis | No pudimos procesar su solicitud | Su petición no se ha podido tramitar | 0.8465 |
  | Sin relación | El pago fue rechazado por el banco | Mañana lloverá en la costa | -0.0330 |
  | Sin relación | Actualiza tu contraseña cada tres meses | El restaurante abre a las ocho | 0.0125 |
  | Negación | El pago fue aprobado | El pago no fue aprobado | 0.6458 |

  El par estrella supera 0.80: el ejemplo de `product.md` y AC-04 se quedan
  como están, y en el README aparece como **87%**. El coseno negativo del
  primer par sin relación confirma que el recorte a [0, 1] de RN-05 hace falta.
  La negación queda en 0.65, bajo el umbral inicial: el margen entre ella y la
  paráfrasis más baja (0.85) es el dato a vigilar en la calibración de T-11.
  La carga del modelo tardó ~23 s en frío (NF-03: una sola vez por proceso).

---

## Cómo retomar

1. Lee este archivo.
2. Lee `docs/specs/001-validacion-semantica/tasks.md` y busca la primera tarea
   sin marcar.
3. Ejecuta `/implement T-XX` con esa tarea.
4. Al terminar la sesión, ejecuta `/handoff`.
