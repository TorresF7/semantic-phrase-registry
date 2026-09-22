---
name: security-review
description: Revisión de seguridad del código de este proyecto. Úsala sobre cualquier cambio que toque entrada de datos, respuestas HTTP, consultas a la base, configuración o despliegue.
---

# Revisión de seguridad

Revisa el cambio contra esta lista. Para cada punto responde una de tres cosas:
**cumple**, **no aplica** (diciendo por qué), o **hallazgo** (con archivo, línea
y cómo se explota).

No inventes riesgos teóricos para llenar el informe. Un hallazgo sin escenario
de explotación concreto no es un hallazgo.

## Entrada de datos

- [ ] Toda entrada del cliente pasa por un schema Pydantic con tipo, rango y un
      tope defensivo de tamaño. Nada llega crudo a la lógica. La longitud de
      negocio (3 a 280 sobre el texto normalizado) la aplica el dominio, no el
      schema.
- [ ] La validación del servidor existe aunque el cliente ya valide (Artículo 8).
- [ ] La normalización Unicode se aplica antes de comparar, para que no se pueda
      esquivar la detección con caracteres equivalentes.
- [ ] Los parámetros de paginación tienen máximo. `limite=999999` debe ser `422`,
      no un volcado de la tabla.

## Base de datos

- [ ] Todas las consultas son parametrizadas. Ningún f-string ni concatenación
      dentro de `text()` o de una sentencia SQL.
- [ ] El usuario de la aplicación no es superusuario de PostgreSQL. En Compose
      local **no aplica**: la migración ejecuta `CREATE EXTENSION`, que exige
      superusuario, y es un entorno de desarrollo. Sí aplica en T-19.
- [ ] Las escrituras que deben ser atómicas están en una transacción.

## Respuestas

- [ ] Ninguna respuesta de error incluye traza, nombre de clase, ruta de
      archivo, consulta SQL ni versión de librería.
- [ ] El código de estado es el correcto: `422` validación, `409` conflicto de
      negocio, `503` dependencia caída, `500` solo lo inesperado.
- [ ] Los mensajes al cliente no revelan estructura interna.

## Configuración y secretos

- [ ] Ningún secreto, cadena de conexión, clave o contraseña en el código o en
      el historial de Git.
- [ ] `.env` está en `.gitignore`. Existe `.env.example` con nombres pero sin
      valores reales.
- [ ] Ningún secreto en variables `VITE_*`: se incrustan en el paquete público.

## Exposición

- [ ] CORS con lista explícita de orígenes. Nunca `allow_origins=["*"]` junto a
      credenciales.
- [ ] En Compose, PostgreSQL no publica puerto hacia afuera (solo en el
      `override` de desarrollo).
- [ ] Las imágenes Docker corren con un usuario sin privilegios, no como root.
- [ ] Si hay despliegue público (T-19): HTTPS, límite de peticiones por IP en
      el proxy (D-11), cabeceras `X-Content-Type-Options`, `X-Frame-Options` y
      una CSP básica. Sin despliegue público, **no aplica**.

## Frontend

- [ ] Sin `dangerouslySetInnerHTML` en ninguna parte.
- [ ] El contenido que escribe la persona se renderiza como texto, nunca como
      HTML.
- [ ] Ninguna URL se construye concatenando entrada del usuario sin codificar.

## Dependencias

- [ ] Las versiones están fijadas, no abiertas.
- [ ] No se agregó ninguna dependencia que no esté justificada en el plan.

## Formato del informe

```
## Revisión de seguridad — T-nn

### Hallazgos
1. [ALTO] adapters/api/errores.py:34 — la respuesta de 500 incluye str(exc),
   que expone la consulta SQL. Un atacante aprende la estructura de la tabla
   provocando un error de tipo.
   Corrección: registrar la excepción en el log y devolver un mensaje genérico.

### Verificado sin hallazgos
- Consultas parametrizadas, CORS, secretos, frontend.

### No aplica
- Despliegue: este cambio no toca infraestructura.
```

Ordena los hallazgos por severidad: ALTO, MEDIO, BAJO.
