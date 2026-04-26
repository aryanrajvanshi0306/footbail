import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icons/*.png", "icons/*.svg"],
      manifest: false, // We manage our own /public/manifest.json
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,png,svg,woff2}"],
        runtimeCaching: [
          {
            // API calls — network-first, fallback to cache
            urlPattern: ({ url }) => url.pathname.startsWith("/auth") ||
              url.pathname.startsWith("/matches") ||
              url.pathname.startsWith("/players") ||
              url.pathname.startsWith("/footage"),
            handler: "NetworkFirst",
            options: {
              cacheName: "footbail-api-cache",
              expiration: { maxEntries: 100, maxAgeSeconds: 300 },
            },
          },
          {
            // HLS video segments — cache-first for offline replay
            urlPattern: /\.m3u8$|\.ts$/,
            handler: "CacheFirst",
            options: {
              cacheName: "footbail-video-cache",
              expiration: { maxEntries: 50, maxAgeSeconds: 86400 },
            },
          },
          {
            // Static assets — stale while revalidate
            urlPattern: /\.(js|css|woff2|png|svg|ico)$/,
            handler: "StaleWhileRevalidate",
            options: { cacheName: "footbail-static-cache" },
          },
        ],
      },
    }),
  ],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/auth": { target: "http://api:8000", changeOrigin: true },
      "/matches": { target: "http://api:8000", changeOrigin: true },
      "/players": { target: "http://api:8000", changeOrigin: true },
      "/footage": { target: "http://api:8000", changeOrigin: true },
      "/coaches": { target: "http://api:8000", changeOrigin: true },
      "/referees": { target: "http://api:8000", changeOrigin: true },
      "/admin": { target: "http://api:8000", changeOrigin: true },
      "/health": { target: "http://api:8000", changeOrigin: true },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
          query: ["@tanstack/react-query"],
          ui: ["lucide-react"],
        },
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/tests/setup.ts",
    coverage: { reporter: ["text", "lcov"] },
  },
});
