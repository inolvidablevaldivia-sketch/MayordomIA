"""Router de Categorías"""
from fastapi import APIRouter, HTTPException
from app.models.firestore import (
    crear_categoria, listar_categorias_por_unidad, get_db, registrar_evento,
)

router = APIRouter()


@router.get("/")
def get_categorias(unidad_id: str | None = None):
    if unidad_id:
        return listar_categorias_por_unidad(unidad_id)
    db = get_db()
    docs = db.collection("categorias").where("activa", "==", True).stream()
    return [{**d.to_dict(), "id": d.id} for d in docs]


@router.post("/")
def post_categoria(data: dict):
    c = crear_categoria(data)
    registrar_evento({
        "tipo": "creacion", "entidad": "categoria",
        "entidad_id": c["id"], "usuario": "default",
    })
    return c


@router.put("/{categoria_id}")
def put_categoria(categoria_id: str, data: dict):
    db = get_db()
    ref = db.collection("categorias").document(categoria_id)
    if not ref.get().exists:
        raise HTTPException(404, "Categoría no encontrada")
    ref.update(data)
    return {**ref.get().to_dict(), "id": categoria_id}


@router.delete("/{categoria_id}")
def delete_categoria(categoria_id: str):
    db = get_db()
    ref = db.collection("categorias").document(categoria_id)
    if not ref.get().exists:
        raise HTTPException(404, "Categoría no encontrada")
    ref.update({"activa": False})
    return {"mensaje": "Categoría desactivada"}
