import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
export default defineConfig({
  plugins: [react(), tailwindcss()],
  envDir: "..",
  server: {
    proxy: {
      "/health": "http://127.0.0.1:8000",
      "/auth": "http://127.0.0.1:8000",
      "/demo": "http://127.0.0.1:8000",
      "/employees": "http://127.0.0.1:8000",
      "/hr/dashboard": "http://127.0.0.1:8000",
      "/dataset/status": "http://127.0.0.1:8000",
      "/dataset/upload": "http://127.0.0.1:8000",
      "/dataset/profiles": "http://127.0.0.1:8000",
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          charts: ["recharts"],
          vendor: ["react", "react-dom", "react-router-dom"],
        },
      },
    },
  },
});
