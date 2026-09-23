// Tests del adaptador de API: lo que el cliente hace con cada respuesta HTTP.
// `fetch` se sustituye por un doble; ninguna petición sale de la prueba. Los
// tests de `App` y de la lista sustituyen este módulo entero, así que es aquí
// donde se comprueba la traducción de respuestas a valores del tipo
// discriminado (patrón "Adaptador de API").

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { guardarFrase, listarFrases, validarFrase } from "./cliente";
import type { DatosDuplicado } from "./tipos";

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
});

function respuestaJson(estado: number, cuerpo: unknown): Response {
  return new Response(JSON.stringify(cuerpo), {
    status: estado,
    headers: { "Content-Type": "application/json" },
  });
}

const DUPLICADO: DatosDuplicado = {
  motivo: "SEMANTICO",
  puntaje: 0.87,
  umbral_aplicado: 0.75,
  mas_parecida: { id: 1, texto: "La entidad bancaria rechazó la transacción" },
};

describe("cliente de la API", () => {
  it("ac10: un 409 al guardar se traduce a posible_duplicado con los detalles del servidor", async () => {
    fetchMock.mockResolvedValueOnce(
      respuestaJson(409, {
        codigo: "POSIBLE_DUPLICADO",
        mensaje: "Ya existe una frase muy parecida.",
        detalles: DUPLICADO,
      }),
    );

    const resultado = await guardarFrase("El pago fue rechazado por el banco", false);

    expect(resultado).toEqual({ tipo: "posible_duplicado", duplicado: DUPLICADO });
    const [url, opciones] = fetchMock.mock.calls[0] ?? [];
    expect(String(url)).toMatch(/\/frases$/);
    expect(opciones?.body).toBe(
      JSON.stringify({ texto: "El pago fue rechazado por el banco", confirmar_duplicado: false }),
    );
  });

  it("un 200 con una forma que no es la del contrato se trata como RESPUESTA_INESPERADA", async () => {
    fetchMock.mockResolvedValueOnce(respuestaJson(200, { es_posible_duplicado: "no" }));

    const resultado = await validarFrase("El pago fue rechazado");

    expect(resultado).toEqual({
      ok: false,
      error: expect.objectContaining({ codigo: "RESPUESTA_INESPERADA", estado_http: 200 }),
    });
  });

  it("un 502 de nginx con cuerpo HTML se trata como RESPUESTA_INESPERADA", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response("<html><body><h1>502 Bad Gateway</h1></body></html>", {
        status: 502,
        headers: { "Content-Type": "text/html" },
      }),
    );

    const resultado = await listarFrases(20, 0);

    expect(resultado).toEqual({
      ok: false,
      error: {
        codigo: "RESPUESTA_INESPERADA",
        mensaje: "El servidor respondió algo inesperado. Inténtalo de nuevo.",
        detalles: null,
        estado_http: 502,
      },
    });
  });

  it("si la red falla, validar y guardar devuelven SIN_CONEXION sin código HTTP", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));

    const validacion = await validarFrase("El pago fue rechazado");
    const guardado = await guardarFrase("El pago fue rechazado", false);

    const esperado = expect.objectContaining({ codigo: "SIN_CONEXION", estado_http: null });
    expect(validacion).toEqual({ ok: false, error: esperado });
    expect(guardado).toEqual({ tipo: "error", error: esperado });
  });
});

// El tiempo límite se lee de VITE_API_TIMEOUT_MS al cargar el módulo: cada test
// fija la variable y vuelve a importar el cliente (D-38).
describe("tiempo límite de las peticiones (D-38)", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
    vi.resetModules();
  });

  async function importarCliente(tiempoLimite: string): Promise<typeof import("./cliente")> {
    vi.stubEnv("VITE_API_TIMEOUT_MS", tiempoLimite);
    vi.resetModules();
    return import("./cliente");
  }

  // Un servidor que nunca contesta: la promesa solo se rechaza al abortarse.
  function servidorMudo(): void {
    fetchMock.mockImplementation(
      (_url, opciones) =>
        new Promise<Response>((_resolver, rechazar) => {
          const senal = opciones?.signal;
          senal?.addEventListener("abort", () => rechazar(senal.reason));
        }),
    );
  }

  it("fetch recibe una señal que aborta con el valor configurado", async () => {
    const timeout = vi.spyOn(AbortSignal, "timeout");
    const cliente = await importarCliente("2500");
    fetchMock.mockResolvedValueOnce(respuestaJson(200, { total: 0 }));

    await cliente.listarFrases(20, 0);

    expect(timeout).toHaveBeenCalledWith(2500);
    expect(fetchMock.mock.calls[0]?.[1]?.signal).toBeInstanceOf(AbortSignal);
  });

  it("un valor que no es un entero positivo usa el valor por defecto, 15000 ms", async () => {
    const timeout = vi.spyOn(AbortSignal, "timeout");
    const cliente = await importarCliente("mucho");
    fetchMock.mockResolvedValueOnce(respuestaJson(200, { total: 0 }));

    await cliente.listarFrases(20, 0);

    expect(timeout).toHaveBeenCalledWith(15000);
  });

  it("si el servidor no contesta a tiempo, validar, guardar y listar devuelven SIN_CONEXION sin código HTTP", async () => {
    const cliente = await importarCliente("20");
    servidorMudo();

    const validacion = await cliente.validarFrase("El pago fue rechazado");
    const guardado = await cliente.guardarFrase("El pago fue rechazado", false);
    const listado = await cliente.listarFrases(20, 0);

    const esperado = expect.objectContaining({ codigo: "SIN_CONEXION", estado_http: null });
    expect(validacion).toEqual({ ok: false, error: esperado });
    expect(guardado).toEqual({ tipo: "error", error: esperado });
    expect(listado).toEqual({ ok: false, error: esperado });
  });

  it("si el tiempo se agota mientras llega el cuerpo, también es SIN_CONEXION", async () => {
    const cliente = await importarCliente("20");
    // Llegan las cabeceras, pero el cuerpo se corta al abortarse, como en fetch.
    fetchMock.mockImplementation(async (_url, opciones) => {
      const senal = opciones?.signal;
      const cuerpo = new ReadableStream<Uint8Array>({
        start(controlador) {
          senal?.addEventListener("abort", () => controlador.error(senal.reason));
        },
      });
      return new Response(cuerpo, { status: 200 });
    });

    const validacion = await cliente.validarFrase("El pago fue rechazado");

    expect(validacion).toEqual({
      ok: false,
      error: expect.objectContaining({ codigo: "SIN_CONEXION", estado_http: null }),
    });
  });
});
