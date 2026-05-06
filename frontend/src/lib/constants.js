export const TIER_CLASSES = {
  bronze: 'bg-gradient-to-br from-[#8C5A40] via-[#C89B7B] to-[#5C3622] text-[#FFE8D6]',
  silver: 'bg-gradient-to-br from-[#A6A6A6] via-[#E6E6E6] to-[#737373] text-[#0a0a0a]',
  gold: 'bg-gradient-to-br from-[#B38C00] via-[#FFD700] to-[#806400] text-[#1a1200]',
  toty: 'bg-gradient-to-br from-[#00E5FF] via-[#0055FF] to-[#001133] border-2 border-[#00E5FF] text-white',
};

export const REACTION_LABELS = {
  boot: { icon: '👟', label: 'Boot' },
  gloves: { icon: '🧤', label: 'Save' },
  whistle: { icon: '📣', label: 'Ref' },
  fire: { icon: '🔥', label: 'Fire' },
  hundred: { icon: '💯', label: '100' },
};

export const EVENT_META = {
  kickoff:       { label: 'KICKOFF',      color: '#32ADE6', icon: '▶' },
  goal:          { label: 'GOAL',         color: '#34C759', icon: '⚽' },
  foul:          { label: 'FOUL',         color: '#FFCC00', icon: '!' },
  yellow_card:   { label: 'YELLOW CARD',  color: '#FFCC00', icon: '▮' },
  red_card:      { label: 'RED CARD',     color: '#FF3B30', icon: '▮' },
  offside:       { label: 'OFFSIDE',      color: '#FF3B30', icon: '⚑' },
  onside:        { label: 'ONSIDE',       color: '#34C759', icon: '✓' },
  substitution:  { label: 'SUBSTITUTION', color: '#A1A1A1', icon: '↔' },
  complete:      { label: 'FULL TIME',    color: '#FFFFFF', icon: '■' },
  camera_on:     { label: 'CAMERA ON',    color: '#FF3B30', icon: '◉' },
  camera_off:    { label: 'CAMERA OFF',   color: '#737373', icon: '◌' },
};

export const fmtINR = (paise) => {
  if (paise == null) return '—';
  const rupees = paise / 100;
  return '₹' + rupees.toLocaleString('en-IN');
};

export const fmtRelative = (iso) => {
  if (!iso) return '';
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
};
