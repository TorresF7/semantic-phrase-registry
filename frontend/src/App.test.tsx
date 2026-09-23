// Tests del registro en línea (T-22): campo, botón principal que avanza por
// pasos, y el veredicto (`unica`, `posible_duplicado`, `conflicto`, `error`,
// `guardada`), según la máquina de estados y la tabla de transiciones de
// `plan.md` §5 y la skill `ui-design` v2 (D-27). Se prueban a través de `App`
// porque es ahí donde vive la máquina de estados de `useValidacion`. El
// cliente de API se sustituye por completo: ningún test hace peticiones
// reales. `GET /frases` no es parte de esta tarea: solo se deja un doble que
// resuelve una página vacía para que `App` pueda montarse sin fallar.

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

const NOMBRE_CAMPO = "Registrar frase";
const BOTON_INICIAL = "Comprobar similitud";

function porcentaje(valor: number): number {
  return Math.round(valor * 100);
}

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
    mensaje: "El servicio de comparación no está disponible.",
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

describe("registro en línea (T-22)", () => {
  it("el contador de caracteres cuenta puntos de código, no unidades UTF-16", async () => {
    const usuario = userEvent.setup();
    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });

    await usuario.type(campo, "😀ab");

    expect(screen.getByText("3 / 280")).toBeInTheDocument();
  });

  it("el botón principal 'Comprobar similitud' está deshabilitado con menos de 3 caracteres", async () => {
    const usuario = userEvent.setup();
    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });

    expect(screen.getByRole("button", { name: BOTON_INICIAL })).toBeDisabled();

    await usuario.type(campo, "ab");

    expect(screen.getByRole("button", { name: BOTON_INICIAL })).toBeDisabled();
  });

  it("el mínimo de 3 caracteres se mide sobre el texto normalizado: tres espacios dejan el botón deshabilitado", async () => {
    const usuario = userEvent.setup();
    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });

    await usuario.type(campo, "   ");

    // El contador también mide el texto normalizado, igual que el servidor.
    expect(screen.getByText("0 / 280")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: BOTON_INICIAL })).toBeDisabled();
  });

  describe("aviso de longitud en el pie del campo (RN-01)", () => {
    const AVISO_MINIMO = "La frase debe tener al menos 3 caracteres.";
    const AVISO_MAXIMO = "La frase no puede tener más de 280 caracteres.";

    function pieDelCampo(): HTMLElement {
      const pie = document.getElementById("pie-frase");
      if (pie === null) throw new Error("falta #pie-frase");
      return pie;
    }

    it("con el campo vacío no muestra ningún aviso", () => {
      render(<App />);

      expect(within(pieDelCampo()).queryByText(AVISO_MINIMO)).not.toBeInTheDocument();
      expect(within(pieDelCampo()).queryByText(AVISO_MAXIMO)).not.toBeInTheDocument();
    });

    it.each(["ab", "   ", "  ab  "])(
      "con %j, que normaliza a menos de 3 caracteres, muestra el mismo aviso que el servidor",
      async (texto) => {
        const usuario = userEvent.setup();
        render(<App />);
        const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });

        await usuario.type(campo, texto);

        expect(within(pieDelCampo()).getByText(AVISO_MINIMO)).toBeInTheDocument();
        expect(campo).toHaveAccessibleDescription(expect.stringContaining(AVISO_MINIMO));
      },
    );

    it("con 281 caracteres normalizados muestra el aviso del máximo y deshabilita el botón", async () => {
      const usuario = userEvent.setup();
      render(<App />);
      const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });

      await usuario.click(campo);
      await usuario.paste("a".repeat(281));

      expect(within(pieDelCampo()).getByText(AVISO_MAXIMO)).toBeInTheDocument();
      expect(screen.getByText("281 / 280")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: BOTON_INICIAL })).toBeDisabled();
    });

    it("285 caracteres escritos que normalizan a 275 no muestran aviso y dejan comprobar", async () => {
      const usuario = userEvent.setup();
      render(<App />);
      const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });

      // 137 + 11 espacios + 137 = 285; al colapsar los espacios, 137 + 1 + 137 = 275.
      await usuario.click(campo);
      await usuario.paste("a".repeat(137) + " ".repeat(11) + "b".repeat(137));

      expect(within(pieDelCampo()).queryByText(AVISO_MAXIMO)).not.toBeInTheDocument();
      expect(screen.getByText("275 / 280")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: BOTON_INICIAL })).toBeEnabled();
    });

    it("con una frase válida no muestra aviso", async () => {
      const usuario = userEvent.setup();
      render(<App />);
      const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });

      await usuario.type(campo, "abc");

      expect(within(pieDelCampo()).queryByText(AVISO_MINIMO)).not.toBeInTheDocument();
    });
  });

  it("al validar con puntaje sobre el umbral pasa a posible_duplicado y muestra la frase existente, el medidor y las acciones", async () => {
    const usuario = userEvent.setup();
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: true,
        motivo: "SEMANTICO",
        puntaje: 0.91,
        umbral_aplicado: 0.75,
        mas_parecida: crearFraseResumen({ id: 42, texto: "El pago fue rechazado por el banco" }),
      }),
    });
    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, "La entidad bancaria rechazó la transacción");
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));

    const veredicto = await screen.findByRole("alert");
    expect(
      within(veredicto).getByText("Ya existe una frase con el mismo significado"),
    ).toBeInTheDocument();
    expect(within(veredicto).getByText("Tu frase")).toBeInTheDocument();
    expect(within(veredicto).getByText("Registrada")).toBeInTheDocument();
    expect(
      within(veredicto).getByText("La entidad bancaria rechazó la transacción"),
    ).toBeInTheDocument();
    expect(within(veredicto).getByText("El pago fue rechazado por el banco")).toBeInTheDocument();
    expect(
      within(veredicto).getByRole("img", { name: "Similitud 91 %, umbral 75 %" }),
    ).toBeInTheDocument();
    expect(within(veredicto).getByRole("button", { name: "Editar frase" })).toBeInTheDocument();
    expect(
      within(veredicto).getByRole("button", { name: "Guardar de todos modos" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Guardar frase" })).toBeDisabled();
  });

  it("el duplicado exacto se anuncia como 'Esta frase ya existe tal cual', con 'Registrada (idéntica)' y sin medidor", async () => {
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
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, "hola mundo");
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));

    const veredicto = await screen.findByRole("alert");
    expect(within(veredicto).getByText("Esta frase ya existe tal cual")).toBeInTheDocument();
    expect(within(veredicto).getByText("Registrada (idéntica)")).toBeInTheDocument();
    expect(within(veredicto).queryByRole("img")).not.toBeInTheDocument();
  });

  it("la frase única muestra 'No hay otra frase con el mismo significado', la más cercana y el medidor, y habilita Guardar frase", async () => {
    const usuario = userEvent.setup();
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: false,
        motivo: null,
        puntaje: 0.42,
        umbral_aplicado: 0.75,
        mas_parecida: crearFraseResumen({ id: 5, texto: "Una frase completamente distinta" }),
      }),
    });
    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, "Una frase nueva");
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));

    const veredicto = await screen.findByRole("status");
    expect(
      within(veredicto).getByText("No hay otra frase con el mismo significado"),
    ).toBeInTheDocument();
    expect(
      within(veredicto).getByText("La más cercana es «Una frase completamente distinta»"),
    ).toBeInTheDocument();
    expect(
      within(veredicto).getByRole("img", { name: "Similitud 42 %, umbral 75 %" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Guardar frase" })).toBeEnabled();
  });

  it("la frase única con la base vacía muestra 'Es la primera frase del catálogo.' sin medidor", async () => {
    const usuario = userEvent.setup();
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: false,
        motivo: null,
        puntaje: null,
        mas_parecida: null,
      }),
    });
    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, "Una frase nueva");
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));

    const veredicto = await screen.findByRole("status");
    expect(within(veredicto).getByText("Es la primera frase del catálogo.")).toBeInTheDocument();
    expect(within(veredicto).queryByRole("img")).not.toBeInTheDocument();
  });

  it("ac16: tras guardar una frase única muestra 'Frase guardada.', vacía el campo y le devuelve el foco", async () => {
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
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));
    await screen.findByText("No hay otra frase con el mismo significado");

    await usuario.click(screen.getByRole("button", { name: "Guardar frase" }));

    const confirmacion = await screen.findByRole("status");
    expect(within(confirmacion).getByText("Frase guardada.")).toBeInTheDocument();
    expect(within(confirmacion).getByText("Ya aparece en la lista.")).toBeInTheDocument();
    expect(campo).toHaveValue("");
    expect(campo).toHaveFocus();
    expect(guardarFraseMock).toHaveBeenCalledWith(texto, false);
  });

  it("ac16: tras guardar de todos modos desde posible_duplicado muestra 'Frase guardada como duplicado confirmado.', vacía el campo y le devuelve el foco", async () => {
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
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));
    await screen.findByRole("alert");

    await usuario.click(screen.getByRole("button", { name: "Guardar de todos modos" }));

    const confirmacion = await screen.findByRole("status");
    expect(
      within(confirmacion).getByText("Frase guardada como duplicado confirmado."),
    ).toBeInTheDocument();
    expect(within(confirmacion).getByText("Ya aparece en la lista.")).toBeInTheDocument();
    expect(campo).toHaveValue("");
    expect(campo).toHaveFocus();
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
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));
    await screen.findByText("No hay otra frase con el mismo significado");
    await usuario.click(screen.getByRole("button", { name: "Guardar frase" }));
    await screen.findByText("Frase guardada.");

    await usuario.type(campo, "N");

    expect(screen.queryByText("Frase guardada.")).not.toBeInTheDocument();
  });

  it("ac16b: editar el texto tras una validación única oculta el veredicto y el botón principal vuelve a 'Comprobar similitud'", async () => {
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
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));
    await screen.findByText("No hay otra frase con el mismo significado");
    expect(screen.getByRole("button", { name: "Guardar frase" })).toBeEnabled();

    await usuario.type(campo, "!");

    expect(
      screen.queryByText("No hay otra frase con el mismo significado"),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Guardar frase" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: BOTON_INICIAL })).toBeInTheDocument();
  });

  it("ac16b: editar el texto tras un posible duplicado oculta el veredicto y el botón principal vuelve a 'Comprobar similitud'", async () => {
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
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));
    await screen.findByRole("alert");

    await usuario.type(campo, "!");

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: BOTON_INICIAL })).toBeInTheDocument();
  });

  it("ac16b: Editar frase en el veredicto de posible_duplicado lo hace desaparecer, conserva el texto y devuelve el foco al campo", async () => {
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
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));
    const veredicto = await screen.findByRole("alert");

    await usuario.click(within(veredicto).getByRole("button", { name: "Editar frase" }));

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(campo).toHaveValue(texto);
    expect(campo).toHaveFocus();
    expect(screen.getByRole("button", { name: BOTON_INICIAL })).toBeInTheDocument();
  });

  it("ac21: el 409 al guardar desde unica pasa a conflicto, distinto de posible_duplicado, con la frase encontrada, el medidor y las acciones", async () => {
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
        puntaje: 0.83,
        umbral_aplicado: 0.75,
        mas_parecida: crearFraseResumen({ id: 99, texto: "Otra frase registrada justo antes" }),
      }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));
    await screen.findByText("No hay otra frase con el mismo significado");

    await usuario.click(screen.getByRole("button", { name: "Guardar frase" }));

    const veredicto = await screen.findByRole("alert");
    expect(
      within(veredicto).getByText("Alguien registró una frase parecida mientras revisabas"),
    ).toBeInTheDocument();
    expect(
      within(veredicto).getByText(
        "Al guardar volvimos a comparar y el resultado cambió. La frase no se guardó.",
      ),
    ).toBeInTheDocument();
    expect(within(veredicto).getByText("Otra frase registrada justo antes")).toBeInTheDocument();
    expect(
      within(veredicto).getByRole("img", { name: `Similitud ${porcentaje(0.83)} %, umbral 75 %` }),
    ).toBeInTheDocument();
    expect(within(veredicto).getByRole("button", { name: "Editar frase" })).toBeInTheDocument();
    expect(
      within(veredicto).getByRole("button", { name: "Guardar de todos modos" }),
    ).toBeInTheDocument();
    expect(
      within(veredicto).queryByText("Ya existe una frase con el mismo significado"),
    ).not.toBeInTheDocument();
    expect(campo).toHaveValue(texto);
  });

  it("ac21: Guardar de todos modos desde conflicto envía confirmar_duplicado true y muestra 'Frase guardada como duplicado confirmado.'", async () => {
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
        mas_parecida: crearFraseResumen({ id: 99, texto: "Otra frase registrada justo antes" }),
      }),
    });
    guardarFraseMock.mockResolvedValueOnce({
      tipo: "guardada",
      frase: crearFrase({ texto, estado: "DUPLICADO_CONFIRMADO" }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));
    await screen.findByText("No hay otra frase con el mismo significado");
    await usuario.click(screen.getByRole("button", { name: "Guardar frase" }));
    const veredicto = await screen.findByRole("alert");

    await usuario.click(within(veredicto).getByRole("button", { name: "Guardar de todos modos" }));

    const confirmacion = await screen.findByRole("status");
    expect(
      within(confirmacion).getByText("Frase guardada como duplicado confirmado."),
    ).toBeInTheDocument();
    expect(guardarFraseMock).toHaveBeenNthCalledWith(2, texto, true);
  });

  it("ac21: Editar frase desde conflicto conserva el texto y devuelve el foco al campo", async () => {
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
        mas_parecida: crearFraseResumen({ id: 99, texto: "Otra frase registrada justo antes" }),
      }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));
    await screen.findByText("No hay otra frase con el mismo significado");
    await usuario.click(screen.getByRole("button", { name: "Guardar frase" }));
    const veredicto = await screen.findByRole("alert");

    await usuario.click(within(veredicto).getByRole("button", { name: "Editar frase" }));

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(campo).toHaveValue(texto);
    expect(campo).toHaveFocus();
    expect(screen.getByRole("button", { name: BOTON_INICIAL })).toBeInTheDocument();
  });

  it("un error 503 al validar muestra 'No se pudo comparar la frase' y el mensaje de la API, y Reintentar repite la validación", async () => {
    const usuario = userEvent.setup();
    const texto = "Una frase cualquiera";
    validarFraseMock.mockResolvedValueOnce({ ok: false, error: crearErrorApi() });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));

    const veredicto = await screen.findByRole("alert");
    expect(within(veredicto).getByText("No se pudo comparar la frase")).toBeInTheDocument();
    expect(
      within(veredicto).getByText("El servicio de comparación no está disponible."),
    ).toBeInTheDocument();
    // Reintentar es el botón principal en `error` (ui-design), no una acción del veredicto.
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

    await screen.findByText("No hay otra frase con el mismo significado");
    expect(validarFraseMock).toHaveBeenNthCalledWith(2, texto);
  });

  it("un error con código SIN_CONEXION muestra el texto fijo de servicio sin respuesta", async () => {
    const usuario = userEvent.setup();
    const texto = "Una frase cualquiera";
    validarFraseMock.mockResolvedValueOnce({
      ok: false,
      error: crearErrorApi({
        codigo: "SIN_CONEXION",
        mensaje: "No pudimos conectar con el servidor.",
        estado_http: null,
      }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));

    const veredicto = await screen.findByRole("alert");
    expect(
      within(veredicto).getByText(
        "El servicio no responde. La frase no se guardó; reintenta en unos segundos.",
      ),
    ).toBeInTheDocument();
  });

  it("un error con código RESPUESTA_INESPERADA muestra el texto fijo de servicio sin respuesta", async () => {
    const usuario = userEvent.setup();
    const texto = "Una frase cualquiera";
    validarFraseMock.mockResolvedValueOnce({
      ok: false,
      error: crearErrorApi({
        codigo: "RESPUESTA_INESPERADA",
        mensaje: "El servidor respondió algo inesperado.",
        estado_http: 502,
      }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));

    const veredicto = await screen.findByRole("alert");
    expect(
      within(veredicto).getByText(
        "El servicio no responde. La frase no se guardó; reintenta en unos segundos.",
      ),
    ).toBeInTheDocument();
  });

  it("un error 422 al validar muestra el mensaje sin ofrecer Reintentar, y el botón principal vuelve a 'Comprobar similitud'", async () => {
    const usuario = userEvent.setup();
    // El 422 lo decide el servidor: el cliente simulado lo devuelve para un
    // texto que en el cliente pasa el mínimo.
    const texto = "Una frase cualquiera";
    validarFraseMock.mockResolvedValueOnce({
      ok: false,
      error: crearErrorApi({
        codigo: "FRASE_INVALIDA",
        mensaje: "La frase debe tener entre 3 y 280 caracteres.",
        estado_http: 422,
      }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));

    const veredicto = await screen.findByRole("alert");
    expect(within(veredicto).getByText("No se pudo comparar la frase")).toBeInTheDocument();
    expect(
      within(veredicto).getByText("La frase debe tener entre 3 y 280 caracteres."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reintentar" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: BOTON_INICIAL })).toBeInTheDocument();
  });

  it("un error al guardar y Reintentar repiten el guardado con el mismo confirmar_duplicado", async () => {
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
      tipo: "error",
      error: crearErrorApi({
        codigo: "BASE_DATOS_NO_DISPONIBLE",
        mensaje: "La base de datos no está disponible.",
        estado_http: 503,
      }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, texto);
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));
    await screen.findByText("No hay otra frase con el mismo significado");
    await usuario.click(screen.getByRole("button", { name: "Guardar frase" }));

    const veredicto = await screen.findByRole("alert");
    expect(within(veredicto).getByText("La base de datos no está disponible.")).toBeInTheDocument();
    // Reintentar es el botón principal en `error` (ui-design), no una acción del veredicto.
    const reintentar = screen.getByRole("button", { name: "Reintentar" });

    guardarFraseMock.mockResolvedValueOnce({
      tipo: "guardada",
      frase: crearFrase({ texto, estado: "UNICA" }),
    });

    await usuario.click(reintentar);

    await screen.findByText("Frase guardada.");
    expect(guardarFraseMock).toHaveBeenNthCalledWith(2, texto, false);
  });

  it("Ctrl + Enter en el campo equivale a presionar el botón principal", async () => {
    const usuario = userEvent.setup();
    const texto = "Una frase cualquiera";
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: false,
        puntaje: null,
        mas_parecida: null,
      }),
    });

    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, texto);

    await usuario.keyboard("{Control>}{Enter}{/Control}");

    await screen.findByText("No hay otra frase con el mismo significado");
    expect(validarFraseMock).toHaveBeenCalledWith(texto);
  });

  it("ac16: el veredicto no está dentro de otra región viva: su propio rol lo anuncia una sola vez", async () => {
    const usuario = userEvent.setup();
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: true,
        motivo: "SEMANTICO",
        puntaje: 0.91,
        mas_parecida: crearFraseResumen(),
      }),
    });
    render(<App />);
    const campo = screen.getByRole("textbox", { name: NOMBRE_CAMPO });
    await usuario.type(campo, "La entidad bancaria rechazó la transacción");
    await usuario.click(screen.getByRole("button", { name: BOTON_INICIAL }));

    const veredicto = await screen.findByRole("alert");
    expect(veredicto.parentElement?.closest("[aria-live]")).toBeNull();
  });
});

// Promesa que el test controla a mano, para observar la operación en curso.
function crearPromesaControlada<T>(): {
  promesa: Promise<T>;
  resolver: (valor: T) => void;
} {
  let resolver: (valor: T) => void = () => {};
  const promesa = new Promise<T>((resolve) => {
    resolver = resolve;
  });
  return { promesa, resolver };
}

describe("foco con teclado (D-36)", () => {
  const TEXTO = "La entidad bancaria rechazó la transacción";

  async function comprobarConTeclado(usuario: ReturnType<typeof userEvent.setup>): Promise<void> {
    await usuario.type(screen.getByRole("textbox", { name: NOMBRE_CAMPO }), TEXTO);
    await usuario.tab();
    expect(screen.getByRole("button", { name: BOTON_INICIAL })).toHaveFocus();
    await usuario.keyboard("{Enter}");
  }

  it("mientras comprueba, el botón conserva el foco, queda aria-disabled y no admite otro clic", async () => {
    const usuario = userEvent.setup();
    const pendiente = crearPromesaControlada<Awaited<ReturnType<typeof validarFrase>>>();
    validarFraseMock.mockReturnValueOnce(pendiente.promesa);
    render(<App />);

    await comprobarConTeclado(usuario);

    const boton = screen.getByRole("button", { name: "Comprobando…" });
    expect(boton).toHaveFocus();
    expect(boton).toHaveAttribute("aria-disabled", "true");
    await usuario.click(boton);
    expect(validarFraseMock).toHaveBeenCalledTimes(1);

    pendiente.resolver({ ok: true, datos: crearResultadoValidacion() });
    await screen.findByText("No hay otra frase con el mismo significado");
  });

  // Desde el campo con Ctrl+Enter: jsdom no quita el foco a un botón que se
  // deshabilita, así que partir del botón no probaría nada.
  it("si la frase es única, el foco pasa a 'Guardar frase', también desde el campo con Ctrl+Enter", async () => {
    const usuario = userEvent.setup();
    validarFraseMock.mockResolvedValueOnce({ ok: true, datos: crearResultadoValidacion() });
    render(<App />);

    await usuario.type(screen.getByRole("textbox", { name: NOMBRE_CAMPO }), TEXTO);
    await usuario.keyboard("{Control>}{Enter}{/Control}");

    await screen.findByText("No hay otra frase con el mismo significado");
    expect(screen.getByRole("button", { name: "Guardar frase" })).toHaveFocus();
  });

  it("si es un posible duplicado, el foco pasa a 'Editar frase'", async () => {
    const usuario = userEvent.setup();
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: true,
        motivo: "SEMANTICO",
        puntaje: 0.91,
        mas_parecida: crearFraseResumen(),
      }),
    });
    render(<App />);

    await comprobarConTeclado(usuario);

    const veredicto = await screen.findByRole("alert");
    expect(within(veredicto).getByRole("button", { name: "Editar frase" })).toHaveFocus();
  });

  it("si el guardado da conflicto (409), el foco pasa a 'Editar frase'", async () => {
    const usuario = userEvent.setup();
    validarFraseMock.mockResolvedValueOnce({ ok: true, datos: crearResultadoValidacion() });
    guardarFraseMock.mockResolvedValueOnce({
      tipo: "posible_duplicado",
      duplicado: crearDatosDuplicado(),
    });
    render(<App />);

    await comprobarConTeclado(usuario);
    await screen.findByText("No hay otra frase con el mismo significado");
    await usuario.keyboard("{Enter}");

    const veredicto = await screen.findByRole("alert");
    expect(within(veredicto).getByRole("button", { name: "Editar frase" })).toHaveFocus();
  });

  it("mientras guarda de todos modos, el botón conserva el foco y no admite otro clic", async () => {
    const usuario = userEvent.setup();
    const pendiente = crearPromesaControlada<Awaited<ReturnType<typeof guardarFrase>>>();
    validarFraseMock.mockResolvedValueOnce({
      ok: true,
      datos: crearResultadoValidacion({
        es_posible_duplicado: true,
        motivo: "SEMANTICO",
        puntaje: 0.91,
        mas_parecida: crearFraseResumen(),
      }),
    });
    guardarFraseMock.mockReturnValueOnce(pendiente.promesa);
    render(<App />);

    await comprobarConTeclado(usuario);
    const veredicto = await screen.findByRole("alert");
    const boton = within(veredicto).getByRole("button", { name: "Guardar de todos modos" });
    boton.focus();
    await usuario.keyboard("{Enter}");

    expect(boton).toHaveFocus();
    expect(boton).toHaveAttribute("aria-disabled", "true");
    await usuario.click(boton);
    expect(guardarFraseMock).toHaveBeenCalledTimes(1);

    pendiente.resolver({ tipo: "guardada", frase: crearFrase({ estado: "DUPLICADO_CONFIRMADO" }) });
    await screen.findByText("Frase guardada como duplicado confirmado.");
  });
});
