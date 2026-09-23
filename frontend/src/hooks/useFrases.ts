// Listado paginado por desplazamiento (RN-17). Máquina de estados de la lista
// (plan §5, CH-02): cargando → ok | vacia | error. Una unión discriminada en
// lugar de banderas de carga y error sueltas.

import { useEffect, useState } from "react";

import { listarFrases } from "../api/cliente";
import type { PaginaFrases } from "../api/tipos";

export const TAMANO_PAGINA = 20;

export type EstadoLista =
  | { tipo: "cargando" }
  | { tipo: "ok"; pagina: PaginaFrases }
  | { tipo: "vacia" }
  | { tipo: "error" };

export type Frases = {
  estado: EstadoLista;
  anteriores: () => void;
  siguientes: () => void;
  reintentar: () => void;
  irAPrimeraPagina: () => void;
};

export function useFrases(): Frases {
  const [desplazamiento, setDesplazamiento] = useState(0);
  // Cambia para volver a pedir la misma página (reintentar, o volver a la
  // primera cuando ya se estaba en ella).
  const [peticion, setPeticion] = useState(0);
  const [estado, setEstado] = useState<EstadoLista>({ tipo: "cargando" });

  useEffect(() => {
    // Descarta la respuesta de una petición que ya no es la última.
    let vigente = true;
    setEstado({ tipo: "cargando" });
    void listarFrases(TAMANO_PAGINA, desplazamiento).then((respuesta) => {
      if (!vigente) return;
      if (!respuesta.ok) setEstado({ tipo: "error" });
      else if (respuesta.datos.total === 0) setEstado({ tipo: "vacia" });
      else setEstado({ tipo: "ok", pagina: respuesta.datos });
    });
    return () => {
      vigente = false;
    };
  }, [desplazamiento, peticion]);

  function anteriores(): void {
    setDesplazamiento((actual) => Math.max(0, actual - TAMANO_PAGINA));
  }

  function siguientes(): void {
    setDesplazamiento((actual) => actual + TAMANO_PAGINA);
  }

  function reintentar(): void {
    setPeticion((actual) => actual + 1);
  }

  // Tras guardar, la frase nueva está al principio del orden (AC-16).
  function irAPrimeraPagina(): void {
    setDesplazamiento(0);
    setPeticion((actual) => actual + 1);
  }

  return { estado, anteriores, siguientes, reintentar, irAPrimeraPagina };
}
