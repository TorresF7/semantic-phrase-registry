// Tabla de frases registradas y sus estados (ui-design v2, AC-19, AC-20). Por
// hasta 900 px las filas se muestran como fichas con la misma semántica.

import { useEffect, useRef, useState } from "react";

import type { ItemListado, PaginaFrases } from "../api/tipos";
import type { EstadoLista } from "../hooks/useFrases";
import EstadoVacio from "./EstadoVacio";
import estilos from "./ListaFrases.module.css";

// Tiempo que una fila queda resaltada al saltar a ella (~1 s, ui-design).
const DURACION_RESALTADO_MS = 1000;

// Anchos de las barras de esqueleto de Frase y Más parecida, por fila: varían
// para que no parezca una rejilla, igual que en el prototipo.
const ANCHOS_ESQUELETO: ReadonlyArray<readonly [number, number]> = [
  [62, 48],
  [44, 70],
  [70, 40],
  [38, 56],
  [55, 64],
];

type Props = {
  estado: EstadoLista;
  onAnteriores: () => void;
  onSiguientes: () => void;
  onReintentar: () => void;
  // Frase recién guardada: se resalta cuando aparece en la página.
  idNueva: number | null;
  onNuevaResaltada: () => void;
};

export default function ListaFrases({
  estado,
  onAnteriores,
  onSiguientes,
  onReintentar,
  idNueva,
  onNuevaResaltada,
}: Props) {
  const filas = useRef(new Map<number, HTMLTableRowElement>());
  const temporizador = useRef<number | undefined>(undefined);
  const [resaltada, setResaltada] = useState<number | null>(null);

  function resaltar(id: number): void {
    const fila = filas.current.get(id);
    if (fila === undefined) return;
    const reducido = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
    fila.scrollIntoView?.({ block: "center", behavior: reducido ? "auto" : "smooth" });
    setResaltada(id);
    window.clearTimeout(temporizador.current);
    temporizador.current = window.setTimeout(() => setResaltada(null), DURACION_RESALTADO_MS);
  }

  useEffect(() => () => window.clearTimeout(temporizador.current), []);

  useEffect(() => {
    if (idNueva === null || estado.tipo !== "ok") return;
    if (estado.pagina.items.some((item) => item.id === idNueva)) {
      resaltar(idNueva);
      onNuevaResaltada();
    }
    // Depende solo de los datos: `resaltar` y `onNuevaResaltada` no deciden nada.
  }, [estado, idNueva]);

  return (
    <section className={estilos.listado} aria-labelledby="titulo-listado">
      <div className={estilos.cabecera}>
        <h2 id="titulo-listado" className={estilos.titulo}>
          Frases registradas
        </h2>
        <Resumen estado={estado} />
      </div>

      <Anuncio estado={estado} />

      {estado.tipo === "cargando" && <TablaEsqueleto />}
      {estado.tipo === "ok" && (
        <Tabla
          pagina={estado.pagina}
          resaltada={resaltada}
          filas={filas.current}
          onIrA={resaltar}
        />
      )}
      {estado.tipo === "vacia" && <EstadoVacio />}
      {estado.tipo === "error" && (
        <div className={`${estilos.mensaje} ${estilos.error}`} role="alert">
          <h3 className={estilos.mensajeTitulo}>No se pudo cargar la lista</h3>
          <p className={estilos.mensajeTexto}>
            El servidor no respondió. Las frases guardadas no se han perdido.
          </p>
          <button type="button" className="boton boton--secundario" onClick={onReintentar}>
            Reintentar
          </button>
        </div>
      )}

      {/* La paginación solo aparece si hay más de una página (AC-20). */}
      {estado.tipo === "ok" && estado.pagina.total > estado.pagina.limite && (
        <Paginacion
          pagina={estado.pagina}
          onAnteriores={onAnteriores}
          onSiguientes={onSiguientes}
        />
      )}
    </section>
  );
}

function Resumen({ estado }: { estado: EstadoLista }) {
  switch (estado.tipo) {
    case "cargando":
      return (
        <span className={`${estilos.esqueleto} ${estilos.esqueletoResumen}`} aria-hidden="true" />
      );
    case "ok":
      // Solo el `total` de la respuesta: el contrato no da otros conteos.
      return (
        <p className={estilos.resumen}>
          {estado.pagina.total === 1 ? "1 frase" : `${estado.pagina.total} frases`}
        </p>
      );
    case "vacia":
      return <p className={estilos.resumen}>0 frases</p>;
    case "error":
      return null;
  }
}

// Región viva de la lista: siempre montada, para que el lector de pantalla
// anuncie sus cambios. Sin rol `status`: ese es el del veredicto. El error no
// pasa por aquí porque ya se anuncia con `role="alert"`.
function Anuncio({ estado }: { estado: EstadoLista }) {
  return (
    <p className={estilos.oculto} aria-live="polite">
      {textoAnuncio(estado)}
    </p>
  );
}

function textoAnuncio(estado: EstadoLista): string {
  switch (estado.tipo) {
    case "cargando":
      return "Cargando frases…";
    case "ok": {
      const { total, desplazamiento, items } = estado.pagina;
      return `Mostrando ${desplazamiento + 1}–${desplazamiento + items.length} de ${total} frases`;
    }
    case "vacia":
      return "No hay frases registradas";
    case "error":
      // Vacío a propósito: el mensaje de error ya se anuncia con role="alert".
      return "";
  }
}

// Roles explícitos en toda la tabla: hasta 900 px las fichas cambian su
// `display`, y algunos navegadores dejan entonces de exponer filas y celdas.
function Encabezados() {
  return (
    <thead role="rowgroup">
      <tr role="row">
        <th scope="col" role="columnheader">
          Frase
        </th>
        <th scope="col" role="columnheader" className={estilos.colEstado}>
          Estado
        </th>
        <th scope="col" role="columnheader" className={estilos.colSimilitud}>
          Similitud
        </th>
        <th scope="col" role="columnheader" className={estilos.colParecida}>
          Más parecida al registrar
        </th>
        <th scope="col" role="columnheader" className={estilos.colFecha}>
          Registrada
        </th>
      </tr>
    </thead>
  );
}

// Mismas columnas que una fila real: nada se mueve al llegar los datos (AC-20).
function TablaEsqueleto() {
  return (
    <table className={estilos.tabla} role="table">
      <Encabezados />
      <tbody role="rowgroup" aria-busy="true">
        {ANCHOS_ESQUELETO.map(([anchoFrase, anchoReferencia], indice) => (
          <tr key={indice} role="row" className={estilos.filaEsqueleto} aria-hidden="true">
            <td role="cell" className={estilos.celdaFrase}>
              <span className={estilos.esqueleto} style={{ width: `${anchoFrase}%` }} />
            </td>
            <td role="cell" className={estilos.celdaEstado}>
              <span className={`${estilos.esqueleto} ${estilos.esqueletoEstado}`} />
            </td>
            <td role="cell" className={estilos.celdaSimilitud}>
              <span className={`${estilos.esqueleto} ${estilos.esqueletoSimilitud}`} />
            </td>
            <td role="cell" className={estilos.celdaReferencia}>
              <span className={estilos.esqueleto} style={{ width: `${anchoReferencia}%` }} />
            </td>
            <td role="cell" className={estilos.celdaFecha}>
              <span className={`${estilos.esqueleto} ${estilos.esqueletoFecha}`} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

type PropsTabla = {
  pagina: PaginaFrases;
  resaltada: number | null;
  filas: Map<number, HTMLTableRowElement>;
  onIrA: (id: number) => void;
};

function Tabla({ pagina, resaltada, filas, onIrA }: PropsTabla) {
  const idsEnPagina = new Set(pagina.items.map((item) => item.id));

  return (
    <table className={estilos.tabla} role="table">
      <Encabezados />
      <tbody role="rowgroup">
        {pagina.items.map((item) => (
          <tr
            key={item.id}
            ref={(fila) => {
              if (fila === null) filas.delete(item.id);
              else filas.set(item.id, fila);
            }}
            role="row"
            className={item.id === resaltada ? estilos.resaltada : undefined}
          >
            <td role="cell" className={estilos.celdaFrase}>
              {item.texto}
            </td>
            <td role="cell" className={estilos.celdaEstado}>
              {/* Con texto: la información nunca va solo en el color. */}
              {item.estado === "DUPLICADO_CONFIRMADO" ? (
                <span className={`${estilos.etiqueta} ${estilos.etiquetaDuplicado}`}>
                  Duplicado confirmado
                </span>
              ) : (
                <span className={`${estilos.etiqueta} ${estilos.etiquetaUnica}`}>Única</span>
              )}
            </td>
            <td role="cell" className={estilos.celdaSimilitud}>
              <MicroMedidor item={item} />
            </td>
            <td role="cell" className={estilos.celdaReferencia}>
              <Referencia item={item} enPagina={idsEnPagina} onIrA={onIrA} />
            </td>
            <td role="cell" className={estilos.celdaFecha}>
              <time dateTime={item.creada_en}>{formatearFecha(item.creada_en)}</time>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// Sin marca de umbral: el listado no trae `umbral_aplicado` y cada frase se
// guardó con el suyo (RN-13). El color sale del estado (ui-design, D-27).
function MicroMedidor({ item }: { item: ItemListado }) {
  if (item.puntaje_similitud === null) return <span className={estilos.nada}>—</span>;
  const porcentaje = Math.round(item.puntaje_similitud * 100);
  const duplicado = item.estado === "DUPLICADO_CONFIRMADO";

  return (
    <span className={`${estilos.micro} ${duplicado ? estilos.microDuplicado : ""}`}>
      <span className={estilos.microCifra}>{porcentaje} %</span>
      <span className={estilos.microPista} aria-hidden="true">
        <span className={estilos.microRelleno} style={{ width: `${porcentaje}%` }} />
      </span>
    </span>
  );
}

type PropsReferencia = {
  item: ItemListado;
  enPagina: Set<number>;
  onIrA: (id: number) => void;
};

// Solo en duplicados confirmados (AC-19). Es un botón solo si la referida está
// en la página actual: la tabla no navega a otra página.
function Referencia({ item, enPagina, onIrA }: PropsReferencia) {
  const referida = item.estado === "DUPLICADO_CONFIRMADO" ? item.mas_parecida : null;
  if (referida === null) return <span className={estilos.nada}>—</span>;
  if (!enPagina.has(referida.id))
    return <span className={estilos.referencia}>{referida.texto}</span>;

  return (
    <button
      type="button"
      className={`${estilos.referencia} ${estilos.enlace}`}
      onClick={() => onIrA(referida.id)}
    >
      {referida.texto}
    </button>
  );
}

type PropsPaginacion = {
  pagina: PaginaFrases;
  onAnteriores: () => void;
  onSiguientes: () => void;
};

function Paginacion({ pagina, onAnteriores, onSiguientes }: PropsPaginacion) {
  const inicio = pagina.desplazamiento + 1;
  const fin = pagina.desplazamiento + pagina.items.length;

  return (
    <nav className={estilos.pie} aria-label="Paginación">
      <p className={estilos.rango}>{`${inicio}–${fin} de ${pagina.total}`}</p>
      <div className={estilos.paginador}>
        <button
          type="button"
          className={`boton boton--secundario ${estilos.botonPagina}`}
          disabled={pagina.desplazamiento === 0}
          onClick={onAnteriores}
        >
          Anteriores
        </button>
        <button
          type="button"
          className={`boton boton--secundario ${estilos.botonPagina}`}
          disabled={fin >= pagina.total}
          onClick={onSiguientes}
        >
          Siguientes
        </button>
      </div>
    </nav>
  );
}

const formatoDia = new Intl.DateTimeFormat("es", { day: "numeric", month: "short" });
const formatoHora = new Intl.DateTimeFormat("es", { hour: "2-digit", minute: "2-digit" });

// "22 sept · 14:45", en la zona local. Una fecha que no se puede leer no debe
// tumbar la pantalla entera: sin ella, la frase se sigue mostrando.
function formatearFecha(iso: string): string {
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return "";
  return `${formatoDia.format(fecha)} · ${formatoHora.format(fecha)}`;
}
