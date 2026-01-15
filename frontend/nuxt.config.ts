// nuxt.config.ts
export default defineNuxtConfig({
  compatibilityDate: '2025-01-06',
  devtools: { enabled: true },

  modules: [
    '@pinia/nuxt' // Chỉ giữ lại Pinia
  ],

  css: [
    './assets/css/styles.css'
  ],

  runtimeConfig: {
    public: {
      // 🚨 THAY ĐỔI URL NÀY: Dán tunnel URL của BACKEND (port 5000)
      // Ví dụ: https://abc123.trycloudflare.com/api
      // Hiện tại: https://api.nanoproai.shop/api (DOMAIN THẬT)
      apiBase: 'https://api.nanoproai.shop/api'
    }
  },

  devServer: {
    host: '0.0.0.0',
    port: 3000
  },

  // Cấu hình để hỗ trợ external access
  ssr: false, // Tắt SSR cho dev để tránh vấn đề hydration

  // Serve frontend from /web path
  app: {
    baseURL: '/web'
  },

  nitro: {
    baseURL: '/web',
    devProxy: {
      '/api': {
        target: 'http://localhost:5000/api',
        changeOrigin: true
      }
    }
  },

  vite: {
    base: '/web/',
    server: {
      // 🚨 THAY ĐỔI URL NÀY: Dán tunnel URL của FRONTEND (port 3000)
      // Ví dụ: ['abc456.trycloudflare.com', 'localhost', 'all']
      // Hiện tại: DOMAIN THẬT - web.nanoproai.shop
      allowedHosts: [
        'web.nanoproai.shop',
        'api.nanoproai.shop',
        'recaptcha.nanoproai.shop'
      ],
      fs: {
        // Allow serving files outside project root for Cloudflare tunnel
        strict: false,
        // Allow access to node_modules for tunnel
        allow: ['D:/get_recapch/server_new/frontend/node_modules']
      },
      // Additional headers for CORS and tunnel support
      cors: true,
      hmr: {
        port: 3000,
        host: 'localhost'
      }
    },
    // Optimize dependencies and disable @fs paths for tunnel compatibility
    optimizeDeps: {
      exclude: ['@vue/devtools-api']
    },
    // Disable @fs paths which cause issues with path-based routing
    resolve: {
      alias: {
        '@': '/src'
      }
    },
    build: {
      rollupOptions: {
        // Ensure no absolute paths in build
        external: []
      }
    }
  }
})