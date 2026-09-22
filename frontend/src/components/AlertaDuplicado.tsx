import type { DatosDuplicado } from "../api/tipos";
import BotonCarga from "./BotonCarga";
import estilos from "./AlertaDuplicado.module.css";

type Props = {
  duplicado: DatosDuplicado;
  guardando: boolean;
  onGuardar: () => void;
  onCancelar: () => void;
};

export default function AlertaDuplicado({ duplicado, guardando, onGuardar, onCancelar }: Props) {
  const exacto = duplicado.motivo === "EXACTO";
  // En el duplicado exacto no hay porcentaje: es una coincidencia literal, no
  // un cálculo (ui-design).
  const porcentaje =
    !exacto && duplicado.puntaje !== null ? Math.round(duplicado.puntaje * 100) : null;

  return (
    <div className={estilos.alerta} role="alert">
      <p className={estilos.titulo}>
        <span aria-hidden="true">⚠</span>
        {exacto ? "Esta frase ya existe tal cual" : "Esta frase se parece mucho a una existente"}
      </p>
      <div className={estilos.cuerpo}>
        {duplicado.mas_parecida && <p className={estilos.frase}>{duplicado.mas_parecida.texto}</p>}
        {porcentaje !== null && <p className={estilos.similitud}>{porcentaje}% de similitud</p>}
        <div className={estilos.acciones}>
          <BotonCarga
            etiqueta="Guardar de todos modos"
            etiquetaCargando="Guardando…"
            cargando={guardando}
            variante="secundario"
            onClick={onGuardar}
          />
          <button
            type="button"
            className="boton boton--discreto"
            disabled={guardando}
            onClick={onCancelar}
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
