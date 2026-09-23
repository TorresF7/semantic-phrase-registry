# Documentación del proyecto

Mapa de los documentos. Si buscas algo, empieza aquí.

## Por dónde empezar

| Si quieres... | Lee |
|---|---|
| Entender qué es esto y por qué existe | [`context/product.md`](context/product.md) |
| Saber qué hace exactamente el sistema | [`context/business-rules.md`](context/business-rules.md) |
| Entender cómo está construido | [`context/architecture.md`](context/architecture.md) |
| Saber por qué se tomó una decisión técnica | [`decisions.md`](decisions.md) |
| Retomar el trabajo donde quedó | [`STATUS.md`](STATUS.md) |

## Los documentos

### Contexto — qué es el sistema

- **[`context/product.md`](context/product.md)** — el problema que se resuelve,
  quiénes lo usan, qué está dentro y fuera de alcance, y los requisitos no
  funcionales con objetivos medibles.
- **[`context/business-rules.md`](context/business-rules.md)** — las 19 reglas
  de negocio numeradas. **Es la fuente única de verdad del comportamiento.**
  Cualquier discusión sobre qué debe hacer el sistema se resuelve aquí.
- **[`context/architecture.md`](context/architecture.md)** — las cuatro capas,
  los diagramas de estructura y de flujo, el modelo de embeddings, la
  configuración y el enfoque de escalabilidad.
- **[`context/patterns.md`](context/patterns.md)** — los patrones de diseño
  aplicados, el problema que resuelve cada uno, y los que se descartaron con su
  motivo.
- **[`context/glossary.md`](context/glossary.md)** — el vocabulario común.
  Mismo término en el código, los tests, los commits y la interfaz.

### Gobierno — cómo se trabaja

- **[`constitution.md`](constitution.md)** — 12 principios no negociables. Ante
  un conflicto, ganan estos.
- **[`decisions.md`](decisions.md)** — cada decisión técnica con su fecha, su
  motivo, las alternativas descartadas y el costo aceptado.
- **[`changes/`](changes/) ** — propuestas de cambio sobre specs ya aprobadas.
  Nada se altera sobre la marcha.

### Especificaciones — qué se construye

- **[`specs/001-validacion-semantica/spec.md`](specs/001-validacion-semantica/spec.md)**
  — historias de usuario, 25 criterios de aceptación en Dado/Cuando/Entonces, y
  29 casos borde decididos.
- **[`specs/001-validacion-semantica/plan.md`](specs/001-validacion-semantica/plan.md)**
  — contrato de la API, modelo de datos, puertos, seguridad y estrategia de
  pruebas.
- **[`specs/001-validacion-semantica/tasks.md`](specs/001-validacion-semantica/tasks.md)**
  — 30 tareas atómicas con dependencias y ruta crítica.

### Estado

- **[`STATUS.md`](STATUS.md)** — dónde quedó el trabajo, qué sigue y qué dudas
  están abiertas. Se actualiza al cerrar cada sesión.
- **[`CHANGELOG.md`](CHANGELOG.md)** — historial de cambios de comportamiento.

## La cadena de trazabilidad

Todo el sistema se sostiene sobre esta cadena. Cualquier línea de código debe
poder recorrerla hacia atrás hasta una necesidad del producto:

```
product.md  →  RN-nn  →  AC-nn  →  test_acnn_...  →  commit (T-nn)
 el problema   la regla   el criterio   la prueba        el código
```

Si un eslabón falta, algo está mal: código sin regla que lo justifique, regla
sin criterio que la verifique, o criterio sin test que lo pruebe.
