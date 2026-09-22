// Botón que muestra una operación en curso sin cambiar de ancho (ui-design).
// Solo la etiqueta visible forma parte del nombre accesible.

type Props = {
  etiqueta: string;
  etiquetaCargando: string;
  cargando: boolean;
  deshabilitado?: boolean;
  variante: "primario" | "secundario";
  onClick: () => void;
};

export default function BotonCarga({
  etiqueta,
  etiquetaCargando,
  cargando,
  deshabilitado = false,
  variante,
  onClick,
}: Props) {
  return (
    <button
      type="button"
      className={`boton boton--${variante}`}
      disabled={cargando || deshabilitado}
      aria-busy={cargando}
      onClick={onClick}
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
}
