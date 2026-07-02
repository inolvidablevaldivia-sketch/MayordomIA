"""
MayordomIA - Capa de datos Firestore
Operaciones CRUD para todas las colecciones.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from google.cloud import firestore
from google.cloud.firestore import Client as FirestoreClient

from app.config import settings

# ─── Conexión a Firestore ────────────────────────────────────
_db: FirestoreClient | None = None


def get_db() -> FirestoreClient:
    """Obtiene la instancia de Firestore (singleton)."""
    global _db
    if _db is None:
        creds = settings.firebase_credentials
        if creds is None:
            raise RuntimeError(
                "Firebase credentials no configuradas. Revisa tu archivo .env"
            )
        import firebase_admin
        from firebase_admin import credentials, firestore as admin_firestore

        if not firebase_admin._apps:
            cred = credentials.Certificate(creds)
            firebase_admin.initialize_app(cred)

        _db = admin_firestore.client()
    return _db


# ─── Helpers ─────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.utcnow()


def _uid() -> str:
    return str(uuid.uuid4())


def _doc_to_dict(doc: firestore.DocumentSnapshot) -> dict:
    """Convierte un documento Firestore a dict con su ID."""
    if not doc.exists:
        return {}
    data = doc.to_dict()
    data["id"] = doc.id
    return data


# ══════════════════════════════════════════════════════════════
# UNIDADES
# ══════════════════════════════════════════════════════════════

UNIDADES = "unidades"


def crear_unidad(data: dict) -> dict:
    db = get_db()
    uid = _uid()
    now = _now()
    doc = {
        "nombre": data["nombre"],
        "descripcion": data.get("descripcion", ""),
        "color": data.get("color", "#4F46E5"),
        "estado": "activa",
        "created_at": now,
        "updated_at": now,
        "created_by": data.get("created_by", "default"),
        "archived_at": None,
    }
    db.collection(UNIDADES).document(uid).set(doc)
    doc["id"] = uid
    return doc


def obtener_unidad(unidad_id: str) -> dict | None:
    db = get_db()
    doc = db.collection(UNIDADES).document(unidad_id).get()
    return _doc_to_dict(doc) if doc.exists else None


def listar_unidades(activas: bool = True) -> list[dict]:
    db = get_db()
    if activas:
        docs = db.collection(UNIDADES).where("estado", "==", "activa").stream()
    else:
        docs = db.collection(UNIDADES).stream()
    return [_doc_to_dict(d) for d in docs]


def actualizar_unidad(unidad_id: str, data: dict) -> dict | None:
    db = get_db()
    ref = db.collection(UNIDADES).document(unidad_id)
    doc = ref.get()
    if not doc.exists:
        return None
    data["updated_at"] = _now()
    ref.update(data)
    return _doc_to_dict(ref.get())


def archivar_unidad(unidad_id: str) -> dict | None:
    db = get_db()
    ref = db.collection(UNIDADES).document(unidad_id)
    doc = ref.get()
    if not doc.exists:
        return None
    updates = {
        "estado": "archivada",
        "archived_at": _now(),
        "updated_at": _now(),
    }
    ref.update(updates)
    return _doc_to_dict(ref.get())


# ══════════════════════════════════════════════════════════════
# CATEGORÍAS
# ══════════════════════════════════════════════════════════════

CATEGORIAS = "categorias"


def crear_categoria(data: dict) -> dict:
    db = get_db()
    uid = _uid()
    now = _now()
    doc = {
        "nombre": data["nombre"],
        "unidad_id": data["unidad_id"],
        "tipo": data.get("tipo", "gasto"),
        "parent_id": data.get("parent_id"),
        "activa": True,
        "created_at": now,
        "updated_at": now,
    }
    db.collection(CATEGORIAS).document(uid).set(doc)
    doc["id"] = uid
    return doc


def listar_categorias_por_unidad(unidad_id: str) -> list[dict]:
    db = get_db()
    docs = (
        db.collection(CATEGORIAS)
        .where("unidad_id", "==", unidad_id)
        .where("activa", "==", True)
        .stream()
    )
    return [_doc_to_dict(d) for d in docs]


# ══════════════════════════════════════════════════════════════
# PRODUCTOS
# ══════════════════════════════════════════════════════════════

PRODUCTOS = "productos"


def crear_producto(data: dict) -> dict:
    db = get_db()
    uid = _uid()
    now = _now()
    doc = {
        "nombre_principal": data["nombre_principal"],
        "aliases": data.get("aliases", []),
        "unidad_medida": data.get("unidad_medida", "unidad"),
        "stock_actual": 0.0,
        "stock_minimo": data.get("stock_minimo", 0.0),
        "precio_promedio": 0.0,
        "mejor_precio_historico": None,
        "ultimo_precio": None,
        "comercios_conocidos": [],
        "categoria_sugerida_id": data.get("categoria_sugerida_id"),
        "created_at": now,
        "updated_at": now,
    }
    db.collection(PRODUCTOS).document(uid).set(doc)
    doc["id"] = uid
    return doc


def obtener_producto(producto_id: str) -> dict | None:
    db = get_db()
    doc = db.collection(PRODUCTOS).document(producto_id).get()
    return _doc_to_dict(doc) if doc.exists else None


def buscar_producto_por_nombre(nombre: str) -> dict | None:
    """Busca producto por nombre principal o alias (búsqueda exacta)."""
    db = get_db()
    # Primero por nombre exacto
    docs = (
        db.collection(PRODUCTOS)
        .where("nombre_principal", "==", nombre)
        .limit(1)
        .stream()
    )
    for d in docs:
        return _doc_to_dict(d)
    # Luego por alias
    docs = (
        db.collection(PRODUCTOS)
        .where("aliases", "array_contains", nombre)
        .limit(1)
        .stream()
    )
    for d in docs:
        return _doc_to_dict(d)
    return None


def buscar_productos_por_texto(texto: str, limit: int = 10) -> list[dict]:
    """Búsqueda parcial (cliente) de productos."""
    db = get_db()
    docs = db.collection(PRODUCTOS).stream()
    results = []
    texto_lower = texto.lower()
    for d in docs:
        data = _doc_to_dict(d)
        nombre = data.get("nombre_principal", "").lower()
        aliases = [a.lower() for a in data.get("aliases", [])]
        if texto_lower in nombre or any(texto_lower in a for a in aliases):
            results.append(data)
            if len(results) >= limit:
                break
    return results


def actualizar_producto(producto_id: str, data: dict) -> dict | None:
    db = get_db()
    ref = db.collection(PRODUCTOS).document(producto_id)
    doc = ref.get()
    if not doc.exists:
        return None
    data["updated_at"] = _now()
    ref.update(data)
    return _doc_to_dict(ref.get())


def agregar_alias_producto(producto_id: str, alias: str) -> dict | None:
    db = get_db()
    ref = db.collection(PRODUCTOS).document(producto_id)
    doc = ref.get()
    if not doc.exists:
        return None
    aliases = doc.to_dict().get("aliases", [])
    if alias not in aliases:
        aliases.append(alias)
        ref.update({"aliases": aliases, "updated_at": _now()})
    return _doc_to_dict(ref.get())


def fusionar_productos(producto_origen_id: str, producto_destino_id: str) -> dict | None:
    """Fusiona producto_origen en producto_destino."""
    db = get_db()
    origen_ref = db.collection(PRODUCTOS).document(producto_origen_id)
    destino_ref = db.collection(PRODUCTOS).document(producto_destino_id)
    origen = origen_ref.get()
    destino = destino_ref.get()

    if not origen.exists or not destino.exists:
        return None

    origen_data = origen.to_dict()
    destino_data = destino.to_dict()

    # Combinar aliases (nombre principal del origen como alias)
    nuevos_aliases = list(set(
        destino_data.get("aliases", [])
        + origen_data.get("aliases", [])
        + [origen_data["nombre_principal"]]
    ))

    # Combinar comercios
    nuevos_comercios = list(set(
        destino_data.get("comercios_conocidos", [])
        + origen_data.get("comercios_conocidos", [])
    ))

    # Actualizar destino
    destino_ref.update({
        "aliases": nuevos_aliases,
        "comercios_conocidos": nuevos_comercios,
        "stock_actual": destino_data.get("stock_actual", 0) + origen_data.get("stock_actual", 0),
        "updated_at": _now(),
    })

    # Marcar origen como fusionado (soft delete)
    origen_ref.update({
        "fusionado_en": producto_destino_id,
        "updated_at": _now(),
    })

    return _doc_to_dict(destino_ref.get())


# ══════════════════════════════════════════════════════════════
# COMERCIOS
# ══════════════════════════════════════════════════════════════

COMERCIOS = "comercios"


def crear_comercio(data: dict) -> dict:
    db = get_db()
    uid = _uid()
    now = _now()
    doc = {
        "nombre": data["nombre"],
        "rubro": data.get("rubro"),
        "direccion": data.get("direccion"),
        "created_at": now,
        "updated_at": now,
    }
    db.collection(COMERCIOS).document(uid).set(doc)
    doc["id"] = uid
    return doc


def buscar_comercio_por_nombre(nombre: str) -> dict | None:
    db = get_db()
    docs = (
        db.collection(COMERCIOS)
        .where("nombre", "==", nombre)
        .limit(1)
        .stream()
    )
    for d in docs:
        return _doc_to_dict(d)
    return None


def listar_comercios() -> list[dict]:
    db = get_db()
    docs = db.collection(COMERCIOS).stream()
    return [_doc_to_dict(d) for d in docs]


def fusionar_comercios(origen_id: str, destino_id: str) -> dict | None:
    db = get_db()
    destino_ref = db.collection(COMERCIOS).document(destino_id)
    if not destino_ref.get().exists:
        return None
    # Marcar origen como fusionado
    db.collection(COMERCIOS).document(origen_id).update({
        "fusionado_en": destino_id,
        "updated_at": _now(),
    })
    return _doc_to_dict(destino_ref.get())


# ══════════════════════════════════════════════════════════════
# CUENTAS FINANCIERAS
# ══════════════════════════════════════════════════════════════

CUENTAS = "cuentas"


def crear_cuenta(data: dict) -> dict:
    db = get_db()
    uid = _uid()
    now = _now()
    doc = {
        "nombre": data["nombre"],
        "tipo": data.get("tipo", "efectivo"),
        "banco": data.get("banco"),
        "numero": data.get("numero"),
        "saldo_actual": data.get("saldo_actual", 0.0),
        "tarjeta_info": data.get("tarjeta_info"),
        "activa": True,
        "created_at": now,
        "updated_at": now,
    }
    db.collection(CUENTAS).document(uid).set(doc)
    doc["id"] = uid
    return doc


def obtener_cuenta(cuenta_id: str) -> dict | None:
    db = get_db()
    doc = db.collection(CUENTAS).document(cuenta_id).get()
    return _doc_to_dict(doc) if doc.exists else None


def listar_cuentas(activas: bool = True) -> list[dict]:
    db = get_db()
    if activas:
        docs = db.collection(CUENTAS).where("activa", "==", True).stream()
    else:
        docs = db.collection(CUENTAS).stream()
    return [_doc_to_dict(d) for d in docs]


def actualizar_saldo_cuenta(cuenta_id: str, delta: float) -> None:
    """Actualiza el saldo de una cuenta sumando/restado delta."""
    db = get_db()
    ref = db.collection(CUENTAS).document(cuenta_id)
    doc = ref.get()
    if doc.exists:
        saldo = doc.to_dict().get("saldo_actual", 0.0)
        ref.update({"saldo_actual": saldo + delta, "updated_at": _now()})


# ══════════════════════════════════════════════════════════════
# MOVIMIENTOS
# ══════════════════════════════════════════════════════════════

MOVIMIENTOS = "movimientos"


def crear_movimiento(data: dict) -> dict:
    db = get_db()
    uid = _uid()
    now = _now()
    doc = {
        "tipo": data["tipo"],
        "unidad_id": data["unidad_id"],
        "cuenta_id": data.get("cuenta_id"),
        "comercio_id": data.get("comercio_id"),
        "items": data.get("items", []),
        "total": data.get("total", 0.0),
        "moneda": data.get("moneda", "CLP"),
        "estado_pago": data.get("estado_pago", "pagado"),
        "fecha": data.get("fecha", now),
        "nota": data.get("nota"),
        "numero_documento": data.get("numero_documento"),
        "fingerprint": data.get("fingerprint"),
        "boleta_url": data.get("boleta_url"),
        "boleta_texto_ocr": data.get("boleta_texto_ocr"),
        "es_correccion": data.get("es_correccion", False),
        "movimiento_original_id": data.get("movimiento_original_id"),
        "created_at": now,
        "updated_at": now,
        "created_by": data.get("created_by", "default"),
    }
    db.collection(MOVIMIENTOS).document(uid).set(doc)
    doc["id"] = uid
    return doc


def obtener_movimiento(mov_id: str) -> dict | None:
    db = get_db()
    doc = db.collection(MOVIMIENTOS).document(mov_id).get()
    return _doc_to_dict(doc) if doc.exists else None


def listar_movimientos_por_unidad(
    unidad_id: str,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    tipo: str | None = None,
    limit: int = 50,
) -> list[dict]:
    db = get_db()
    query = db.collection(MOVIMIENTOS).where("unidad_id", "==", unidad_id)
    if tipo:
        query = query.where("tipo", "==", tipo)
    if desde:
        query = query.where("fecha", ">=", desde)
    if hasta:
        query = query.where("fecha", "<=", hasta)
    docs = query.order_by("fecha", direction=firestore.Query.DESCENDING).limit(limit).stream()
    return [_doc_to_dict(d) for d in docs]


def buscar_duplicado(fingerprint: str, ventana_horas: int = 24) -> list[dict]:
    """Busca movimientos con el mismo fingerprint en las últimas X horas."""
    db = get_db()
    from datetime import timedelta
    desde = _now() - timedelta(hours=ventana_horas)
    docs = (
        db.collection(MOVIMIENTOS)
        .where("fingerprint", "==", fingerprint)
        .where("fecha", ">=", desde)
        .limit(3)
        .stream()
    )
    return [_doc_to_dict(d) for d in docs]


# ══════════════════════════════════════════════════════════════
# RADAR DE PRECIOS
# ══════════════════════════════════════════════════════════════

RADAR = "radar_precios"


def crear_radar(data: dict) -> dict:
    db = get_db()
    uid = _uid()
    now = _now()
    doc = {
        "producto_id": data["producto_id"],
        "producto_nombre": data["producto_nombre"],
        "precio": data["precio"],
        "comercio_id": data.get("comercio_id"),
        "comercio_nombre": data.get("comercio_nombre"),
        "fecha": data.get("fecha", now),
        "created_at": now,
        "created_by": data.get("created_by", "default"),
    }
    db.collection(RADAR).document(uid).set(doc)
    doc["id"] = uid
    return doc


def listar_radar_por_producto(producto_id: str, limit: int = 20) -> list[dict]:
    db = get_db()
    docs = (
        db.collection(RADAR)
        .where("producto_id", "==", producto_id)
        .order_by("fecha", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [_doc_to_dict(d) for d in docs]


# ══════════════════════════════════════════════════════════════
# EVENTOS DE AUDITORÍA
# ══════════════════════════════════════════════════════════════

AUDITORIA = "auditoria"


def registrar_evento(data: dict) -> dict:
    db = get_db()
    uid = _uid()
    doc = {
        "tipo": data["tipo"],
        "entidad": data["entidad"],
        "entidad_id": data["entidad_id"],
        "usuario": data.get("usuario", "default"),
        "fecha": data.get("fecha", _now()),
        "cambios": data.get("cambios", {}),
        "metadata": data.get("metadata", {}),
    }
    db.collection(AUDITORIA).document(uid).set(doc)
    doc["id"] = uid
    return doc


# ══════════════════════════════════════════════════════════════
# APRENDIZAJE (CORRECCIONES)
# ══════════════════════════════════════════════════════════════

APRENDIZAJE = "aprendizaje"


def guardar_correccion(data: dict) -> dict:
    """Guarda una corrección de aprendizaje (alias, asociación)."""
    db = get_db()
    # Verificar si ya existe
    docs = (
        db.collection(APRENDIZAJE)
        .where("texto_original", "==", data["texto_original"])
        .where("texto_corregido", "==", data["texto_corregido"])
        .where("tipo", "==", data["tipo"])
        .limit(1)
        .stream()
    )
    for d in docs:
        # Incrementar contador
        d.reference.update({"contador_usos": firestore.Increment(1)})
        result = _doc_to_dict(d)
        result["contador_usos"] = d.to_dict().get("contador_usos", 0) + 1
        return result

    uid = _uid()
    doc = {
        "texto_original": data["texto_original"],
        "texto_corregido": data["texto_corregido"],
        "tipo": data["tipo"],
        "entidad_id": data.get("entidad_id"),
        "usuario": data.get("usuario", "default"),
        "fecha": _now(),
        "contador_usos": 1,
    }
    db.collection(APRENDIZAJE).document(uid).set(doc)
    doc["id"] = uid
    return doc


def obtener_correcciones(tipo: str | None = None) -> list[dict]:
    """Obtiene todas las correcciones almacenadas para cargar en la memoria de la IA."""
    db = get_db()
    if tipo:
        docs = db.collection(APRENDIZAJE).where("tipo", "==", tipo).stream()
    else:
        docs = db.collection(APRENDIZAJE).stream()
    return [_doc_to_dict(d) for d in docs]


# ══════════════════════════════════════════════════════════════
# USUARIOS
# ══════════════════════════════════════════════════════════════

USUARIOS = "usuarios"


def obtener_o_crear_usuario(user_id: str, username: str | None = None,
                             first_name: str | None = None) -> dict:
    db = get_db()
    ref = db.collection(USUARIOS).document(str(user_id))
    doc = ref.get()
    if doc.exists:
        ref.update({"last_login": _now()})
        return _doc_to_dict(doc)
    data = {
        "username": username,
        "first_name": first_name,
        "rol": "admin",
        "activo": True,
        "created_at": _now(),
        "last_login": _now(),
    }
    ref.set(data)
    data["id"] = str(user_id)
    return data
