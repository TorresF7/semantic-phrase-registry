// Tests de la tabla y los estados del listado (T-23): esqueleto de carga,
// estado vacío, error con reintento, paginación por botones solo con más de
// una página, y la columna "Más parecida al registrar" (AC-19). Se prueban a
// través de `App` porque es ahí donde vive `useFrases` y donde se conecta el
// guardado exitoso con la recarga de la primera página (AC-16). El cliente de
// API se sustituye por completo: ningún test hace peticiones reales.
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

// `mas_parecida` todavía no existe en el tipo `ItemListado` (T-23 lo añade).
// Se incluye igual en la fábrica porque es el contrato que el componente debe
// leer; hasta que el tipo se actualice, TypeScript lo acepta como propiedad
// adicional al transpilar con Vite (no hay chequeo de tipos en `vitest run`).
function crearItemListado(overrides: Partial<ItemListado> = {}): ItemListado {
  return {
    id: 1,
    texto: "Una frase registrada",
    estado: "UNICA",
    puntaje_similitud: null,
    mas_parecida: null,
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

// Igual que `requerido`, para nodos del DOM que pueden no existir
// (`closest` devuelve `Element | null`).
function elementoRequerido(elemento: Element | null): HTMLElement {
  if (!(elemento instanceof HTMLElement)) {
    throw new Error("Se esperaba un elemento en el DOM y no había ninguno.");
  }
  return elemento;
}

// Las celdas de una fila, en el orden de las columnas del contrato: Frase,
// Estado, Similitud, Más parecida al registrar, Registrada.
function celdas(fila: HTMLElement): HTMLElement[] {
  return within(fila).getAllByRole("cell");
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

describe("tabla y estados de la lista (T-23)", () => {
  it("al montar pide la primera página con listarFrases(20, 0)", () => {
    render(<App />);

    expect(listarFrasesMock).toHaveBeenCalledWith(20, 0);
  });

  it("con datos en la página muestra la tabla con sus cinco columnas, el resumen y la similitud en porcentaje", async () => {
    const items: ItemListado[] = [
      crearItemListado({
        id: 5,
        texto: "Frase única registrada",
        estado: "UNICA",
        puntaje_similitud: 0.42,
      }),
      crearItemListado({
        id: 6,
        texto: "Frase guardada pese a la alerta",
        estado: "DUPLICADO_CONFIRMADO",
        puntaje_similitud: 0.91,
        mas_parecida: { id: 5, texto: "Frase única registrada" },
      }),
    ];
    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 2, items }),
    });

    render(<App />);

    const region = await screen.findByRole("region", { name: NOMBRE_LISTADO });
    expect(within(region).getByText("2 frases")).toBeInTheDocument();

    const tabla = within(region).getByRole("table");
    const encabezados = within(tabla)
      .getAllByRole("columnheader")
      .map((encabezado) => encabezado.textContent);
    expect(encabezados).toEqual([
      "Frase",
      "Estado",
      "Similitud",
      "Más parecida al registrar",
      "Registrada",
    ]);

    // El texto aparece dos veces: en su celda y como más parecida de la fila 6
    // (AC-19). `selector: "td"` toma la celda de la propia frase.
    const filaUnica = elementoRequerido(
      screen.getByText("Frase única registrada", { selector: "td" }).closest("tr"),
    );
    expect(within(filaUnica).getByText("Única")).toBeInTheDocument();
    expect(requerido(celdas(filaUnica)[2]).textContent).toContain("42 %");
    expect(requerido(celdas(filaUnica)[3]).textContent).toBe("—");

    const filaDuplicada = elementoRequerido(
      screen.getByText("Frase guardada pese a la alerta").closest("tr"),
    );
    expect(within(filaDuplicada).getByText("Duplicado confirmado")).toBeInTheDocument();
    expect(requerido(celdas(filaDuplicada)[2]).textContent).toContain("91 %");
  });

  it("ac19: la frase más parecida se muestra como botón cuando está en la página actual", async () => {
    const items: ItemListado[] = [
      crearItemListado({ id: 4, texto: "Compré un auto", estado: "UNICA" }),
      crearItemListado({
        id: 10,
        texto: "Compré un carro",
        estado: "DUPLICADO_CONFIRMADO",
        puntaje_similitud: 0.95,
        mas_parecida: { id: 4, texto: "Compré un auto" },
      }),
    ];
    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 2, items }),
    });

    render(<App />);

    const fila = elementoRequerido((await screen.findByText("Compré un carro")).closest("tr"));
    expect(within(fila).getByRole("button", { name: "Compré un auto" })).toBeInTheDocument();
  });

  it("ac19: la frase más parecida se muestra como texto plano cuando no está en la página actual", async () => {
    const items: ItemListado[] = [
      crearItemListado({
        id: 10,
        texto: "Compré un carro",
        estado: "DUPLICADO_CONFIRMADO",
        puntaje_similitud: 0.95,
        mas_parecida: { id: 4, texto: "Compré un auto" },
      }),
    ];
    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 1, items }),
    });

    render(<App />);

    const fila = elementoRequerido((await screen.findByText("Compré un carro")).closest("tr"));
    expect(within(fila).queryByRole("button", { name: "Compré un auto" })).not.toBeInTheDocument();
    expect(within(fila).getByText("Compré un auto")).toBeInTheDocument();
  });

  it("ac19: la primera frase registrada, sin frase más parecida, muestra — en esa columna", async () => {
    const items: ItemListado[] = [
      crearItemListado({ id: 1, texto: "La entidad bancaria rechazó la transacción" }),
    ];
    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 1, items }),
    });

    render(<App />);

    const fila = elementoRequerido(
      (await screen.findByText("La entidad bancaria rechazó la transacción")).closest("tr"),
    );
    expect(requerido(celdas(fila)[3]).textContent).toBe("—");
  });

  it("ac20: mientras el listado no resuelve, el cuerpo de la tabla tiene aria-busy y 5 filas de esqueleto con 5 celdas cada una", async () => {
    const { promesa, resolver } = crearPromesaControlada<Resultado<PaginaFrases>>();
    listarFrasesMock.mockReturnValueOnce(promesa);

    const { container } = render(<App />);

    expect(screen.getByText("Cargando frases…")).toBeInTheDocument();

    const cuerpo = elementoRequerido(container.querySelector("tbody"));
    expect(cuerpo).toHaveAttribute("aria-busy", "true");

    const filas = cuerpo.querySelectorAll("tr");
    expect(filas).toHaveLength(5);
    filas.forEach((fila) => {
      expect(fila).toHaveAttribute("aria-hidden", "true");
      expect(fila.querySelectorAll("td")).toHaveLength(5);
    });

    resolver({ ok: true, datos: paginaVacia() });
    await screen.findByText("Todavía no hay frases");
  });

  it("ac20: con total 0 muestra el estado vacío y ningún encabezado de columna", async () => {
    listarFrasesMock.mockResolvedValueOnce({ ok: true, datos: paginaVacia() });

    render(<App />);

    expect(await screen.findByText("Todavía no hay frases")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Escribe la primera en el campo de arriba. Como no habrá nada con qué compararla, se guardará como única.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryAllByRole("columnheader")).toHaveLength(0);
  });

  it("ac20: si listarFrases falla muestra el error con role alert y Reintentar repite la petición", async () => {
    const usuario = userEvent.setup();
    listarFrasesMock.mockResolvedValueOnce({ ok: false, error: crearErrorApi() });

    render(<App />);

    const region = await screen.findByRole("region", { name: NOMBRE_LISTADO });
    const alerta = within(region).getByRole("alert");
    expect(within(alerta).getByText("No se pudo cargar la lista")).toBeInTheDocument();
    expect(
      within(alerta).getByText("El servidor no respondió. Las frases guardadas no se han perdido."),
    ).toBeInTheDocument();
    expect(within(region).queryAllByRole("columnheader")).toHaveLength(0);

    const reintentar = within(alerta).getByRole("button", { name: "Reintentar" });
    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 1, items: crearItems(1, 1) }),
    });

    await usuario.click(reintentar);

    expect(listarFrasesMock).toHaveBeenNthCalledWith(2, 20, 0);
    expect(await within(region).findByText("Frase número 1")).toBeInTheDocument();
  });

  it("ac20: con el total igual o menor que el tamaño de página no se muestran controles de paginación", async () => {
    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 3, items: crearItems(3, 1) }),
    });

    render(<App />);
    const region = await screen.findByRole("region", { name: NOMBRE_LISTADO });
    await within(region).findByText("Frase número 1");

    expect(within(region).queryByRole("button", { name: "Anteriores" })).not.toBeInTheDocument();
    expect(within(region).queryByRole("button", { name: "Siguientes" })).not.toBeInTheDocument();
  });

  it("ac20: con más de 20 frases muestra '1–20 de 26', Anteriores deshabilitado y Siguientes habilitado", async () => {
    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 26, desplazamiento: 0, items: crearItems(20, 1) }),
    });

    render(<App />);
    const region = await screen.findByRole("region", { name: NOMBRE_LISTADO });
    await within(region).findByText("Frase número 1");

    expect(within(region).getByText("26 frases")).toBeInTheDocument();
    expect(within(region).getByText("1–20 de 26")).toBeInTheDocument();
    expect(within(region).getByRole("button", { name: "Anteriores" })).toBeDisabled();
    expect(within(region).getByRole("button", { name: "Siguientes" })).toBeEnabled();
  });

  it("ac20: pulsar Siguientes pide listarFrases(20, 20) y muestra '21–26 de 26' con los controles invertidos", async () => {
    const usuario = userEvent.setup();
    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 26, desplazamiento: 0, items: crearItems(20, 1) }),
    });
    render(<App />);
    const region = await screen.findByRole("region", { name: NOMBRE_LISTADO });
    await within(region).findByText("1–20 de 26");

    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 26, desplazamiento: 20, items: crearItems(6, 21) }),
    });

    await usuario.click(within(region).getByRole("button", { name: "Siguientes" }));

    expect(await within(region).findByText("21–26 de 26")).toBeInTheDocument();
    expect(within(region).getByText("26 frases")).toBeInTheDocument();
    expect(listarFrasesMock).toHaveBeenNthCalledWith(2, 20, 20);
    expect(within(region).getByRole("button", { name: "Siguientes" })).toBeDisabled();
    expect(within(region).getByRole("button", { name: "Anteriores" })).toBeEnabled();
  });

  it("ac20: pulsar Anteriores desde la segunda página vuelve a pedir listarFrases(20, 0)", async () => {
    const usuario = userEvent.setup();
    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 26, desplazamiento: 0, items: crearItems(20, 1) }),
    });
    render(<App />);
    const region = await screen.findByRole("region", { name: NOMBRE_LISTADO });
    await within(region).findByText("1–20 de 26");

    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 26, desplazamiento: 20, items: crearItems(6, 21) }),
    });
    await usuario.click(within(region).getByRole("button", { name: "Siguientes" }));
    await within(region).findByText("21–26 de 26");

    listarFrasesMock.mockResolvedValueOnce({
      ok: true,
      datos: crearPaginaFrases({ total: 26, desplazamiento: 0, items: crearItems(20, 1) }),
    });

    await usuario.click(within(region).getByRole("button", { name: "Anteriores" }));

    expect(await within(region).findByText("1–20 de 26")).toBeInTheDocument();
    expect(within(region).getByText("26 frases")).toBeInTheDocument();
    expect(listarFrasesMock).toHaveBeenNthCalledWith(3, 20, 0);
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

    const campo = screen.getByRole("textbox", { name: "Registrar frase" });
    await usuario.type(campo, textoNuevo);
    await usuario.click(screen.getByRole("button", { name: "Comprobar similitud" }));
    await screen.findByText("No hay otra frase con el mismo significado");
    await usuario.click(screen.getByRole("button", { name: "Guardar frase" }));

    expect(await within(region).findByText(textoNuevo)).toBeInTheDocument();
    expect(within(region).getByText("1–20 de 26")).toBeInTheDocument();
    expect(listarFrasesMock).toHaveBeenNthCalledWith(3, 20, 0);
  });
});
