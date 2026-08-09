import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Vite powers the local React development server and production build.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
  },
});
