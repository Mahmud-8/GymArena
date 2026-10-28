import { defineConfig } from 'vite';

export default defineConfig({
  base: '/kiosk/',
  server: { proxy: { '/api': 'http://127.0.0.1:8105' } },
  build: { sourcemap: false },
});
