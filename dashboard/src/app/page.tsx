'use client';

import { useEffect, useState } from 'react';
import {
  TrendingUp, TrendingDown, DollarSign, ShoppingCart,
  Package, Building2, Store, AlertTriangle
} from 'lucide-react';
import { getDashboardResumen, getMovimientosRecientes, getProductosBajos } from '@/lib/api';

function formatCLP(amount: number): string {
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    maximumFractionDigits: 0,
  }).format(amount);
}

export default function DashboardPage() {
  const [resumen, setResumen] = useState<any>(null);
  const [movimientos, setMovimientos] = useState<any[]>([]);
  const [productosBajos, setProductosBajos] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [r, m, p] = await Promise.all([
          getDashboardResumen(),
          getMovimientosRecientes(10),
          getProductosBajos(),
        ]);
        setResumen(r);
        setMovimientos(m);
        setProductosBajos(p);
      } catch (e) {
        console.error('Error cargando dashboard:', e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  const stats = [
    {
      label: 'Compras del mes',
      value: formatCLP(resumen?.mes_actual?.compras || 0),
      icon: ShoppingCart,
      color: 'text-red-600',
      bg: 'bg-red-50',
    },
    {
      label: 'Ventas del mes',
      value: formatCLP(resumen?.mes_actual?.ventas || 0),
      icon: TrendingUp,
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
    {
      label: 'Utilidad',
      value: formatCLP(resumen?.mes_actual?.utilidad || 0),
      icon: DollarSign,
      color: 'text-primary-600',
      bg: 'bg-primary-50',
    },
    {
      label: 'Transacciones',
      value: resumen?.mes_actual?.transacciones || 0,
      icon: TrendingDown,
      color: 'text-slate-600',
      bg: 'bg-slate-100',
    },
  ];

  const entities = [
    { label: 'Unidades', value: resumen?.conteos?.unidades || 0, icon: Building2 },
    { label: 'Productos', value: resumen?.conteos?.productos || 0, icon: Package },
    { label: 'Comercios', value: resumen?.conteos?.comercios || 0, icon: Store },
    { label: 'Cuentas', value: resumen?.conteos?.cuentas || 0, icon: DollarSign },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-slate-900">Dashboard</h2>
        <p className="text-slate-500 mt-1">Resumen de tu actividad financiera</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl p-5 shadow-sm border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">{stat.label}</p>
                <p className="text-2xl font-bold mt-1 text-slate-900">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-lg ${stat.bg}`}>
                <stat.icon size={20} className={stat.color} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Entities & Alertas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Entidades */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">📊 Resumen General</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {entities.map((e) => (
              <div key={e.label} className="text-center p-4 bg-slate-50 rounded-lg">
                <e.icon size={24} className="mx-auto text-primary-600 mb-2" />
                <p className="text-2xl font-bold text-slate-900">{e.value}</p>
                <p className="text-sm text-slate-500">{e.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Alertas de stock */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <AlertTriangle size={18} className="text-amber-500" />
            Stock Bajo
          </h3>
          {productosBajos.length === 0 ? (
            <p className="text-sm text-slate-400">✅ Todos los productos están sobre el mínimo.</p>
          ) : (
            <div className="space-y-3">
              {productosBajos.map((p) => (
                <div key={p.id} className="flex items-center justify-between p-3 bg-amber-50 rounded-lg">
                  <div>
                    <p className="font-medium text-sm text-slate-900">{p.nombre_principal}</p>
                    <p className="text-xs text-slate-500">
                      {p.stock_actual} / {p.stock_minimo} {p.unidad_medida}
                    </p>
                  </div>
                  <span className="text-xs font-bold text-amber-700 bg-amber-100 px-2 py-1 rounded">
                    COMPRAR
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Últimos movimientos */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">📋 Últimos Movimientos</h3>
        {movimientos.length === 0 ? (
          <p className="text-slate-400 text-sm">No hay movimientos registrados aún.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-3 px-2 text-slate-500 font-medium">Tipo</th>
                  <th className="text-left py-3 px-2 text-slate-500 font-medium">Unidad</th>
                  <th className="text-left py-3 px-2 text-slate-500 font-medium">Productos</th>
                  <th className="text-right py-3 px-2 text-slate-500 font-medium">Total</th>
                  <th className="text-right py-3 px-2 text-slate-500 font-medium">Fecha</th>
                </tr>
              </thead>
              <tbody>
                {movimientos.map((m) => (
                  <tr key={m.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-3 px-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        m.tipo === 'compra' ? 'bg-red-100 text-red-700' :
                        m.tipo === 'venta' ? 'bg-green-100 text-green-700' :
                        m.tipo === 'uso' ? 'bg-blue-100 text-blue-700' :
                        'bg-slate-100 text-slate-600'
                      }`}>
                        {m.tipo}
                      </span>
                    </td>
                    <td className="py-3 px-2 text-slate-700">{m.unidad_id}</td>
                    <td className="py-3 px-2 text-slate-600">
                      {m.items?.map((i: any) => i.producto_nombre).join(', ') || '-'}
                    </td>
                    <td className="py-3 px-2 text-right font-medium">
                      {formatCLP(m.total || 0)}
                    </td>
                    <td className="py-3 px-2 text-right text-slate-500 text-xs">
                      {m.fecha ? new Date(m.fecha._seconds ? m.fecha._seconds * 1000 : m.fecha).toLocaleDateString('es-CL') : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
