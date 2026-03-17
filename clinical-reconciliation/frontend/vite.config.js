import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0', // Allow access from host when running in Docker
    proxy: {
      '/api': {
        target: process.env.VITE_API_BACKEND || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
