'use client';

import { useEffect, useState } from 'react';
import { Plus, Store, GitMerge } from 'lucide-react';
import { getComercios, createComercio, fusionarComercios } from '@/lib/api';

export default function ComerciosPage() {
  const [comercios, setComercios] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ nombre: '', rubro: '', direccion: '' });
  const [fusionForm, setFusionForm] = useState({ origen: '', destino: '' });

  async function load() {
    try { setComercios(await getComercios()); } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate() {
    if (!form.nombre.trim()) return;
    await createComercio(form);
    setForm({ nombre: '', rubro: '', direccion: '' });
    load();
  }

  async function handleFusion() {
    if (!fusionForm.origen || !fusionForm.destino) return;
    if (!confirm('¿Fusionar comercios?')) return;
    await fusionarComercios(fusionForm.origen, fusionForm.destino);
    setFusionForm({ origen: '', destino: '' });
    load();
  }

  if (loading) {
    return <div className="flex items-center justify-center h-96"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-slate-900">Comercios</h2>
          <p className="text-slate-500 mt-1">Administra los locales donde compras</p>
        </div>
        <button onClick={() => setForm({ ...form, nombre: '' })}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
          <Plus size={18} /> Nuevo Comercio
        </button>
      </div>

      {/* Form crear */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input type="text" placeholder="Nombre" value={form.nombre}
            onChange={(e) => setForm({ ...form, nombre: e.target.value })}
            className="px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-primary-500" />
          <input type="text" placeholder="Rubro (opcional)" value={form.rubro}
            onChange={(e) => setForm({ ...form, rubro: e.target.value })}
            className="px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-primary-500" />
          <input type="text" placeholder="Dirección (opcional)" value={form.direccion}
            onChange={(e) => setForm({ ...form, direccion: e.target.value })}
            className="px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-primary-500" />
          <button onClick={handleCreate} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">Crear</button>
        </div>
      </div>

      {/* Lista */}
      {comercios.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <Store size={48} className="mx-auto text-slate-300 mb-4" />
          <p className="text-slate-500">No hay comercios registrados.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {comercios.filter((c: any) => !c.fusionado_en).map((c: any) => (
            <div key={c.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
              <h3 className="font-semibold text-slate-900">{c.nombre}</h3>
              {c.rubro && <p className="text-sm text-slate-500">{c.rubro}</p>}
              {c.direccion && <p className="text-xs text-slate-400 mt-1">{c.direccion}</p>}
            </div>
          ))}
        </div>
      )}

      {/* Fusión */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <GitMerge size={18} /> Fusionar Comercios
        </h3>
        <div className="flex items-center gap-4">
          <select value={fusionForm.origen}
            onChange={(e) => setFusionForm({ ...fusionForm, origen: e.target.value })}
            className="px-3 py-2 border rounded-lg outline-none flex-1">
            <option value="">Origen...</option>
            {comercios.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
          <span>→</span>
          <select value={fusionForm.destino}
            onChange={(e) => setFusionForm({ ...fusionForm, destino: e.target.value })}
            className="px-3 py-2 border rounded-lg outline-none flex-1">
            <option value="">Destino...</option>
            {comercios.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
          <button onClick={handleFusion} className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700">Fusionar</button>
        </div>
      </div>
    </div>
  );
}
