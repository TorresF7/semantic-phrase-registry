# Registro de decisiones

Cada decisión técnica relevante, con su fecha, su motivo y lo que se descartó.
Se agregan al final. Una decisión no se borra: si cambia, se agrega otra que la
sustituye y se marca la anterior como SUSTITUIDA.

Formato: `D-nn`.

---

### D-01 — PostgreSQL con pgvector para la búsqueda de similitud
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** Los embeddings se almacenan en una columna `vector(384)` y la
búsqueda del vecino más cercano se resuelve en SQL con el operador `<=>`.

**Por qué.** El requisito no funcional NF-01 exige p95 por debajo de 400 ms con
100 000 frases. Cargar todos los vectores en memoria de la aplicación crece de
forma lineal en tiempo y memoria por cada petición, y empeora con varias
réplicas. El motor de base de datos con un índice HNSW resuelve la búsqueda de
forma sublineal.

**Alternativas descartadas.**
- *NumPy en memoria*: más simple de escribir, insostenible con volumen y
  con varias réplicas.
- *Base vectorial dedicada (Qdrant, Pinecone)*: añade un servicio más a operar
  para un volumen que PostgreSQL maneja sin problema, y el resto del sistema ya
  es relacional.

**Costo aceptado.** HNSW es un índice aproximado; en casos raros puede no
devolver el vecino exacto. Aceptable para detectar duplicados.

---

### D-02 — Modelo multilingüe `paraphrase-multilingual-MiniLM-L12-v2`
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** Se usa ese modelo de `sentence-transformers`, de 384 dimensiones,
ejecutándose localmente en CPU.

**Por qué.** Las frases del dominio son en español. Los modelos entrenados solo
en inglés producen puntajes poco fiables con texto en castellano. Este está
entrenado específicamente para reconocer paráfrasis, que es literalmente el
problema. Corre sin GPU y no requiere clave ni conexión a ningún servicio de
pago.

**Alternativas descartadas.**
- *`all-MiniLM-L6-v2`*: más popular y ligero, pero solo inglés.
- *API de embeddings de un proveedor comercial*: añade costo por petición,
  dependencia de red y envío de datos fuera de la organización. El puerto
  `ProveedorEmbeddings` deja la puerta abierta a cambiarlo si algún día se
  quiere.

---

### D-03 — Arquitectura hexagonal ligera
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** Cuatro carpetas en el backend: `domain`, `application`, `ports`,
`adapters`. Las dependencias externas entran por `typing.Protocol`. (Las
"cuatro capas" de `architecture.md` —interfaz, negocio, datos, IA— son la vista
funcional; estas carpetas son cómo se reparten en código.)

**Por qué.** El sistema integra tres cosas que cambian a ritmos distintos:
interfaz, datos y un proveedor de IA. Separarlas explícitamente evita que un
cambio de modelo arrastre cambios en la lógica de negocio. Además permite probar
toda la lógica de validación con
un embedder falso, sin descargar el modelo ni levantar PostgreSQL, lo que
mantiene la suite de tests en segundos.

**Alternativas descartadas.**
- *Estructura plana tipo `routers/services/models`*: suficiente para un CRUD,
  pero mezcla la política de umbral con el acceso a datos.
- *Framework de inyección de dependencias*: innecesario. `Depends` de FastAPI
  basta.

---

### D-04 — Revalidación en el servidor al guardar
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** `POST /frases` no confía en el resultado de validación que trae el
cliente. Recalcula la validación completa antes de decidir.

**Por qué.** Entre que una persona valida y presiona guardar pueden pasar
minutos. Otra persona pudo registrar una frase parecida en ese intervalo. Si el
servidor aceptara el veredicto del cliente, el duplicado entraría sin alerta.
Es también una superficie de manipulación trivial desde el cliente.

**Costo aceptado.** Una generación de embedding adicional por guardado. Son
milisegundos.

---

### D-05 — Sin autenticación
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** No se implementa autenticación ni gestión de usuarios.

**Por qué.** El dominio no tiene concepto de propiedad: las frases son de un
repositorio compartido y ninguna regla de negocio depende de quién las creó.
Agregar autenticación introduciría entidades, pantallas y tests que no sirven a
ninguna RN.

**Mitigación en despliegue.** Si la aplicación se publica en una red abierta, la
protección va en la capa de infraestructura: límite de peticiones por IP y, de
ser necesario, autenticación básica en el proxy inverso. La integración con el
SSO corporativo queda documentada como siguiente paso.

---

### D-06 — Validación síncrona, sin colas
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** La validación se resuelve dentro de la misma petición HTTP. No hay
broker, ni workers, ni notificaciones asíncronas.

**Por qué.** La persona está frente a la pantalla esperando el resultado para
decidir si confirma o cancela. Un flujo asíncrono obligaría a sondear o a abrir
un canal en tiempo real para devolver algo que tarda milisegundos.

**Cuándo cambiaría.** Si se cambia el modelo de embeddings, habría que
recalcular el vector de todas las frases existentes. Ese sí es un trabajo por
lotes y ahí una cola tendría sentido. Está fuera del alcance actual.

---

### D-07 — Umbral calibrado con datos, no elegido a ojo
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** El valor por defecto del umbral se determina con un script que
evalúa un conjunto de pares de frases en español etiquetados como equivalentes o
distintos, y reporta precisión y exhaustividad para varios umbrales.

**Por qué.** El umbral es el único parámetro que decide el comportamiento visible
del sistema. Elegir 0.8 porque "suena bien" es indefendible. Con el reporte se
puede explicar qué se gana y qué se pierde al moverlo, y la organización puede
ajustarlo por entorno sin tocar código.

---

### D-08 — TypeScript en el frontend
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** React con TypeScript en modo estricto, no JavaScript.

**Por qué.** El contrato de la API tiene formas con campos que pueden ser nulos
según el caso: puntaje nulo con base vacía, frase más parecida ausente. Los tipos
obligan a tratar esos casos explícitamente en la interfaz en lugar de descubrirlos
en tiempo de ejecución.

---

### D-09 — Similitud coseno sobre vectores normalizados por el dominio
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** La medida de similitud es el coseno. Todo embedding pasa por
`domain/vectores.py::normalizar_vector` antes de compararse y de persistirse,
sin importar qué proveedor lo generó. El adaptador de Hugging Face además pide
`encode(..., normalize_embeddings=True)`, pero eso es una optimización, no la
garantía.

**Por qué el coseno.** El modelo fue entrenado con un objetivo basado en coseno:
usar otra medida introduciría un desajuste entre cómo se entrenó y cómo se usa.

**Por qué normalizar, y por qué en el dominio.** El coseno ya divide por las
normas, así que normalizar **no cambia el puntaje**; no es una cuestión de
precisión. Se normaliza por tres motivos prácticos: los vectores guardados
quedan homogéneos aunque mañana los genere otro proveedor (NF-08); coseno y
producto interno pasan a ser intercambiables, lo que deja abierto usar `<#>` si
alguna vez hace falta; y el doble de prueba en memoria puede comparar con un
producto punto trivial. Ponerlo en el dominio, y no confiar en el proveedor,
convierte RN-19 en una regla verificable con el embedder falso (AC-17) en lugar
de una promesa de una librería externa.

**Alternativas evaluadas.**
- *Distancia euclidiana*: sobre vectores normalizados es equivalente al coseno,
  porque `‖a−b‖² = 2(1 − cos)`. Mismo orden; es la misma decisión escrita de
  otra forma.
- *Producto interno (`<#>`)*: idéntico al coseno sobre vectores normalizados y
  algo más rápido. Se mantiene `<=>` porque expresa la intención; la diferencia
  es despreciable a este volumen.
- *Medidas léxicas (Jaccard, Levenshtein, trigramas)*: comparan letras, no
  significado. No resuelven el problema que motiva el sistema, aunque sí lo
  complementarían (ver abajo).

**Lo que sí sería mejor, y por qué no se hace ahora.**
La mejora real no es cambiar de medida, sino agregar una **segunda etapa**:

1. *Cross-encoder para reordenar.* Un bi-encoder, que es lo que usamos, codifica
   cada frase por separado y compara vectores; es rápido y permite precalcular.
   Un cross-encoder procesa las dos frases juntas y es notablemente más preciso,
   pero no se puede precalcular: hay que ejecutar el modelo por cada par. El
   esquema habitual es recuperar las K candidatas con el bi-encoder y reordenar
   solo esas K con el cross-encoder. Queda fuera de alcance porque multiplica la
   latencia y el volumen actual no lo justifica.
2. *Búsqueda híbrida.* Combinar el puntaje semántico con uno léxico, como la
   similitud de trigramas de PostgreSQL, capturaría duplicados con errores
   tipográficos que el modelo puede pasar por alto.

Ambas están documentadas como siguiente paso. El puerto `ProveedorEmbeddings` y
la política de umbral aislada permiten añadirlas sin tocar el resto.

---

### D-10 — Aplicación síncrona de punta a punta
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** Puertos, casos de uso, repositorio y endpoints son síncronos
(`def`). SQLAlchemy con la sesión síncrona y el driver `psycopg` 3. No hay
`async`, ni `asyncpg`, ni `pytest-asyncio`.

**Por qué.** Las dos operaciones costosas son de CPU (generar el embedding) y
de base de datos con una sola consulta por petición. `encode()` bloquea el hilo
que lo llama; dentro de un endpoint `async def` congelaría el bucle de eventos
para todas las peticiones. FastAPI ejecuta los endpoints `def` en un grupo de
hilos, que es exactamente el modelo de concurrencia que esto necesita. Además,
un solo modo evita tener dobles de prueba en dos sabores y elimina toda una
categoría de errores ("olvidé el `await`").

**Alternativas descartadas.**
- *Todo asíncrono con `run_in_threadpool` alrededor de `encode()`*: funciona,
  pero añade complejidad para obtener el mismo comportamiento.
- *Mezcla*: peor que cualquiera de las dos puras.

**Costo aceptado.** Ninguno medible a este volumen.

---

### D-11 — Sin límite de peticiones en la aplicación
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** La API no implementa límite de peticiones por IP. Si se despliega
en una red abierta, el límite va en el proxy inverso (T-19), junto con HTTPS y
las cabeceras de seguridad.

**Por qué.** Ninguna regla de negocio ni requisito no funcional lo pide.
Implementarlo en la aplicación tiene tres problemas: detrás de nginx todas las
peticiones llegan con la IP del proxy, así que el límite sería global y no por
persona; un contador en memoria por proceso contradice NF-04, porque cada
réplica llevaría su propia cuenta; y la suite de API, que hace más de sesenta
peticiones desde el mismo cliente, recibiría `429` intermitentes.

**Alternativas descartadas.**
- *`slowapi` en la aplicación*: es lo que se había planteado. Descartado por lo
  anterior.

**Costo aceptado.** En desarrollo y en una red interna no hay protección
contra abuso. Es el mismo supuesto de D-05.

---

### D-12 — Tipos de React y Testing Library 15 en el frontend
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** Se añaden `@types/react` y `@types/react-dom` (rama 18) a las
dependencias de desarrollo del frontend. `@testing-library/react` se fija en
la rama 15.

**Por qué.** React 18 no trae sus propios tipos: sin `@types/*`, TypeScript en
modo estricto (D-08) no compila ni un solo componente. Faltaban en la lista
cerrada del plan §9b. La rama 16 de Testing Library pide
`@testing-library/dom` como dependencia par, que tampoco está en §9b; la 15 la
incluye, es compatible con React 18 y evita añadir otra dependencia.

**Alternativas descartadas.**
- *React 19, que no necesita instalar los tipos aparte*: el stack fija React 18.
- *Testing Library 16 más `@testing-library/dom`*: una dependencia más sin
  ninguna ventaja con React 18.

**Costo aceptado.** Pasar a React 19 obligará a revisar estas dos versiones.

---

### D-13 — Compose arranca sin `.env` y el backend migra al iniciar
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** Cada variable de `docker-compose.yml` tiene un valor por defecto
de desarrollo (`${VAR:-valor}`), y el `.env` de la raíz se carga como
`env_file` opcional. Dentro de Compose, `DATABASE_URL` se fija siempre contra
el servicio `db`, por encima de lo que traiga el `.env`. El contenedor del
backend ejecuta `alembic upgrade head && exec uvicorn ...`. El frontend se
sirve con `nginxinc/nginx-unprivileged`.

**Por qué.** NF-07 exige que `docker compose up` funcione en una máquina
limpia sin pasos manuales, y copiar un `.env` lo es. El `.env` de desarrollo
apunta a `localhost`, que dentro del contenedor no es la base. Migrar al
arrancar deja el esquema listo sin intervención; si la migración falla, uvicorn
no arranca (Artículo 9). La variante sin privilegios de nginx cumple el plan §6
sin tocar la configuración de usuarios.

**Alternativas descartadas.**
- *`.env` obligatorio*: rompe NF-07.
- *Servicio aparte para migrar*: un servicio más sin necesidad con una sola
  réplica.

**Costo aceptado.** Con varias réplicas, todas intentarían migrar a la vez.
Alembic lo serializa con la transacción, pero en producción convendría un paso
de migración separado.

---

### D-14 — Configuración con nombres en español y alias a las variables
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** `Configuracion` usa campos en español (`umbral_similitud`,
`nombre_modelo`...) con `validation_alias` a las variables de entorno en inglés
de `architecture.md`. `HF_HOME` no forma parte de la clase. El `.env` se busca
en la raíz del repositorio, y los tests construyen con `_env_file=None`.
`requires-python` es `>=3.11`, con ruff y mypy apuntando a 3.11.

**Por qué.** El código sigue el glosario y las variables siguen la tabla ya
publicada. `HF_HOME` la lee `huggingface_hub` directamente, y un campo que nadie
consulta es la abstracción sin uso que prohíbe el Artículo 7. Sin
`_env_file=None`, el `.env` de cada máquina cambiaría el resultado de los tests.
El `>=` permite desarrollar con el Python local (3.13) mientras la imagen usa
3.11.

**Alternativas descartadas.**
- *Campos con el nombre de la variable (`similarity_threshold`)*: rompe la
  regla de nombres en español.

**Costo aceptado.** Una sintaxis moderna de 3.12 o posterior no la detecta ruff;
la detectaría la imagen al construirse.

---

### D-15 — Migración inicial escrita a mano
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** La migración `0001` traduce el DDL del plan §2 a mano, sin
`target_metadata` ni `--autogenerate`. La dimensión 384 está escrita en la
migración y no se lee de `EMBEDDING_DIMENSION`. El `downgrade` elimina la tabla
y el tipo `estado_frase` y conserva la extensión `vector`.

**Por qué.** Cuando se escribió no había modelos ORM, y el autogenerado no
reproduce con fidelidad los índices HNSW ni los operadores vectoriales. Una
migración describe el esquema de un momento y no puede variar con la
configuración; la coincidencia con el modelo real la comprueba el arranque
(B-14). La extensión puede estar compartida, y el `upgrade` la crea con
`IF NOT EXISTS`.

**Costo aceptado.** Cuando existan los modelos ORM, habrá que mantenerlos
coherentes con la migración a mano, no por comparación automática.
