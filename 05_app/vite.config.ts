// Vite builds frontend/ into frontend/dist, which the FastAPI backend serves on the same origin.
// In dev, the Vite server (:5173) proxies /api to the backend (:8000) so the browser sees one origin, like on Apps.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  root: "frontend",
  plugins: [react()],
  build: { outDir: "dist", emptyOutDir: true, chunkSizeWarningLimit: 4000 },
  server: { port: 5173, proxy: { "/api": { target: "http://localhost:8000", changeOrigin: true } } },
});
