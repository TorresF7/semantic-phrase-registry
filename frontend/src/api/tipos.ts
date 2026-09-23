// Espejo literal del contrato de la API (plan §1). Los campos que el contrato
// permite nulos se tipan nulos.

export type Motivo = "EXACTO" | "SEMANTICO";
export type EstadoFrase = "UNICA" | "DUPLICADO_CONFIRMADO";

export type FraseResumen = {
  id: number;
  texto: string;
};

// POST /frases/validar → 200 (plan §1.1)
export type ResultadoValidacion = {
  es_posible_duplicado: boolean;
  motivo: Motivo | null;
  puntaje: number | null;
  umbral_aplicado: number;
  mas_parecida: FraseResumen | null;
  modelo: string;
};

// `detalles` del 409 de POST /frases (plan §1.2). No trae `modelo`: la alerta
// no lo necesita, y un resultado de validación también cumple este tipo.
export type DatosDuplicado = {
  motivo: Motivo | null;
  puntaje: number | null;
  umbral_aplicado: number;
  mas_parecida: FraseResumen | null;
};

// POST /frases → 201 (plan §1.2)
export type Frase = {
  id: number;
  texto: string;
  estado: EstadoFrase;
  puntaje_similitud: number | null;
  id_mas_parecida: number | null;
  umbral_aplicado: number;
  modelo: string;
  creada_en: string;
};

// GET /frases → 200 (plan §1.3)
export type ItemListado = {
  id: number;
  texto: string;
  estado: EstadoFrase;
  puntaje_similitud: number | null;
  // La frase más parecida al registrar esta (RN-17, AC-19); null si no la hubo.
  mas_parecida: FraseResumen | null;
  creada_en: string;
};

export type PaginaFrases = {
  total: number;
  limite: number;
  desplazamiento: number;
  items: ItemListado[];
};

// Forma uniforme de error (plan §1.5). `estado_http` es el código HTTP, o `null`
// cuando la petición ni siquiera llegó al servidor.
export type ErrorApi = {
  codigo: string;
  mensaje: string;
  detalles: Record<string, unknown> | null;
  estado_http: number | null;
};

export type Resultado<T> = { ok: true; datos: T } | { ok: false; error: ErrorApi };

// El 409 es una respuesta prevista del contrato, no un error (RN-12).
export type ResultadoGuardado =
  | { tipo: "guardada"; frase: Frase }
  | { tipo: "posible_duplicado"; duplicado: DatosDuplicado }
  | { tipo: "error"; error: ErrorApi };
