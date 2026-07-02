"""Router de Comercios"""
from fastapi import APIRouter, HTTPException
from app.models.firestore import (
    crear_comercio, buscar_comercio_por_nombre, listar_comercios,
    fusionar_comercios, registrar_evento, get_db,
)

router = APIRouter()


@router.get("/")
def get_comercios():
    return listar_comercios()


@router.post("/")
def post_comercio(data: dict):
    c = crear_comercio(data)
    registrar_evento({
        "tipo": "creacion", "entidad": "comercio",
        "entidad_id": c["id"], "usuario": "default",
    })
    return c


@router.post("/fusionar")
def post_fusionar(data: dict):
    origen = data.get("origen_id")
    destino = data.get("destino_id")
    if not origen or not destino:
        raise HTTPException(400, "origen_id y destino_id requeridos")
    c = fusionar_comercios(origen, destino)
    if not c:
        raise HTTPException(404, "Comercio destino no encontrado")
    registrar_evento({
        "tipo": "fusion", "entidad": "comercio",
        "entidad_id": destino, "usuario": "default",
    })
    return c


@router.put("/{comercio_id}")
def put_comercio(comercio_id: str, data: dict):
    db = get_db()
    ref = db.collection("comercios").document(comercio_id)
    if not ref.get().exists:
        raise HTTPException(404, "Comercio no encontrado")
    ref.update(data)
    return {**ref.get().to_dict(), "id": comercio_id}
