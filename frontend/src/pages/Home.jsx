import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Plus, Send } from 'lucide-react';
import { api, getUser } from '../lib/api';
import { REACTION_LABELS, fmtRelative } from '../lib/constants';
import FIFACard from '../components/FIFACard';
import LFGWidget from '../components/LFGWidget';

export default function Home() {
  const me = getUser();
  const nav = useNavigate();
  const [posts, setPosts] = useState([]);
  const [text, setText] = useState('');
  const [profile, setProfile] = useState(me);

  const loadPosts = async () => {
    const r = await api.get('/posts');
    setPosts(r.data);
  };

  useEffect(() => { loadPosts(); api.get('/auth/me').then((r) => setProfile(r.data)).catch(() => {}); }, []);

  const send = async () => {
    if (!text.trim()) return;
    await api.post('/posts', { content: text });
    setText('');
    toast.success('Posted to feed');
    loadPosts();
  };

  const react = async (id, type) => {
    await api.post(`/posts/${id}/react`, { reaction: type });
    loadPosts();
  };

  return (
    <div className="pb-24" data-testid="home-page">
      {/* Greeting + card */}
      <div className="px-4 pt-4">
        <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">Good evening</div>
        <div className="font-display text-3xl">{(profile?.name || 'PLAYER').toUpperCase()} 👋</div>
      </div>

      {profile?.role === 'player' && (
        <div className="mx-4 mt-4 bg-bg-card border border-line p-4 grid grid-cols-[auto_1fr] gap-4 items-center" data-testid="home-card-block">
          <FIFACard
            overall={profile.overall || 74}
            position={profile.position || 'CM'}
            name={profile.name?.split(' ')[0]}
            attributes={profile.attributes}
            tier={profile.card_tier || 'silver'}
            size="sm"
          />
          <div>
            <div className="font-display text-2xl leading-none">{profile.name?.toUpperCase()}</div>
            <div className="font-mono text-xs text-accent-amber uppercase tracking-widest">{profile.position} · OYP {profile.card_tier?.toUpperCase()}</div>
            <div className="mt-3 font-mono text-xs text-ink-muted">XP {profile.xp || 0} / {profile.xp_to_next || 1000}</div>
            <div className="h-1.5 bg-line mt-1 relative">
              <div className="absolute left-0 top-0 bottom-0 bg-brand-accent" style={{ width: `${Math.min(100, ((profile.xp || 0) / (profile.xp_to_next || 1000)) * 100)}%` }} />
            </div>
            <div className="grid grid-cols-2 gap-2 mt-3">
              <Stat label="Matches" value={profile.stats?.matches ?? 0} />
              <Stat label="Goals" value={profile.stats?.goals ?? 0} />
              <Stat label="Assists" value={profile.stats?.assists ?? 0} />
              <Stat label="Streak 🔥" value={profile.stats?.streak ?? 0} />
            </div>
          </div>
        </div>
      )}

      {/* LFG Widget */}
      <div className="mx-4 mt-4">
        <LFGWidget />
      </div>

      {/* Composer */}
      <div className="mx-4 mt-6 bg-bg-card border border-line" data-testid="post-composer">
        <textarea
          data-testid="post-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="What's the score on the pitch today?"
          className="w-full bg-transparent p-4 text-white outline-none resize-none min-h-[80px]"
        />
        <div className="flex justify-between items-center px-4 py-2 border-t border-line">
          <div className="font-mono text-[10px] text-ink-muted uppercase tracking-widest">{text.length}/280</div>
          <button
            data-testid="post-submit-btn"
            onClick={send}
            disabled={!text.trim()}
            className="flex items-center gap-2 bg-accent-green text-black font-bold px-4 h-9 font-mono uppercase tracking-widest text-xs disabled:opacity-40 hover:bg-[#00C853]"
          >
            <Send className="w-3.5 h-3.5" /> Post
          </button>
        </div>
      </div>

      {/* Feed */}
      <div className="mt-6 space-y-3 px-4" data-testid="home-feed">
        <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">SOCIAL FEED</div>
        {posts.length === 0 && <div className="text-center text-ink-muted py-12">No posts yet. Be first.</div>}
        {posts.map((p) => (
          <PostCard key={p.id} p={p} onReact={react} />
        ))}
      </div>

      {/* FAB */}
      <button
        data-testid="fab-create-match"
        onClick={() => nav('/matches/create')}
        className="fixed bottom-24 right-6 w-14 h-14 bg-accent-green text-black font-bold flex items-center justify-center shadow-glow-red hover:bg-[#00C853] z-30"
      >
        <Plus className="w-6 h-6" strokeWidth={2.5} />
      </button>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-bg-elevated border border-line p-2">
      <div className="font-mono text-[9px] uppercase tracking-widest text-ink-muted">{label}</div>
      <div className="font-mono font-bold text-base">{value}</div>
    </div>
  );
}

export function PostCard({ p, onReact }) {
  return (
    <div className="bg-bg-card border border-line p-4" data-testid={`post-${p.id}`}>
      <div className="flex items-center gap-3 mb-2">
        <div className="w-9 h-9 rounded-full bg-bg-elevated border border-line flex items-center justify-center font-display text-lg">
          {p.user_name?.[0]?.toUpperCase()}
        </div>
        <div className="flex-1">
          <div className="font-bold text-sm">{p.user_name}</div>
          <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">
            {p.user_position || 'Player'} · {fmtRelative(p.created_at)}
          </div>
        </div>
        {p.user_tier && (
          <div className={`text-[10px] font-mono uppercase tracking-widest px-2 py-1 ${p.user_tier === 'gold' ? 'bg-yellow-600 text-black' : p.user_tier === 'silver' ? 'bg-zinc-300 text-black' : 'bg-amber-800 text-white'}`}>
            {p.user_tier}
          </div>
        )}
      </div>
      <div className="text-base whitespace-pre-wrap">{p.content}</div>
      <div className="flex gap-1 mt-3 flex-wrap">
        {Object.entries(REACTION_LABELS).map(([k, m]) => (
          <button
            key={k}
            data-testid={`react-${k}-${p.id}`}
            onClick={() => onReact(p.id, k)}
            className="flex items-center gap-1 px-2 py-1 border border-line hover:border-accent-green text-xs font-mono"
          >
            <span>{m.icon}</span>
            <span>{p.reactions?.[k] || 0}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
