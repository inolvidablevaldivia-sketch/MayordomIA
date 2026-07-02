"""Router de Movimientos"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from app.models.firestore import (
    crear_movimiento, obtener_movimiento, listar_movimientos_por_unidad,
    registrar_evento, get_db,
)

router = APIRouter()


@router.get("/")
def get_movimientos(
    unidad_id: str | None = None,
    desde: str | None = None,
    hasta: str | None = None,
    tipo: str | None = None,
    limit: int = 50,
):
    if unidad_id:
        d = datetime.fromisoformat(desde) if desde else None
        h = datetime.fromisoformat(hasta) if hasta else None
        return listar_movimientos_por_unidad(
            unidad_id, desde=d, hasta=h, tipo=tipo, limit=limit,
        )
    db = get_db()
    docs = db.collection("movimientos").order_by(
        "fecha", direction="DESCENDING"
    ).limit(limit).stream()
    return [{**d.to_dict(), "id": d.id} for d in docs]


@router.get("/{movimiento_id}")
def get_movimiento(movimiento_id: str):
    m = obtener_movimiento(movimiento_id)
    if not m:
        raise HTTPException(404, "Movimiento no encontrado")
    return m


@router.put("/{movimiento_id}")
def put_movimiento(movimiento_id: str, data: dict):
    db = get_db()
    ref = db.collection("movimientos").document(movimiento_id)
    if not ref.get().exists:
        raise HTTPException(404, "Movimiento no encontrado")
    ref.update(data)
    registrar_evento({
        "tipo": "correccion", "entidad": "movimiento",
        "entidad_id": movimiento_id, "usuario": "default",
        "cambios": data,
    })
    return {**ref.get().to_dict(), "id": movimiento_id}
