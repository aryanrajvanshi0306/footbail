import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { ChevronLeft, Plus } from 'lucide-react';
import { api } from '../../lib/api';
import { fmtINR } from '../../lib/constants';

export default function AdminTurfs() {
  const [turfs, setTurfs] = useState([]);
  const [owners, setOwners] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', city: 'Mumbai', address: '', price_per_slot: 120000, owner_id: '' });

  const load = () => {
    api.get('/turfs').then((r) => setTurfs(r.data));
    api.get('/admin/users?role=turf_owner').then((r) => setOwners(r.data));
  };
  useEffect(() => { load(); }, []);

  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/turfs', form);
      toast.success('Turf added');
      setShowForm(false);
      setForm({ name: '', city: 'Mumbai', address: '', price_per_slot: 120000, owner_id: '' });
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    }
  };

  return (
    <div className="min-h-screen bg-bg" data-testid="admin-turfs-page">
      <header className="border-b border-line">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/admin" className="font-mono text-[10px] uppercase tracking-widest text-ink-muted flex items-center gap-1 hover:text-white" data-testid="back-to-admin"><ChevronLeft className="w-3 h-3" /> Control Room</Link>
          <div className="font-display text-2xl tracking-wider">TURFS</div>
          <button data-testid="add-turf-btn" onClick={() => setShowForm(true)} className="bg-accent-green text-black font-bold px-3 h-9 inline-flex items-center gap-1 font-mono uppercase text-xs tracking-widest hover:bg-[#00C853]">
            <Plus className="w-4 h-4" /> Add Turf
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6 grid md:grid-cols-2 gap-3">
        {turfs.map((t) => (
          <div key={t.id} className="bg-bg-card border border-line overflow-hidden">
            <div className="h-32 bg-cover bg-center" style={{ backgroundImage: `url(${t.image})` }} />
            <div className="p-4">
              <div className="font-display text-xl">{t.name.toUpperCase()}</div>
              <div className="font-mono text-[10px] uppercase tracking-widest text-ink-muted">{t.city} · {t.address}</div>
              <div className="flex justify-between mt-3">
                <span className="font-mono text-xs">★ {t.rating}</span>
                <span className="font-mono font-bold">{fmtINR(t.price_per_slot)}</span>
              </div>
            </div>
          </div>
        ))}
      </main>

      {showForm && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" data-testid="add-turf-modal">
          <form onSubmit={submit} className="bg-bg-card border border-line w-full max-w-md p-6 space-y-3">
            <div className="font-display text-2xl">ADD TURF</div>
            <input data-testid="t-name" placeholder="Name" required value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} className="w-full bg-bg border border-line h-12 px-3 outline-none focus:border-accent-green" />
            <input data-testid="t-city" placeholder="City" required value={form.city} onChange={(e) => setForm({...form, city: e.target.value})} className="w-full bg-bg border border-line h-12 px-3 outline-none focus:border-accent-green" />
            <input data-testid="t-addr" placeholder="Address" required value={form.address} onChange={(e) => setForm({...form, address: e.target.value})} className="w-full bg-bg border border-line h-12 px-3 outline-none focus:border-accent-green" />
            <input data-testid="t-price" type="number" placeholder="Price per slot (paise)" required value={form.price_per_slot} onChange={(e) => setForm({...form, price_per_slot: parseInt(e.target.value || 0)})} className="w-full bg-bg border border-line h-12 px-3 outline-none focus:border-accent-green" />
            <select data-testid="t-owner" value={form.owner_id} onChange={(e) => setForm({...form, owner_id: e.target.value})} className="w-full bg-bg border border-line h-12 px-3 outline-none focus:border-accent-green">
              <option value="">— Owner (optional, defaults to admin) —</option>
              {owners.map((o) => <option key={o.id} value={o.id}>{o.name} · {o.email}</option>)}
            </select>
            <div className="flex gap-2 pt-2">
              <button data-testid="t-cancel" type="button" onClick={() => setShowForm(false)} className="flex-1 border border-line h-12 font-mono uppercase tracking-widest hover:border-white">Cancel</button>
              <button data-testid="t-submit" type="submit" className="flex-1 bg-accent-green text-black font-bold h-12 font-display text-xl tracking-widest uppercase hover:bg-[#00C853]">Save</button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
