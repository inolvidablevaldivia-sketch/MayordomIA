"""
MayordomIA - Modelos de datos (Pydantic Schemas)
Todos los modelos que representan las entidades del sistema.
"""
from __future__ import annotations

import uuid
from datetime import datetime, date
from enum import Enum
from typing import Optional, Annotated

from pydantic import BaseModel, Field, StringConstraints


# ============================================================
# Tipos y Enums
# ============================================================

class TipoMovimiento(str, Enum):
    COMPRA = "compra"
    USO = "uso"
    VENTA = "venta"
    MERMA = "merma"
    CORRECCION = "correccion"
    DEVOLUCION = "devolucion"


class TipoCuenta(str, Enum):
    EFECTIVO = "efectivo"
    CUENTA_CORRIENTE = "cuenta_corriente"
    CUENTA_VISTA = "cuenta_vista"
    CAJA = "caja"
    TARJETA_CREDITO = "tarjeta_credito"


class EstadoPago(str, Enum):
    PENDIENTE = "pendiente"
    PAGADO = "pagado"
    COMPROMETIDO = "comprometido"


class EstadoUnidad(str, Enum):
    ACTIVA = "activa"
    ARCHIVADA = "archivada"


class TipoEvento(str, Enum):
    CREACION = "creacion"
    EDICION = "edicion"
    CORRECCION = "correccion"
    FUSION = "fusion"
    SEPARACION = "separacion"
    ARCHIVADO = "archivado"
    REACTIVACION = "reactivacion"


# ============================================================
# Unidad
# ============================================================

class UnidadBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: str | None = None
    color: str = "#4F46E5"


class UnidadCreate(UnidadBase):
    pass


class UnidadUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    color: str | None = None


class Unidad(UnidadBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    estado: EstadoUnidad = EstadoUnidad.ACTIVA
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "default"
    archived_at: datetime | None = None


# ============================================================
# Categoría
# ============================================================

class CategoriaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    unidad_id: str
    tipo: str = "gasto"  # gasto | ingreso
    parent_id: str | None = None  # para subcategorías


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nombre: str | None = None
    parent_id: str | None = None
    activa: bool | None = None


class Categoria(CategoriaBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    activa: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# Producto
# ============================================================

class ProductoBase(BaseModel):
    nombre_principal: str = Field(..., min_length=1, max_length=200)
    unidad_medida: str = "unidad"  # unidad, kg, g, litros, ml, etc.
    stock_minimo: float = 0.0
    categoria_sugerida_id: str | None = None


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    nombre_principal: str | None = None
    unidad_medida: str | None = None
    stock_minimo: float | None = None
    categoria_sugerida_id: str | None = None


class Producto(ProductoBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    aliases: list[str] = Field(default_factory=list)
    stock_actual: float = 0.0
    precio_promedio: float = 0.0
    mejor_precio_historico: float | None = None
    ultimo_precio: float | None = None
    comercios_conocidos: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# Comercio
# ============================================================

class ComercioBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    rubro: str | None = None
    direccion: str | None = None


class ComercioCreate(ComercioBase):
    pass


class ComercioUpdate(BaseModel):
    nombre: str | None = None
    rubro: str | None = None
    direccion: str | None = None


class Comercio(ComercioBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# Cuenta Financiera
# ============================================================

class CuentaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    tipo: TipoCuenta = TipoCuenta.EFECTIVO
    banco: str | None = None
    numero: str | None = None
    saldo_actual: float = 0.0


class TarjetaCreditoInfo(BaseModel):
    banco: str | None = None
    fecha_cierre: int = 15  # día del mes
    fecha_pago: int = 25  # día del mes
    cupo: float | None = None
    permite_cuotas: bool = True


class CuentaCreate(CuentaBase):
    tarjeta_info: TarjetaCreditoInfo | None = None


class CuentaUpdate(BaseModel):
    nombre: str | None = None
    banco: str | None = None
    saldo_actual: float | None = None
    tarjeta_info: TarjetaCreditoInfo | None = None
    activa: bool | None = None


class Cuenta(CuentaBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tarjeta_info: TarjetaCreditoInfo | None = None
    activa: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# Movimiento (Compra, Venta, Uso, Merma, etc.)
# ============================================================

class MovimientoItem(BaseModel):
    """Un ítem dentro de un movimiento"""
    producto_id: str
    producto_nombre: str
    cantidad: float
    unidad: str = "unidad"
    precio_unitario: float = 0.0
    subtotal: float = 0.0
    categoria_id: str | None = None


class MovimientoBase(BaseModel):
    tipo: TipoMovimiento
    unidad_id: str
    cuenta_id: str | None = None
    comercio_id: str | None = None
    items: list[MovimientoItem] = Field(default_factory=list)
    total: float = 0.0
    moneda: str = "CLP"
    estado_pago: EstadoPago = EstadoPago.PAGADO
    fecha: datetime = Field(default_factory=datetime.utcnow)
    nota: str | None = None
    numero_documento: str | None = None  # N° de boleta/factura


class MovimientoCreate(MovimientoBase):
    pass


class MovimientoUpdate(BaseModel):
    tipo: TipoMovimiento | None = None
    cuenta_id: str | None = None
    items: list[MovimientoItem] | None = None
    total: float | None = None
    estado_pago: EstadoPago | None = None
    nota: str | None = None


class Movimiento(MovimientoBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    fingerprint: str | None = None  # hash para detección de duplicados
    boleta_url: str | None = None  # URL de la boleta en Storage
    boleta_texto_ocr: str | None = None  # texto extraído de la boleta
    es_correccion: bool = False
    movimiento_original_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "default"


# ============================================================
# Radar de Precios
# ============================================================

class RadarPrecioBase(BaseModel):
    producto_id: str
    producto_nombre: str
    precio: float
    comercio_id: str | None = None
    comercio_nombre: str | None = None
    fecha: datetime = Field(default_factory=datetime.utcnow)


class RadarPrecioCreate(RadarPrecioBase):
    pass


class RadarPrecio(RadarPrecioBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "default"


# ============================================================
# Evento de Auditoría
# ============================================================

class EventoAuditoria(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tipo: TipoEvento
    entidad: str  # unidad, producto, comercio, movimiento, etc.
    entidad_id: str
    usuario: str
    fecha: datetime = Field(default_factory=datetime.utcnow)
    cambios: dict = Field(default_factory=dict)  # antes/después
    metadata: dict = Field(default_factory=dict)


# ============================================================
# Corrección de Aprendizaje (Alias, asociaciones)
# ============================================================

class AprendizajeCorreccion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    texto_original: str
    texto_corregido: str
    tipo: str  # producto_alias, comercio_alias, unidad_asociacion
    entidad_id: str | None = None
    usuario: str
    fecha: datetime = Field(default_factory=datetime.utcnow)
    contador_usos: int = 1


# ============================================================
# Usuario
# ============================================================

class Usuario(BaseModel):
    id: str  # Telegram user ID
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    rol: str = "admin"
    activo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# Consultas (para la IA)
# ============================================================

class ConsultaRequest(BaseModel):
    texto: str
    user_id: str
    chat_id: str


class ConsultaResponse(BaseModel):
    respuesta: str
    datos: dict | None = None
    botones: list[dict] | None = None
    accion: str | None = None  # confirmar_duplicado, confirmar_fusion, etc.
