// Máquina de estados del formulario (plan §5). Una unión discriminada en lugar
// de banderas sueltas: "validando y con error a la vez" no se puede escribir.

import { useState } from "react";

import { guardarFrase, validarFrase } from "../api/cliente";
import type { DatosDuplicado, ErrorApi, Frase, ResultadoValidacion } from "../api/tipos";

type Operacion = { tipo: "validar" } | { tipo: "guardar"; duplicado: DatosDuplicado | null };

export type EstadoFormulario =
  | { tipo: "inactivo" }
  | { tipo: "validando" }
  | { tipo: "unica"; resultado: ResultadoValidacion }
  | { tipo: "posible_duplicado"; duplicado: DatosDuplicado }
  // `duplicado` no es nulo cuando se guarda desde la alerta: la alerta sigue
  // en pantalla mientras se espera la respuesta.
  | { tipo: "guardando"; duplicado: DatosDuplicado | null }
  | { tipo: "guardada"; frase: Frase }
  | { tipo: "error"; mensaje: string; reintentar: Operacion | null };

export type Validacion = {
  texto: string;
  estado: EstadoFormulario;
  cambiarTexto: (texto: string) => void;
  validar: () => void;
  guardar: () => void;
  cancelar: () => void;
  reintentar: () => void;
};

type Opciones = {
  // Se avisa a quien orquesta para que refresque el listado (AC-16).
  alGuardar?: () => void;
};

export function useValidacion({ alGuardar }: Opciones = {}): Validacion {
  const [texto, setTexto] = useState("");
  const [estado, setEstado] = useState<EstadoFormulario>({ tipo: "inactivo" });

  function aError(error: ErrorApi, operacion: Operacion): EstadoFormulario {
    // Un 422 no se arregla repitiendo: hay que corregir el texto.
    const reintentar = error.estado_http === 422 ? null : operacion;
    return { tipo: "error", mensaje: error.mensaje, reintentar };
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

  // Confirmar el duplicado se decide sobre el texto validado: solo quien ve la
  // alerta puede confirmar (RN-12, AC-16b).
  async function ejecutarGuardado(duplicado: DatosDuplicado | null): Promise<void> {
    setEstado({ tipo: "guardando", duplicado });
    const respuesta = await guardarFrase(texto, duplicado !== null);
    switch (respuesta.tipo) {
      case "guardada":
        setTexto("");
        setEstado({ tipo: "guardada", frase: respuesta.frase });
        alGuardar?.();
        break;
      case "posible_duplicado":
        // El servidor revalidó y encontró algo nuevo (RN-11).
        setEstado({ tipo: "posible_duplicado", duplicado: respuesta.duplicado });
        break;
      case "error":
        setEstado(aError(respuesta.error, { tipo: "guardar", duplicado }));
        break;
    }
  }

  function cambiarTexto(nuevo: string): void {
    setTexto(nuevo);
    // Cualquier resultado caduca al editar (AC-16b).
    setEstado({ tipo: "inactivo" });
  }

  function validar(): void {
    if (estado.tipo === "validando" || estado.tipo === "guardando") return;
    void ejecutarValidacion();
  }

  function guardar(): void {
    if (estado.tipo === "unica") void ejecutarGuardado(null);
    else if (estado.tipo === "posible_duplicado") void ejecutarGuardado(estado.duplicado);
  }

  function cancelar(): void {
    if (estado.tipo === "posible_duplicado") setEstado({ tipo: "inactivo" });
  }

  function reintentar(): void {
    if (estado.tipo !== "error" || estado.reintentar === null) return;
    const operacion = estado.reintentar;
    if (operacion.tipo === "validar") void ejecutarValidacion();
    else void ejecutarGuardado(operacion.duplicado);
  }

  return { texto, estado, cambiarTexto, validar, guardar, cancelar, reintentar };
}
