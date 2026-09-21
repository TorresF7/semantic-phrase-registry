# Patrones de diseño aplicados

Cada patrón de esta lista está aquí porque resuelve un problema concreto del
sistema. Ninguno está por completitud académica.

La regla que los gobierna es el Artículo 7 de la constitución: un patrón que no
se puede justificar señalando una regla de negocio o un requisito no funcional
es sobreingeniería y se elimina.

---

## Backend

### Puertos y adaptadores (arquitectura hexagonal)

**Dónde:** `ports/` declara las interfaces; `adapters/` las implementa.

**Problema que resuelve.** El sistema depende de dos cosas lentas y externas:
PostgreSQL y un modelo de 470 MB. Sin esta separación, cada test de la lógica de
validación necesitaría ambas, la suite tardaría minutos y nadie la correría.
Además, NF-08 exige poder cambiar de proveedor de IA sin tocar el negocio.

**Cómo se verifica.** El hook de cierre ejecuta un `grep` que falla si
`domain/` o `application/` importan algo de `adapters/`. No es una convención
que se recuerda, es una comprobación que corre sola.

### Repositorio

**Dónde:** `ports/repositorio.py` y `adapters/persistence/`.

**Problema que resuelve.** La consulta del vecino más cercano usa el operador
`<=>` de pgvector, que es específico de PostgreSQL. Encapsularla detrás de
`buscar_mas_parecida(embedding)` permite que el caso de uso exprese su intención
sin conocer SQL, y que el `RepositorioEnMemoria` de los tests implemente la
misma operación con una lista.

**Detalle importante.** El repositorio traduce entre modelo ORM y entidad de
dominio. Los modelos SQLAlchemy no salen de `adapters/persistence/`: si salieran,
el dominio quedaría atado al ORM por la puerta de atrás.

### Estrategia

**Dónde:** `ProveedorEmbeddings`, con `HuggingFaceEmbedder` y `FakeEmbedder`.

**Problema que resuelve.** Los criterios AC-04, AC-05 y AC-06 necesitan puntajes
exactos: 0.89 para el caso sobre el umbral, 0.42 para el de debajo, un empate
para el desempate. Con el modelo real esos valores no se pueden fijar, dependen
de lo que devuelva el modelo. El embedder falso los programa.

Es también lo que haría posible pasar a un proveedor remoto: un adaptador nuevo,
cero cambios en el negocio.

### Inyección de dependencias por constructor

**Dónde:** los casos de uso reciben sus puertos al construirse; `Depends` de
FastAPI los provee en la capa HTTP.

**Problema que resuelve.** Permite sustituir dependencias en los tests con
`app.dependency_overrides` sin parchear módulos ni usar `monkeypatch`.

**Lo que se descarta.** Un contenedor de inyección de dependencias. Con dos
casos de uso y dos puertos, `Depends` sobra.

### Objetos de valor y funciones puras

**Dónde:** `domain/normalizacion.py`, `domain/politica.py`,
`ResultadoValidacion`.

**Problema que resuelve.** La normalización (RN-02) y la política de umbral
(RN-06) son las dos reglas más propensas a error sutil: un `>` en lugar de `>=`
cambia el comportamiento en el caso borde B-08 y ningún test de integración lo
detectaría. Como funciones puras se prueban directamente, con decenas de casos,
en milisegundos.

### Traducción de excepciones en la frontera

**Dónde:** `HuggingFaceEmbedder` convierte cualquier fallo en
`ErrorProveedorEmbeddings`; el manejador global de FastAPI lo convierte en 503.

**Problema que resuelve.** Sin esto, una excepción de `sentence_transformers`
viajaría hasta la capa HTTP, y el dominio quedaría acoplado a los tipos de error
de una librería. También es lo que garantiza RN-16: ninguna traza interna llega
al cliente.

---

## Frontend

### Máquina de estados con unión discriminada

**Dónde:** `EstadoFormulario` en `hooks/useValidacion.ts`.

**Problema que resuelve.** Con banderas booleanas sueltas (`cargando`, `error`,
`resultado`) son representables estados contradictorios: cargando y con error a
la vez, o resultado presente mientras se valida. Con una unión discriminada esos
estados **no se pueden escribir**, y el compilador obliga a tratar cada caso.

### Adaptador de API

**Dónde:** `api/cliente.ts`.

**Problema que resuelve.** Ningún componente conoce URLs, `fetch` ni códigos
HTTP. El `409` de RN-12 no es una excepción inesperada: el cliente lo traduce a
un valor del tipo discriminado, porque es una respuesta prevista del contrato.

### Hooks personalizados

**Dónde:** `useFrases`, `useValidacion`.

**Problema que resuelve.** Separan la lógica de estado del renderizado, de forma
que se prueban sin montar componentes.

### Presentacional y contenedor

**Dónde:** `App` orquesta; `FormularioFrase`, `ListaFrases` y `AlertaDuplicado`
reciben props y emiten eventos.

**Problema que resuelve.** Los componentes de presentación se prueban con props,
sin red ni contexto. `AlertaDuplicado` se verifica pasándole un resultado
inventado.

### Elevación del estado

**Dónde:** el estado del formulario vive en `App`.

**Problema que resuelve.** Guardar una frase tiene que refrescar la lista. Con
el estado repartido harían falta trucos de sincronización entre hermanos.

---

## Patrones descartados, y por qué

Saber qué se descartó vale tanto como saber qué se usó.

| Patrón | Por qué no |
|---|---|
| Gestión de estado global (Redux, Zustand) | El estado cabe en dos hooks y no se comparte entre rutas, porque no hay rutas |
| Context de React | No hay prop drilling: el árbol tiene dos niveles |
| Render props, componentes de orden superior | Los hooks ya resuelven la reutilización de lógica |
| Componentes compuestos | Hay uno solo y no se reutiliza |
| Contenedor de inyección de dependencias | Dos casos de uso y dos puertos; `Depends` basta |
| Repositorio genérico con `TypeVar` | Una sola entidad. La generalización no tendría un segundo caso que la justifique |
| CQRS | No hay asimetría entre lectura y escritura que lo motive |
| Unidad de trabajo | Una sola operación transaccional; la sesión de SQLAlchemy ya la cubre |
| Capa de servicios además de los casos de uso | Sería una indirección sin responsabilidad propia |
| Patrón observador o bus de eventos | No hay nada que reaccione a la creación de una frase |

---

## Cómo se comprueba que esto no es solo un documento

| Afirmación | Comprobación |
|---|---|
| El dominio no depende de infraestructura | `grep` automático en el hook de cierre |
| Los puertos son intercambiables | La suite de `application/` corre entera con dobles |
| La política de umbral es pura | Sus tests no construyen ningún adaptador |
| Los estados imposibles no existen | `tsc --noEmit` en modo estricto, en el hook de cierre y en CI |
| Ningún componente llama a `fetch` | `grep -rn "fetch(" src/components/` devuelve vacío, en el hook de cierre |
