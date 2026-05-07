/**
 * City Anime Theming System
 * - NEVER names the anime
 * - NEVER uses character names
 * - Exposes CSS --city-accent + --city-pattern (SVG data URI)
 * - Push copy uses coded language
 */

// SVG data-URI helper
const svgDataURI = (svg) => `url("data:image/svg+xml,${encodeURIComponent(svg)}")`;

// Each city: { accent, pattern (tile SVG), pushPrefix (city-coded language), subtitle }
export const CITY_THEMES = {
  Mumbai: {
    accent: '#F5A623',
    subtitle: 'Straw Hat City',
    pushPrefix: 'Set sail, captain —',
    pattern: svgDataURI(`<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120' width='120' height='120'>
      <g fill='none' stroke='%23F5A623' stroke-width='1.2' stroke-linecap='round' opacity='0.9'>
        <path d='M0 60 Q 20 48, 40 60 T 80 60 T 120 60'/>
        <path d='M0 80 Q 20 68, 40 80 T 80 80 T 120 80'/>
        <path d='M0 40 Q 20 28, 40 40 T 80 40 T 120 40'/>
      </g>
    </svg>`),
  },
  Delhi: {
    accent: '#FF6B00',
    subtitle: 'Hidden Leaf',
    pushPrefix: 'Mission briefing —',
    pattern: svgDataURI(`<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120' width='120' height='120'>
      <g fill='%23FF6B00' opacity='0.9'>
        <polygon points='60,22 66,48 92,48 70,62 78,88 60,72 42,88 50,62 28,48 54,48'/>
      </g>
    </svg>`),
  },
  Bangalore: {
    accent: '#00C853',
    subtitle: 'Plus Ultra',
    pushPrefix: 'Go beyond —',
    pattern: svgDataURI(`<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120' width='120' height='120'>
      <g stroke='%2300C853' stroke-width='1' fill='none' opacity='0.95'>
        <circle cx='30' cy='30' r='3' fill='%2300C853'/>
        <circle cx='90' cy='30' r='3' fill='%2300C853'/>
        <circle cx='30' cy='90' r='3' fill='%2300C853'/>
        <circle cx='90' cy='90' r='3' fill='%2300C853'/>
        <circle cx='60' cy='60' r='3' fill='%2300C853'/>
        <path d='M30 30 L60 60 L90 30 M30 90 L60 60 L90 90 M30 30 L30 90 M90 30 L90 90'/>
      </g>
    </svg>`),
  },
  Kolkata: {
    accent: '#7C3AED',
    subtitle: 'Cursed City',
    pushPrefix: 'The pact is sealed —',
    pattern: svgDataURI(`<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120' width='120' height='120'>
      <g fill='none' stroke='%237C3AED' stroke-width='1.3' opacity='0.95'>
        <ellipse cx='60' cy='60' rx='26' ry='10'/>
        <circle cx='60' cy='60' r='4' fill='%237C3AED'/>
        <path d='M20 60 Q40 40, 60 60 Q 80 80, 100 60'/>
      </g>
    </svg>`),
  },
  Chennai: {
    accent: '#FFD600',
    subtitle: 'Power Spark',
    pushPrefix: 'Power level rising —',
    pattern: svgDataURI(`<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120' width='120' height='120'>
      <g fill='%23FFD600' opacity='0.95'>
        <polygon points='60,30 64,54 88,50 70,68 86,90 60,78 34,90 50,68 32,50 56,54'/>
      </g>
    </svg>`),
  },
  Hyderabad: {
    accent: '#00897B',
    subtitle: 'The Wall',
    pushPrefix: 'Hold the line —',
    pattern: svgDataURI(`<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120' width='120' height='120'>
      <g fill='none' stroke='%2300897B' stroke-width='1.5' opacity='0.95'>
        <rect x='12' y='24' width='24' height='18'/>
        <rect x='44' y='24' width='24' height='18'/>
        <rect x='76' y='24' width='24' height='18'/>
        <rect x='28' y='50' width='24' height='18'/>
        <rect x='60' y='50' width='24' height='18'/>
        <rect x='12' y='76' width='24' height='18'/>
        <rect x='44' y='76' width='24' height='18'/>
        <rect x='76' y='76' width='24' height='18'/>
      </g>
    </svg>`),
  },
  Pune: {
    accent: '#E91E63',
    subtitle: 'Breath of Flame',
    pushPrefix: 'Steady your breathing —',
    pattern: svgDataURI(`<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120' width='120' height='120'>
      <g fill='%23E91E63' opacity='0.9'>
        <path d='M30 20 Q 38 30, 30 44 Q 22 30, 30 20 Z'/>
        <path d='M80 60 Q 88 70, 80 84 Q 72 70, 80 60 Z'/>
        <path d='M50 80 Q 58 92, 50 104 Q 42 92, 50 80 Z'/>
      </g>
    </svg>`),
  },
  Kochi: {
    accent: '#FFEB3B',
    subtitle: 'Gotta Catch',
    pushPrefix: 'A challenger appears —',
    pattern: svgDataURI(`<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 120' width='120' height='120'>
      <g fill='none' stroke='%23FFEB3B' stroke-width='1.8' opacity='0.95'>
        <circle cx='60' cy='60' r='26'/>
        <path d='M34 60 h52'/>
        <circle cx='60' cy='60' r='6' fill='%23FFEB3B'/>
      </g>
    </svg>`),
  },
};

export const DEFAULT_CITY = 'Mumbai';

export function getCityTheme(city) {
  return CITY_THEMES[city] || CITY_THEMES[DEFAULT_CITY];
}

/**
 * Apply city theme to :root as CSS vars.
 * Pass null/undefined to reset to Mumbai default.
 */
export function applyCityTheme(city) {
  const theme = getCityTheme(city);
  const root = document.documentElement;
  root.style.setProperty('--city-accent', theme.accent);
  root.style.setProperty('--city-pattern', theme.pattern);
  root.dataset.city = city || DEFAULT_CITY;
}
