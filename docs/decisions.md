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

**Excepción (T-10).** El `lifespan` de `app/main.py` es `async def` porque
FastAPI no admite otro. No contiene ningún `await` y corre antes de atender
peticiones: la carga síncrona del modelo no congela a nadie.

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

---

### D-16 — Ruff sin N818 para las excepciones en español
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** `pyproject.toml` ignora la regla N818 de ruff. Las excepciones
se llaman `ErrorDominio`, `ErrorInfraestructura`, `FraseInvalida`, etc., como
fija la skill `python-backend`.

**Por qué.** N818 exige el sufijo inglés `Error` en toda excepción que herede
de `Exception`. Cumplirla obligaría a nombres como `ErrorDominioError`, que
contradicen el glosario.

**Alternativas descartadas.**
- *`noqa` en cada clase*: el mismo efecto, pero repartido y fácil de olvidar.
- *Renombrar al inglés*: rompe la regla de nombres en español.

**Costo aceptado.** Ruff ya no avisa de una excepción mal nombrada; lo cubre la
revisión de código.

---

### D-17 — Conformidad de los dobles con los puertos comprobada por mypy
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.** Cada doble de `tests/dobles/` termina con una asignación tipada
dentro de `if TYPE_CHECKING:` (`_conforme: RepositorioFrases =
RepositorioEnMemoria()`), y se comprueba con `mypy app tests/dobles`. El
`RepositorioEnMemoria` no normaliza el texto que recibe en
`buscar_por_texto_normalizado`: lo recibe ya normalizado, igual que la consulta
SQL del plan §2.

**Por qué.** Los puertos son `Protocol` sin herencia, así que solo mypy detecta
que un doble dejó de cumplirlos. `mypy tests` entero no funciona en local:
`pytest` arrastra los stubs de numpy 2, que usan sintaxis de 3.12, y el
proyecto apunta a 3.11. Si el doble normalizara la consulta, ocultaría un caso
de uso que olvide normalizar y el adaptador real fallaría.

**Alternativas descartadas.**
- *Test en tiempo de ejecución con `isinstance` y `runtime_checkable`*: solo
  comprueba nombres de métodos, no firmas.
- *Herencia explícita de los `Protocol`*: contradice la skill (compatibilidad
  por forma).

**Costo aceptado.** El hook de cierre solo ejecuta `mypy app` y no vigila esta
comprobación; queda pendiente llevarla al hook o a CI (T-16).

---

### D-18 — Contratos del dominio y de los casos de uso
**Fecha:** 2026-09-21 · **Estado:** vigente

**Decisión.**
- Las entidades (`Frase`, `FraseNueva`, `ResultadoValidacion`) y los enums
  `EstadoFrase` y `MotivoDuplicado` son dataclasses inmutables en
  `domain/entidades.py`.
- `normalizar_y_validar(texto, longitud_maxima)` devuelve el texto normalizado
  o lanza `FraseInvalida` con un mensaje para la persona que incluye el máximo.
- `PosibleDuplicado` lleva el `ResultadoValidacion` en su atributo `resultado`,
  del que el 409 sacará sus `detalles`.
- `ValidarFrase.validar(texto)` y `GuardarFrase.guardar(texto,
  confirmar_duplicado)`. Ambos reciben `(repositorio, embedder, umbral,
  longitud_maxima)`; `GuardarFrase` construye su propio `ValidarFrase`.
- `texto_original` se guarda tal como llegó, sin recortar (RN-02).
- `id_mas_parecida` y `puntaje_similitud` se guardan también en estado `UNICA`
  cuando hubo vecino.

**Por qué.** Son los contratos que consumen T-09 y T-12a, y conviene que estén
escritos. Construir `ValidarFrase` dentro de `GuardarFrase` garantiza que la
revalidación usa los mismos puertos y el mismo umbral (RN-11). Que la excepción
lleve el resultado evita que la capa HTTP vuelva a validar.

**Alternativas descartadas.**
- *Inyectar `ValidarFrase` en `GuardarFrase`*: permitiría cablearlos con
  umbrales distintos.
- *Modelos Pydantic en el dominio*: no hace falta validación en tiempo de
  ejecución dentro del dominio.

**Costo aceptado.** `ResultadoValidacion.mas_parecida` es una `Frase` completa,
aunque la API solo expone `{id, texto}`. Se revisa en T-09 si obliga a
rellenar campos ficticios.

---

### D-19 — Vecino más cercano: desempate fuera del índice HNSW
**Fecha:** 2026-09-22 · **Estado:** vigente

**Decisión.** `buscar_mas_parecida` pide las 5 frases más cercanas ordenando
**solo** por distancia coseno, en una subconsulta, y aplica el desempate de
RN-08 (`distancia ASC, id ASC`) sobre esas 5. Es la alternativa prevista en el
plan §2. Además, mypy salta los stubs de numpy (`follow_imports = "skip"` en
`pyproject.toml`).

**Por qué.** `EXPLAIN` con pgvector 0.8.2 y 5000 filas mostró que
`ORDER BY embedding <=> :v, id LIMIT 1` produce `Seq Scan` + `Sort`: el índice
HNSW solo sirve un `ORDER BY` por la distancia sola. Con la subconsulta, el plan
es `Index Scan using idx_frases_embedding` seguido de un `Incremental Sort`
sobre 5 filas (comprobado sobre la consulta que genera SQLAlchemy, con 3000
filas). Sin eso, NF-02 no se cumple. En cuanto a mypy: `pgvector` importa numpy,
cuyos stubs usan sintaxis de Python 3.12, y `mypy app` dejaba de funcionar al
entrar el adaptador. Ningún módulo del proyecto usa numpy directamente.

**Alternativas descartadas.**
- *Conservar `ORDER BY distancia, id`*: exacto en el desempate, pero lineal
  en el número de frases.
- *Ordenar solo por distancia, sin desempate*: el orden entre empates de un
  índice aproximado no está garantizado y rompería RN-08.
- *Subir `python_version` de mypy a 3.12*: el proyecto apunta a 3.11.

**Costo aceptado.** Si más de 5 frases empatan exactamente en el puntaje más
alto, o si HNSW omite alguna de las empatadas, puede no ganar la de id menor.
Es el mismo compromiso de aproximación que ya asume el índice (architecture.md).

---

### D-20 — Umbral por defecto 0.75, calibrado con 32 pares
**Fecha:** 2026-09-22 · **Estado:** vigente · **Cierra:** Q-01

**Decisión.** `SIMILARITY_THRESHOLD` vale 0.75 por defecto. El valor sale de
`scripts/calibrar_umbral.py` sobre `datos/pares_etiquetados.csv`: 32 pares en
español, 14 equivalentes, que incluyen los seis de T-00, paráfrasis del
dominio, negaciones, antónimos, pares del mismo tema con distinto significado
y pares sin relación. El script recomienda el umbral de mayor F1 y, si hay
empate, el más bajo.

| Umbral | Precisión | Exhaustividad | F1 | Falsos positivos | Falsos negativos |
|---|---|---|---|---|---|
| 0.60 | 0.500 | 0.714 | 0.588 | 10 | 4 |
| 0.65 | 0.556 | 0.714 | 0.625 | 8 | 4 |
| 0.70 | 0.562 | 0.643 | 0.600 | 7 | 5 |
| **0.75** | 0.727 | 0.571 | **0.640** | 3 | 6 |
| 0.80 | 0.727 | 0.571 | 0.640 | 3 | 6 |
| 0.85 | 0.600 | 0.214 | 0.316 | 2 | 11 |
| 0.90 | 0.333 | 0.071 | 0.118 | 2 | 13 |
| 0.95 | 0.000 | 0.000 | 0.000 | 1 | 14 |

**Por qué 0.75 y no 0.80.** Empatan en F1 porque ningún par cae entre 0.75
y 0.80 (el más cercano por debajo es 0.7344 y por encima, 0.8035). Pero con
0.80 hay cuatro paráfrasis verdaderas a menos de 0.03 del umbral: "La factura
se envió a tu correo / Te mandamos la factura por email" (0.8247), "Tu tarjeta
ha caducado / La tarjeta está vencida" (0.8202), "Tu cuenta ha sido bloqueada
/ Hemos suspendido el acceso a tu cuenta" (0.8162) y "Cliente con pago
pendiente / Cliente que todavía no ha pagado" (0.8161). Con 0.75 tienen margen.
Además, los dos errores no cuestan lo mismo: un falso positivo solo pide a la
persona que confirme (RN-12); un falso negativo deja entrar un duplicado sin
aviso. El propietario eligió 0.75 frente a conservar 0.80.

**Límites conocidos del modelo.** Esto es lo que D-07 pedía: poder explicar
qué se gana y qué se pierde al mover el umbral. Hay errores que ningún umbral
corrige.

1. *Falsos positivos que ningún umbral evita.* El modelo no distingue cambios
   de número, lugar o dirección. "El envío sale desde Madrid / El envío llega a
   Madrid" puntúa 0.9659 y "El pedido llegará en tres días / … en tres
   semanas", 0.9121: los dos **por encima** del par estrella (0.8735), así que
   cualquier umbral que detecte el par estrella también los marca a ellos.
   "El cliente solicitó un reembolso / … una factura" puntúa 0.8035. Son los
   tres falsos positivos de 0.75. Para la persona usuaria esto significa que la
   alerta a veces señala una frase que no es la misma, y le toca decidir. Es
   justo para lo que existe la confirmación de RN-12.
2. *Paráfrasis con vocabulario distinto que no se detectan.* Seis paráfrasis
   quedan por debajo de 0.75. Por ejemplo, "El producto está agotado / No
   quedan unidades disponibles de este artículo" puntúa 0.4039, y "La
   contraseña es incorrecta / La clave que ingresaste no es válida", 0.4854.
   Esa es la exhaustividad del 57 %: el sistema detecta bien las paráfrasis
   que comparten palabras y pierde las que las cambian casi todas.
3. *Negaciones cerca del umbral.* Las tres negaciones del conjunto quedan
   entre 0.6458 y 0.7008: con 0.75 ni se detectan ni se confunden, pero están
   a menos de 0.11 del umbral. Es el dato a vigilar si alguien baja
   `SIMILARITY_THRESHOLD` por entorno. Con 0.70 ya se cuela "Se aceptan
   devoluciones / No se aceptan devoluciones"; con 0.65, dos de las tres, y con
   0.60, las tres. Los
   antónimos (0.45 a 0.72) se comportan igual.

El F1 máximo es 0.64. Si la organización necesita más precisión o más
exhaustividad, lo que hay que cambiar es el modelo (NF-08), no el umbral.

**Alternativas descartadas.**
- *Conservar 0.80*: mismo F1 con estos datos y sin cambiar documentos, pero
  deja sin margen a paráfrasis que caigan entre 0.75 y 0.80.
- *0.65 o 0.70, más exhaustividad*: dejan pasar como duplicado casi todas las
  negaciones y antónimos del conjunto, lo que duplica los falsos positivos.

**Costo aceptado.** 32 pares escritos por el equipo son una muestra pequeña y
sesgada. Hay que repetir la calibración con frases reales del repositorio en
cuanto existan: basta con ampliar el CSV y volver a ejecutar el script.

---

### D-21 — Modelo sin cargar: un sustituto que falla solo al generar
**Fecha:** 2026-09-22 · **Estado:** vigente · **Corrige:** plan §4

**Decisión.** Si el modelo no cargó al arrancar (`app.state.embedder` es
`None`), `obtener_embedder` devuelve un `EmbedderNoDisponible` que toma el
nombre y la dimensión de la configuración y cuyo `generar` lanza
`ErrorProveedorEmbeddings`. La dependencia ya no falla por sí misma.

**Por qué.** El plan §4 decía que la dependencia lanzara la excepción. Como
FastAPI resuelve las dependencias antes de ejecutar el endpoint, validar un
duplicado exacto con el modelo caído respondía `503`, lo que contradice RN-15
("la validación de un duplicado exacto no necesita al proveedor y por eso
responde con normalidad aunque esté caído") y B-20. Lo detectó la revisión de
T-12a. Con el sustituto, el caso de uso decide igual que con un proveedor que
falla al invocarse: el duplicado exacto responde `200`, y todo lo que necesita
un vector (validar una frase nueva, guardar) responde `503`.

**Alternativas descartadas.**
- *Pasar al caso de uso una fábrica perezosa del embedder*: obliga a cambiar
  las firmas de `ValidarFrase` y `GuardarFrase` (D-18) para resolver un
  problema de la capa HTTP.
- *Mantener el 503 anticipado y corregir RN-15*: la regla tiene sentido. El
  duplicado exacto es barato y no depende del modelo.

**Costo aceptado.** AC-18 dice que con el modelo sin cargar "validar y guardar
responden 503", sin mencionar la excepción del duplicado exacto. Hay que
precisarlo (RN-15 prevalece) antes de escribir sus tests en T-12b.

---

### D-22 — Detalles del contrato HTTP fijados al implementarlo
**Fecha:** 2026-09-22 · **Estado:** vigente

**Decisión.** Al implementar T-12a y T-12b se fijaron detalles que el plan §1
no concretaba:
- `detalles` se **omite** en las respuestas de error que no lo necesitan (404,
  405, 500, 503), en vez de enviarlo vacío o nulo.
- En `FRASE_INVALIDA` y `PARAMETROS_INVALIDOS`, `detalles` es un objeto
  `{campo: mensaje}`. Un JSON mal formado se reporta con el campo `cuerpo`.
- Los mensajes de Pydantic se sustituyen por mensajes fijos en español según
  el tipo de error (`missing`, `string_type`, `bool_type`…); el resto recibe
  "Valor no válido."
- `confirmar_duplicado` es un booleano **estricto**: `"true"`, `"si"` o `1`
  responden `422`.
- `desplazamiento` admite como máximo 2⁶³−1, el máximo de BIGINT. Por encima,
  PostgreSQL rechazaba la consulta y la API respondía `503` como si la base
  estuviera caída.
- `/salud` informa `base_datos: "no_disponible"` cuando `esta_disponible()`
  falla.
- Los manejadores de excepciones son `def`, no `async def`: Starlette los
  acepta y así se respeta D-10.
- FastAPI solo traduce a `422` el `JSONDecodeError`. Cualquier otro fallo al
  leer el cuerpo lo lanza como `HTTPException(400)`: bytes que no son UTF-8
  (`UnicodeDecodeError`) o un anidamiento que agota la recursión
  (`RecursionError`). Ese `400` se responde como `422 PARAMETROS_INVALIDOS`
  con `{"cuerpo": "El cuerpo no es JSON válido."}`, igual que un JSON mal
  formado (AC-02b, plan §1). *Corregido el 2026-09-23: antes esta decisión
  afirmaba que la aplicación no generaba ninguna `HTTPException` distinta de
  404/405, y ese `400` salía como `ERROR_INTERNO`.*
- Cualquier otra `HTTPException` distinta de 400, 404 y 405 conserva su
  estado y responde `ERROR_INTERNO`. Tal como se usan FastAPI y Starlette
  aquí (solo cuerpos JSON, sin `Form`, `UploadFile` ni `StaticFiles`), no se
  genera ninguna. Si se añade alguno de esos componentes, hay que revisar
  esta regla: el `400` de los formularios no se refiere al campo `cuerpo`.

**Por qué.** Cada punto responde a RN-16 (forma predecible, sin detalles
internos), a RN-12 (la confirmación es explícita) o a un fallo encontrado en
revisión: el `desplazamiento` sin tope lo detectó `security-review`.

**Alternativas descartadas.**
- *`detalles: null` o `{}` siempre presente*: añade ruido y no aporta nada.
- *Pasar los mensajes de Pydantic tal cual*: están en inglés y nombran tipos
  internos.
- *Booleano laxo*: "true" como texto no es una confirmación explícita.

**Costo aceptado.** La tabla de mensajes por tipo de Pydantic hay que
ampliarla si aparecen tipos de error nuevos. Mientras tanto, reciben el
mensaje genérico.


---

### D-23 — Tokens de diseño para grosores, alturas y zonas reservadas
**Fecha:** 2026-09-22 · **Estado:** SUSTITUIDA por D-27

**Decisión.** Se añadieron a `tokens.css` y a la skill `ui-design` los tokens
`--foco-grosor`, `--foco-separacion`, `--borde-fino`, `--borde-grueso`,
`--alto-tactil`, `--alto-zona-resultado` y `--alto-tarjeta`. El único valor
escrito a mano fuera de `tokens.css` es el punto de corte `@media (max-width:
640px)`.

**Por qué.** La skill prohíbe escribir a mano cualquier color, espacio o
tamaño, pero exigía valores (el anillo de foco de 2px, el objetivo táctil de
44px, el borde de 3px de la alerta, el hueco reservado para que la lista no
salte) que no tenían token. La regla y sus propios ejemplos se contradecían.
CSS no admite `var()` dentro de una media query: de ahí la excepción del
punto de corte, que es único.

**Alternativas descartadas.**
- *Escribir esos valores a mano como excepción*: la comprobación de "ningún
  valor a mano" deja de ser mecánica.
- *Calcularlos con `calc()` a partir de los de espaciado*: resultados como
  `calc(var(--esp-12) - var(--esp-1))` para 44px esconden la intención.

**Costo aceptado.** `--alto-zona-resultado` (13rem) y `--alto-tarjeta` (4.5rem)
son estimaciones del alto real. Si cambia la tipografía o el contenido de la
alerta, hay que revisarlos a ojo.

**Sustituida.** Por D-27 (CH-02, 2026-09-22): los tokens de esta decisión quedan
reemplazados por los de la skill `ui-design` v2, que ya no reserva espacio para
el resultado y usa un único punto de corte de 720 px.

---

### D-24 — Detalles de la máquina de estados del formulario
**Fecha:** 2026-09-22 · **Estado:** vigente, precisada por D-27 · **Precisa:** plan §5

**Decisión.**
- Durante `guardando` el veredicto vigente (única, posible duplicado o
  conflicto) sigue en pantalla y el botón principal muestra Guardando….
  `guardando` lleva ese veredicto; Guardar de todos modos envía
  `confirmar_duplicado: true` exactamente cuando es de posible duplicado o
  conflicto.
- Hay un solo botón principal, cuyo texto sigue el paso (ui-design v2). En
  `posible_duplicado` y `conflicto` queda deshabilitado y se guarda desde el
  veredicto con Guardar de todos modos.
- Un error `422` no ofrece Reintentar: repetirlo daría lo mismo, hay que
  corregir el texto. Cualquier otro error sí.
- El error del listado usa un mensaje fijo ("No pudimos cargar las frases."),
  no el `mensaje` del cliente.
- `BotonCarga` apila las dos etiquetas en la misma celda de una rejilla para
  que el botón no cambie de ancho al pasar a "Validando…".
- Guardar avisa a `App` con la opción `alGuardar` de `useValidacion`, que
  devuelve el listado a la primera página (AC-16).

**Por qué.** Con `guardando` sin datos, la alerta desaparecía mientras se
guardaba y volvía a aparecer si llegaba un `409`: un salto visual sin motivo.
Decidir la confirmación a partir del estado, y no de un parámetro, ata la
decisión al texto validado (AC-16b).

**Alternativas descartadas.**
- *`min-width` fijo en los botones*: sería un valor escrito a mano (D-23, hoy D-27).
- *Un contexto de React para avisar del guardado*: el árbol tiene dos niveles
  (patterns.md).

**Costo aceptado.** Si una página ya cargada del listado falla al cambiar de
página, la caja de error la sustituye de golpe: la reserva de alto solo se
aplica mientras carga.

---

### D-25 — Alcance de la integración continua
**Fecha:** 2026-09-22 · **Estado:** vigente

**Decisión.** `.github/workflows/ci.yml` tiene tres trabajos: backend (`ruff`,
`mypy app tests/dobles` y la suite rápida), integración (servicio
`pgvector/pgvector:pg16` con la base `banco_frases_test` migrada por Alembic) y
frontend (`tsc --noEmit`, `vitest run` y `npm run build`). `torch` se instala
desde el índice de CPU, con la versión leída de `pyproject.toml`. Los tests
`slow` no corren en CI.

**Por qué.** Es la lista de T-16. `mypy tests` entero tiene un error heredado
(STATUS.md), así que se comprueba lo mismo que el hook más los dobles, cuya
conformidad con los puertos depende de mypy (D-17). Los tests `slow`
descargarían 470 MB en cada ejecución.

**Alternativas descartadas.**
- *Cachear el modelo en CI para correr `slow`*: más configuración para un
  único test que ya se ejecuta en local.
- *Fijar las acciones por SHA*: se fijaron por versión mayor, suficiente para
  un repositorio sin secretos en CI.

**Costo aceptado.** `actions/checkout@v4`, `setup-python@v5` y `setup-node@v4`
apuntan a Node 20, deprecado, y GitHub ya los ejecuta a la fuerza con Node 24.
Hay que subir de versión mayor antes de que dejen de funcionar. `format:check`
del frontend tampoco corre.

---

### D-26 — Semillas fuera de la imagen e idempotentes
**Fecha:** 2026-09-22 · **Estado:** vigente

**Decisión.** `scripts/sembrar_frases.py` guarda 10 frases con el caso de uso
`GuardarFrase`, sin confirmar nunca un duplicado. No está en la imagen del
backend. Con Docker se copia al contenedor con `docker compose cp` y se
ejecuta con `docker compose exec -e PYTHONPATH=/srv`. Las 10 frases son
distintas entre sí (la similitud máxima entre ellas es 0.50) e incluyen "La
entidad bancaria rechazó la transacción" para el ejemplo del README.

**Por qué.** Pasar por el caso de uso garantiza embedding y metadatos (RN-13,
RN-14), igual que la API. Sin confirmar duplicados, volver a ejecutarlo omite
todas las frases como duplicado exacto: no hace falta llevar la cuenta de qué
se sembró. `cp` + `exec` funciona igual en bash, PowerShell y Linux.

**Alternativas descartadas.**
- *`docker compose run -v ./scripts:/srv/scripts`*: la ruta relativa no se
  resolvió en Windows.
- *Pasar el script por la entrada estándar*: PowerShell no tiene `<` y su
  tubería puede estropear las tildes.
- *Copiar `scripts/` en la imagen*: lleva a producción código que solo sirve
  en desarrollo.
- *Insertar con SQL directo*: se saltaría la validación y habría que calcular
  los vectores a mano.

**Costo aceptado.** Son dos comandos en lugar de uno, y en Git Bash para
Windows hay que anteponer `MSYS_NO_PATHCONV=1` al segundo.

---

### D-27 — Interfaz de una sola pantalla con registro en línea
**Fecha:** 2026-09-22 · **Estado:** vigente · **Origen:** CH-02 · **Sustituye:** D-23

**Decisión.** Una sola pantalla: el registro y su veredicto van en línea sobre
la tabla de frases, sin modales ni paneles laterales. El listado devuelve,
para cada frase, el texto de la frase más parecida al registrarla
(`mas_parecida`, RN-17, AC-19), resuelto con un `LEFT JOIN` en la misma
consulta de la página. Ante un posible duplicado la acción destacada es
"Editar frase" y la secundaria "Guardar de todos modos"; "Cancelar"
desaparece. Un `409` al guardar tiene su propio estado, `conflicto`, con su
criterio de aceptación AC-21 (adenda de CH-02). Los
tokens de diseño pasan a la v2 de la skill `ui-design`, que sustituye a los de
D-23, con un único punto de corte de 720 px.

**Por qué.** La persona compara su frase con el catálogo mientras decide.
Ocultar la lista para registrar le quita justamente ese contexto. La versión
anterior dejaba un hueco reservado que empujaba la lista fuera de la primera
pantalla, mostraba Validar y Guardar con el mismo peso, y la lista no
explicaba a qué frase se parecía un duplicado confirmado.

**Alternativas descartadas.**
- *Modal o panel lateral para registrar*: oculta la lista mientras se escribe.
- *Dos columnas fijas*: en pantallas medianas la tabla queda demasiado
  estrecha para cinco columnas.
- *Plantilla administrativa comercial*: licencia incompatible con un
  repositorio público y añade Bootstrap y jQuery a un proyecto React.
- *Resolver `mas_parecida` en el frontend*: una petición por fila (N+1).
- *Umbral en la barra superior y conteo de duplicados*: ningún endpoint los
  expone; el umbral ya se ve en el medidor de cada veredicto.
- *Fuentes web (IBM Plex)*: autoalojarlas añade dependencias fuera del plan
  §9b; cargarlas de un tercero rompe NF-07.

**Precisa D-24.** El formulario deja de tener un botón Guardar propio junto a
los de la alerta: hay un solo botón principal cuyo texto sigue el paso. En
`posible_duplicado` y `conflicto` queda deshabilitado y se guarda desde el
veredicto con Guardar de todos modos. Durante ese guardado el veredicto
sigue en pantalla y el botón principal muestra Guardando…. El resto de D-24
sigue en vigor: sin Reintentar ante un `422`, mensaje fijo en el error del
listado, `BotonCarga` sin cambio de ancho y el aviso `alGuardar`.

**Precisa:** el micro-medidor de la tabla no lleva marca de umbral (motivo en
la skill `ui-design`).

**Costo aceptado.** En móvil el veredicto empuja la lista hacia abajo. Se
mitiga con el veredicto compacto y las filas en formato ficha.

---

### D-28 — Detalles de implementación del rediseño (T-20 a T-23)
**Fecha:** 2026-09-22 · **Estado:** vigente · **Precisa:** D-27, plan §5, skill `ui-design`

**Decisión.**
- El mínimo de 3 caracteres que habilita "Comprobar similitud" se mide sobre
  el texto normalizado según RN-02 (NFKC, recorte, colapso de espacios,
  minúsculas), como el servidor y el prototipo: "   " no llega a comprobarse.
  El contador y el máximo siguen sobre el texto crudo.
- El campo usa `readOnly`, no `disabled`, mientras se valida o se guarda: así
  conserva el foco y la persona no puede editar el texto en curso.
- Las duraciones de animación son tokens de movimiento: `--duracion-spinner`
  (800 ms) y `--duracion-brillo` (1.2 s), en `tokens.css` y en la skill.
  `prefers-reduced-motion` las anula.
- La fila recién guardada se resalta en la lista: `alGuardar` recibe la frase
  guardada y `App` pasa su id a `ListaFrases`, que la resalta al aparecer.
- Las barras del esqueleto miden `--espacio-3` (12 px) y no los 10 px del
  prototipo: no hay token de 10 px y la regla de no escribir valores pesa más.
- En el frontend, `esItemListado` y `esFrase` comparten los campos comunes pero
  validan por separado: el `201` no trae `mas_parecida` y el listado sí.

**Descartado.** Contar el mínimo sobre el texto crudo (dejaba pasar "   " hasta
un `422` evitable); duraciones escritas en cada CSS; umbral de la última
validación para el micro-medidor (ver D-27).

**Costo aceptado.** La normalización del cliente es una aproximación de la del
servidor (Artículo 8): en casos raros de NFKC puede habilitar el botón y el
servidor responder `422`, que se muestra sin Reintentar.

---

### D-29 — Regiones vivas y roles de tabla (T-24)
**Fecha:** 2026-09-23 · **Estado:** vigente · **Precisa:** skill `ui-design` (accesibilidad)

**Decisión.**
- El veredicto se anuncia solo por su rol (`alert` para duplicado, conflicto y
  error; `status` para única y guardada). Su contenedor no lleva `aria-live`:
  dos regiones vivas anidadas se anuncian dos veces.
- La lista tiene un párrafo oculto con `aria-live="polite"` que siempre está
  montado y cambia de texto: «Cargando frases…», «Mostrando 1–20 de 26
  frases», «No hay frases registradas». En error queda vacío, porque el
  mensaje ya lleva `role="alert"`. No usa `role="status"`, que es del
  veredicto: dos `status` en pantalla serían ambiguos para quien navega por
  regiones, y para los tests.
- La tabla y el esqueleto declaran roles explícitos (`table`, `rowgroup`,
  `row`, `columnheader`, `cell`). Por debajo de 720 px las fichas cambian el
  `display`, y WebKit deja entonces de exponer la semántica de tabla. En
  Chromium, el árbol de accesibilidad a 360 px conserva tabla, filas y celdas.

**Descartado.** Mantener `aria-live` en el contenedor y quitar los roles del
veredicto: la skill exige los roles y `alert` es la forma más fiable de un
anuncio asertivo. `aria-live` en toda la sección de la lista: leería la tabla
entera a cada cambio de página.

**Costo aceptado.** Un `role="status"` que entra en el DOM junto con su
contenido no se anuncia igual de fiable en todos los lectores de pantalla. La
verificación se hizo en jsdom y en el árbol de accesibilidad de Chromium.

---

### D-30 — Codificación del cuerpo: se exige UTF-8, se toleran UTF-16/32
**Fecha:** 2026-09-23 · **Estado:** vigente · **Precisa:** plan §1 · **Cierra:** Q-07

**Decisión.** El contrato exige que el cliente envíe JSON en UTF-8
(RFC 8259, §8.1). El servidor no rechaza las demás codificaciones que
`json.loads` reconoce por sí solo: UTF-8 con BOM, y UTF-16 y UTF-32 con o sin
BOM (sin BOM, las detecta por la posición de los bytes nulos). Las acepta
porque el texto se decodifica igual que en UTF-8 y pasa por la misma
normalización (RN-02) y la misma validación (RN-01, RN-03). Un cuerpo que no
se puede decodificar sigue respondiendo `422 PARAMETROS_INVALIDOS` con el
campo `cuerpo` (D-22).

**Por qué.** Lo decidió el propietario al revisar la observación de
`security-review` en el fix del cuerpo no UTF-8. Rechazarlas no protege nada:
la detección de duplicados no se puede esquivar así, porque se compara el
texto decodificado y normalizado. Además exigiría leer los bytes a mano antes
de FastAPI, un código que hoy no existe.

**Descartado.** Rechazar con `422` todo cuerpo que no sea UTF-8 estricto.

**Costo aceptado.** El servidor es más tolerante de lo que dice el contrato.
Un cliente que dependa de esa tolerancia funciona, pero incumple el contrato,
y no hay test que la fije: si una versión futura de FastAPI o Starlette la
quitara, esos cuerpos pasarían a responder `422`, y sería conforme al
contrato.

---

### D-31 — Columnas estables y punto de corte en 900 px (CH-03)
**Fecha:** 2026-09-23 · **Estado:** vigente · **Precisa:** D-27 (punto de corte), skill `ui-design` · **Cierra:** Q-06

**Decisión.**
- Un solo punto de corte en **900 px** para toda la pantalla, en lugar de
  720 px. Las menciones a 720 px en D-23, D-27 y D-29 describen lo que se
  decidió entonces.
- Por encima del punto de corte, la tabla usa `table-layout: fixed`. Estado,
  Similitud, Más parecida y Registrada tienen ancho fijo con cuatro tokens
  (`--ancho-col-estado` 184px, `--ancho-col-similitud` 148px,
  `--ancho-col-parecida` 176px, `--ancho-col-fecha` 152px). **Frase no tiene
  ancho y se queda con el espacio restante.** Se elimina
  `.colFrase { width: 40% }`. A 901 px la tabla mide ≈ 852 px (viewport − 15
  de barra de desplazamiento − 32 de gutter − 2 de borde), y Frase recibe
  ≈ 192 px frente a los 176 de Más parecida.
- `html { scrollbar-gutter: stable; }` (ampliación decidida en T-25): el hueco
  de la barra de desplazamiento vertical se reserva siempre. Sin esto, la
  barra aparece al llegar los datos y Frase y las fichas pierden 15 px.

**Por qué.** T-24 midió que las columnas se movían entre 15 y 50 px al pasar
del esqueleto a los datos y que, a 721 px, Frase se quedaba en 62 px. Con
`fixed`, los anchos no dependen del contenido. Con el punto de corte en
900 px, la tabla solo tiene cinco columnas cuando hay sitio para ellas.

**Descartado.**
- *Reparto 60/40 entre Frase y Más parecida con `calc()`*: fue lo aceptado al
  principio, pero Chromium trata como `auto` un `calc()` con porcentaje en una
  columna de tabla y sale 50/50.
- *`60%` y `40%` junto a los px*: da 60/40 en Chromium, pero depende de un
  caso que la especificación de CSS no fija.
- *Solo una de las dos alternativas*: (a) deja Frase en ≈ 113–136 px a
  721 px; (b) no quita el salto del esqueleto.
- *No hacer nada*: la skill quedaba incumplida.

**Costo aceptado.** Entre 721 y 900 px, la pantalla pasa al diseño de una
columna: registro, veredicto y fichas. Con una barra de desplazamiento clásica
(Windows y Linux con ratón), el hueco de 15 px queda a la derecha aunque la
página no tenga barra; con barras superpuestas (macOS, móviles) no ocupa
nada. A 1080 px Frase recibe ≈ 36 % de la
tabla en lugar del 40 %. Los tokens de ancho llevan un margen sobre lo medido
con Segoe UI, y en macOS o Android no se han medido: si una fuente del
sistema es más ancha, hay que subirlos.

---

### D-32 — Caracteres de control: se rechazan en el dominio
**Fecha:** 2026-09-23 · **Estado:** vigente · **Precisa:** RN-01, spec (AC-01, B-27)

**Decisión.**
- «Texto plano» (RN-01) excluye los caracteres de control Unicode (categoría
  `Cc`) que no son espacios. `normalizar_y_validar` los busca en el texto ya
  normalizado: los que son espacio (tabulación, saltos de línea, U+001C–U+001F,
  U+0085) ya se colapsaron, así que cualquier `Cc` que quede es un error.
  Responde `422 FRASE_INVALIDA` con «La frase contiene caracteres no
  permitidos.».
- `RepositorioPostgres` deja pasar `DataError` sin traducirlo a
  `ErrorRepositorio`. Un dato rechazado no es una base caída; si alguno
  llegara, el manejador genérico responde `500 ERROR_INTERNO` sin traza.

**Por qué.** La auditoría previa a la entrega encontró que `"ab\u0000cd"`
respondía `503 BASE_DATOS_NO_DISPONIBLE`: PostgreSQL no admite U+0000 en
columnas de texto, el driver lanzaba `DataError` y el repositorio lo
traducía, como todo `SQLAlchemyError`, a base caída. Lo pidió el propietario.

**Descartado.** Quitar U+0000 en silencio al normalizar: cambiaría el texto
original que se guarda sin avisar a la persona.

**Costo aceptado.** Los caracteres invisibles que no son `Cc` (formato `Cf`,
como U+200B de ancho cero) siguen aceptándose: dos frases que solo difieren
en uno de ellos no son duplicado exacto. Cambiarlo necesita propuesta.

---

### D-33 — El registro mide y avisa sobre el texto normalizado
**Fecha:** 2026-09-23 · **Estado:** vigente · **Precisa:** D-28, skill `ui-design` (registro)

**Decisión.**
- El contador, el máximo que deshabilita "Comprobar similitud" y el aviso usan
  la misma cifra: los puntos de código del texto normalizado (RN-01, RN-02),
  como el servidor. D-28 dejaba el contador y el máximo sobre el texto crudo.
- Si hay algo escrito y esa cifra es menor que 3 o mayor que
  `VITE_MAX_PHRASE_LENGTH`, `#pie-frase` muestra el mismo texto que
  `FraseInvalida` en el servidor, en el lugar del atajo «Ctrl + Enter para
  continuar». Con el campo vacío no hay aviso. Como `#pie-frase` es la
  descripción accesible del campo, el aviso se lee al enfocarlo.

**Por qué.** La auditoría previa a la entrega: el botón se deshabilitaba sin
decir por qué, y con el máximo sobre el texto crudo, 285 caracteres que
normalizan a 275 quedaban bloqueados aunque el servidor los acepta. Los
criterios los fijó el propietario: aviso solo con texto escrito, y todo sobre
el texto normalizado.

**Descartado.** Mantener el contador sobre el texto crudo: se vería 285 / 280
sin aviso y con el botón habilitado.

**Costo aceptado.** "   " muestra 0 / 280, que puede sorprender. La
normalización del cliente sigue siendo una aproximación (D-28): en casos raros
de NFKC el aviso y el servidor pueden no coincidir, y manda el servidor.

---

### D-34 — Documentación interactiva bajo `/api/v1`
**Fecha:** 2026-09-23 · **Estado:** vigente · **Precisa:** plan §1

**Decisión.** Swagger UI se sirve en `/api/v1/docs` y el esquema en
`/api/v1/openapi.json`. ReDoc y la redirección OAuth de Swagger se
desactivan.

**Por qué.** nginx solo reenvía `/api/` al backend: con las rutas por defecto
(`/docs`, `/openapi.json`), en Compose la documentación no se podía abrir y
nginx devolvía la SPA. Lo pidió el propietario en la auditoría previa a la
entrega.

**Descartado.** Añadir a `nginx.conf` reglas para `/docs` y `/openapi.json`:
son más rutas fuera de `/api/` que mantener, y en desarrollo sin Docker
seguirían en otra ruta.

**Costo aceptado.** La documentación deja de estar en `/docs` al trabajar sin
Docker. Queda en `http://localhost:8000/api/v1/docs`, y el README lo indica.

---

### D-35 — PostgreSQL publicado solo con `docker-compose.dev.yml`
**Fecha:** 2026-09-23 · **Estado:** vigente · **Precisa:** plan §9 (entorno Docker), NF-07

**Decisión.** El archivo que publica el 5432 de `db` en el host se llama
`docker-compose.dev.yml` y se aplica con
`docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db`.
`docker compose up` a secas solo publica el 8080.

**Por qué.** Con el nombre `docker-compose.override.yml`, Compose lo aplicaba
siempre, y `docker compose up` fallaba en una máquina que ya tenía un
PostgreSQL local en el 5432, en contra de NF-07.

**Descartado.** Publicar otro puerto del host (por ejemplo 5433): obligaría a
cambiar `DATABASE_URL` y `TEST_DATABASE_URL` por defecto y seguiría
publicando la base sin necesidad.

**Costo aceptado.** El comando para levantar la base de desarrollo es más
largo, y quien lo olvide verá los tests de integración fallar por conexión
rechazada.

---

### D-36 — El foco sigue a la operación en el registro
**Fecha:** 2026-09-23 · **Estado:** vigente · **Precisa:** D-27, D-28, skill ui-design

**Decisión.** Un botón con una operación en curso («Comprobando…»,
«Guardando…», y «Editar frase» y «Guardar de todos modos» mientras se guarda)
lleva `aria-disabled="true"` e ignora el clic, en lugar de `disabled`. Se ve
igual que deshabilitado. Al llegar el veredicto, el foco va a «Guardar frase» si
es `unica`, y a «Editar frase» si es `posible_duplicado` o `conflicto`.
`disabled` real queda para lo que depende del texto (longitud fuera de rango,
duplicado pendiente de decidir).

**Por qué.** Con `disabled`, el navegador quita el foco al botón que se acaba de
pulsar con el teclado y lo deja en `BODY`: quien usa el teclado tenía que
volver a recorrer la página tras cada comprobación. Lo detectó la auditoría
previa a la entrega (bloque B).

**Descartado.** Devolver el foco al campo: obliga a otro Tab para llegar a la
acción siguiente, que es lo que casi siempre se quiere hacer.

**Costo aceptado.** Los tests de jsdom no reproducen la pérdida de foco de
`disabled`; lo que la evita se prueba comprobando `aria-disabled` y que el foco
llega a la acción siguiente desde el campo (Ctrl+Enter).

---

### D-37 — Cambiar de página conserva la página anterior
**Fecha:** 2026-09-23 · **Estado:** vigente · **Precisa:** plan §5, skill ui-design, AC-20

**Decisión.** La lista tiene un estado más, `cambiando`, con la página que se
estaba viendo. Al pedir otra página con una ya a la vista, la tabla se queda,
atenuada (`--opacidad-cambiando`) y con `aria-busy="true"`, y la paginación
sigue montada. Los botones de paginación usan `aria-disabled` en los extremos y
mientras cambia de página, e ignoran el clic. El esqueleto queda para cuando no
hay nada que mostrar: la primera carga y el Reintentar tras un error.

**Por qué.** Con el esqueleto en cada cambio, la tabla cambiaba de altura, el
scroll saltaba arriba y el botón pulsado se desmontaba, así que el foco se
perdía. Con `disabled` en los extremos, llegar a la última página también
dejaba el foco en `BODY`. Lo detectó la auditoría previa a la entrega
(bloque B).

**Descartado.** Mantener la página anterior sin marcarla: quien la ve no sabría
que está desactualizada y podría pulsar un enlace de «Más parecida» que ya no
corresponde.

**Costo aceptado.** Un estado más en la máquina de la lista. Si la página nueva
falla, se pasa a `error` y la anterior desaparece, igual que antes.
