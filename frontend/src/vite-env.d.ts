/// <reference types="vite/client" />

// Variables públicas: Vite las incrusta en el paquete. Ningún secreto aquí.
interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
