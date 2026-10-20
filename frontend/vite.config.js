import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import path from 'path'
import fs from 'fs'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    tailwindcss(),
    {
      name: 'preserve-vad',
      // vad 目录有 86MB 的 wasm 文件，经常被浏览器占用，
      // 导致 emptyOutDir 清空输出目录时删除失败、整个构建报错。
      // 构建结束后如果输出目录缺少 vad，就从 public 补回去。
      closeBundle() {
        const outDir = path.resolve(__dirname, '../backend/static/frontend')
        const srcVad = path.resolve(__dirname, 'public/vad')
        const outVad = path.join(outDir, 'vad')

        if (fs.existsSync(srcVad) && !fs.existsSync(outVad)) {
          fs.mkdirSync(outDir, { recursive: true })
          fs.cpSync(srcVad, outVad, { recursive: true })
          console.log('[preserve-vad] 已补回 vad 目录')
        }
      },
    },
  ],
  build: {
    outDir: path.resolve(__dirname, '../backend/static/frontend'), // 打包到 Django static
    emptyOutDir: true,
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
