// Máquina de estados del registro (plan §5, CH-02). Una unión discriminada en
// lugar de banderas sueltas: "validando y con error a la vez" no se puede escribir.

import { useState } from "react";

import { guardarFrase, validarFrase } from "../api/cliente";
import type { DatosDuplicado, ErrorApi, Frase, ResultadoValidacion } from "../api/tipos";

// Estados con veredicto desde los que se puede guardar.
export type EstadoConVeredicto =
  | { tipo: "unica"; resultado: ResultadoValidacion }
  | { tipo: "posible_duplicado"; duplicado: DatosDuplicado }
  // El 409 del guardado: el servidor revalidó y la base había cambiado (RN-11, AC-21).
  | { tipo: "conflicto"; duplicado: DatosDuplicado };

type Operacion = { tipo: "validar" } | { tipo: "guardar"; desde: EstadoConVeredicto };

export type EstadoFormulario =
  | { tipo: "inactivo" }
  | { tipo: "validando" }
  | EstadoConVeredicto
  // `desde` es el veredicto sobre el que se guarda: sigue en pantalla mientras
  // se espera la respuesta (D-24, D-27).
  | { tipo: "guardando"; desde: EstadoConVeredicto }
  | { tipo: "guardada"; frase: Frase }
  // `reintentar` es nulo ante un 422: repetirlo daría lo mismo (D-24).
  | { tipo: "error"; codigo: string; mensaje: string; reintentar: Operacion | null };

export type Validacion = {
  texto: string;
  estado: EstadoFormulario;
  cambiarTexto: (texto: string) => void;
  validar: () => void;
  guardar: () => void;
  guardarDeTodosModos: () => void;
  editar: () => void;
  reintentar: () => void;
};

type Opciones = {
  // Se avisa a quien orquesta para que refresque el listado (AC-16) y resalte
  // la frase guardada (ui-design).
  alGuardar?: (frase: Frase) => void;
};

export function useValidacion({ alGuardar }: Opciones = {}): Validacion {
  const [texto, setTexto] = useState("");
  const [estado, setEstado] = useState<EstadoFormulario>({ tipo: "inactivo" });

  function aError(error: ErrorApi, operacion: Operacion): EstadoFormulario {
    const reintentar = error.estado_http === 422 ? null : operacion;
    return { tipo: "error", codigo: error.codigo, mensaje: error.mensaje, reintentar };
  }

  async function ejecutarValidacion(): Promise<void> {
    setEstado({ tipo: "validando" });
    const respuesta = await validarFrase(texto);
    if (!respuesta.ok) {
      setEstado(aError(respuesta.error, { tipo: "validar" }));
    } else if (respuesta.datos.es_posible_duplicado) {
      setEstado({ tipo: "posible_duplicado", duplicado: respuesta.datos });
    } else {
      setEstado({ tipo: "unica", resultado: respuesta.datos });
    }
  }

  // Confirmar el duplicado se decide sobre el texto validado: solo se confirma
  // desde un veredicto de duplicado (RN-12, AC-16b).
  async function ejecutarGuardado(desde: EstadoConVeredicto): Promise<void> {
    setEstado({ tipo: "guardando", desde });
    const respuesta = await guardarFrase(texto, desde.tipo !== "unica");
    switch (respuesta.tipo) {
      case "guardada":
        setTexto("");
        setEstado({ tipo: "guardada", frase: respuesta.frase });
        alGuardar?.(respuesta.frase);
        break;
      case "posible_duplicado":
        setEstado({ tipo: "conflicto", duplicado: respuesta.duplicado });
        break;
      case "error":
        setEstado(aError(respuesta.error, { tipo: "guardar", desde }));
        break;
    }
  }

  function cambiarTexto(nuevo: string): void {
    setTexto(nuevo);
    // Cualquier veredicto caduca al editar: correspondía a otro texto (AC-16b).
    setEstado({ tipo: "inactivo" });
  }

  function validar(): void {
    if (estado.tipo === "validando" || estado.tipo === "guardando") return;
    void ejecutarValidacion();
  }

  function guardar(): void {
    if (estado.tipo === "unica") void ejecutarGuardado(estado);
  }

  function guardarDeTodosModos(): void {
    if (estado.tipo === "posible_duplicado" || estado.tipo === "conflicto") {
      void ejecutarGuardado(estado);
    }
  }

  function editar(): void {
    // Conserva el texto: la persona lo corrige (AC-16b).
    if (estado.tipo === "posible_duplicado" || estado.tipo === "conflicto") {
      setEstado({ tipo: "inactivo" });
    }
  }

  function reintentar(): void {
    if (estado.tipo !== "error" || estado.reintentar === null) return;
    const operacion = estado.reintentar;
    if (operacion.tipo === "validar") void ejecutarValidacion();
    else void ejecutarGuardado(operacion.desde);
  }

  return {
    texto,
    estado,
    cambiarTexto,
    validar,
    guardar,
    guardarDeTodosModos,
    editar,
    reintentar,
  };
}
