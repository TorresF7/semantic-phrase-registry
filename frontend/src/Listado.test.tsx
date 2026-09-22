// Tests del listado de frases y sus estados (T-15): carga, vacío, error con
// reintento, paginación por botones y la etiqueta de duplicado confirmado. Se
// prueban a través de `App` porque es ahí donde vive `useFrases` y donde se
// conecta el guardado exitoso con la recarga de la primera página (AC-16). El
// cliente de API se sustituye por completo: ningún test hace peticiones reales.
// No se modifica `App.test.tsx`; este archivo tiene sus propios dobles del
// módulo `./api/cliente`, independientes de los de aquel.

import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import App from "./App";
import { guardarFrase, listarFrases, validarFrase } from "./api/cliente";
import type {
  ErrorApi,
  Frase,
  ItemListado,
  PaginaFrases,
  Resultado,
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
const NOMBRE_LISTADO = "Frases registradas";

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
    codigo: "SIN_CONEXION",
    mensaje: "No pudimos conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.",
    detalles: null,
    estado_http: null,
    ...overrides,
  };
}

function crearItemListado(overrides: Partial<ItemListado> = {}): ItemListado {
  return {
    id: 1,
    texto: "Una frase registrada",
    estado: "UNICA",
    puntaje_similitud: null,
    creada_en: "2026-09-20T10:00:00Z",
    ...overrides,
  };
}

// Genera `cantidad` elementos con id y texto distintos, empezando en `idInicial`.
function crearItems(cantidad: number, idInicial: number): ItemListado[] {
  return Array.from({ length: cantidad }, (_, indice) => {
    const id = idInicial + indice;
    return crearItemListado({ id, texto: `Frase número ${id}` });
  });
}

function crearPaginaFrases(overrides: Partial<PaginaFrases> = {}): PaginaFrases {
  return { total: 0, limite: 20, desplazamiento: 0, items: [], ...overrides };
}

function paginaVacia(): PaginaFrases {
  return crearPaginaFrases();
}

// Evita `as` y `any`: convierte un valor posiblemente ausente (por
// `noUncheckedIndexedAccess`) en uno requerido, o falla con un mensaje claro.
function requerido<T>(valor: T | undefined): T {
  if (valor === undefined) {
    throw new Error("Se esperaba un valor y no había ninguno.");
  }
  return valor;
}

// Promesa que el test controla a mano, para comprobar el estado de carga antes
// de que la petición resuelva.
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

beforeEach(() => {
  validarFraseMock.mockReset();
  guardarFraseMock.mockReset();
  listarFrasesMock.mockReset();
  listarFrasesMock.mockResolvedValue({ ok: true, datos: paginaVacia() });
});

describe("listado de frases y sus estados (T-15)", () => {
  it("al montar pide la primera página con listarFrases(20, 0)", () => {
    render(<App />);

    expect(listarFrasesMock).toHaveBeenCalledWith(20, 0);
  });

  it("mientras la petición no resuelve muestra 'Cargando frases…' y la lista con aria-busy", async () => {
    const { promesa, resolver } = crearPromesaControlada<Resultado<PaginaFrases>>();
    listarFrasesMock.mockReturnValueOnce(promesa);

    render(<App />);

    expect(screen.getByText("Cargando frases…")).toBeInTheDocument();
    const lista = screen.getByRole("list", { name: NOMBRE_LISTADO });
    expect(lista).toHaveAttribute("aria-busy", "true");

    resolver({ ok: true, datos: paginaVacia() });
    await screen.findByText("Todavía no hay frases registradas. Escribe la primera arriba.");
  });

  it("con la base vacía muestra el estado vacío y ningún listitem", async () => {
    listarFrasesMock.mockResolvedValueOnce({ ok: true, datos: paginaVacia() });

    render(<App />);

    expect(
      await screen.findByText("Todavía no hay frases registradas. Escribe la primera arriba."),
    ).toBeInTheDocument();
    expect(screen.queryAllByRole("listitem")).toHaveLength(0);
  });

  it("cada frase aparece como listitem con su texto, y solo las duplicado confirmado llevan la etiqueta", async () => {
    const items: ItemListado[] = [
      crearItemListado({ id: 5, texto: "Frase única registrada", estado: "UNICA" }),
      crearItemListado({
        id: 6,
        texto: "Frase guardada pese a la alerta",
        estado: "DUPLICADO_CONFIRMADO",
        puntaje_similitud: 0.91,
      }),
    ];
    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 2, items }),
    });

    render(<App />);

    const lista = await screen.findByRole("list", { name: NOMBRE_LISTADO });
    const elementos = within(lista).getAllByRole("listitem");
    expect(elementos).toHaveLength(2);

    const unica = requerido(elementos[0]);
    const duplicada = requerido(elementos[1]);
    expect(within(unica).getByText("Frase única registrada")).toBeInTheDocument();
    expect(within(unica).queryByText("Duplicado confirmado")).not.toBeInTheDocument();

    expect(within(duplicada).getByText("Frase guardada pese a la alerta")).toBeInTheDocument();
    expect(within(duplicada).getByText("Duplicado confirmado")).toBeInTheDocument();

    expect(within(lista).queryByText(/%/)).not.toBeInTheDocument();
    expect(within(lista).queryByText("0.91")).not.toBeInTheDocument();
  });

  it("en la primera página muestra '1–20 de 25', con Anteriores deshabilitado y Siguientes habilitado", async () => {
    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 25, desplazamiento: 0, items: crearItems(20, 1) }),
    });

    render(<App />);
    await screen.findByRole("list", { name: NOMBRE_LISTADO });
    const region = screen.getByRole("region", { name: NOMBRE_LISTADO });

    expect(within(region).getByText("1–20 de 25")).toBeInTheDocument();
    expect(within(region).getByRole("button", { name: "Anteriores" })).toBeDisabled();
    expect(within(region).getByRole("button", { name: "Siguientes" })).toBeEnabled();
  });

  it("pulsar Siguientes pide la página siguiente y muestra '21–25 de 25' con los controles invertidos", async () => {
    const usuario = userEvent.setup();
    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 25, desplazamiento: 0, items: crearItems(20, 1) }),
    });
    render(<App />);
    await screen.findByRole("list", { name: NOMBRE_LISTADO });
    const region = screen.getByRole("region", { name: NOMBRE_LISTADO });

    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 25, desplazamiento: 20, items: crearItems(5, 21) }),
    });

    await usuario.click(within(region).getByRole("button", { name: "Siguientes" }));

    expect(await within(region).findByText("21–25 de 25")).toBeInTheDocument();
    expect(listarFrasesMock).toHaveBeenNthCalledWith(2, 20, 20);
    expect(within(region).getByRole("button", { name: "Siguientes" })).toBeDisabled();
    expect(within(region).getByRole("button", { name: "Anteriores" })).toBeEnabled();
  });

  it("pulsar Anteriores desde la segunda página vuelve a pedir listarFrases(20, 0)", async () => {
    const usuario = userEvent.setup();
    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 25, desplazamiento: 0, items: crearItems(20, 1) }),
    });
    render(<App />);
    await screen.findByRole("list", { name: NOMBRE_LISTADO });
    const region = screen.getByRole("region", { name: NOMBRE_LISTADO });

    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 25, desplazamiento: 20, items: crearItems(5, 21) }),
    });
    await usuario.click(within(region).getByRole("button", { name: "Siguientes" }));
    await within(region).findByText("21–25 de 25");

    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 25, desplazamiento: 0, items: crearItems(20, 1) }),
    });

    await usuario.click(within(region).getByRole("button", { name: "Anteriores" }));

    expect(await within(region).findByText("1–20 de 25")).toBeInTheDocument();
    expect(listarFrasesMock).toHaveBeenNthCalledWith(3, 20, 0);
  });

  it("si listarFrases falla muestra 'No pudimos cargar las frases.' y Reintentar repite la petición", async () => {
    const usuario = userEvent.setup();
    listarFrasesMock.mockResolvedValueOnce({ ok: false, error: crearErrorApi() });

    render(<App />);

    const region = await screen.findByRole("region", { name: NOMBRE_LISTADO });
    expect(within(region).getByText("No pudimos cargar las frases.")).toBeInTheDocument();
    const reintentar = within(region).getByRole("button", { name: "Reintentar" });

    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 1, items: crearItems(1, 1) }),
    });

    await usuario.click(reintentar);

    expect(await within(region).findByText("Frase número 1")).toBeInTheDocument();
    expect(listarFrasesMock).toHaveBeenNthCalledWith(2, 20, 0);
  });

  it("ac16: tras guardar desde la segunda página, el listado vuelve a la primera y muestra la frase nueva sin recargar", async () => {
    const usuario = userEvent.setup();
    const textoNuevo = "Una frase completamente nueva para el listado";

    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 25, desplazamiento: 0, items: crearItems(20, 1) }),
    });
    render(<App />);
    const region = await screen.findByRole("region", { name: NOMBRE_LISTADO });

    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 25, desplazamiento: 20, items: crearItems(5, 21) }),
    });
    await usuario.click(within(region).getByRole("button", { name: "Siguientes" }));
    await within(region).findByText("21–25 de 25");

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
      frase: crearFrase({ id: 200, texto: textoNuevo, estado: "UNICA" }),
    });
    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({
        total: 26,
        desplazamiento: 0,
        items: [
          crearItemListado({ id: 200, texto: textoNuevo, estado: "UNICA" }),
          ...crearItems(19, 1),
        ],
      }),
    });

    const campo = screen.getByRole("textbox", { name: "Frase" });
    await usuario.type(campo, textoNuevo);
    await usuario.click(screen.getByRole("button", { name: "Validar" }));
    await screen.findByText("No encontramos frases parecidas. Puedes guardarla.");
    await usuario.click(screen.getByRole("button", { name: "Guardar" }));

    expect(await within(region).findByText(textoNuevo)).toBeInTheDocument();
    expect(within(region).getByText("1–20 de 26")).toBeInTheDocument();
    expect(listarFrasesMock).toHaveBeenNthCalledWith(3, 20, 0);
  });
});
