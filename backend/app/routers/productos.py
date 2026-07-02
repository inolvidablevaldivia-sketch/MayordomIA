"""Router de Productos"""
from fastapi import APIRouter, HTTPException
from app.models.firestore import (
    crear_producto, obtener_producto, buscar_producto_por_nombre,
    buscar_productos_por_texto, actualizar_producto,
    agregar_alias_producto, fusionar_productos, registrar_evento,
    get_db,
)

router = APIRouter()


@router.get("/")
def get_productos(buscar: str | None = None):
    if buscar:
        return buscar_productos_por_texto(buscar)
    db = get_db()
    docs = db.collection("productos").stream()
    return [{**d.to_dict(), "id": d.id} for d in docs]


@router.get("/{producto_id}")
def get_producto(producto_id: str):
    p = obtener_producto(producto_id)
    if not p:
        raise HTTPException(404, "Producto no encontrado")
    return p


@router.post("/")
def post_producto(data: dict):
    p = crear_producto(data)
    registrar_evento({
        "tipo": "creacion", "entidad": "producto",
        "entidad_id": p["id"], "usuario": "default",
    })
    return p


@router.put("/{producto_id}")
def put_producto(producto_id: str, data: dict):
    p = actualizar_producto(producto_id, data)
    if not p:
        raise HTTPException(404, "Producto no encontrado")
    return p


@router.post("/{producto_id}/alias")
def post_alias(producto_id: str, alias: dict):
    p = agregar_alias_producto(producto_id, alias.get("alias", ""))
    if not p:
        raise HTTPException(404, "Producto no encontrado")
    return p


@router.post("/fusionar")
def post_fusionar(data: dict):
    origen = data.get("origen_id")
    destino = data.get("destino_id")
    if not origen or not destino:
        raise HTTPException(400, "origen_id y destino_id requeridos")
    p = fusionar_productos(origen, destino)
    if not p:
        raise HTTPException(404, "Producto(s) no encontrado(s)")
    registrar_evento({
        "tipo": "fusion", "entidad": "producto",
        "entidad_id": destino, "usuario": "default",
        "cambios": {"origen": origen, "destino": destino},
    })
    return p
