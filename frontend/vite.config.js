import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// 开发时 /api 代理到本地 FastAPI（app.cli serve 默认 8000），生产构建产物由 FastAPI 直接托管。
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    emptyOutDir: true,
    sourcemap: false,
  },
});
