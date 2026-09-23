// Veredicto del registro (ui-design v2, CH-02): unica, posible_duplicado,
// conflicto, error y guardada. Solo se pinta cuando hay uno.

import type { Ref } from "react";

import type { DatosDuplicado } from "../api/tipos";
import type { EstadoFormulario } from "../hooks/useValidacion";
import estilos from "./Veredicto.module.css";

// Sin respuesta útil del servidor no hay `mensaje` que mostrar (plan §5).
const CODIGOS_SIN_RESPUESTA = new Set(["SIN_CONEXION", "RESPUESTA_INESPERADA"]);
const MENSAJE_SIN_RESPUESTA =
  "El servicio no responde. La frase no se guardó; reintenta en unos segundos.";

type Props = {
  estado: EstadoFormulario;
  texto: string;
  onEditar: () => void;
  onGuardarDeTodosModos: () => void;
  // Quien orquesta lleva aquí el foco al llegar un duplicado (D-36).
  refEditar?: Ref<HTMLButtonElement>;
};

export default function Veredicto({
  estado,
  texto,
  onEditar,
  onGuardarDeTodosModos,
  refEditar,
}: Props) {
  // Mientras se guarda, sigue a la vista el veredicto sobre el que se guarda.
  const guardando = estado.tipo === "guardando";
  const vista = estado.tipo === "guardando" ? estado.desde : estado;

  switch (vista.tipo) {
    case "unica": {
      const { puntaje, umbral_aplicado, mas_parecida } = vista.resultado;
      return (
        <div className={`${estilos.veredicto} ${estilos.ok}`} role="status">
          <p className={estilos.cabecera}>No hay otra frase con el mismo significado</p>
          <div className={estilos.cuerpo}>
            {mas_parecida !== null && puntaje !== null ? (
              <div className={estilos.columnas}>
                <p className={estilos.texto}>La más cercana es «{mas_parecida.texto}»</p>
                <Medidor puntaje={puntaje} umbral={umbral_aplicado} />
              </div>
            ) : (
              <p className={estilos.texto}>Es la primera frase del catálogo.</p>
            )}
          </div>
        </div>
      );
    }
    case "posible_duplicado":
    case "conflicto":
      return (
        <Duplicado
          duplicado={vista.duplicado}
          conflicto={vista.tipo === "conflicto"}
          texto={texto}
          guardando={guardando}
          onEditar={onEditar}
          onGuardarDeTodosModos={onGuardarDeTodosModos}
          refEditar={refEditar}
        />
      );
    case "error":
      return (
        <div className={`${estilos.veredicto} ${estilos.error}`} role="alert">
          <p className={estilos.cabecera}>No se pudo comparar la frase</p>
          <div className={estilos.cuerpo}>
            <p className={estilos.texto}>
              {CODIGOS_SIN_RESPUESTA.has(vista.codigo) ? MENSAJE_SIN_RESPUESTA : vista.mensaje}
            </p>
          </div>
        </div>
      );
    case "guardada":
      return (
        <p className={estilos.guardada} role="status">
          <span>
            {vista.frase.estado === "DUPLICADO_CONFIRMADO"
              ? "Frase guardada como duplicado confirmado."
              : "Frase guardada."}
          </span>
          <span>Ya aparece en la lista.</span>
        </p>
      );
    case "inactivo":
    case "validando":
      return null;
  }
}

type PropsDuplicado = {
  duplicado: DatosDuplicado;
  conflicto: boolean;
  texto: string;
  guardando: boolean;
  onEditar: () => void;
  onGuardarDeTodosModos: () => void;
  refEditar?: Ref<HTMLButtonElement>;
};

function Duplicado({
  duplicado,
  conflicto,
  texto,
  guardando,
  onEditar,
  onGuardarDeTodosModos,
  refEditar,
}: PropsDuplicado) {
  const exacto = duplicado.motivo === "EXACTO";
  const cabecera = conflicto
    ? "Alguien registró una frase parecida mientras revisabas"
    : exacto
      ? "Esta frase ya existe tal cual"
      : "Ya existe una frase con el mismo significado";

  return (
    <div className={`${estilos.veredicto} ${estilos.duplicado}`} role="alert">
      <p className={estilos.cabecera}>{cabecera}</p>
      <div className={estilos.cuerpo}>
        {conflicto && (
          <p className={estilos.texto}>
            Al guardar volvimos a comparar y el resultado cambió. La frase no se guardó.
          </p>
        )}
        <div className={estilos.columnas}>
          <dl className={estilos.par}>
            <div>
              <dt>Tu frase</dt>
              <dd>{texto}</dd>
            </div>
            {duplicado.mas_parecida !== null && (
              <div>
                <dt>{exacto ? "Registrada (idéntica)" : "Registrada"}</dt>
                <dd>{duplicado.mas_parecida.texto}</dd>
              </div>
            )}
          </dl>
          {/* El exacto es una coincidencia literal, no un cálculo: sin medidor. */}
          {!exacto && duplicado.puntaje !== null && (
            <Medidor puntaje={duplicado.puntaje} umbral={duplicado.umbral_aplicado} />
          )}
        </div>
        <div className={estilos.acciones}>
          {/* La acción segura pesa más (ui-design). Mientras se guarda, los dos
              botones usan aria-disabled y no disabled: conservan el foco (D-36). */}
          <button
            ref={refEditar}
            type="button"
            className="boton boton--secundario"
            aria-disabled={guardando || undefined}
            onClick={() => {
              if (!guardando) onEditar();
            }}
          >
            Editar frase
          </button>
          <button
            type="button"
            className="boton boton--discreto"
            aria-disabled={guardando || undefined}
            onClick={() => {
              if (!guardando) onGuardarDeTodosModos();
            }}
          >
            Guardar de todos modos
          </button>
        </div>
      </div>
    </div>
  );
}

type PropsMedidor = { puntaje: number; umbral: number };

function Medidor({ puntaje, umbral }: PropsMedidor) {
  const porcentaje = Math.round(puntaje * 100);
  const porcentajeUmbral = Math.round(umbral * 100);
  // Se compara sin redondear, como la política del servidor (RN-05, RN-06).
  const supera = puntaje >= umbral;

  return (
    <div
      className={`${estilos.medidor} ${supera ? estilos.supera : ""}`}
      role="img"
      aria-label={`Similitud ${porcentaje} %, umbral ${porcentajeUmbral} %`}
    >
      <div className={estilos.medidorFila}>
        <span>Similitud de significado</span>
        <span className={estilos.cifra}>{porcentaje} %</span>
      </div>
      <div className={estilos.pista}>
        <div className={estilos.relleno} style={{ width: `${porcentaje}%` }} />
        <div className={estilos.marca} style={{ left: `${porcentajeUmbral}%` }} />
      </div>
      <div className={estilos.escala} aria-hidden="true">
        <span style={{ left: "0%" }}>0</span>
        <span className={estilos.escalaUmbral} style={{ left: `${porcentajeUmbral}%` }}>
          umbral {porcentajeUmbral}
        </span>
        <span style={{ left: "100%" }}>100</span>
      </div>
    </div>
  );
}
