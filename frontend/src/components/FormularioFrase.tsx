import type { EstadoFormulario } from "../hooks/useValidacion";
import AlertaDuplicado from "./AlertaDuplicado";
import BotonCarga from "./BotonCarga";
import estilos from "./FormularioFrase.module.css";

type Props = {
  texto: string;
  estado: EstadoFormulario;
  maxCaracteres: number;
  onCambiarTexto: (texto: string) => void;
  onValidar: () => void;
  onGuardar: () => void;
  onCancelar: () => void;
  onReintentar: () => void;
};

export default function FormularioFrase({
  texto,
  estado,
  maxCaracteres,
  onCambiarTexto,
  onValidar,
  onGuardar,
  onCancelar,
  onReintentar,
}: Props) {
  // Puntos de código, igual que el servidor: un emoji cuenta 1 (RN-01).
  const caracteres = [...texto].length;
  const ocupado = estado.tipo === "validando" || estado.tipo === "guardando";
  // La alerta sigue en pantalla mientras se guarda desde ella.
  const duplicado =
    estado.tipo === "posible_duplicado" || estado.tipo === "guardando" ? estado.duplicado : null;
  const guardandoUnica = estado.tipo === "guardando" && estado.duplicado === null;
  const sinResultado =
    estado.tipo === "inactivo" ||
    estado.tipo === "validando" ||
    estado.tipo === "error" ||
    estado.tipo === "guardada";

  return (
    <section className={estilos.formulario}>
      <div className={estilos.campo}>
        <label htmlFor="frase" className={estilos.etiqueta}>
          Frase
        </label>
        <textarea
          id="frase"
          className={estilos.texto}
          rows={3}
          value={texto}
          disabled={ocupado}
          onChange={(evento) => onCambiarTexto(evento.target.value)}
        />
        <p className={`${estilos.contador} ${caracteres > maxCaracteres ? estilos.excedido : ""}`}>
          {caracteres} / {maxCaracteres}
        </p>
      </div>

      <div className={estilos.acciones}>
        <BotonCarga
          etiqueta="Validar"
          etiquetaCargando="Validando…"
          cargando={estado.tipo === "validando"}
          deshabilitado={ocupado}
          variante="primario"
          onClick={onValidar}
        />
        <BotonCarga
          etiqueta="Guardar"
          etiquetaCargando="Guardando…"
          cargando={guardandoUnica}
          deshabilitado={estado.tipo !== "unica"}
          variante="primario"
          onClick={onGuardar}
        />
      </div>
      {sinResultado && <p className={estilos.pista}>Valida la frase antes de guardar</p>}

      <div className={estilos.resultado}>
        {estado.tipo === "unica" && (
          <p className={`${estilos.aviso} ${estilos.neutro}`} role="status">
            No encontramos frases parecidas. Puedes guardarla.
          </p>
        )}
        {duplicado !== null && (
          <AlertaDuplicado
            duplicado={duplicado}
            guardando={estado.tipo === "guardando"}
            onGuardar={onGuardar}
            onCancelar={onCancelar}
          />
        )}
        {estado.tipo === "guardada" && (
          <p className={`${estilos.aviso} ${estilos.exito}`} role="status">
            {estado.frase.estado === "DUPLICADO_CONFIRMADO"
              ? "Frase guardada como duplicado confirmado."
              : "Frase guardada."}
          </p>
        )}
        {estado.tipo === "error" && (
          <div className={`${estilos.aviso} ${estilos.peligro}`} role="alert">
            <p>{estado.mensaje}</p>
            {estado.reintentar !== null && (
              <button type="button" className="boton boton--secundario" onClick={onReintentar}>
                Reintentar
              </button>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
