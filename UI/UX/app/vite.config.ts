import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
const apiTarget = process.env.RECTO_API_TARGET ?? 'http://127.0.0.1:8766'
if (!/^http:\/\/127\.0\.0\.1:[0-9]{4,5}$/.test(apiTarget)) throw new Error('RECTO_API_TARGET must be an exact loopback HTTP origin')

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '127.0.0.1',
    proxy: { '/api': { target: apiTarget, changeOrigin: true, timeout: 65000 } },
  },
})
