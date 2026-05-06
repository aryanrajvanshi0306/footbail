/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}', './public/index.html'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: { DEFAULT: '#050505', card: '#111111', elevated: '#1A1A1A', var: '#000000' },
        brand: { primary: '#FF3B30', secondary: '#007AFF', accent: '#E6FF00' },
        ink: { DEFAULT: '#FFFFFF', muted: '#A1A1A1', dim: '#737373' },
        line: { DEFAULT: '#262626', soft: '#1A1A1A' },
        status: { success: '#34C759', warning: '#FFCC00', danger: '#FF3B30', info: '#32ADE6' },
      },
      fontFamily: {
        display: ['"Bebas Neue"', 'sans-serif'],
        body: ['"DM Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: { DEFAULT: '0px', sm: '0px', md: '0px', lg: '0px', full: '9999px' },
      boxShadow: {
        'hard': '4px 4px 0 rgba(0,0,0,0.4)',
        'glow-red': '0 0 20px rgba(255,59,48,0.5)',
        'glow-yellow': '0 0 20px rgba(230,255,0,0.4)',
      },
      keyframes: {
        'slide-up': { '0%': { transform: 'translateY(20px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
        'pulse-red': { '0%,100%': { boxShadow: '0 0 0 0 rgba(255,59,48,0.7)' }, '50%': { boxShadow: '0 0 0 12px rgba(255,59,48,0)' } },
        'scan': { '0%': { transform: 'translateY(-100%)' }, '100%': { transform: 'translateY(100%)' } },
        'count-up': { '0%': { transform: 'translateY(10px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
      },
      animation: {
        'slide-up': 'slide-up 300ms ease-out',
        'pulse-red': 'pulse-red 2s infinite',
        'scan': 'scan 3s linear infinite',
        'count-up': 'count-up 400ms ease-out',
      },
    },
  },
  plugins: [],
};
