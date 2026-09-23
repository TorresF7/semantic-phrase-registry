// Adaptador de la API: el único módulo que conoce URLs, `fetch` y códigos HTTP.
// Toda respuesta se comprueba en tiempo de ejecución antes de tiparla: lo que
// no tiene la forma del contrato se trata como error, nunca se da por bueno.

import type {
  DatosDuplicado,
  ErrorApi,
  EstadoFrase,
  Frase,
  FraseResumen,
  ItemListado,
  Motivo,
  PaginaFrases,
  Resultado,
  ResultadoGuardado,
  ResultadoValidacion,
} from "./tipos";

const URL_BASE: string = import.meta.env.VITE_API_URL ?? "/api/v1";

// Sin respuesta en este tiempo, la petición se aborta y cuenta como sin
// conexión (D-38). Holgado: validar con el modelo cargado tarda milisegundos.
const TIEMPO_LIMITE_POR_DEFECTO_MS = 15000;
const tiempoLimiteConfigurado = Number(import.meta.env.VITE_API_TIMEOUT_MS);
const TIEMPO_LIMITE_MS =
  Number.isInteger(tiempoLimiteConfigurado) && tiempoLimiteConfigurado > 0
    ? tiempoLimiteConfigurado
    : TIEMPO_LIMITE_POR_DEFECTO_MS;

const ERROR_RED: ErrorApi = {
  codigo: "SIN_CONEXION",
  mensaje: "No pudimos conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.",
  detalles: null,
  estado_http: null,
};

const MENSAJE_INESPERADO = "El servidor respondió algo inesperado. Inténtalo de nuevo.";

export async function validarFrase(texto: string): Promise<Resultado<ResultadoValidacion>> {
  return pedir("/frases/validar", enviarJson({ texto }), esResultadoValidacion);
}

export async function guardarFrase(
  texto: string,
  confirmarDuplicado: boolean,
): Promise<ResultadoGuardado> {
  const respuesta = await enviar(
    "/frases",
    enviarJson({ texto, confirmar_duplicado: confirmarDuplicado }),
  );
  if (!respuesta.ok) {
    return { tipo: "error", error: respuesta.error };
  }
  const { estado, cuerpo } = respuesta;
  if (estado === 201 && esFrase(cuerpo)) {
    return { tipo: "guardada", frase: cuerpo };
  }
  // El servidor revalidó y encontró un posible duplicado (RN-11, RN-12).
  if (estado === 409 && esObjeto(cuerpo) && esDatosDuplicado(cuerpo["detalles"])) {
    return { tipo: "posible_duplicado", duplicado: cuerpo["detalles"] };
  }
  return { tipo: "error", error: aErrorApi(estado, cuerpo) };
}

export async function listarFrases(
  limite: number,
  desplazamiento: number,
): Promise<Resultado<PaginaFrases>> {
  const parametros = new URLSearchParams({
    limite: String(limite),
    desplazamiento: String(desplazamiento),
  });
  return pedir(`/frases?${parametros.toString()}`, { method: "GET" }, esPaginaFrases);
}

// --- Transporte ---------------------------------------------------------------

type Respuesta = { ok: true; estado: number; cuerpo: unknown } | { ok: false; error: ErrorApi };

async function enviar(ruta: string, opciones: RequestInit): Promise<Respuesta> {
  const senal = AbortSignal.timeout(TIEMPO_LIMITE_MS);
  let respuesta: Response;
  try {
    respuesta = await fetch(`${URL_BASE}${ruta}`, { ...opciones, signal: senal });
  } catch {
    return { ok: false, error: ERROR_RED };
  }
  const cuerpo = await leerJson(respuesta);
  // Si el tiempo se agotó mientras llegaba el cuerpo, tampoco hubo respuesta.
  if (senal.aborted) {
    return { ok: false, error: ERROR_RED };
  }
  return { ok: true, estado: respuesta.status, cuerpo };
}

async function pedir<T>(
  ruta: string,
  opciones: RequestInit,
  esValido: (valor: unknown) => valor is T,
): Promise<Resultado<T>> {
  const respuesta = await enviar(ruta, opciones);
  if (!respuesta.ok) {
    return respuesta;
  }
  const { estado, cuerpo } = respuesta;
  if (estado >= 200 && estado < 300 && esValido(cuerpo)) {
    return { ok: true, datos: cuerpo };
  }
  return { ok: false, error: aErrorApi(estado, cuerpo) };
}

function enviarJson(cuerpo: Record<string, unknown>): RequestInit {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
  };
}

async function leerJson(respuesta: Response): Promise<unknown> {
  try {
    const cuerpo: unknown = await respuesta.json();
    return cuerpo;
  } catch {
    // Un 502 de nginx, por ejemplo, llega como HTML.
    return null;
  }
}

function aErrorApi(estado: number, cuerpo: unknown): ErrorApi {
  if (
    esObjeto(cuerpo) &&
    typeof cuerpo["codigo"] === "string" &&
    typeof cuerpo["mensaje"] === "string"
  ) {
    const detalles = cuerpo["detalles"];
    return {
      codigo: cuerpo["codigo"],
      mensaje: cuerpo["mensaje"],
      detalles: esObjeto(detalles) ? detalles : null,
      estado_http: estado,
    };
  }
  return {
    codigo: "RESPUESTA_INESPERADA",
    mensaje: MENSAJE_INESPERADO,
    detalles: null,
    estado_http: estado,
  };
}

// --- Comprobación de forma ----------------------------------------------------

function esObjeto(valor: unknown): valor is Record<string, unknown> {
  return typeof valor === "object" && valor !== null && !Array.isArray(valor);
}

function esNumeroONulo(valor: unknown): valor is number | null {
  return valor === null || typeof valor === "number";
}

function esMotivoONulo(valor: unknown): valor is Motivo | null {
  return valor === null || valor === "EXACTO" || valor === "SEMANTICO";
}

function esEstadoFrase(valor: unknown): valor is EstadoFrase {
  return valor === "UNICA" || valor === "DUPLICADO_CONFIRMADO";
}

function esFraseResumen(valor: unknown): valor is FraseResumen {
  return esObjeto(valor) && typeof valor["id"] === "number" && typeof valor["texto"] === "string";
}

function esDatosDuplicado(valor: unknown): valor is DatosDuplicado {
  return (
    esObjeto(valor) &&
    esMotivoONulo(valor["motivo"]) &&
    esNumeroONulo(valor["puntaje"]) &&
    typeof valor["umbral_aplicado"] === "number" &&
    (valor["mas_parecida"] === null || esFraseResumen(valor["mas_parecida"]))
  );
}

function esResultadoValidacion(valor: unknown): valor is ResultadoValidacion {
  return (
    esObjeto(valor) &&
    typeof valor["es_posible_duplicado"] === "boolean" &&
    typeof valor["modelo"] === "string" &&
    esDatosDuplicado(valor)
  );
}

// Campos que comparten la frase creada (201) y el elemento del listado.
function tieneCamposDeFrase(valor: Record<string, unknown>): boolean {
  return (
    typeof valor["id"] === "number" &&
    typeof valor["texto"] === "string" &&
    esEstadoFrase(valor["estado"]) &&
    esNumeroONulo(valor["puntaje_similitud"]) &&
    typeof valor["creada_en"] === "string"
  );
}

function esItemListado(valor: unknown): valor is ItemListado {
  return (
    esObjeto(valor) &&
    tieneCamposDeFrase(valor) &&
    (valor["mas_parecida"] === null || esFraseResumen(valor["mas_parecida"]))
  );
}

function esFrase(valor: unknown): valor is Frase {
  return (
    esObjeto(valor) &&
    tieneCamposDeFrase(valor) &&
    esNumeroONulo(valor["id_mas_parecida"]) &&
    typeof valor["umbral_aplicado"] === "number" &&
    typeof valor["modelo"] === "string"
  );
}

function esPaginaFrases(valor: unknown): valor is PaginaFrases {
  return (
    esObjeto(valor) &&
    typeof valor["total"] === "number" &&
    typeof valor["limite"] === "number" &&
    typeof valor["desplazamiento"] === "number" &&
    Array.isArray(valor["items"]) &&
    valor["items"].every(esItemListado)
  );
}
