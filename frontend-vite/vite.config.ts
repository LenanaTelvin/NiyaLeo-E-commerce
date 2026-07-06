import { defineConfig } from 'vite'
// Suppress TS error if type declarations for the plugin are missing
// @ts-ignore
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})