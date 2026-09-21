# Constitución del proyecto

Principios no negociables. Prevalecen sobre cualquier sugerencia, conveniencia o
atajo. Si una instrucción contradice un artículo, gana el artículo y hay que
decirlo en voz alta.

---

### Artículo 1 — La spec manda

Nada se implementa sin una spec aprobada. Si aparece un requisito nuevo a mitad
del trabajo, se detiene la implementación, se escribe una propuesta en
`docs/changes/` y se decide. No se implementa "de paso".

### Artículo 2 — La dependencia apunta hacia adentro

`domain` no importa nada de infraestructura. `application` no importa
`adapters`. Toda dependencia externa entra por un puerto. Si para escribir un
test hace falta una base de datos o descargar un modelo, la capa está mal
diseñada.

### Artículo 3 — El test va antes

Cada criterio de aceptación tiene un test escrito antes que su implementación, y
ese test debe fallar al escribirse. Un test que pasa desde el primer momento no
está probando nada.

### Artículo 4 — Trazabilidad completa

Regla de negocio → criterio de aceptación → test → commit. Cada eslabón nombra
al anterior. Un test se llama `test_ac07_base_vacia_devuelve_puntaje_nulo`. Un
commit termina en `(T05)`. Cualquier línea de código debe poder justificarse
señalando una RN.

### Artículo 5 — Los errores son parte del contrato

Todo error tiene código, mensaje y forma predecible. Ninguna excepción llega
cruda al cliente. Ninguna traza interna se expone. Los casos borde se escriben
en la spec antes de programar, no se descubren en producción.

### Artículo 6 — Configuración fuera del código

Ningún valor de entorno vive en el código: ni cadenas de conexión, ni umbrales,
ni orígenes CORS, ni nombres de modelo. Todo entra por variables de entorno con
un valor por defecto sensato para desarrollo. Ningún secreto se versiona.

### Artículo 7 — Simplicidad deliberada

Se implementa lo que está en el alcance y nada más. Agregar una capa, un
servicio o una librería exige justificarlo contra una regla de negocio o un
requisito no funcional. La sobreingeniería es un defecto, no una virtud.

### Artículo 8 — El servidor no confía en el cliente

Toda validación relevante se ejecuta en el servidor, aunque el cliente ya la
haya hecho. La validación del frontend existe solo para la experiencia de uso.

### Artículo 9 — Fallar cerrado

Ante un fallo de un componente crítico, el sistema rechaza la operación en lugar
de completarla a medias. Nunca se persiste una frase sin haberla validado.

### Artículo 10 — El historial cuenta la historia

Commits pequeños, atómicos, en español y en formato convencional. El historial
debe leerse como el relato de cómo se construyó el sistema: primero la spec,
después los tests, después el código.

### Artículo 11 — La documentación sigue al código

Si un cambio altera el comportamiento, la spec, `decisions.md` y `CHANGELOG.md`
se actualizan en el mismo commit. Documentación desactualizada es peor que
ninguna.

### Artículo 12 — Contexto explícito

Ninguna sesión de trabajo debe depender de lo que se conversó en otra. Todo lo
que un colaborador necesita saber está en `docs/`. `STATUS.md` dice siempre
dónde quedó el trabajo.
