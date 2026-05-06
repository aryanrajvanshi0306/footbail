import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { api } from '../lib/api';
import { PostCard } from './Home';

export default function Feed() {
  const [posts, setPosts] = useState([]);
  const load = () => api.get('/posts').then((r) => setPosts(r.data));
  useEffect(() => { load(); }, []);
  const react = async (id, type) => {
    await api.post(`/posts/${id}/react`, { reaction: type });
    load();
  };

  return (
    <div className="px-4 pt-4 pb-24" data-testid="feed-page">
      <div>
        <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">Football Native</div>
        <div className="font-display text-3xl">FEED</div>
      </div>

      <div className="flex gap-2 mt-3 mb-4 overflow-x-auto" data-testid="feed-filters">
        {['All', 'Friends', 'My City', 'My Turfs', 'AI Insights'].map((f) => (
          <button key={f} className="px-3 py-1.5 border border-line font-mono text-[10px] uppercase tracking-widest hover:border-brand-primary whitespace-nowrap">
            {f}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {posts.length === 0 && <div className="text-ink-muted text-sm py-12 text-center">No posts yet.</div>}
        {posts.map((p) => <PostCard key={p.id} p={p} onReact={react} />)}
      </div>
    </div>
  );
}
