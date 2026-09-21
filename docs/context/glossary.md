# Glosario

Vocabulario común del proyecto. Se usa igual en el código, en los tests, en los
commits y en la interfaz.

| Término | Significado |
|---|---|
| **Frase** | Texto corto registrado por una persona. Entre 3 y 280 caracteres normalizados |
| **Texto original** | La frase tal como la escribió la persona. Es la que se muestra en pantalla |
| **Texto normalizado** | Versión en minúsculas, sin espacios sobrantes y con Unicode NFKC. Solo se usa para comparar, nunca se muestra |
| **Embedding** | Lista de 384 números que representa el significado de una frase. Frases con significado parecido producen listas parecidas |
| **Similitud coseno** | Medida de qué tan alineados están dos embeddings. Va de 0 a 1 aproximadamente; 1 significa el mismo significado |
| **Puntaje** | El valor de similitud coseno obtenido contra la frase más parecida |
| **Umbral** | Valor a partir del cual consideramos que dos frases significan lo mismo. Configurable, por defecto 0.80 |
| **Posible duplicado** | Frase cuyo puntaje es mayor o igual al umbral |
| **Duplicado exacto** | Frase cuyo texto normalizado coincide letra por letra con una existente. Puntaje 1.0 |
| **Frase más parecida** | La frase registrada con el puntaje más alto respecto a la frase nueva |
| **Estado** | Situación con la que quedó registrada una frase: `UNICA` o `DUPLICADO_CONFIRMADO` |
| **Validar** | Operación de solo lectura que compara una frase contra las registradas y devuelve el resultado, sin guardar nada |
| **Guardar** | Operación que revalida y, si corresponde, persiste la frase con sus metadatos |
| **Confirmar duplicado** | Decisión explícita de la persona de guardar una frase pese a la alerta |
| **Puerto** | Interfaz que declara qué necesita la aplicación, sin decir cómo se hace. Se define con `typing.Protocol` |
| **Adaptador** | Implementación concreta de un puerto: PostgreSQL, Hugging Face, el embedder falso de los tests |
| **Embedder falso** | Implementación determinista de `ProveedorEmbeddings` usada en tests. No carga ningún modelo |
| **pgvector** | Extensión de PostgreSQL que permite almacenar vectores y buscar el más cercano con operadores SQL |
| **HNSW** | Tipo de índice de pgvector para búsqueda aproximada de vecinos cercanos |
| **RN-nn** | Identificador de una regla de negocio en `business-rules.md` |
| **AC-nn** | Identificador de un criterio de aceptación en la spec de una funcionalidad |
| **T-nn** | Identificador de una tarea en `tasks.md` |

## En la interfaz no decimos

| No mostrar | Mostrar |
|---|---|
| "embedding" | — (no se menciona) |
| "similitud coseno 0.8734" | "87% de similitud" |
| "umbral" | "muy parecida a una frase existente" |
| "estado: DUPLICADO_CONFIRMADO" | "guardada como duplicado confirmado" |
| "HTTP 409" | "Ya existe una frase muy parecida" |
