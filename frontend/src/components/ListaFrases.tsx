import type { ItemListado } from "../api/tipos";
import type { EstadoListado } from "../hooks/useFrases";
import EstadoVacio from "./EstadoVacio";
import estilos from "./ListaFrases.module.css";

type Props = {
  estado: EstadoListado;
  onAnteriores: () => void;
  onSiguientes: () => void;
  onReintentar: () => void;
};

// Fecha absoluta en la zona local: no hay que recalcularla (ui-design).
const formatoFecha = new Intl.DateTimeFormat("es", { dateStyle: "medium", timeStyle: "short" });

export default function ListaFrases({ estado, onAnteriores, onSiguientes, onReintentar }: Props) {
  const cargando = estado.tipo === "cargando";
  const pagina = estado.tipo === "lista" ? estado.pagina : null;
  const items = pagina?.items ?? [];

  return (
    <section className={estilos.listado} aria-labelledby="titulo-listado">
      <h2 id="titulo-listado" className={estilos.titulo}>
        Frases registradas
      </h2>

      <div className={cargando ? estilos.reserva : undefined}>
        {cargando && <p className={estilos.cargando}>Cargando frases…</p>}
        {estado.tipo === "error" && (
          <div className={estilos.error} role="alert">
            <p>No pudimos cargar las frases.</p>
            <button type="button" className="boton boton--secundario" onClick={onReintentar}>
              Reintentar
            </button>
          </div>
        )}
        {pagina?.total === 0 && <EstadoVacio />}
        <ul className={estilos.lista} aria-labelledby="titulo-listado" aria-busy={cargando}>
          {items.map((item) => (
            <Elemento key={item.id} item={item} />
          ))}
        </ul>
      </div>

      {pagina !== null && pagina.total > 0 && (
        <nav className={estilos.paginacion} aria-label="Paginación">
          <button
            type="button"
            className="boton boton--secundario"
            disabled={pagina.desplazamiento === 0}
            onClick={onAnteriores}
          >
            Anteriores
          </button>
          <p className={estilos.rango}>
            {textoRango(pagina.desplazamiento, items.length, pagina.total)}
          </p>
          <button
            type="button"
            className="boton boton--secundario"
            disabled={pagina.desplazamiento + items.length >= pagina.total}
            onClick={onSiguientes}
          >
            Siguientes
          </button>
        </nav>
      )}
    </section>
  );
}

function Elemento({ item }: { item: ItemListado }) {
  return (
    <li className={estilos.tarjeta}>
      <p className={estilos.texto}>{item.texto}</p>
      <p className={estilos.metadatos}>
        <time dateTime={item.creada_en}>{formatoFecha.format(new Date(item.creada_en))}</time>
        {/* Con texto: la información nunca va solo en el color. */}
        {item.estado === "DUPLICADO_CONFIRMADO" && (
          <span className={estilos.etiqueta}>Duplicado confirmado</span>
        )}
      </p>
    </li>
  );
}

function textoRango(desplazamiento: number, cantidad: number, total: number): string {
  if (cantidad === 0) return `0 de ${total}`;
  return `${desplazamiento + 1}–${desplazamiento + cantidad} de ${total}`;
}
