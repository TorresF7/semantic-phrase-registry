# Propuestas de cambio

Cuando aparece un requisito nuevo o hay que alterar el comportamiento de una
spec ya aprobada, **no se toca la spec directamente**. Se crea aquí una
propuesta, se decide, y solo entonces se aplica.

Esto existe porque durante la implementación siempre surgen cosas. Si se meten
"de paso", al final nadie sabe por qué el sistema hace lo que hace.

## Flujo

1. Crear `docs/changes/CH-nn-<slug>.md` con la plantilla de abajo.
2. Revisarla (el subagente `spec-reviewer` ayuda).
3. Decidir: aceptada o rechazada. **La decisión es humana.**
4. Si se acepta: actualizar `business-rules.md` y la spec afectada, agregar la
   decisión a `decisions.md` si corresponde, anotar en `CHANGELOG.md`, y mover
   este archivo a `docs/changes/aplicados/`.
5. Si se rechaza: se conserva con el motivo. Saber qué se descartó y por qué
   vale tanto como saber qué se hizo.

## Plantilla

```markdown
# CH-nn — <título corto>

**Fecha:** AAAA-MM-DD
**Estado:** propuesta | aceptada | rechazada | aplicada
**Afecta a:** RN-xx, spec 001, AC-xx

## Qué se propone cambiar
Una o dos frases.

## Por qué
Qué problema aparece si no se hace. Si no hay problema concreto, no hay cambio.

## Impacto
- Reglas de negocio afectadas:
- Criterios de aceptación a agregar, modificar o eliminar:
- Tareas afectadas:
- Tests que hay que reescribir:

## Alternativas consideradas
Incluida la de no hacer nada.

## Decisión
Quién decidió, cuándo y con qué argumento.
```

## Índice

| ID | Título | Estado |
|---|---|---|
| [CH-01](aplicados/CH-01-ac18-duplicado-exacto-sin-modelo.md) | AC-18: el duplicado exacto se valida aunque el modelo no haya cargado | aplicada |
| [CH-02](aplicados/CH-02-rediseno-interfaz.md) | Rediseño de la interfaz en una sola pantalla | aplicada |
| [CH-03](aplicados/CH-03-columnas-estables-tabla.md) | Columnas estables en la tabla de frases | aplicada |
| [CH-04](CH-04-caracteres-invisibles.md) | Caracteres invisibles (`Cf`) en la normalización | propuesta |
