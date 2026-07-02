/**
 * Cliente API para MayordomIA Dashboard
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

async function fetchAPI(endpoint: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(error.message || `Error ${res.status}`);
  }
  return res.json();
}

// ─── Dashboard ───
export async function getDashboardResumen() {
  return fetchAPI('/dashboard/resumen');
}

export async function getMovimientosRecientes(limit = 20) {
  return fetchAPI(`/dashboard/movimientos-recientes?limit=${limit}`);
}

export async function getProductosBajos() {
  return fetchAPI('/dashboard/productos-bajos');
}

// ─── Unidades ───
export async function getUnidades(activas = true) {
  return fetchAPI(`/unidades?activas=${activas}`);
}

export async function createUnidad(data: Record<string, unknown>) {
  return fetchAPI('/unidades', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateUnidad(id: string, data: Record<string, unknown>) {
  return fetchAPI(`/unidades/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function archiveUnidad(id: string) {
  return fetchAPI(`/unidades/${id}`, { method: 'DELETE' });
}

// ─── Productos ───
export async function getProductos(buscar?: string) {
  const query = buscar ? `?buscar=${encodeURIComponent(buscar)}` : '';
  return fetchAPI(`/productos${query}`);
}

export async function createProducto(data: Record<string, unknown>) {
  return fetchAPI('/productos', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateProducto(id: string, data: Record<string, unknown>) {
  return fetchAPI(`/productos/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function addAlias(id: string, alias: string) {
  return fetchAPI(`/productos/${id}/alias`, {
    method: 'POST',
    body: JSON.stringify({ alias }),
  });
}

export async function fusionarProductos(origenId: string, destinoId: string) {
  return fetchAPI('/productos/fusionar', {
    method: 'POST',
    body: JSON.stringify({ origen_id: origenId, destino_id: destinoId }),
  });
}

// ─── Comercios ───
export async function getComercios() {
  return fetchAPI('/comercios');
}

export async function createComercio(data: Record<string, unknown>) {
  return fetchAPI('/comercios', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function fusionarComercios(origenId: string, destinoId: string) {
  return fetchAPI('/comercios/fusionar', {
    method: 'POST',
    body: JSON.stringify({ origen_id: origenId, destino_id: destinoId }),
  });
}

// ─── Cuentas ───
export async function getCuentas() {
  return fetchAPI('/cuentas');
}

export async function createCuenta(data: Record<string, unknown>) {
  return fetchAPI('/cuentas', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateCuenta(id: string, data: Record<string, unknown>) {
  return fetchAPI(`/cuentas/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// ─── Movimientos ───
export async function getMovimientos(params?: Record<string, string>) {
  const query = params ? '?' + new URLSearchParams(params).toString() : '';
  return fetchAPI(`/movimientos${query}`);
}

// ─── Consultas ───
export async function getGastos(unidad?: string) {
  const query = unidad ? `?unidad=${encodeURIComponent(unidad)}` : '';
  return fetchAPI(`/consultas/gastos${query}`);
}

export async function getInventario() {
  return fetchAPI('/consultas/inventario');
}

export async function getDeudas() {
  return fetchAPI('/consultas/deudas');
}

export async function getRentabilidad() {
  return fetchAPI('/consultas/rentabilidad');
}

export async function getPrecios(producto: string) {
  return fetchAPI(`/consultas/precios?producto=${encodeURIComponent(producto)}`);
}
