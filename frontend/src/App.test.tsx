// Tests del flujo completo de la pantalla única (T-14): formulario, alerta de
// posible duplicado y confirmación de guardado. Se prueban a través de `App`
// porque es ahí donde vive la máquina de estados de `useValidacion` (plan §5).
// El cliente de API se sustituye por completo: ningún test hace peticiones
// reales. `GET /frases` (T-15) no es parte de esta tarea: solo se deja un doble
// que resuelve una página vacía para que `App` pueda montarse sin fallar.

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import App from "./App";
import { guardarFrase, listarFrases, validarFrase } from "./api/cliente";
import type {
  DatosDuplicado,
  ErrorApi,
  Frase,
  FraseResumen,
  PaginaFrases,
  ResultadoValidacion,
} from "./api/tipos";

vi.mock("./api/cliente", () => ({
  validarFrase: vi.fn(),
  guardarFrase: vi.fn(),
  listarFrases: vi.fn(),
}));

const validarFraseMock = vi.mocked(validarFrase);
const guardarFraseMock = vi.mocked(guardarFrase);
const listarFrasesMock = vi.mocked(listarFrases);

const MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2";

function crearFraseResumen(overrides: Partial<FraseResumen> = {}): FraseResumen {
  return { id: 1, texto: "El pago fue rechazado por el banco", ...overrides };
}

function crearResultadoValidacion(
  overrides: Partial<ResultadoValidacion> = {},
): ResultadoValidacion {
  return {
    es_posible_duplicado: false,
    motivo: null,
    puntaje: null,
    umbral_aplicado: 0.75,
    mas_parecida: null,
    modelo: MODELO,
    ...overrides,
  };
}

function crearDatosDuplicado(overrides: Partial<DatosDuplicado> = {}): DatosDuplicado {
  return {
    motivo: "SEMANTICO",
    puntaje: 0.91,
    umbral_aplicado: 0.75,
    mas_parecida: crearFraseResumen(),
    ...overrides,
  };
}

function crearFrase(overrides: Partial<Frase> = {}): Frase {
  return {
    id: 10,
    texto: "Una frase cualquiera",
    estado: "UNICA",
    puntaje_similitud: null,
    id_mas_parecida: null,
    umbral_aplicado: 0.75,
    modelo: MODELO,
    creada_en: "2026-09-22T10:00:00Z",
    ...overrides,
  };
}

function crearErrorApi(overrides: Partial<ErrorApi> = {}): ErrorApi {
  return {
    codigo: "SERVICIO_IA_NO_DISPONIBLE",
    mensaje: "El servicio no está disponible.",
    detalles: null,
    estado_http: 503,
    ...overrides,
  };
}

function paginaVacia(): PaginaFrases {
  return { total: 0, limite: 20, desplazamiento: 0, items: [] };
}

beforeEach(() => {
  validarFraseMock.mockReset();
  guardarFraseMock.mockReset();
  listarFrasesMock.mockReset();
  listarFrasesMock.mockResolvedValue({ ok: true, datos: paginaVacia() });
});

describe("formulario, alerta y confirmación (T-14)", () => {
  it("el botón Guardar está deshabilitado sin validación previa y explica por qué", () => {
    render(<App />);

    expect(screen.getByRole("button", { name: "Guardar" })).toBeDisabled();
    expect(screen.getByText("Valida la frase antes de guardar")).toBeInTheDocument();
  });

  it("el contador de caracteres cuenta puntos de código, no unidades UTF-16", async () => {
    const usuario = userEvent.setup();
    render(<App />);
    const campo = screen.getByRole("textbox", { name: "Frase" });

    await usuario.type(campo, "😀ab");

    expect(screen.getByText("3 / 280")).toBeInTheDocument();
  });

  it("al validar con puntaje sobre el umbral muestra la alerta con la frase existente y el porcentaje", async () => {
    const usuario = userEvent.setup();
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: true,
        motivo: "SEMANTICO",
        puntaje: 0.8735,
        mas_parecida: crearFraseResumen({ id: 42, texto: "El pago fue rechazado por el banco" }),
      }),
    });
    render(<App />);
    const campo = screen.getByRole("textbox", { name: "Frase" });
    await usuario.type(campo, "La entidad bancaria rechazó la transacción");
    await usuario.click(screen.getByRole("button", { name: "Validar" }));

    const alerta = await screen.findByRole("alert");
    expect(
      within(alerta).getByText("Esta frase se parece mucho a una existente"),
    ).toBeInTheDocument();
    expect(within(alerta).getByText("El pago fue rechazado por el banco")).toBeInTheDocument();
    expect(within(alerta).getByText("87% de similitud")).toBeInTheDocument();
  });

  it("el duplicado exacto se anuncia sin mostrar ningún porcentaje", async () => {
    const usuario = userEvent.setup();
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: true,
        motivo: "EXACTO",
        puntaje: 1,
        mas_parecida: crearFraseResumen({ id: 7, texto: "Hola mundo" }),
      }),
    });
    render(<App />);
    const campo = screen.getByRole("textbox", { name: "Frase" });
    await usuario.type(campo, "hola mundo");
    await usuario.click(screen.getByRole("button", { name: "Validar" }));

    const alerta = await screen.findByRole("alert");
    expect(within(alerta).getByText("Esta frase ya existe tal cual")).toBeInTheDocument();
    expect(within(alerta).queryByText(/% de similitud/)).not.toBeInTheDocument();
  });

  it("la frase única se anuncia sin porcentaje ni frase más cercana, y habilita Guardar", async () => {
    const usuario = userEvent.setup();
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: false,
        motivo: null,
        puntaje: 0.42,
        mas_parecida: crearFraseResumen({ id: 5, texto: "Una frase completamente distinta" }),
      }),
    });
    render(<App />);
    const campo = screen.getByRole("textbox", { name: "Frase" });
    await usuario.type(campo, "Una frase nueva");
    await usuario.click(screen.getByRole("button", { name: "Validar" }));

    const estado = await screen.findByRole("status");
    expect(
      within(estado).getByText("No encontramos frases parecidas. Puedes guardarla."),
    ).toBeInTheDocument();
    expect(within(estado).queryByText(/% de similitud/)).not.toBeInTheDocument();
    expect(within(estado).queryByText("Una frase completamente distinta")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Guardar" })).toBeEnabled();
  });

  it("ac16: tras guardar una frase única muestra 'Frase guardada.' y vacía el campo", async () => {
    const usuario = userEvent.setup();
    const texto = "Una frase completamente nueva";
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: false,
        puntaje: null,
        mas_parecida: null,
      }),
    });
    guardarFraseMock.mockResolvedValueOnce({
      tipo: "guardada",
      frase: crearFrase({ texto, estado: "UNICA" }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: "Frase" });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: "Validar" }));
    await screen.findByText("No encontramos frases parecidas. Puedes guardarla.");

    await usuario.click(screen.getByRole("button", { name: "Guardar" }));

    const confirmacion = await screen.findByRole("status");
    expect(confirmacion).toHaveTextContent("Frase guardada.");
    expect(campo).toHaveValue("");
    expect(guardarFraseMock).toHaveBeenCalledWith(texto, false);
  });

  it("ac16: tras guardar de todos modos muestra 'Frase guardada como duplicado confirmado.' y vacía el campo", async () => {
    const usuario = userEvent.setup();
    const texto = "La entidad bancaria rechazó la transacción";
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: true,
        motivo: "SEMANTICO",
        puntaje: 0.8735,
        mas_parecida: crearFraseResumen({ id: 42, texto: "El pago fue rechazado por el banco" }),
      }),
    });
    guardarFraseMock.mockResolvedValueOnce({
      tipo: "guardada",
      frase: crearFrase({ texto, estado: "DUPLICADO_CONFIRMADO" }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: "Frase" });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: "Validar" }));
    await screen.findByRole("alert");

    await usuario.click(screen.getByRole("button", { name: "Guardar de todos modos" }));

    const confirmacion = await screen.findByRole("status");
    expect(confirmacion).toHaveTextContent("Frase guardada como duplicado confirmado.");
    expect(campo).toHaveValue("");
    expect(guardarFraseMock).toHaveBeenCalledWith(texto, true);
  });

  it("ac16: la confirmación de guardado desaparece al empezar a escribir una frase nueva", async () => {
    const usuario = userEvent.setup();
    const texto = "Una frase completamente nueva";
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: false,
        puntaje: null,
        mas_parecida: null,
      }),
    });
    guardarFraseMock.mockResolvedValueOnce({
      tipo: "guardada",
      frase: crearFrase({ texto, estado: "UNICA" }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: "Frase" });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: "Validar" }));
    await screen.findByText("No encontramos frases parecidas. Puedes guardarla.");
    await usuario.click(screen.getByRole("button", { name: "Guardar" }));
    await screen.findByText("Frase guardada.");

    await usuario.type(campo, "N");

    expect(screen.queryByText("Frase guardada.")).not.toBeInTheDocument();
  });

  it("ac16b: editar el texto tras una validación única oculta el resultado y deshabilita Guardar", async () => {
    const usuario = userEvent.setup();
    const texto = "Una frase completamente nueva";
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: false,
        puntaje: null,
        mas_parecida: null,
      }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: "Frase" });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: "Validar" }));
    await screen.findByText("No encontramos frases parecidas. Puedes guardarla.");
    expect(screen.getByRole("button", { name: "Guardar" })).toBeEnabled();

    await usuario.type(campo, "!");

    expect(
      screen.queryByText("No encontramos frases parecidas. Puedes guardarla."),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Guardar" })).toBeDisabled();
  });

  it("ac16b: editar el texto tras un posible duplicado oculta la alerta y deshabilita Guardar", async () => {
    const usuario = userEvent.setup();
    const texto = "La entidad bancaria rechazó la transacción";
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: true,
        motivo: "SEMANTICO",
        puntaje: 0.8735,
        mas_parecida: crearFraseResumen({ id: 42, texto: "El pago fue rechazado por el banco" }),
      }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: "Frase" });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: "Validar" }));
    await screen.findByRole("alert");

    await usuario.type(campo, "!");

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Guardar" })).toBeDisabled();
  });

  it("ac16b: Cancelar en la alerta la hace desaparecer y conserva el texto escrito", async () => {
    const usuario = userEvent.setup();
    const texto = "La entidad bancaria rechazó la transacción";
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: true,
        motivo: "SEMANTICO",
        puntaje: 0.8735,
        mas_parecida: crearFraseResumen({ id: 42, texto: "El pago fue rechazado por el banco" }),
      }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: "Frase" });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: "Validar" }));
    await screen.findByRole("alert");

    await usuario.click(screen.getByRole("button", { name: "Cancelar" }));

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(campo).toHaveValue(texto);
    expect(screen.getByRole("button", { name: "Guardar" })).toBeDisabled();
  });

  it("el 409 del guardado vuelve a mostrar la alerta con los datos nuevos y conserva el texto", async () => {
    const usuario = userEvent.setup();
    const texto = "Una frase que el servidor sí considera parecida";
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: false,
        puntaje: null,
        mas_parecida: null,
      }),
    });
    guardarFraseMock.mockResolvedValueOnce({
      tipo: "posible_duplicado",
      duplicado: crearDatosDuplicado({
        motivo: "SEMANTICO",
        puntaje: 0.91,
        mas_parecida: crearFraseResumen({ id: 99, texto: "Otra frase registrada justo antes" }),
      }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: "Frase" });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: "Validar" }));
    await screen.findByText("No encontramos frases parecidas. Puedes guardarla.");

    await usuario.click(screen.getByRole("button", { name: "Guardar" }));

    const alerta = await screen.findByRole("alert");
    expect(within(alerta).getByText("Otra frase registrada justo antes")).toBeInTheDocument();
    expect(within(alerta).getByText("91% de similitud")).toBeInTheDocument();
    expect(campo).toHaveValue(texto);
  });

  it("un error 503 al validar muestra el mensaje y Reintentar repite la validación", async () => {
    const usuario = userEvent.setup();
    const texto = "Una frase cualquiera";
    validarFraseMock.mockResolvedValueOnce({ ok: false, error: crearErrorApi() });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: "Frase" });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: "Validar" }));

    await screen.findByText("El servicio no está disponible.");
    const reintentar = screen.getByRole("button", { name: "Reintentar" });

    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: false,
        puntaje: null,
        mas_parecida: null,
      }),
    });

    await usuario.click(reintentar);

    await screen.findByText("No encontramos frases parecidas. Puedes guardarla.");
    expect(validarFraseMock).toHaveBeenNthCalledWith(2, texto);
  });

  it("un error 422 al validar muestra el mensaje sin ofrecer Reintentar", async () => {
    const usuario = userEvent.setup();
    const texto = "ab";
    validarFraseMock.mockResolvedValueOnce({
      ok: false,
      error: crearErrorApi({
        codigo: "FRASE_INVALIDA",
        mensaje: "La frase debe tener entre 3 y 280 caracteres.",
        estado_http: 422,
      }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: "Frase" });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: "Validar" }));

    await screen.findByText("La frase debe tener entre 3 y 280 caracteres.");
    expect(screen.queryByRole("button", { name: "Reintentar" })).not.toBeInTheDocument();
  });
});
