import { useState } from "react";

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
  // La frase recién guardada se resalta cuando aparece en la lista (ui-design).
  const [idNueva, setIdNueva] = useState<number | null>(null);
  const validacion = useValidacion({
    alGuardar: (frase) => {
      setIdNueva(frase.id);
      frases.irAPrimeraPagina();
    },
  });

  return (
    <>
      <header className={estilos.barra}>
        <div className={estilos.barraInterior}>
          <h1 className={estilos.nombre}>Banco de Frases</h1>
          <p className={estilos.subtitulo}>Comparación por significado</p>
        </div>
      </header>
      <main className="pagina">
        <FormularioFrase
          texto={validacion.texto}
          estado={validacion.estado}
          maxCaracteres={MAX_CARACTERES}
          onCambiarTexto={validacion.cambiarTexto}
          onValidar={validacion.validar}
          onGuardar={validacion.guardar}
          onGuardarDeTodosModos={validacion.guardarDeTodosModos}
          onEditar={validacion.editar}
          onReintentar={validacion.reintentar}
        />
        <ListaFrases
          estado={frases.estado}
          onAnteriores={frases.anteriores}
          onSiguientes={frases.siguientes}
          onReintentar={frases.reintentar}
          idNueva={idNueva}
          onNuevaResaltada={() => setIdNueva(null)}
        />
      </main>
    </>
  );
}
