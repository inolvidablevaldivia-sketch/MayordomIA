'use client';

import { useEffect, useState } from 'react';
import { Plus, Search, Package, GitMerge, Tags } from 'lucide-react';
import { getProductos, createProducto, addAlias, fusionarProductos } from '@/lib/api';

export default function ProductosPage() {
  const [productos, setProductos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [buscar, setBuscar] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ nombre_principal: '', unidad_medida: 'unidad', stock_minimo: 0 });
  const [aliasForm, setAliasForm] = useState<{ [key: string]: string }>({});
  const [fusionForm, setFusionForm] = useState({ origen: '', destino: '' });

  async function load() {
    try {
      const data = await getProductos(buscar || undefined);
      setProductos(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [buscar]);

  async function handleCreate() {
    if (!form.nombre_principal.trim()) return;
    await createProducto(form);
    setForm({ nombre_principal: '', unidad_medida: 'unidad', stock_minimo: 0 });
    setShowForm(false);
    load();
  }

  async function handleAddAlias(id: string) {
    const alias = aliasForm[id];
    if (!alias?.trim()) return;
    await addAlias(id, alias);
    setAliasForm({ ...aliasForm, [id]: '' });
    load();
  }

  async function handleFusion() {
    if (!fusionForm.origen || !fusionForm.destino) return;
    if (!confirm(`¿Fusionar "${fusionForm.origen}" en "${fusionForm.destino}"?`)) return;
    await fusionarProductos(fusionForm.origen, fusionForm.destino);
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
          <h2 className="text-3xl font-bold text-slate-900">Productos</h2>
          <p className="text-slate-500 mt-1">Gestiona tu catálogo de productos, aliases y stock</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus size={18} /> Nuevo Producto
        </button>
      </div>

      {/* Búsqueda */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar producto..."
            value={buscar}
            onChange={(e) => setBuscar(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none"
          />
        </div>
      </div>

      {/* Form crear */}
      {showForm && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="text-lg font-semibold mb-4">Nuevo Producto</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <input type="text" placeholder="Nombre principal" value={form.nombre_principal}
              onChange={(e) => setForm({ ...form, nombre_principal: e.target.value })}
              className="px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-primary-500" />
            <select value={form.unidad_medida}
              onChange={(e) => setForm({ ...form, unidad_medida: e.target.value })}
              className="px-3 py-2 border rounded-lg outline-none">
              <option value="unidad">Unidad</option>
              <option value="kg">Kilogramos</option>
              <option value="g">Gramos</option>
              <option value="litros">Litros</option>
              <option value="ml">Mililitros</option>
              <option value="caja">Caja</option>
            </select>
            <input type="number" placeholder="Stock mínimo" value={form.stock_minimo}
              onChange={(e) => setForm({ ...form, stock_minimo: Number(e.target.value) })}
              className="px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-primary-500" />
            <button onClick={handleCreate} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">Crear</button>
          </div>
        </div>
      )}

      {/* Tabla */}
      {productos.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <Package size={48} className="mx-auto text-slate-300 mb-4" />
          <p className="text-slate-500">No hay productos registrados.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="text-left py-3 px-4 font-medium text-slate-500">Producto</th>
                <th className="text-left py-3 px-4 font-medium text-slate-500">Aliases</th>
                <th className="text-center py-3 px-4 font-medium text-slate-500">Stock</th>
                <th className="text-center py-3 px-4 font-medium text-slate-500">Últ. Precio</th>
                <th className="text-center py-3 px-4 font-medium text-slate-500">Mejor Precio</th>
                <th className="text-center py-3 px-4 font-medium text-slate-500">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {productos.map((p) => (
                <tr key={p.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3 px-4">
                    <p className="font-medium text-slate-900">{p.nombre_principal}</p>
                    <p className="text-xs text-slate-400">{p.unidad_medida}</p>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex flex-wrap gap-1">
                      {p.aliases?.map((a: string) => (
                        <span key={a} className="px-2 py-0.5 bg-primary-50 text-primary-700 rounded text-xs">{a}</span>
                      ))}
                      <div className="flex gap-1 mt-1">
                        <input
                          type="text"
                          placeholder="+ alias"
                          value={aliasForm[p.id] || ''}
                          onChange={(e) => setAliasForm({ ...aliasForm, [p.id]: e.target.value })}
                          className="w-20 px-2 py-0.5 border rounded text-xs outline-none"
                          onKeyDown={(e) => e.key === 'Enter' && handleAddAlias(p.id)}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className={`font-medium ${p.stock_actual <= p.stock_minimo ? 'text-amber-600' : 'text-slate-700'}`}>
                      {p.stock_actual || 0}
                    </span>
                    {p.stock_minimo > 0 && <span className="text-xs text-slate-400">/{p.stock_minimo}</span>}
                  </td>
                  <td className="py-3 px-4 text-center text-slate-600">
                    {p.ultimo_precio ? `$${p.ultimo_precio.toLocaleString('es-CL')}` : '-'}
                  </td>
                  <td className="py-3 px-4 text-center text-green-600 font-medium">
                    {p.mejor_precio_historico ? `$${p.mejor_precio_historico.toLocaleString('es-CL')}` : '-'}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button className="text-xs text-primary-600 hover:underline">Editar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Fusión */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <GitMerge size={18} /> Fusionar Productos
        </h3>
        <div className="flex items-center gap-4">
          <select value={fusionForm.origen}
            onChange={(e) => setFusionForm({ ...fusionForm, origen: e.target.value })}
            className="px-3 py-2 border rounded-lg outline-none flex-1">
            <option value="">Seleccionar origen...</option>
            {productos.map(p => <option key={p.id} value={p.id}>{p.nombre_principal}</option>)}
          </select>
          <span className="text-slate-400">→</span>
          <select value={fusionForm.destino}
            onChange={(e) => setFusionForm({ ...fusionForm, destino: e.target.value })}
            className="px-3 py-2 border rounded-lg outline-none flex-1">
            <option value="">Seleccionar destino...</option>
            {productos.map(p => <option key={p.id} value={p.id}>{p.nombre_principal}</option>)}
          </select>
          <button onClick={handleFusion}
            className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700">
            Fusionar
          </button>
        </div>
      </div>
    </div>
  );
}
