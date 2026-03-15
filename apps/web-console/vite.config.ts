import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy API calls to control-api in dev to avoid CORS and use runtime config
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ui/runtime-config.json': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom'],
          router: ['react-router'],
          query: ['@tanstack/react-query'],
          table: ['@tanstack/react-table'],
        },
      },
    },
  },
})
