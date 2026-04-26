import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        g: "#00ff88",       // footbAIl green
        gb: "#00cc6a",      // green dark
        surface: "#13131a",
        card: "#1a1a26",
        border: "#2a2a3d",
        muted: "#6b7280",
        danger: "#ef4444",
        warning: "#f59e0b",
        info: "#3b82f6",
      },
      fontFamily: {
        sans: ["'Inter'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      animation: {
        "pulse-g": "pulse-g 2s ease-in-out infinite",
        "slide-up": "slide-up 0.3s ease-out",
        "fade-in": "fade-in 0.4s ease-out",
      },
      keyframes: {
        "pulse-g": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(16px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
      },
      backgroundImage: {
        "hero-gradient": "linear-gradient(135deg, #0a0a0f 0%, #111122 50%, #0d1a0d 100%)",
        "card-gradient": "linear-gradient(135deg, #1a1a26 0%, #13131a 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
