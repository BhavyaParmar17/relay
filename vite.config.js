import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the Flask API runs on :5000 and Vite proxies /api to it.
// On Vercel, /api/* is served by api/index.py (see vercel.json).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://127.0.0.1:5000" },
  },
});
