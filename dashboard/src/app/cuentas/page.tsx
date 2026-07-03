'use client';

import { useEffect, useState } from 'react';
import { Plus, CreditCard, Banknote, Building2, Wallet, Edit3, Trash2, X, Save } from 'lucide-react';
import { getCuentas, createCuenta, updateCuenta } from '@/lib/api';

const tipoIconos: Record<string, any> = {
  efectivo: Banknote,
  cuenta_corriente: Building2,
  cuenta_vista: Building2,
  caja: Wallet,
  tarjeta_credito: CreditCard,
};

export default function CuentasPage() {
  const [cuentas, setCuentas] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState({
    nombre: '', tipo: 'efectivo', banco: '', saldo_actual: 0,
    tarjeta_info: { banco: '', fecha_cierre: 15, fecha_pago: 25, cupo: 0, permite_cuotas: true },
  });

  async function load() {
    try { setCuentas(await getCuentas()); } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  function resetForm() {
    setForm({
      nombre: '', tipo: 'efectivo', banco: '', saldo_actual: 0,
      tarjeta_info: { banco: '', fecha_cierre: 15, fecha_pago: 25, cupo: 0, permite_cuotas: true },
    });
    setEditingId(null);
    setShowForm(false);
  }

  function startEdit(cuenta: any) {
    setForm({
      nombre: cuenta.nombre || '',
      tipo: cuenta.tipo || 'efectivo',
      banco: cuenta.banco || '',
      saldo_actual: cuenta.saldo_actual || 0,
      tarjeta_info: cuenta.tarjeta_info || { banco: '', fecha_cierre: 15, fecha_pago: 25, cupo: 0, permite_cuotas: true },
    });
    setEditingId(cuenta.id);
    setShowForm(true);
  }

  async function handleSave() {
    if (!form.nombre.trim()) return;
    const data: any = { ...form };
    if (form.tipo !== 'tarjeta_credito') delete data.tarjeta_info;

    if (editingId) {
      await updateCuenta(editingId, data);
    } else {
      await createCuenta(data);
    }
    resetForm();
    load();
  }

  async function handleDelete(id: string) {
    if (!confirm('Desactivar esta cuenta?')) return;
    await updateCuenta(id, { activa: false } as any);
    load();
  }

  function formatCLP(n: number) {
    return new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', maximumFractionDigits: 0 }).format(n);
  }

  if (loading) {
    return <div className="flex items-center justify-center h-96"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" /></div>;
  }

  const cuentasActivas = cuentas.filter((c: any) => c.activa !== false);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-slate-900">Cuentas Financieras</h2>
          <p className="text-slate-500 mt-1">Administra tus medios de pago y fuentes de dinero</p>
        </div>
        <button onClick={() => { resetForm(); setShowForm(!showForm); }}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
          <Plus size={18} /> Nueva Cuenta
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">{editingId ? 'Editar Cuenta' : 'Nueva Cuenta'}</h3>
            <button onClick={resetForm} className="text-slate-400 hover:text-slate-600"><X size={20} /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input type="text" placeholder="Nombre" value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.target.value })}
              className="px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-primary-500" />
            <select value={form.tipo}
              onChange={(e) => setForm({ ...form, tipo: e.target.value })}
              className="px-3 py-2 border rounded-lg outline-none">
              <option value="efectivo">Efectivo</option>
              <option value="cuenta_corriente">Cuenta Corriente</option>
              <option value="cuenta_vista">Cuenta Vista</option>
              <option value="caja">Caja</option>
              <option value="tarjeta_credito">Tarjeta de Credito</option>
            </select>
            <input type="number" placeholder="Saldo actual" value={form.saldo_actual}
              onChange={(e) => setForm({ ...form, saldo_actual: Number(e.target.value) })}
              className="px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-primary-500" />
            {form.tipo !== 'efectivo' && form.tipo !== 'caja' && (
              <input type="text" placeholder="Banco" value={form.banco}
                onChange={(e) => setForm({ ...form, banco: e.target.value })}
                className="px-3 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-primary-500" />
            )}
            {form.tipo === 'tarjeta_credito' && (
              <>
                <input type="number" placeholder="Dia de cierre" value={form.tarjeta_info.fecha_cierre}
                  onChange={(e) => setForm({ ...form, tarjeta_info: { ...form.tarjeta_info, fecha_cierre: Number(e.target.value) } })}
                  className="px-3 py-2 border rounded-lg outline-none" />
                <input type="number" placeholder="Dia de pago" value={form.tarjeta_info.fecha_pago}
                  onChange={(e) => setForm({ ...form, tarjeta_info: { ...form.tarjeta_info, fecha_pago: Number(e.target.value) } })}
                  className="px-3 py-2 border rounded-lg outline-none" />
                <input type="number" placeholder="Cupo (opcional)" value={form.tarjeta_info.cupo || ''}
                  onChange={(e) => setForm({ ...form, tarjeta_info: { ...form.tarjeta_info, cupo: Number(e.target.value) } })}
                  className="px-3 py-2 border rounded-lg outline-none" />
              </>
            )}
            <button onClick={handleSave} className="flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium">
              <Save size={16} /> {editingId ? 'Guardar Cambios' : 'Crear Cuenta'}
            </button>
          </div>
        </div>
      )}

      {/* Lista */}
      {cuentasActivas.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <CreditCard size={48} className="mx-auto text-slate-300 mb-4" />
          <p className="text-slate-500">No tienes cuentas registradas.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cuentasActivas.map((c) => {
            const Icon = tipoIconos[c.tipo] || Banknote;
            return (
              <div key={c.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-slate-100 rounded-lg">
                      <Icon size={20} className="text-slate-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900">{c.nombre}</h3>
                      <p className="text-xs text-slate-500 capitalize">{c.tipo.replace('_', ' ')}</p>
                    </div>
                  </div>
                </div>
                <div className="mt-4">
                  <p className="text-2xl font-bold text-slate-900">{formatCLP(c.saldo_actual || 0)}</p>
                  {c.tarjeta_info && (
                    <div className="mt-2 text-xs text-slate-500 space-y-1">
                      <p>Cierre: dia {c.tarjeta_info.fecha_cierre}</p>
                      <p>Pago: dia {c.tarjeta_info.fecha_pago}</p>
                      {c.tarjeta_info.cupo > 0 && <p>Cupo: {formatCLP(c.tarjeta_info.cupo)}</p>}
                    </div>
                  )}
                </div>
                {/* BOTONES EDITAR Y ELIMINAR */}
                <div className="mt-4 pt-3 border-t flex gap-3">
                  <button onClick={() => startEdit(c)}
                    className="flex items-center gap-1 text-xs text-slate-500 hover:text-primary-600 transition-colors">
                    <Edit3 size={14} /> Editar
                  </button>
                  <button onClick={() => handleDelete(c.id)}
                    className="flex items-center gap-1 text-xs text-slate-500 hover:text-red-600 transition-colors">
                    <Trash2 size={14} /> Desactivar
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}