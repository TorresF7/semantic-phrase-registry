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
- Docker Compose con `db` (pgvector), `backend` y `frontend` (nginx sin
  privilegios, proxy de `/api`), imágenes multietapa y `GET /api/v1/salud`
  provisional (T-02).
- Configuración por entorno en `app/config.py`; un umbral fuera de [0, 1] o no
  numérico impide el arranque (RN-06, B-24, T-03).
- Migración inicial con Alembic: extensión `vector`, tipo `estado_frase`, tabla
  `frases` e índices del plan §2, incluido HNSW. El backend migra al arrancar
  (T-04).
- D-12: `@types/react`, `@types/react-dom` y Testing Library 15 en el frontend.
- D-13 a D-15: Compose sin `.env` obligatorio y migración al arrancar;
  configuración con nombres en español; migración inicial escrita a mano.
- Dominio: normalización y validación de longitud, política de umbral con
  `>=` sin redondear, recorte a [0, 1], normalización de vectores y jerarquía
  de errores (T-05).
- Puertos `ProveedorEmbeddings` y `RepositorioFrases`; dobles `FakeEmbedder` y
  `RepositorioEnMemoria` con los mismos desempates que el SQL (T-06).
- Caso de uso `ValidarFrase`: duplicado exacto sin llamar al proveedor,
  semántico con vector normalizado, base vacía y desempate determinista (T-07).
- Caso de uso `GuardarFrase`: revalidación completa, confirmación explícita,
  embedding del duplicado exacto generado al guardar y metadatos inmutables
  (T-08).
- D-16 a D-18: ruff sin N818; conformidad de los dobles comprobada por mypy;
  contratos del dominio y de los casos de uso.
- Repositorio PostgreSQL síncrono con pgvector: duplicado exacto, vecino más
  cercano con desempate por id sobre los 5 candidatos del índice HNSW, listado
  paginado, `esta_disponible()` y traducción de fallos a `ErrorRepositorio`
  (T-09).
- `scripts/preparar_base_test.sh` crea y migra `banco_frases_test` (T-09).
- D-19: el desempate por id del vecino más cercano se resuelve fuera del
  índice; mypy no analiza los stubs de numpy.
- Adaptador `HuggingFaceEmbedder` con import perezoso y traducción de fallos
  a `ErrorProveedorEmbeddings`. El `lifespan` carga el modelo una vez desde
  `app.state.fabrica_embedder`: si no carga, arranca degradado (B-09); si su
  dimensión no coincide con `EMBEDDING_DIMENSION`, el arranque falla (B-14)
  (T-10).
- `POST /api/v1/frases/validar` y `POST /api/v1/frases` con schemas propios
  (tope defensivo de 2000 caracteres, `confirmar_duplicado` booleano estricto),
  puntaje redondeado a 4 decimales solo al serializar, forma de error uniforme
  en todos los códigos, incluidos los que genera FastAPI (404, 405, 422), y
  CORS desde `CORS_ORIGINS` (T-12a).
- D-21: con el modelo sin cargar, validar un duplicado exacto responde `200`
  (RN-15, B-20); lo que necesita un vector responde `503` (T-12a).
- `GET /api/v1/frases` paginado (`limite` de 1 a 100, `desplazamiento` ≥ 0,
  `422 PARAMETROS_INVALIDOS` fuera de rango) y `GET /api/v1/salud` completo:
  `503 degradado` si el modelo no cargó o la base no responde. `/docs` muestra
  un ejemplo por cada código de cada endpoint (T-12b).
- Cliente de API tipado en el frontend: `api/tipos.ts`, espejo del contrato, y
  `api/cliente.ts`, que comprueba la forma de cada respuesta en tiempo de
  ejecución, traduce los errores a `ErrorApi` y el `409` a un posible duplicado
  (T-13).
- D-19 a D-22: desempate del vecino fuera del índice HNSW; umbral 0.75;
  sustituto del modelo sin cargar; detalles del contrato HTTP (`detalles`
  omitido, booleano estricto, tope de `desplazamiento`, `base_datos:
  "no_disponible"`).
- Tokens de diseño en `src/estilos/tokens.css`, reinicio de estilos y layout de
  una columna (T-13b).
- Pantalla de validación: formulario con contador por puntos de código, botón
  Guardar deshabilitado hasta validar, alerta de posible duplicado con la frase
  existente y el porcentaje (sin porcentaje en el duplicado exacto), Cancelar
  conservando el texto, el `409` del guardado vuelve a mostrar la alerta, y
  confirmación de guardado distinta para única y para duplicado confirmado
  (AC-16, AC-16b, T-14).
- Listado de frases paginado de 20 en 20, con estado vacío, carga, error con
  Reintentar y la etiqueta "Duplicado confirmado". Tras guardar, vuelve a la
  primera página (AC-16, T-15).
- Integración continua en GitHub Actions: lint, tipos, suite rápida,
  integración con pgvector y comprobaciones del frontend (T-16).
- README completo: instalación con y sin Docker, variables de entorno,
  arquitectura, decisiones, ejemplo `curl` y calibración del umbral (T-17).
- `scripts/sembrar_frases.py`: 10 frases de ejemplo guardadas con
  `GuardarFrase`. Se puede ejecutar varias veces sin duplicar nada (T-18).
- D-23 a D-26: tokens de diseño nuevos, detalles de la máquina de estados del
  formulario, alcance de CI y semillas fuera de la imagen.

### Cambiado
- El registro avisa en el pie del campo cuando el texto normalizado tiene
  menos de 3 o más de 280 caracteres, con los mismos textos que el servidor.
  El contador y el máximo pasan a medir el texto normalizado (D-33).
- CH-02: rediseño de la interfaz en una sola pantalla (D-27, sustituye a
  D-23). `GET /frases` incluye en cada elemento `mas_parecida: { id, texto } |
  null` (RN-17, AC-19). AC-16b pasa de "Cancelar" a "Editar frase", que conserva
  el texto y devuelve el foco. Nuevo estado `conflicto` para el `409` al
  guardar, cubierto por AC-21 (adenda de CH-02); D-24 queda precisada por
  D-27. En `unica` se muestra la frase más cercana con su medidor. La lista
  gana estados de carga, vacía y error, y paginación solo con más de una página
  (AC-20). Diseño adaptable con un punto de corte en 720 px. Implementado en
  T-20 a T-24.
- Interfaz v2 (T-20 a T-23): tokens de la skill `ui-design` v2 con dos tokens
  de movimiento; barra superior; registro en línea con un botón principal por
  pasos, veredicto con par de frases y medidor, y `conflicto` para el `409`;
  tabla de cinco columnas con micro-medidor sin marca de umbral (el listado no
  trae `umbral_aplicado`) y enlace a la más parecida; fichas por debajo de
  720 px. El mínimo de 3 caracteres del botón se mide sobre el texto
  normalizado (D-28). D-24 se generaliza: el veredicto vigente sigue en
  pantalla durante cualquier guardado.
- Accesibilidad (T-24): el contenedor del veredicto ya no lleva `aria-live`
  (sus roles `alert`/`status` ya son regiones vivas; anidadas se anunciaban dos
  veces). La lista gana una región viva de cortesía siempre montada ("Cargando
  frases…", "Mostrando 1–20 de 26 frases", "No hay frases registradas"). La
  tabla declara roles explícitos para que las fichas conserven la semántica de
  tabla. La lista de verificación visual queda con un punto sin superar: las
  columnas se desplazan al pasar del esqueleto a los datos (CH-03, propuesta).
- CH-03 aceptada (D-31, cierra Q-06): punto de corte único en 900 px y tabla
  con `table-layout: fixed`, cuatro columnas de ancho fijo con token propio y
  Frase con el espacio restante, para que las columnas no se muevan al pasar
  del esqueleto a los datos. Se descartó el reparto 60/40 con `calc()`, que
  Chromium no aplica en columnas de tabla. Se implementa en T-25.
- Interfaz (T-25, CH-03): punto de corte en 900 px y columnas estables. Por
  encima, la tabla usa `table-layout: fixed` con cuatro columnas de ancho fijo
  y Frase con el espacio restante; `html` reserva el hueco de la barra de
  desplazamiento. Entre el esqueleto y los datos no cambia ningún ancho a
  1080, 901, 900, 800, 390 ni 360 px.
- Codificación del cuerpo (D-30, cierra Q-07): el contrato exige JSON UTF-8 y
  el servidor tolera UTF-16/32 y UTF-8 con BOM. Sin cambios de código.
- CH-01: AC-18 y B-09 precisan que, con el modelo sin cargar, un duplicado
  exacto se sigue validando (`200`) y que guardarlo sin confirmar da `409`; solo
  lo que necesita generar un vector responde `503` (RN-15, B-20, D-21).
- El umbral por defecto pasa de 0.80 a **0.75**, calibrado con
  `scripts/calibrar_umbral.py` sobre 32 pares etiquetados en
  `datos/pares_etiquetados.csv` (D-20, cierra Q-01, T-11).

Auditoría previa al primer commit:
- Se embebe el texto normalizado, no el original (RN-02, RN-05).
- El duplicado exacto confirmado genera su embedding al guardar (RN-14, AC-11b).
- Aplicación síncrona de punta a punta (D-10); sin límite de peticiones en la
  aplicación (D-11).
- Puntaje recortado a [0, 1] y comparado sin redondear (RN-05, B-15, B-16).
- Desempate por identificador también en el duplicado exacto y en el listado
  (RN-08, RN-17).
- La normalización de vectores es del dominio, no del proveedor (RN-19, D-09).
- Longitud medida sobre el texto normalizado, en el dominio (RN-01, AC-02).

### Corregido
- `docker-compose.override.yml` se aplicaba siempre y publicaba el 5432:
  `docker compose up` fallaba en máquinas con un PostgreSQL local (NF-07). Pasa
  a llamarse `docker-compose.dev.yml` y solo se aplica con `-f` (D-35).
- `LOG_LEVEL` se leía pero no se aplicaba. El arranque configura ahora el
  registro raíz con ese nivel.
- Swagger UI y el esquema OpenAPI estaban en `/docs` y `/openapi.json`, que
  nginx no reenvía: en Compose no se podían abrir. Pasan a `/api/v1/docs` y
  `/api/v1/openapi.json`; ReDoc se desactiva (plan §1, D-34).
- Un texto con U+0000 respondía `503 BASE_DATOS_NO_DISPONIBLE`, porque
  PostgreSQL no admite ese carácter y el repositorio traducía cualquier error a
  base caída. Ahora el dominio rechaza todo carácter de control que no sea
  espacio con `422 FRASE_INVALIDA` (RN-01, B-27, D-32), y un `DataError` ya no
  se traduce a `503`.
- Un cuerpo que no es JSON UTF-8 legible (bytes que no son UTF-8 o un
  anidamiento sin límite) respondía `400 ERROR_INTERNO`. Ahora responde
  `422 PARAMETROS_INVALIDOS` con el detalle en el campo `cuerpo`, igual que un
  JSON mal formado (AC-02b, RN-16). D-22 queda corregida.

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
