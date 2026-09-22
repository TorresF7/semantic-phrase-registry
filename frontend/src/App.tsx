import FormularioFrase from "./components/FormularioFrase";
import ListaFrases from "./components/ListaFrases";
import { useFrases } from "./hooks/useFrases";
import { useValidacion } from "./hooks/useValidacion";
import estilos from "./App.module.css";

// Solo alimenta el contador; el límite real lo aplica el servidor (Artículo 8).
const MAX_POR_DEFECTO = 280;
const maxConfigurado = Number(import.meta.env.VITE_MAX_PHRASE_LENGTH);
const MAX_CARACTERES =
  Number.isInteger(maxConfigurado) && maxConfigurado > 0 ? maxConfigurado : MAX_POR_DEFECTO;

export default function App() {
  const frases = useFrases();
  const validacion = useValidacion({ alGuardar: frases.irAPrimeraPagina });

  return (
    <main className="pagina">
      <header className={estilos.cabecera}>
        <h1 className={estilos.titulo}>Banco de Frases</h1>
        <p className={estilos.descripcion}>
          Escribe una frase y valídala antes de guardarla: te avisamos si ya existe una que diga lo
          mismo con otras palabras.
        </p>
      </header>
      <FormularioFrase
        texto={validacion.texto}
        estado={validacion.estado}
        maxCaracteres={MAX_CARACTERES}
        onCambiarTexto={validacion.cambiarTexto}
        onValidar={validacion.validar}
        onGuardar={validacion.guardar}
        onCancelar={validacion.cancelar}
        onReintentar={validacion.reintentar}
      />
      <ListaFrases
        estado={frases.estado}
        onAnteriores={frases.anteriores}
        onSiguientes={frases.siguientes}
        onReintentar={frases.reintentar}
      />
    </main>
  );
}
