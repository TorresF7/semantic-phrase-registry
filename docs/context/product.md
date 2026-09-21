# Producto — Banco de Frases

## El problema

Dentro de la organización, distintos equipos registran **frases cortas** en un
repositorio compartido: etiquetas de producto, mensajes al cliente, criterios de
clasificación, nombres de campañas, respuestas predefinidas.

Con el tiempo el repositorio se llena de frases que **dicen lo mismo con otras
palabras**:

- "El pago fue rechazado por el banco"
- "La entidad bancaria rechazó la transacción"

Para un sistema tradicional son dos frases distintas, porque no comparten
palabras. Para una persona son la misma idea. El resultado es un catálogo
inflado, inconsistente y difícil de mantener: el mismo concepto aparece tres
veces con redacciones distintas y nadie sabe cuál es la buena.

Un filtro de texto exacto no resuelve esto. Hace falta comparar **significado**.

## Qué construimos

Una aplicación web donde una persona puede:

1. Escribir una frase nueva en un formulario simple.
2. Ver la lista de frases ya registradas.
3. Presionar **Validar** antes de guardar. El sistema compara la frase nueva
   contra todas las guardadas y responde si hay alguna que signifique lo mismo,
   mostrando cuál es y qué tan parecida es.
4. Si hay un posible duplicado, recibir una alerta clara y decidir:
   **confirmar** el guardado de todos modos, o **cancelar**.

La comparación se hace con un modelo de lenguaje que convierte cada frase en un
vector numérico que representa su significado. Dos frases con significado
parecido producen vectores parecidos. La cercanía se mide con similitud coseno y
se compara contra un umbral configurable.

## Usuarios

Personas del equipo de negocio, sin perfil técnico. Esperan una interfaz de una
sola pantalla, respuestas rápidas y mensajes en lenguaje claro. No deben ver
jerga técnica: no se les muestra "embedding", "coseno" ni "0.8734". Se les
muestra "Esta frase se parece mucho a una existente (87% de similitud)".

## Alcance

**Dentro:**
- Alta de frases con validación semántica previa.
- Listado paginado de frases registradas.
- Detección de duplicados exactos y semánticos.
- Umbral de similitud configurable por entorno.
- Registro de metadatos de la validación: puntaje, frase más parecida, estado,
  modelo utilizado, umbral aplicado, fecha.

**Fuera (decidido, no olvidado):**
- Autenticación y gestión de usuarios. El repositorio es compartido y sin dueño
  por frase.
- Edición y borrado de frases. Solo alta y consulta.
- Categorías, etiquetas o jerarquías.
- Procesamiento asíncrono. La validación es síncrona porque la persona espera el
  resultado para decidir.
- Generación de texto con un LLM. Aquí no se genera contenido, solo se compara.
- Búsqueda libre por texto. El listado es cronológico y paginado.

## Requisitos no funcionales

| # | Requisito | Objetivo medible |
|---|---|---|
| NF-01 | Latencia de validación | p95 por debajo de 400 ms con 100 000 frases registradas. Es un objetivo de diseño que justifica NF-02 y el índice HNSW; no se mide en esta entrega |
| NF-02 | Escalabilidad de la búsqueda | La comparación vectorial se resuelve en el motor de base de datos con un índice aproximado. Nunca se cargan todas las frases en memoria de la aplicación |
| NF-03 | Costo de arranque | El modelo se carga una sola vez al iniciar el proceso, no por petición |
| NF-04 | Escalado horizontal | La API es sin estado. Varias réplicas pueden atender detrás de un balanceador sin coordinación entre ellas |
| NF-05 | Paginación | El listado nunca devuelve el conjunto completo. Tamaño de página máximo: 100 |
| NF-06 | Degradación controlada | Si el modelo de embeddings no está disponible, la API responde 503 y **no** guarda la frase. Nunca se persiste una frase sin validar |
| NF-07 | Reproducibilidad | `docker compose up` deja la aplicación funcionando en una máquina limpia, sin pasos manuales adicionales |
| NF-08 | Portabilidad del proveedor de IA | Cambiar el modelo o pasar a un proveedor remoto debe requerir un adaptador nuevo, sin tocar los casos de uso |

## Cómo se ve el éxito

Una persona escribe "El pago fue rechazado por el banco", presiona Validar, y el
sistema le advierte que ya existe "La entidad bancaria rechazó la transacción"
con un porcentaje alto de similitud, dándole la opción de guardar igual o
cancelar. Todo en menos de medio segundo.

El porcentaje concreto de ese par se mide con el modelo real antes de empezar
(T-00) y es el que aparece en el README.
