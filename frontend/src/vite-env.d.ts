/// <reference types="vite/client" />

// Variables públicas: Vite las incrusta en el paquete. Ningún secreto aquí.
interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_MAX_PHRASE_LENGTH?: string;
  readonly VITE_API_TIMEOUT_MS?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
