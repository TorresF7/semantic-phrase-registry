import estilos from "./EstadoVacio.module.css";

export default function EstadoVacio() {
  return (
    <p className={estilos.vacio}>Todavía no hay frases registradas. Escribe la primera arriba.</p>
  );
}
