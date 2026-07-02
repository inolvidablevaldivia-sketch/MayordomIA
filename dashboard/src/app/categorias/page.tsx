'use client';

import { useEffect, useState } from 'react';
import { Plus, Tags, X } from 'lucide-react';
import { getUnidades } from '@/lib/api';

export default function CategoriasPage() {
  const [unidades, setUnidades] = useState<any[]>([]);
  const [categorias, setCategorias] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ nombre: '', unidad_id: '', tipo: 'gasto', parent_id: '' });

  async function load() {
    try {
      const unids = await getUnidades(true);
      setUnidades(unids);
      // Cargar categorías
      const res = await fetch('/api/categorias');
      if (res.ok) setCategorias(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate() {
    if (!form.nombre.trim() || !form.unidad_id) return;
    const res = await fetch('/api/categorias', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nombre: form.nombre,
        unidad_id: form.unidad_id,
        tipo: form.tipo,
        parent_id: form.parent_id || null,
      }),
    });
    if (res.ok) {
      setForm({ nombre: '', unidad_id: '', tipo: 'gasto', parent_id: '' });
      setShowForm(false);
      load();
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-96"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-slate-900">Categorías</h2>
          <p className="text-slate-500 mt-1">Administra las categorías de gastos e ingresos por Unidad</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus size={18} /> Nueva Categoría
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Nueva Categoría</h3>
            <button onClick={() => setShowForm(false)} className="text-slate-400 hover:text-slate-600">
              <X size={20} />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <input
              type="text" placeholder="Nombre (ej: Insumos)"
              value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              className="px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-primary-500"
            />
            <select
              value={form.unidad_id}
              onChange={(e) => setForm({ ...form, unidad_id: e.target.value })}
              className="px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Seleccionar Unidad</option>
              {unidades.map((u) => (
                <option key={u.id} value={u.id}>{u.nombre}</option>
              ))}
            </select>
            <select
              value={form.tipo}
              onChange={(e) => setForm({ ...form, tipo: e.target.value })}
              className="px-3 py-2 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="gasto">💸 Gasto</option>
              <option value="ingreso">💰 Ingreso</option>
            </select>
            <button
              onClick={handleCreate}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium"
            >
              Crear Categoría
            </button>
          </div>
        </div>
      )}

      {/* Lista por Unidad */}
      {unidades.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <Tags size={48} className="mx-auto text-slate-300 mb-4" />
          <p className="text-slate-500">Crea una Unidad primero para poder agregar categorías.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {unidades.map((u) => {
            const catsDeUnidad = categorias.filter((c: any) => c.unidad_id === u.id);
            const gastos = catsDeUnidad.filter((c: any) => c.tipo === 'gasto');
            const ingresos = catsDeUnidad.filter((c: any) => c.tipo === 'ingreso');

            return (
              <div key={u.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                <div className="flex items-center gap-3 mb-4">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm"
                    style={{ backgroundColor: u.color || '#4F46E5' }}
                  >
                    {u.nombre.charAt(0).toUpperCase()}
                  </div>
                  <h3 className="font-semibold text-slate-900">{u.nombre}</h3>
                  <span className="text-xs text-slate-400">({catsDeUnidad.length} categorías)</span>
                </div>

                {catsDeUnidad.length === 0 ? (
                  <p className="text-sm text-slate-400 italic">Sin categorías aún. Crea una arriba ↑</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {gastos.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-red-500 uppercase mb-2">💸 Gastos</p>
                        <div className="space-y-1">
                          {gastos.map((c: any) => (
                            <div key={c.id} className="flex items-center justify-between text-sm px-3 py-2 bg-red-50 rounded-lg">
                              <span className="text-slate-700">{c.nombre}</span>
                              <span className="text-xs text-slate-400">
                                {c.parent_id ? 'Subcategoría' : 'Principal'}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {ingresos.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-green-500 uppercase mb-2">💰 Ingresos</p>
                        <div className="space-y-1">
                          {ingresos.map((c: any) => (
                            <div key={c.id} className="flex items-center justify-between text-sm px-3 py-2 bg-green-50 rounded-lg">
                              <span className="text-slate-700">{c.nombre}</span>
                              <span className="text-xs text-slate-400">
                                {c.parent_id ? 'Subcategoría' : 'Principal'}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
