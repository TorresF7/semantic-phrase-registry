// Botón que muestra una operación en curso sin cambiar de ancho (ui-design).
// Solo la etiqueta visible forma parte del nombre accesible.

import { forwardRef } from "react";

type Props = {
  etiqueta: string;
  etiquetaCargando: string;
  cargando: boolean;
  deshabilitado?: boolean;
  variante: "primario" | "secundario";
  onClick: () => void;
};

const BotonCarga = forwardRef<HTMLButtonElement, Props>(function BotonCarga(
  { etiqueta, etiquetaCargando, cargando, deshabilitado = false, variante, onClick },
  ref,
) {
  return (
    <button
      ref={ref}
      type="button"
      className={`boton boton--${variante}`}
      // Mientras carga, `aria-disabled` y no `disabled`: un botón deshabilitado
      // pierde el foco y quien usa el teclado acaba en BODY (D-36).
      disabled={deshabilitado && !cargando}
      aria-disabled={cargando || undefined}
      aria-busy={cargando}
      onClick={() => {
        if (!cargando) onClick();
      }}
    >
      <span className="boton__etiquetas">
        <span
          className={`boton__etiqueta${cargando ? " boton__etiqueta--oculta" : ""}`}
          aria-hidden={cargando}
        >
          {etiqueta}
        </span>
        <span
          className={`boton__etiqueta${cargando ? "" : " boton__etiqueta--oculta"}`}
          aria-hidden={!cargando}
        >
          <span className="boton__indicador" aria-hidden="true" />
          {etiquetaCargando}
        </span>
      </span>
    </button>
  );
});

export default BotonCarga;
