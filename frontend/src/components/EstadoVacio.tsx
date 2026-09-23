import estilos from "./EstadoVacio.module.css";

// Sin encabezados de columna: dice qué hacer, no una tabla en blanco (AC-20).
export default function EstadoVacio() {
  return (
    <div className={estilos.vacio}>
      <h3 className={estilos.titulo}>Todavía no hay frases</h3>
      <p className={estilos.texto}>
        Escribe la primera en el campo de arriba. Como no habrá nada con qué compararla, se guardará
        como única.
      </p>
    </div>
  );
}
