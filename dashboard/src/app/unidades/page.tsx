'use client';

import { useEffect, useState } from 'react';
import { Plus, Archive, Edit3, Building2 } from 'lucide-react';
import { getUnidades, createUnidad, archiveUnidad } from '@/lib/api';

export default function UnidadesPage() {
  const [unidades, setUnidades] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ nombre: '', descripcion: '', color: '#4F46E5' });

  async function load() {
    try {
      const data = await getUnidades(true);
      setUnidades(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate() {
    if (!form.nombre.trim()) return;
    await createUnidad(form);
    setForm({ nombre: '', descripcion: '', color: '#4F46E5' });
    setShowForm(false);
    load();
  }

  async function handleArchive(id: string) {
    if (!confirm('¿Archivar esta unidad?')) return;
    await archiveUnidad(id);
    load();
  }

  if (loading) {
    return <div className="flex items-center justify-center h-96"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-slate-900">Unidades</h2>
          <p className="text-slate-500 mt-1">Administra tus actividades económicas</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus size={18} />
          Nueva Unidad
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="text-lg font-semibold mb-4">Nueva Unidad</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input
              type="text"
              placeholder="Nombre (ej: Delirio de Cacao)"
              value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              className="px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
            <input
              type="text"
              placeholder="Descripción"
              value={form.descripcion}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
              className="px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={form.color}
                onChange={(e) => setForm({ ...form, color: e.target.value })}
                className="h-10 w-16 rounded border cursor-pointer"
              />
              <button
                onClick={handleCreate}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                Crear
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Lista */}
      {unidades.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <Building2 size={48} className="mx-auto text-slate-300 mb-4" />
          <p className="text-slate-500">No tienes Unidades creadas aún.</p>
          <p className="text-sm text-slate-400 mt-1">
            Una Unidad representa un emprendimiento o actividad económica.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {unidades.map((u) => (
            <div key={u.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-lg"
                    style={{ backgroundColor: u.color || '#4F46E5' }}
                  >
                    {u.nombre.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">{u.nombre}</h3>
                    {u.descripcion && <p className="text-sm text-slate-500">{u.descripcion}</p>}
                  </div>
                </div>
                <div className="flex gap-1">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    u.estado === 'activa' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'
                  }`}>
                    {u.estado}
                  </span>
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                <button className="flex items-center gap-1 text-xs text-slate-500 hover:text-primary-600">
                  <Edit3 size={14} /> Editar
                </button>
                <button
                  onClick={() => handleArchive(u.id)}
                  className="flex items-center gap-1 text-xs text-slate-500 hover:text-red-600"
                >
                  <Archive size={14} /> Archivar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
