---
name: plan
description: Convierte una spec aprobada en un plan técnico (contrato de API, modelo de datos, puertos, estrategia de pruebas) y en una lista de tareas atómicas. Úsala después de /spec y antes de implementar.
---

# Escribir el plan técnico y las tareas

Aquí decides **cómo** se construye lo que la spec definió. La spec no se toca:
si descubres que falta algo, se abre una propuesta en `docs/changes/`.

## Requisito previo

La spec debe estar aprobada. Si `spec.md` no dice `Estado: aprobada`, detente y
dilo.

Lee `docs/context/architecture.md`, `docs/constitution.md` y `docs/decisions.md`
antes de proponer nada. Si tu plan contradice una decisión vigente, o la
justificas y propones una decisión que la sustituya, o la respetas.

## Parte 1 — `plan.md`

Incluye, en este orden:

1. **Contrato de la API.** Cada endpoint con petición, respuesta exitosa y
   todas las respuestas de error, con ejemplos JSON reales. El catálogo de
   errores va en una tabla: HTTP, código, cuándo ocurre.
2. **Modelo de datos.** DDL completo, índices, y una nota explicando cada
   decisión no obvia: por qué hay o no hay una restricción de unicidad, por qué
   ciertos campos admiten nulos, por qué se duplica un dato de configuración en
   la fila.
3. **Puertos y adaptadores.** Las firmas de los `Protocol` y qué adaptadores los
   implementan, incluidos los dobles de prueba.
4. **Lógica del dominio.** Los casos de uso paso a paso, en prosa numerada. No
   código completo, sí firmas y secuencia.
5. **Frontend.** Estructura de carpetas, máquina de estados de la interfaz y las
   reglas de interacción.
6. **Seguridad.** Tabla de medida y dónde se aplica.
7. **Estrategia de pruebas.** Qué se prueba en cada nivel y con qué dobles.
8. **Entorno.** Servicios de Compose, volúmenes, healthchecks.
9. **Dependencias.** Lista cerrada de librerías y herramientas, de ejecución y
   de desarrollo, en backend y frontend. Nada en forma de "X o Y".
10. **Orden de construcción** y qué se sacrifica primero si falta tiempo.

Regla: cada decisión técnica del plan debe poder señalar la regla de negocio o
el requisito no funcional que la justifica. Si no puede, es sobreingeniería y se
elimina (Artículo 7).

## Parte 2 — `tasks.md`

Divide el trabajo en tareas que cumplan todas estas condiciones:

- Una tarea produce **un commit** (o dos: el de tests y el de implementación).
- Una tarea se puede verificar sola: tiene un Definition of Done concreto, y
  ese DoD se cumple **solo con sus dependencias hechas**, sin adelantar nada
  de tareas posteriores.
- Una tarea menciona qué criterios de aceptación cubre, o dice que no cubre
  ninguno.
- Una tarea declara de qué otras depende.
- Una tarea trae una estimación en S, M o L.

Ordena las tareas de forma que la lógica de negocio quede terminada y probada
primero y lo superficial al final. Incluye al final una **ruta crítica** y una
lista explícita de qué se descarta si el tiempo se acorta.

## Después

1. Invoca al subagente `spec-reviewer` en **modo plan** sobre `plan.md` y
   `tasks.md`. Corrige los bloqueantes antes de seguir.
2. Presenta al humano el plan y las tareas, resumiendo en tres líneas las
   decisiones técnicas más importantes.
3. Registra en `docs/decisions.md` las decisiones nuevas, con alternativas
   descartadas y costo aceptado.
4. Con la aprobación, haz el commit:
   `docs(plan): plan técnico y tareas de <slug>`.
