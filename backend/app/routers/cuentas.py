"""Router de Cuentas Financieras"""
from fastapi import APIRouter, HTTPException
from app.models.firestore import (
    crear_cuenta, obtener_cuenta, listar_cuentas,
    registrar_evento, get_db,
)

router = APIRouter()


@router.get("/")
def get_cuentas():
    return listar_cuentas()


@router.get("/{cuenta_id}")
def get_cuenta(cuenta_id: str):
    c = obtener_cuenta(cuenta_id)
    if not c:
        raise HTTPException(404, "Cuenta no encontrada")
    return c


@router.post("/")
def post_cuenta(data: dict):
    c = crear_cuenta(data)
    registrar_evento({
        "tipo": "creacion", "entidad": "cuenta",
        "entidad_id": c["id"], "usuario": "default",
    })
    return c


@router.put("/{cuenta_id}")
def put_cuenta(cuenta_id: str, data: dict):
    db = get_db()
    ref = db.collection("cuentas").document(cuenta_id)
    if not ref.get().exists:
        raise HTTPException(404, "Cuenta no encontrada")
    ref.update(data)
    registrar_evento({
        "tipo": "edicion", "entidad": "cuenta",
        "entidad_id": cuenta_id, "usuario": "default",
        "cambios": data,
    })
    return {**ref.get().to_dict(), "id": cuenta_id}
