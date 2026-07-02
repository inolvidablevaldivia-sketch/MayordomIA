"""
MayordomIA - Motor de Reglas de Negocio
Procesa las acciones determinadas por la IA y ejecuta la lógica.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Any

from app.models.firestore import (
    crear_movimiento,
    crear_producto,
    crear_comercio,
    crear_radar,
    buscar_producto_por_nombre,
    buscar_comercio_por_nombre,
    buscar_duplicado,
    obtener_producto,
    actualizar_producto,
    obtener_cuenta,
    actualizar_saldo_cuenta,
    guardar_correccion,
    registrar_evento,
    listar_movimientos_por_unidad,
    listar_unidades,
    listar_cuentas,
    listar_radar_por_producto,
    listar_comercios,
    listar_categorias_por_unidad,
    buscar_productos_por_texto,
    get_db,
)
from app.ai.gemini import generar_fingerprint


# ══════════════════════════════════════════════════════════════
# PROCESADOR PRINCIPAL DE ACCIONES
# ══════════════════════════════════════════════════════════════

async def ejecutar_accion(accion_data: dict, user_id: str) -> dict[str, Any]:
    """
    Ejecuta la acción determinada por la IA.
    Retorna una respuesta formateada para el usuario.
    """
    accion = accion_data.get("accion", "conversar")
    datos = accion_data.get("datos", {})
    mensaje = accion_data.get("mensaje", "")

    try:
        if accion == "conversar":
            return {"respuesta": mensaje, "botones": None}

        elif accion == "registrar_compra":
            return await _registrar_compra(datos, user_id, mensaje)

        elif accion == "registrar_venta":
            return await _registrar_venta(datos, user_id, mensaje)

        elif accion == "registrar_uso":
            return await _registrar_uso(datos, user_id, mensaje)

        elif accion == "registrar_merma":
            return await _registrar_merma(datos, user_id, mensaje)

        elif accion == "registrar_radar":
            return await _registrar_radar(datos, user_id, mensaje)

        elif accion == "consultar":
            return await _procesar_consulta(accion_data, user_id)

        elif accion == "confirmar_duplicado":
            return await _confirmar_duplicado(datos, user_id)

        elif accion == "corregir":
            return await _procesar_correccion(datos, user_id, mensaje)

        elif accion == "crear_unidad":
            return await _crear_unidad(datos, user_id, mensaje)

        elif accion == "crear_producto":
            return await _crear_producto(datos, user_id, mensaje)

        else:
            return {"respuesta": f"✅ Entendido. {mensaje}", "botones": None}

    except Exception as e:
        return {
            "respuesta": f"❌ Ocurrió un error al procesar tu solicitud: {str(e)}",
            "botones": None,
            "error": str(e),
        }


# ══════════════════════════════════════════════════════════════
# REGISTRO DE COMPRA
# ══════════════════════════════════════════════════════════════

async def _registrar_compra(datos: dict, user_id: str, mensaje: str) -> dict:
    items = datos.get("items", [])
    comercio_nombre = datos.get("comercio_nombre", "").strip()
    unidad_nombre = datos.get("unidad_nombre", "Casa").strip()
    total = datos.get("total", 0.0)
    medio_pago = datos.get("medio_pago", "efectivo")
    numero_doc = datos.get("numero_documento")
    fecha_str = datos.get("fecha")

    # ─── 1. Resolver o crear comercio ───
    comercio = buscar_comercio_por_nombre(comercio_nombre) if comercio_nombre else None
    if not comercio and comercio_nombre:
        comercio = crear_comercio({"nombre": comercio_nombre})
        registrar_evento({
            "tipo": "creacion", "entidad": "comercio",
            "entidad_id": comercio["id"], "usuario": user_id,
        })

    # ─── 2. Resolver Unidad ───
    unidad = None
    unidades = listar_unidades()
    for u in unidades:
        if u["nombre"].lower() == unidad_nombre.lower():
            unidad = u
            break
    if not unidad and unidades:
        unidad = unidades[0]  # default: primera unidad

    # ─── 3. Resolver o crear productos ───
    items_resueltos = []
    for item in items:
        nombre = item.get("producto_nombre", "").strip()
        cantidad = float(item.get("cantidad", 1))
        precio = float(item.get("precio_unitario", 0))

        producto = buscar_producto_por_nombre(nombre)
        if not producto:
            producto = crear_producto({
                "nombre_principal": nombre,
                "unidad_medida": item.get("unidad", "unidad"),
                "stock_minimo": 0,
            })
            registrar_evento({
                "tipo": "creacion", "entidad": "producto",
                "entidad_id": producto["id"], "usuario": user_id,
            })

        items_resueltos.append({
            "producto_id": producto["id"],
            "producto_nombre": producto["nombre_principal"],
            "cantidad": cantidad,
            "unidad": producto.get("unidad_medida", "unidad"),
            "precio_unitario": precio,
            "subtotal": round(cantidad * precio),
        })

    # ─── 4. Resolver cuenta financiera ───
    cuenta_id = None
    estado_pago = "pagado"
    if medio_pago:
        cuentas = listar_cuentas()
        for c in cuentas:
            if c["nombre"].lower() == medio_pago.lower() or c.get("tipo") == medio_pago.lower():
                cuenta_id = c["id"]
                # Determinar estado_pago según tipo de cuenta
                estado_pago = "comprometido" if c.get("tipo") == "tarjeta_credito" else "pagado"
                break
    else:
        estado_pago = "pagado"

    # ─── 5. Calcular total real ───
    if not total:
        total = sum(it["subtotal"] for it in items_resueltos)

    # ─── 6. Fingerprint para detección de duplicados ───
    fecha_usar = fecha_str or datetime.utcnow().isoformat()
    fp = generar_fingerprint(
        comercio=comercio_nombre,
        fecha=fecha_usar,
        total=total,
        items=items_resueltos,
        numero_documento=numero_doc,
    )

    # ─── 7. Verificar duplicados ───
    duplicados = buscar_duplicado(fp)
    if duplicados:
        return {
            "respuesta": (
                f"⚠️ **Posible duplicado detectado**\n\n"
                f"Ya existe una compra muy similar:\n"
                f"- {duplicados[0].get('comercio_id')}: ${duplicados[0].get('total', 0):,.0f}\n"
                f"- Fecha: {duplicados[0].get('fecha')}\n\n"
                f"¿Deseas registrarla de todas formas?"
            ),
            "botones": [
                {"texto": "✅ Sí, registrar", "callback": f"confirmar_duplicado|si|{fp}"},
                {"texto": "❌ No, cancelar", "callback": "confirmar_duplicado|no"},
            ],
            "accion_pendiente": "confirmar_duplicado",
            "datos_pendientes": {
                "tipo": "compra",
                "unidad_id": unidad["id"] if unidad else None,
                "cuenta_id": cuenta_id,
                "comercio_id": comercio["id"] if comercio else None,
                "items": items_resueltos,
                "total": total,
                "estado_pago": estado_pago,
                "fingerprint": fp,
                "numero_documento": numero_doc,
                "fecha": fecha_usar,
            },
        }

    # ─── 8. Registrar movimiento ───
    from dateutil import parser as dateparser
    try:
        fecha_obj = dateparser.parse(fecha_usar) if fecha_str else datetime.utcnow()
    except Exception:
        fecha_obj = datetime.utcnow()

    movimiento = crear_movimiento({
        "tipo": "compra",
        "unidad_id": unidad["id"] if unidad else "default",
        "cuenta_id": cuenta_id,
        "comercio_id": comercio["id"] if comercio else None,
        "items": items_resueltos,
        "total": total,
        "estado_pago": estado_pago,
        "fingerprint": fp,
        "numero_documento": numero_doc,
        "fecha": fecha_obj,
        "created_by": user_id,
    })

    # ─── 9. Actualizar stock ───
    for item in items_resueltos:
        producto = obtener_producto(item["producto_id"])
        if producto:
            nuevo_stock = producto.get("stock_actual", 0) + item["cantidad"]
            # Actualizar precio
            actualizar_producto(item["producto_id"], {
                "stock_actual": nuevo_stock,
                "ultimo_precio": item["precio_unitario"],
                "comercios_conocidos": list(set(
                    producto.get("comercios_conocidos", []) +
                    ([comercio["id"]] if comercio else [])
                )),
            })

    # ─── 10. Actualizar saldo cuenta ───
    if cuenta_id and estado_pago == "pagado":
        actualizar_saldo_cuenta(cuenta_id, -total)

    # ─── 11. Auditoría ───
    registrar_evento({
        "tipo": "creacion", "entidad": "movimiento",
        "entidad_id": movimiento["id"], "usuario": user_id,
        "cambios": {"total": total, "items": len(items_resueltos)},
    })

    # ─── 12. Respuesta ───
    items_str = "\n".join([
        f"  • {it['cantidad']}x {it['producto_nombre']} @ ${it['precio_unitario']:,.0f} = ${it['subtotal']:,.0f}"
        for it in items_resueltos
    ])
    emoji = "🛒"
    return {
        "respuesta": (
            f"{emoji} **Compra registrada**\n\n"
            f"{items_str}\n\n"
            f"💰 Total: **${total:,.0f}**\n"
            f"🏪 {comercio_nombre or 'Sin comercio'}\n"
            f"📦 Unidad: {unidad['nombre'] if unidad else 'General'}\n"
            f"💳 {medio_pago or 'Efectivo'}\n"
            + (f"📄 Boleta #{numero_doc}\n" if numero_doc else "")
            + f"\n{mensaje}"
        ),
        "botones": [
            {"texto": "✏️ Corregir", "callback": f"corregir_movimiento|{movimiento['id']}"},
            {"texto": "📋 Ver inventario", "callback": "consultar|inventario"},
        ],
    }


# ══════════════════════════════════════════════════════════════
# REGISTRO DE VENTA
# ══════════════════════════════════════════════════════════════

async def _registrar_venta(datos: dict, user_id: str, mensaje: str) -> dict:
    items = datos.get("items", [])
    total = datos.get("total", 0.0)
    unidad_nombre = datos.get("unidad_nombre", "General").strip()
    medio_pago = datos.get("medio_pago", "efectivo")

    # Resolver unidad
    unidades = listar_unidades()
    unidad = next((u for u in unidades if u["nombre"].lower() == unidad_nombre.lower()), None)
    if not unidad and unidades:
        unidad = unidades[0]

    items_resueltos = []
    for item in items:
        nombre = item.get("producto_nombre", "").strip()
        cantidad = float(item.get("cantidad", 1))
        precio = float(item.get("precio_unitario", 0))

        producto = buscar_producto_por_nombre(nombre)
        if not producto:
            producto = crear_producto({
                "nombre_principal": nombre,
                "stock_actual": 0,
            })

        items_resueltos.append({
            "producto_id": producto["id"],
            "producto_nombre": producto["nombre_principal"],
            "cantidad": cantidad,
            "unidad": producto.get("unidad_medida", "unidad"),
            "precio_unitario": precio,
            "subtotal": round(cantidad * precio),
        })

    if not total:
        total = sum(it["subtotal"] for it in items_resueltos)

    # Cuenta (para ingreso)
    cuenta_id = None
    cuentas = listar_cuentas()
    for c in cuentas:
        if c.get("tipo") in ("efectivo", "cuenta_corriente", "cuenta_vista", "caja"):
            cuenta_id = c["id"]
            break

    fp = generar_fingerprint(
        comercio="venta",
        fecha=datetime.utcnow().isoformat(),
        total=total,
        items=items_resueltos,
    )

    movimiento = crear_movimiento({
        "tipo": "venta",
        "unidad_id": unidad["id"] if unidad else "default",
        "cuenta_id": cuenta_id,
        "items": items_resueltos,
        "total": total,
        "estado_pago": "pagado",
        "fingerprint": fp,
        "created_by": user_id,
    })

    # Descontar stock
    for item in items_resueltos:
        producto = obtener_producto(item["producto_id"])
        if producto:
            nuevo_stock = max(0, producto.get("stock_actual", 0) - item["cantidad"])
            actualizar_producto(item["producto_id"], {"stock_actual": nuevo_stock})

    if cuenta_id:
        actualizar_saldo_cuenta(cuenta_id, total)

    registrar_evento({
        "tipo": "creacion", "entidad": "movimiento",
        "entidad_id": movimiento["id"], "usuario": user_id,
        "cambios": {"tipo": "venta", "total": total},
    })

    items_str = "\n".join([
        f"  • {it['cantidad']}x {it['producto_nombre']} @ ${it['precio_unitario']:,.0f}"
        for it in items_resueltos
    ])

    return {
        "respuesta": (
            f"💰 **Venta registrada**\n\n"
            f"{items_str}\n\n"
            f"💵 Ingreso: **${total:,.0f}**\n"
            f"📦 Unidad: {unidad['nombre'] if unidad else 'General'}\n"
            f"\n{mensaje}"
        ),
        "botones": [
            {"texto": "✏️ Corregir", "callback": f"corregir_movimiento|{movimiento['id']}"},
        ],
    }


# ══════════════════════════════════════════════════════════════
# REGISTRO DE USO
# ══════════════════════════════════════════════════════════════

async def _registrar_uso(datos: dict, user_id: str, mensaje: str) -> dict:
    """Uso de un producto (descuenta stock sin transacción financiera)."""
    producto_nombre = datos.get("producto_nombre", "").strip()
    cantidad = float(datos.get("cantidad", 1))
    unidad_nombre = datos.get("unidad_nombre", "General").strip()

    producto = buscar_producto_por_nombre(producto_nombre)
    if not producto:
        return {"respuesta": f"❓ No encontré el producto \"{producto_nombre}\". ¿Puedes ser más específico?", "botones": None}

    unidades = listar_unidades()
    unidad = next((u for u in unidades if u["nombre"].lower() == unidad_nombre.lower()), None)

    movimiento = crear_movimiento({
        "tipo": "uso",
        "unidad_id": unidad["id"] if unidad else "default",
        "items": [{
            "producto_id": producto["id"],
            "producto_nombre": producto["nombre_principal"],
            "cantidad": cantidad,
            "unidad": producto.get("unidad_medida", "unidad"),
            "precio_unitario": 0,
            "subtotal": 0,
        }],
        "total": 0,
        "created_by": user_id,
    })

    # Descontar stock
    nuevo_stock = max(0, producto.get("stock_actual", 0) - cantidad)
    actualizar_producto(producto["id"], {"stock_actual": nuevo_stock})

    return {
        "respuesta": (
            f"📦 **Uso registrado**\n\n"
            f"  • {cantidad}x {producto['nombre_principal']}\n"
            f"  • Stock restante: **{nuevo_stock}** {producto.get('unidad_medida', 'unidad')}\n"
            f"\n{mensaje}"
        ),
        "botones": None,
    }


# ══════════════════════════════════════════════════════════════
# REGISTRO DE MERMA
# ══════════════════════════════════════════════════════════════

async def _registrar_merma(datos: dict, user_id: str, mensaje: str) -> dict:
    producto_nombre = datos.get("producto_nombre", "").strip()
    cantidad = float(datos.get("cantidad", 1))
    motivo = datos.get("motivo", "No especificado")

    producto = buscar_producto_por_nombre(producto_nombre)
    if not producto:
        return {"respuesta": f"❓ No encontré el producto \"{producto_nombre}\".", "botones": None}

    movimiento = crear_movimiento({
        "tipo": "merma",
        "unidad_id": "default",
        "items": [{
            "producto_id": producto["id"],
            "producto_nombre": producto["nombre_principal"],
            "cantidad": cantidad,
            "unidad": producto.get("unidad_medida", "unidad"),
            "precio_unitario": producto.get("ultimo_precio") or producto.get("precio_promedio", 0),
            "subtotal": 0,
        }],
        "total": 0,
        "nota": motivo,
        "created_by": user_id,
    })

    nuevo_stock = max(0, producto.get("stock_actual", 0) - cantidad)
    actualizar_producto(producto["id"], {"stock_actual": nuevo_stock})

    return {
        "respuesta": (
            f"🗑️ **Merma registrada**\n\n"
            f"  • {cantidad}x {producto['nombre_principal']}\n"
            f"  • Motivo: {motivo}\n"
            f"  • Stock restante: **{nuevo_stock}**\n"
        ),
        "botones": None,
    }


# ══════════════════════════════════════════════════════════════
# RADAR DE PRECIOS
# ══════════════════════════════════════════════════════════════

async def _registrar_radar(datos: dict, user_id: str, mensaje: str) -> dict:
    producto_nombre = datos.get("producto_nombre", "").strip()
    precio = float(datos.get("precio", 0))
    comercio_nombre = datos.get("comercio_nombre", "").strip()

    producto = buscar_producto_por_nombre(producto_nombre)
    if not producto:
        producto = crear_producto({"nombre_principal": producto_nombre})

    comercio = buscar_comercio_por_nombre(comercio_nombre) if comercio_nombre else None
    if not comercio and comercio_nombre:
        comercio = crear_comercio({"nombre": comercio_nombre})

    radar = crear_radar({
        "producto_id": producto["id"],
        "producto_nombre": producto["nombre_principal"],
        "precio": precio,
        "comercio_id": comercio["id"] if comercio else None,
        "comercio_nombre": comercio_nombre,
        "created_by": user_id,
    })

    # Actualizar mejor precio histórico del producto
    if not producto.get("mejor_precio_historico") or precio < producto["mejor_precio_historico"]:
        actualizar_producto(producto["id"], {"mejor_precio_historico": precio})

    return {
        "respuesta": (
            f"📡 **Radar actualizado**\n\n"
            f"  🏷️ {producto['nombre_principal']}\n"
            f"  💲 ${precio:,.0f}\n"
            f"  🏪 {comercio_nombre}\n\n"
            f"📊 Mejor precio histórico: **${min(precio, producto.get('mejor_precio_historico') or precio):,.0f}**\n"
            f"\n{mensaje}"
        ),
        "botones": None,
    }


# ══════════════════════════════════════════════════════════════
# CONSULTAS
# ══════════════════════════════════════════════════════════════

async def _procesar_consulta(accion_data: dict, user_id: str) -> dict:
    consulta = accion_data.get("consulta", "")
    filtros = accion_data.get("filtros", {})
    mensaje = accion_data.get("mensaje", "")

    if "gastos_mes" in consulta or "gasto" in consulta:
        return await _consulta_gastos(filtros)

    elif "inventario" in consulta or "stock" in consulta:
        return await _consulta_inventario(filtros)

    elif "deuda" in consulta or "debo" in consulta or "tarjeta" in consulta:
        return await _consulta_deudas(filtros)

    elif "precio" in consulta or "barato" in consulta or "radar" in consulta:
        return await _consulta_precios(filtros)

    elif "utilidad" in consulta or "rentabilidad" in consulta:
        return await _consulta_rentabilidad(filtros)

    else:
        return {"respuesta": mensaje or "📊 Aquí está la información solicitada.", "botones": None}


async def _consulta_gastos(filtros: dict) -> dict:
    unidad_nombre = filtros.get("unidad")
    unidades = listar_unidades()

    if unidad_nombre:
        unidad = next((u for u in unidades if u["nombre"].lower() == unidad_nombre.lower()), None)
    else:
        unidad = None

    ahora = datetime.utcnow()
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_gastos = 0.0
    if unidad:
        movs = listar_movimientos_por_unidad(unidad["id"], desde=inicio_mes, tipo="compra", limit=200)
        total_gastos = sum(m.get("total", 0) for m in movs)
        nombre = unidad["nombre"]
    else:
        for u in unidades:
            movs = listar_movimientos_por_unidad(u["id"], desde=inicio_mes, tipo="compra", limit=200)
            total_gastos += sum(m.get("total", 0) for m in movs)
        nombre = "Global"

    return {
        "respuesta": (
            f"📊 **Gastos del mes** ({nombre})\n\n"
            f"💰 Total gastado: **${total_gastos:,.0f}**\n"
            f"📅 Período: {inicio_mes.strftime('%d/%m/%Y')} → {ahora.strftime('%d/%m/%Y')}\n"
        ),
        "botones": [
            {"texto": "📋 Por categoría", "callback": "consultar|gastos_categoria"},
            {"texto": "📋 Por unidad", "callback": "consultar|gastos_unidad"},
        ],
    }


async def _consulta_inventario(filtros: dict) -> dict:
    db = get_db()
    docs = db.collection("productos").stream()
    productos = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        productos.append(data)

    # Filtrar los que tienen stock > 0
    con_stock = [p for p in productos if p.get("stock_actual", 0) > 0]
    bajo_minimo = [
        p for p in productos
        if 0 < p.get("stock_actual", 0) <= p.get("stock_minimo", 0)
    ]
    sin_stock = [p for p in productos if p.get("stock_actual", 0) <= 0 and p.get("stock_minimo", 0) > 0]

    respuesta = "📦 **Inventario Actual**\n\n"

    if con_stock:
        respuesta += "📋 **Con stock:**\n"
        for p in sorted(con_stock, key=lambda x: x.get("stock_actual", 0), reverse=True)[:10]:
            respuesta += f"  • {p['nombre_principal']}: {p['stock_actual']} {p.get('unidad_medida', 'unidad')}\n"

    if bajo_minimo:
        respuesta += "\n⚠️ **Bajo stock mínimo:**\n"
        for p in bajo_minimo[:5]:
            respuesta += f"  • {p['nombre_principal']}: {p['stock_actual']}/{p['stock_minimo']} {p.get('unidad_medida', 'unidad')}\n"

    if sin_stock:
        respuesta += "\n🛑 **Sin stock (requiere compra):**\n"
        for p in sin_stock[:5]:
            respuesta += f"  • {p['nombre_principal']} (mín: {p['stock_minimo']})\n"

    if not con_stock and not bajo_minimo and not sin_stock:
        respuesta += "No hay productos registrados aún."

    return {"respuesta": respuesta, "botones": None}


async def _consulta_deudas(filtros: dict) -> dict:
    cuentas = listar_cuentas()
    tarjetas = [c for c in cuentas if c.get("tipo") == "tarjeta_credito" and c.get("activa")]

    if not tarjetas:
        return {"respuesta": "💳 No tienes tarjetas de crédito registradas.", "botones": None}

    respuesta = "💳 **Estado de Tarjetas**\n\n"
    for t in tarjetas:
        ti = t.get("tarjeta_info", {})
        respuesta += (
            f"🏦 {t['nombre']}\n"
            f"   Saldo usado: ${abs(t.get('saldo_actual', 0)):,.0f}\n"
            f"   Cierre: día {ti.get('fecha_cierre', '?')} | Pago: día {ti.get('fecha_pago', '?')}\n\n"
        )

    return {"respuesta": respuesta, "botones": None}


async def _consulta_precios(filtros: dict) -> dict:
    producto_nombre = filtros.get("producto", "")
    if not producto_nombre:
        return {"respuesta": "¿De qué producto quieres comparar precios?", "botones": None}

    producto = buscar_producto_por_nombre(producto_nombre)
    if not producto:
        return {"respuesta": f"No tengo registrado el producto \"{producto_nombre}\".", "botones": None}

    radares = listar_radar_por_producto(producto["id"], limit=10)

    respuesta = f"📡 **Radar: {producto['nombre_principal']}**\n\n"
    respuesta += f"📊 Mejor precio histórico: ${producto.get('mejor_precio_historico') or 'N/A'}\n"
    respuesta += f"📊 Último precio: ${producto.get('ultimo_precio') or 'N/A'}\n"
    respuesta += f"📊 Precio promedio: ${producto.get('precio_promedio') or 'N/A'}\n\n"

    if radares:
        respuesta += "🏪 **Precios observados:**\n"
        for r in radares[:5]:
            respuesta += f"  • ${r['precio']:,.0f} en {r.get('comercio_nombre', '?')} ({r.get('fecha', '')})\n"

    return {"respuesta": respuesta, "botones": None}


async def _consulta_rentabilidad(filtros: dict) -> dict:
    unidades = listar_unidades()
    ahora = datetime.utcnow()
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    respuesta = "📈 **Rentabilidad del Mes**\n\n"

    total_ingresos = 0.0
    total_gastos = 0.0

    for u in unidades:
        compras = listar_movimientos_por_unidad(u["id"], desde=inicio_mes, tipo="compra", limit=200)
        ventas = listar_movimientos_por_unidad(u["id"], desde=inicio_mes, tipo="venta", limit=200)

        gastos = sum(m.get("total", 0) for m in compras)
        ingresos = sum(m.get("total", 0) for m in ventas)
        utilidad = ingresos - gastos

        total_gastos += gastos
        total_ingresos += ingresos

        if gastos > 0 or ingresos > 0:
            emoji = "🟢" if utilidad >= 0 else "🔴"
            respuesta += (
                f"{emoji} **{u['nombre']}**\n"
                f"   Ingresos: ${ingresos:,.0f}\n"
                f"   Gastos: ${gastos:,.0f}\n"
                f"   Utilidad: ${utilidad:,.0f}\n\n"
            )

    utilidad_global = total_ingresos - total_gastos
    respuesta += (
        f"🌐 **Global**\n"
        f"   Ingresos: ${total_ingresos:,.0f}\n"
        f"   Gastos: ${total_gastos:,.0f}\n"
        f"   Utilidad: **${utilidad_global:,.0f}**\n"
    )

    return {"respuesta": respuesta, "botones": None}


# ══════════════════════════════════════════════════════════════
# CORRECCIONES Y APRENDIZAJE
# ══════════════════════════════════════════════════════════════

async def _procesar_correccion(datos: dict, user_id: str, mensaje: str) -> dict:
    texto_original = datos.get("texto_original", "")
    texto_corregido = datos.get("texto_corregido", "")
    tipo = datos.get("tipo", "producto_alias")

    guardar_correccion({
        "texto_original": texto_original,
        "texto_corregido": texto_corregido,
        "tipo": tipo,
        "usuario": user_id,
    })

    # También actualizar el alias del producto si existe
    if tipo == "producto_alias":
        producto = buscar_producto_por_nombre(texto_corregido)
        if producto:
            from app.models.firestore import agregar_alias_producto
            agregar_alias_producto(producto["id"], texto_original)

    return {
        "respuesta": (
            f"✅ **¡Aprendido!**\n\n"
            f"\"{texto_original}\" → \"{texto_corregido}\"\n\n"
            f"No volveré a preguntar por esto. {mensaje}"
        ),
        "botones": None,
    }


async def _confirmar_duplicado(datos: dict, user_id: str) -> dict:
    """Confirma o rechaza un duplicado detectado."""
    confirmacion = datos.get("confirmacion", "no")
    datos_pendientes = datos.get("datos_pendientes", {})

    if confirmacion == "si" and datos_pendientes:
        movimiento = crear_movimiento(datos_pendientes)

        # También actualizar stock (la compra original no lo hizo por estar pendiente)
        items = datos_pendientes.get("items", [])
        total = datos_pendientes.get("total", 0)
        for item in items:
            prod = obtener_producto(item["producto_id"])
            if prod:
                nuevo_stock = prod.get("stock_actual", 0) + item["cantidad"]
                actualizar_producto(item["producto_id"], {
                    "stock_actual": nuevo_stock,
                    "ultimo_precio": item["precio_unitario"],
                })

        # Actualizar saldo si corresponde
        cuenta_id = datos_pendientes.get("cuenta_id")
        estado_pago = datos_pendientes.get("estado_pago", "pagado")
        if cuenta_id and estado_pago == "pagado":
            actualizar_saldo_cuenta(cuenta_id, -total)

        registrar_evento({
            "tipo": "creacion", "entidad": "movimiento",
            "entidad_id": movimiento["id"], "usuario": user_id,
            "cambios": {"total": total, "confirmado_duplicado": True},
        })

        return {
            "respuesta": f"✅ **Compra registrada** (confirmada manualmente)\n💰 Total: ${total:,.0f}",
            "botones": None,
        }
    else:
        return {
            "respuesta": "❌ Compra cancelada. No se registró ningún movimiento.",
            "botones": None,
        }


async def _crear_unidad(datos: dict, user_id: str, mensaje: str) -> dict:
    from app.models.firestore import crear_unidad
    unidad = crear_unidad({
        "nombre": datos["nombre"],
        "descripcion": datos.get("descripcion", ""),
        "color": datos.get("color", "#4F46E5"),
        "created_by": user_id,
    })
    registrar_evento({
        "tipo": "creacion", "entidad": "unidad",
        "entidad_id": unidad["id"], "usuario": user_id,
    })
    return {
        "respuesta": f"🏢 **Unidad creada**: {unidad['nombre']}\n\n{mensaje}",
        "botones": None,
    }


async def _crear_producto(datos: dict, user_id: str, mensaje: str) -> dict:
    producto = crear_producto({
        "nombre_principal": datos["nombre"],
        "unidad_medida": datos.get("unidad_medida", "unidad"),
        "stock_minimo": datos.get("stock_minimo", 0),
    })
    return {
        "respuesta": f"📦 **Producto creado**: {producto['nombre_principal']}\n\n{mensaje}",
        "botones": None,
    }
