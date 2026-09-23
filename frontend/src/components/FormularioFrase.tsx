import { useEffect, useLayoutEffect, useRef } from "react";

import type { EstadoFormulario } from "../hooks/useValidacion";
import BotonCarga from "./BotonCarga";
import Veredicto from "./Veredicto";
import estilos from "./FormularioFrase.module.css";

const MINIMO_CARACTERES = 3;

type Props = {
  texto: string;
  estado: EstadoFormulario;
  maxCaracteres: number;
  onCambiarTexto: (texto: string) => void;
  onValidar: () => void;
  onGuardar: () => void;
  onGuardarDeTodosModos: () => void;
  onEditar: () => void;
  onReintentar: () => void;
};

// El botón principal avanza por pasos: su texto y su acción siguen al estado
// (ui-design, tabla del botón principal).
type BotonPrincipal = {
  etiqueta: string;
  etiquetaCargando: string;
  cargando: boolean;
  habilitado: boolean;
  accion: () => void;
};

export default function FormularioFrase({
  texto,
  estado,
  maxCaracteres,
  onCambiarTexto,
  onValidar,
  onGuardar,
  onGuardarDeTodosModos,
  onEditar,
  onReintentar,
}: Props) {
  const campo = useRef<HTMLTextAreaElement>(null);
  // Puntos de código, igual que el servidor: un emoji cuenta 1 (RN-01).
  const caracteres = [...texto].length;
  // El mínimo se mide sobre el texto normalizado, como el servidor (RN-01, RN-03):
  // "   " no llega a comprobarse. El contador y el máximo siguen sobre el texto crudo.
  const longitudValida =
    longitudNormalizada(texto) >= MINIMO_CARACTERES && caracteres <= maxCaracteres;
  const ocupado = estado.tipo === "validando" || estado.tipo === "guardando";
  const principal = botonPrincipal(estado, longitudValida, {
    onValidar,
    onGuardar,
    onReintentar,
  });

  // El campo crece con el contenido hasta --alto-campo-max, que limita el CSS.
  useLayoutEffect(() => {
    const elemento = campo.current;
    if (elemento === null) return;
    elemento.style.height = "auto";
    elemento.style.height = `${elemento.scrollHeight}px`;
  }, [texto]);

  // Tras guardar, el campo vacío recupera el foco para la siguiente frase (AC-16).
  useEffect(() => {
    if (estado.tipo === "guardada") campo.current?.focus();
  }, [estado.tipo]);

  function editar(): void {
    onEditar();
    campo.current?.focus(); // AC-16b
  }

  return (
    <section className={estilos.registro} aria-labelledby="etiqueta-frase">
      <label id="etiqueta-frase" htmlFor="frase" className={estilos.etiqueta}>
        Registrar frase
      </label>
      <div className={estilos.entrada}>
        <textarea
          id="frase"
          ref={campo}
          className={estilos.campo}
          rows={1}
          value={texto}
          // `readOnly` y no `disabled`: el campo conserva el foco durante la operación.
          readOnly={ocupado}
          aria-describedby="pie-frase"
          onChange={(evento) => onCambiarTexto(evento.target.value)}
          onKeyDown={(evento) => {
            if (evento.key === "Enter" && (evento.ctrlKey || evento.metaKey)) {
              evento.preventDefault();
              if (principal.habilitado && !principal.cargando) principal.accion();
            }
          }}
        />
        <BotonCarga
          etiqueta={principal.etiqueta}
          etiquetaCargando={principal.etiquetaCargando}
          cargando={principal.cargando}
          deshabilitado={!principal.habilitado}
          variante="primario"
          onClick={principal.accion}
        />
      </div>
      <p id="pie-frase" className={estilos.pie}>
        <span>
          <kbd>Ctrl</kbd> + <kbd>Enter</kbd> para continuar
        </span>
        <span
          className={`${estilos.contador} ${caracteres > maxCaracteres ? estilos.excedido : ""}`}
        >
          {caracteres} / {maxCaracteres}
        </span>
      </p>
      <div className={estilos.veredicto} aria-live="polite">
        <Veredicto
          estado={estado}
          texto={texto}
          onEditar={editar}
          onGuardarDeTodosModos={onGuardarDeTodosModos}
        />
      </div>
    </section>
  );
}

function botonPrincipal(
  estado: EstadoFormulario,
  longitudValida: boolean,
  acciones: { onValidar: () => void; onGuardar: () => void; onReintentar: () => void },
): BotonPrincipal {
  const comprobar: BotonPrincipal = {
    etiqueta: "Comprobar similitud",
    etiquetaCargando: "Comprobando…",
    cargando: false,
    habilitado: longitudValida,
    accion: acciones.onValidar,
  };
  const guardar: BotonPrincipal = {
    etiqueta: "Guardar frase",
    etiquetaCargando: "Guardando…",
    cargando: false,
    habilitado: false,
    accion: acciones.onGuardar,
  };

  switch (estado.tipo) {
    case "inactivo":
    case "guardada":
      return comprobar;
    case "validando":
      return { ...comprobar, cargando: true };
    case "unica":
      return { ...guardar, habilitado: true };
    // Se guarda desde el veredicto, que explica por qué (D-27).
    case "posible_duplicado":
    case "conflicto":
      return guardar;
    case "guardando":
      return { ...guardar, cargando: true };
    case "error":
      // Con un 422 no hay Reintentar: se corrige el texto y se comprueba de nuevo (D-24).
      return estado.reintentar === null
        ? comprobar
        : {
            etiqueta: "Reintentar",
            etiquetaCargando: "Reintentando…",
            cargando: false,
            habilitado: true,
            accion: acciones.onReintentar,
          };
  }
}

// Longitud en puntos de código del texto normalizado según RN-02: NFKC, recorte,
// colapso de espacios en blanco y minúsculas. Solo decide si se habilita el
// botón; la validación que manda es la del servidor (Artículo 8).
function longitudNormalizada(texto: string): number {
  const normalizado = texto.normalize("NFKC").trim().replace(/\s+/gu, " ").toLowerCase();
  return [...normalizado].length;
}
