/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}', './public/index.html'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Layered dark navy (spec-exact)
        bg: {
          DEFAULT: '#0A0F1E',
          surface: '#111827',
          card: '#1C2333',
          elevated: '#243046',
          var: '#050810',
        },
        // Accents per spec
        accent: {
          green: '#00E676',   // primary CTA, LIVE, FAB, wallet
          blue:  '#38BDF8',   // links, coach, verified
          amber: '#FFB830',   // warnings, referee, XP, challenges
          red:   '#FF4D4D',   // errors, red cards
          purple:'#A78BFA',   // AI, OYP, analysis
          gold:  '#F59E0B',   // MOTM, achievements, leaderboard #1
        },
        // Back-compat aliases so existing JSX doesn't break
        brand: {
          primary:  '#00E676',   // was red; now green (primary CTA)
          secondary:'#38BDF8',   // was blue
          accent:   '#FFB830',   // was neon yellow; now amber (XP, highlights)
        },
        ink: {
          DEFAULT: '#F1F5F9',
          muted:   '#94A3B8',
          dim:     '#475569',
        },
        line: {
          DEFAULT: 'rgba(255,255,255,0.08)',
          strong:  'rgba(255,255,255,0.16)',
        },
        status: { success: '#00E676', warning: '#FFB830', danger: '#FF4D4D', info: '#38BDF8' },
      },
      fontFamily: {
        display: ['"DM Sans"', 'sans-serif'],   // 600/700 for display
        body:    ['"DM Sans"', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '12px',
        sm: '8px',
        md: '12px',
        lg: '16px',
        xl: '20px',
        full: '9999px',
      },
      boxShadow: {
        'card': '0 1px 0 rgba(255,255,255,0.04) inset, 0 8px 24px rgba(0,0,0,0.35)',
        'glow-green':  '0 0 0 1px #00E676, 0 0 24px rgba(0,230,118,0.35)',
        'glow-amber':  '0 0 0 1px #FFB830, 0 0 20px rgba(255,184,48,0.35)',
        'glow-purple': '0 0 0 1px #A78BFA, 0 0 20px rgba(167,139,250,0.35)',
        'glow-red':    '0 0 0 1px #FF4D4D, 0 0 20px rgba(255,77,77,0.4)',
        'city':        '0 0 0 1px var(--city-accent), 0 0 24px color-mix(in srgb, var(--city-accent) 40%, transparent)',
      },
      keyframes: {
        'slide-up':   { '0%': { transform: 'translateY(12px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
        'pulse-live': { '0%,100%': { boxShadow: '0 0 0 0 rgba(0,230,118,0.7)' }, '50%': { boxShadow: '0 0 0 10px rgba(0,230,118,0)' } },
        'pulse-red':  { '0%,100%': { boxShadow: '0 0 0 0 rgba(255,77,77,0.7)' }, '50%': { boxShadow: '0 0 0 10px rgba(255,77,77,0)' } },
        'scan':       { '0%': { transform: 'translateY(-100%)' }, '100%': { transform: 'translateY(100%)' } },
        'count-up':   { '0%': { transform: 'translateY(8px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
        'city-shine': { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
      },
      animation: {
        'slide-up':   'slide-up 300ms ease-out',
        'pulse-live': 'pulse-live 2s infinite',
        'pulse-red':  'pulse-red 2s infinite',
        'scan':       'scan 3s linear infinite',
        'count-up':   'count-up 400ms ease-out',
        'city-shine': 'city-shine 6s linear infinite',
      },
    },
  },
  plugins: [],
};
