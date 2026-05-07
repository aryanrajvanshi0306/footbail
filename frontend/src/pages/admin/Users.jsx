import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { ChevronLeft, UserPlus } from 'lucide-react';
import { api } from '../../lib/api';

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [filter, setFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ email: '', password: '', name: '', role: 'turf_owner', phone: '' });

  const load = () => {
    const q = filter ? `?role=${filter}` : '';
    api.get(`/admin/users${q}`).then((r) => setUsers(r.data));
  };

  useEffect(() => { load(); }, [filter]);

  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/admin/create-user', form);
      toast.success(`${form.role} created`);
      setShowForm(false);
      setForm({ email: '', password: '', name: '', role: 'turf_owner', phone: '' });
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    }
  };

  return (
    <div className="min-h-screen bg-bg" data-testid="admin-users-page">
      <header className="border-b border-line">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/admin" data-testid="back-to-admin" className="font-mono text-[10px] uppercase tracking-widest text-ink-muted flex items-center gap-1 hover:text-white"><ChevronLeft className="w-3 h-3" /> Control Room</Link>
          <div className="font-display text-2xl tracking-wider">USERS</div>
          <button data-testid="create-user-btn" onClick={() => setShowForm(true)} className="bg-accent-green text-black font-bold px-3 h-9 inline-flex items-center gap-1 font-mono uppercase text-xs tracking-widest hover:bg-[#00C853]">
            <UserPlus className="w-4 h-4" /> Create
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6">
        <div className="flex gap-2 mb-4 flex-wrap" data-testid="user-filters">
          {['', 'player', 'coach', 'referee', 'turf_owner', 'admin'].map((r) => (
            <button key={r} data-testid={`filter-${r || 'all'}`} onClick={() => setFilter(r)} className={`px-3 h-9 font-mono text-[10px] uppercase tracking-widest ${filter === r ? 'bg-accent-green text-black font-bold' : 'border border-line hover:border-accent-green'}`}>
              {r || 'All'}
            </button>
          ))}
        </div>

        <div className="bg-bg-card border border-line overflow-x-auto">
          <table className="w-full font-mono text-sm" data-testid="users-table">
            <thead className="bg-bg-elevated border-b border-line">
              <tr>
                {['Name', 'Role', 'Email', 'Phone', 'Created'].map((h) => (
                  <th key={h} className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-ink-muted">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-line hover:bg-bg-elevated">
                  <td className="px-3 py-2">{u.name}</td>
                  <td className="px-3 py-2"><span className="text-[10px] uppercase tracking-widest" style={{ color: u.role === 'admin' ? '#FF3B30' : u.role === 'referee' ? '#FFCC00' : '#fff' }}>{u.role}</span></td>
                  <td className="px-3 py-2 text-ink-muted">{u.email}</td>
                  <td className="px-3 py-2 text-ink-muted">{u.phone || '—'}</td>
                  <td className="px-3 py-2 text-ink-muted text-xs">{u.created_at?.slice(0, 10)}</td>
                </tr>
              ))}
              {users.length === 0 && <tr><td colSpan={5} className="text-center py-8 text-ink-muted">No users.</td></tr>}
            </tbody>
          </table>
        </div>
      </main>

      {showForm && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" data-testid="create-user-modal">
          <form onSubmit={submit} className="bg-bg-card border border-line w-full max-w-md p-6">
            <div className="font-display text-2xl mb-4">CREATE USER</div>
            <div className="space-y-3">
              <select data-testid="cu-role" value={form.role} onChange={(e) => setForm({...form, role: e.target.value})} className="w-full bg-bg border border-line h-12 px-3 outline-none focus:border-accent-green">
                <option value="turf_owner">Turf Owner</option>
                <option value="referee">Referee</option>
              </select>
              <input data-testid="cu-name" placeholder="Full name" required value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} className="w-full bg-bg border border-line h-12 px-3 outline-none focus:border-accent-green" />
              <input data-testid="cu-email" type="email" placeholder="Email" required value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} className="w-full bg-bg border border-line h-12 px-3 outline-none focus:border-accent-green" />
              <input data-testid="cu-phone" placeholder="Phone (optional)" value={form.phone} onChange={(e) => setForm({...form, phone: e.target.value})} className="w-full bg-bg border border-line h-12 px-3 outline-none focus:border-accent-green" />
              <input data-testid="cu-password" type="password" placeholder="Password (min 4)" required value={form.password} onChange={(e) => setForm({...form, password: e.target.value})} className="w-full bg-bg border border-line h-12 px-3 outline-none focus:border-accent-green" />
            </div>
            <div className="flex gap-2 mt-4">
              <button data-testid="cu-cancel" type="button" onClick={() => setShowForm(false)} className="flex-1 border border-line h-12 font-mono uppercase tracking-widest hover:border-white">Cancel</button>
              <button data-testid="cu-submit" type="submit" className="flex-1 bg-accent-green text-black font-bold h-12 font-display text-xl tracking-widest uppercase hover:bg-[#00C853]">Create</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
