# Historial de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Se registra lo que cambia el comportamiento observable o las decisiones, no cada
commit.

---

## [No publicado]

### Agregado
- Documentación de contexto: producto, reglas de negocio, arquitectura, glosario.
- Constitución del proyecto con 12 artículos.
- Especificación `001-validacion-semantica` con 19 reglas de negocio, 22
  criterios de aceptación y 26 casos borde.
- Harness de trabajo con agentes: skills de spec, plan, implementación y cierre
  de sesión; subagentes revisores de spec y plan, tests y código; hooks de
  verificación.
- Decisiones D-01 a D-11 registradas.
- Andamiaje del repositorio: backend con `pyproject.toml` (ruff, mypy estricto,
  marcadores `slow` e `integration`), esqueleto de Vite con TypeScript estricto,
  `.env.example`, `.gitignore` y `.gitattributes` (T-01).
- D-12: `@types/react`, `@types/react-dom` y Testing Library 15 en el frontend.

### Cambiado (auditoría previa al primer commit)
- Se embebe el texto normalizado, no el original (RN-02, RN-05).
- El duplicado exacto confirmado genera su embedding al guardar (RN-14, AC-11b).
- Aplicación síncrona de punta a punta (D-10); sin límite de peticiones en la
  aplicación (D-11).
- Puntaje recortado a [0, 1] y comparado sin redondear (RN-05, B-15, B-16).
- Desempate por identificador también en el duplicado exacto y en el listado
  (RN-08, RN-17).
- La normalización de vectores es del dominio, no del proveedor (RN-19, D-09).
- Longitud medida sobre el texto normalizado, en el dominio (RN-01, AC-02).

---

<!--
Plantilla para nuevas entradas:

## [0.1.0] - AAAA-MM-DD

### Agregado
- ...

### Cambiado
- ...

### Corregido
- ...

### Eliminado
- ...
-->
