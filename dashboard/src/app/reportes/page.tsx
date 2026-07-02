'use client';

import { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, ShoppingCart, DollarSign } from 'lucide-react';
import { getGastos, getRentabilidad, getInventario } from '@/lib/api';

export default function ReportesPage() {
  const [gastos, setGastos] = useState<any>(null);
  const [rentabilidad, setRentabilidad] = useState<any>(null);
  const [inventario, setInventario] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [g, r, i] = await Promise.all([
          getGastos(), getRentabilidad(), getInventario(),
        ]);
        setGastos(g);
        setRentabilidad(r);
        setInventario(i);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-96"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" /></div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-slate-900">Reportes</h2>
        <p className="text-slate-500 mt-1">Información financiera para tomar mejores decisiones</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gastos */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <ShoppingCart size={18} /> Gastos del Mes
          </h3>
          <div className="bg-slate-50 rounded-lg p-4">
            <pre className="text-sm text-slate-700 whitespace-pre-wrap font-mono">
              {gastos?.respuesta || 'No hay datos'}
            </pre>
          </div>
        </div>

        {/* Rentabilidad */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <TrendingUp size={18} /> Rentabilidad
          </h3>
          <div className="bg-slate-50 rounded-lg p-4">
            <pre className="text-sm text-slate-700 whitespace-pre-wrap font-mono">
              {rentabilidad?.respuesta || 'No hay datos'}
            </pre>
          </div>
        </div>

        {/* Inventario */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <BarChart3 size={18} /> Inventario
          </h3>
          <div className="bg-slate-50 rounded-lg p-4">
            <pre className="text-sm text-slate-700 whitespace-pre-wrap font-mono">
              {inventario?.respuesta || 'No hay datos'}
            </pre>
          </div>
        </div>

        {/* Próximos reportes */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <DollarSign size={18} /> Próximamente
          </h3>
          <div className="space-y-2 text-sm text-slate-500">
            <p>📊 Reportes por categoría</p>
            <p>📊 Reportes por producto</p>
            <p>📊 Reportes por comercio</p>
            <p>📊 Reportes por cuenta financiera</p>
            <p>📊 Exportación a Excel / CSV</p>
            <p>📊 Gráficos de tendencias</p>
            <p>🤖 Reportes automáticos (lunes, inicio de mes, inicio de año)</p>
          </div>
        </div>
      </div>
    </div>
  );
}
