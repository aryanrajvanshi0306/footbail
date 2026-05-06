import React from 'react';
import { TIER_CLASSES } from '../lib/constants';

/**
 * FIFA-style Player Card
 * Props: overall, position, name, attributes {pac,sho,pas,dri,def,phy}, tier, avatarLetter
 */
export default function FIFACard({ overall = 74, position = 'CM', name = 'Arjun', attributes = {}, tier = 'silver', size = 'md' }) {
  const attrs = { pac: 76, sho: 71, pas: 79, dri: 74, def: 68, phy: 77, ...(attributes || {}) };
  const cls = TIER_CLASSES[tier] || TIER_CLASSES.silver;
  const sizes = {
    sm: 'w-36 aspect-[2/3] p-3',
    md: 'w-48 aspect-[2/3] p-4',
    lg: 'w-64 aspect-[2/3] p-5',
  };
  return (
    <div
      data-testid="fifa-card"
      className={`relative overflow-hidden ${cls} ${sizes[size]} border border-black/20`}
    >
      {/* shine overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/10 via-transparent to-black/20 pointer-events-none" />
      <div className="relative flex justify-between items-start">
        <div>
          <div className="font-display text-5xl leading-none tracking-tighter" data-testid="card-overall">{overall}</div>
          <div className="font-mono font-bold text-xs tracking-widest opacity-80" data-testid="card-position">{position}</div>
        </div>
        <div className="font-mono text-[10px] uppercase tracking-widest opacity-70">{tier}</div>
      </div>
      <div className="relative my-2 flex items-center justify-center">
        <div className="w-16 h-16 rounded-full bg-black/25 flex items-center justify-center font-display text-3xl leading-none">
          {(name?.[0] || 'A').toUpperCase()}
        </div>
      </div>
      <div className="relative text-center font-display tracking-widest text-sm truncate" data-testid="card-name">
        {name?.toUpperCase?.()}
      </div>
      <div className="relative grid grid-cols-3 gap-x-2 gap-y-1 mt-3 font-mono text-[10px]">
        <div><b className="text-sm">{attrs.pac}</b> PAC</div>
        <div><b className="text-sm">{attrs.sho}</b> SHO</div>
        <div><b className="text-sm">{attrs.pas}</b> PAS</div>
        <div><b className="text-sm">{attrs.dri}</b> DRI</div>
        <div><b className="text-sm">{attrs.def}</b> DEF</div>
        <div><b className="text-sm">{attrs.phy}</b> PHY</div>
      </div>
    </div>
  );
}
