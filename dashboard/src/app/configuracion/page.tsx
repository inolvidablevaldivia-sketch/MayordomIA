'use client';

import { Settings, Database, Bot, Download, Upload, Users } from 'lucide-react';

export default function ConfiguracionPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-slate-900">Configuración</h2>
        <p className="text-slate-500 mt-1">Administra MayordomIA sin modificar código</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Conexiones */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Bot size={18} /> Conexiones
          </h3>
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div>
                <p className="font-medium">Telegram Bot</p>
                <p className="text-slate-500 text-xs">@MayordomIA_Bot</p>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">Conectado</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div>
                <p className="font-medium">Gemini AI</p>
                <p className="text-slate-500 text-xs">gemini-2.0-flash</p>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">Activo</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div>
                <p className="font-medium">Firebase Firestore</p>
                <p className="text-slate-500 text-xs">Base de datos</p>
              </div>
              <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">Conectado</span>
            </div>
          </div>
        </div>

        {/* Datos */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Database size={18} /> Datos
          </h3>
          <div className="space-y-3">
            <button className="w-full flex items-center gap-3 p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors text-sm">
              <Upload size={16} className="text-primary-600" />
              <div className="text-left">
                <p className="font-medium">Importar datos</p>
                <p className="text-xs text-slate-500">Desde Excel (.xlsx) o CSV</p>
              </div>
            </button>
            <button className="w-full flex items-center gap-3 p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors text-sm">
              <Download size={16} className="text-primary-600" />
              <div className="text-left">
                <p className="font-medium">Exportar datos</p>
                <p className="text-xs text-slate-500">Descargar respaldo completo</p>
              </div>
            </button>
          </div>
        </div>

        {/* Usuarios */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Users size={18} /> Usuarios
          </h3>
          <p className="text-sm text-slate-500">
            Próximamente: gestión de múltiples usuarios con diferentes roles y permisos.
          </p>
        </div>

        {/* Sistema */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Settings size={18} /> Sistema
          </h3>
          <div className="space-y-2 text-sm text-slate-500">
            <p>Versión: 1.0.0</p>
            <p>Entorno: Desarrollo</p>
            <p>API: http://localhost:8000</p>
          </div>
        </div>
      </div>
    </div>
  );
}
