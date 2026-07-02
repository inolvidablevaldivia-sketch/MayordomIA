"""Router de Unidades"""
from fastapi import APIRouter, HTTPException
from app.models.firestore import (
    crear_unidad, obtener_unidad, listar_unidades,
    actualizar_unidad, archivar_unidad, registrar_evento,
)

router = APIRouter()


@router.get("/")
def get_unidades(activas: bool = True):
    return listar_unidades(activas=activas)


@router.get("/{unidad_id}")
def get_unidad(unidad_id: str):
    u = obtener_unidad(unidad_id)
    if not u:
        raise HTTPException(404, "Unidad no encontrada")
    return u


@router.post("/")
def post_unidad(data: dict):
    u = crear_unidad(data)
    registrar_evento({
        "tipo": "creacion", "entidad": "unidad",
        "entidad_id": u["id"], "usuario": data.get("created_by", "default"),
    })
    return u


@router.put("/{unidad_id}")
def put_unidad(unidad_id: str, data: dict):
    u = actualizar_unidad(unidad_id, data)
    if not u:
        raise HTTPException(404, "Unidad no encontrada")
    registrar_evento({
        "tipo": "edicion", "entidad": "unidad",
        "entidad_id": unidad_id, "usuario": "default",
        "cambios": data,
    })
    return u


@router.delete("/{unidad_id}")
def delete_unidad(unidad_id: str):
    u = archivar_unidad(unidad_id)
    if not u:
        raise HTTPException(404, "Unidad no encontrada")
    registrar_evento({
        "tipo": "archivado", "entidad": "unidad",
        "entidad_id": unidad_id, "usuario": "default",
    })
    return {"mensaje": "Unidad archivada", "unidad": u}
