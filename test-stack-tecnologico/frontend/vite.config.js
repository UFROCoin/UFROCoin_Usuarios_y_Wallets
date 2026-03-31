import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    host: true, // Requerido para mapear el puerto desde Docker
    port: 5173,
    watch: {
      usePolling: true // Totalmente necesario en Windows cuando se usan volúmenes de Docker
    }
  }
})
