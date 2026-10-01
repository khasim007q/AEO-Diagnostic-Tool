import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    target: "esnext",
    minify: "esbuild",
    rollupOptions: {
      output: {
        manualChunks: {
          vendor_react: ["react", "react-dom"],
          vendor_ui: ["framer-motion", "lucide-react"],
          vendor_charts: ["recharts"],
        },
      },
    },
  },
})
