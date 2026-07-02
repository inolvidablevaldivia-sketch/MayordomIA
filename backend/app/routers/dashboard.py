"""Router específico para el Dashboard Web (datos agregados)"""
from fastapi import APIRouter
from app.models.firestore import get_db

router = APIRouter()


@router.get("/resumen")
def get_resumen():
    """Resumen general para el dashboard."""
    db = get_db()

    # Contar documentos por colección
    unidades_count = len(list(db.collection("unidades").where("estado", "==", "activa").stream()))
    productos_count = len(list(db.collection("productos").stream()))
    comercios_count = len(list(db.collection("comercios").stream()))
    cuentas_count = len(list(db.collection("cuentas").where("activa", "==", True).stream()))
    movimientos_count = len(list(db.collection("movimientos").stream()))

    # Total movimientos del mes
    from datetime import datetime
    inicio_mes = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    movs_mes = list(db.collection("movimientos").where("fecha", ">=", inicio_mes).stream())

    total_compras = sum(
        m.to_dict().get("total", 0) for m in movs_mes
        if m.to_dict().get("tipo") == "compra"
    )
    total_ventas = sum(
        m.to_dict().get("total", 0) for m in movs_mes
        if m.to_dict().get("tipo") == "venta"
    )

    return {
        "conteos": {
            "unidades": unidades_count,
            "productos": productos_count,
            "comercios": comercios_count,
            "cuentas": cuentas_count,
            "movimientos": movimientos_count,
        },
        "mes_actual": {
            "compras": total_compras,
            "ventas": total_ventas,
            "utilidad": total_ventas - total_compras,
            "transacciones": len(movs_mes),
        },
    }


@router.get("/movimientos-recientes")
def get_movimientos_recientes(limit: int = 20):
    """Últimos movimientos para el dashboard."""
    db = get_db()
    docs = (
        db.collection("movimientos")
        .order_by("fecha", direction="DESCENDING")
        .limit(limit)
        .stream()
    )
    return [{**d.to_dict(), "id": d.id} for d in docs]


@router.get("/productos-bajos")
def get_productos_bajos():
    """Productos con stock bajo el mínimo."""
    db = get_db()
    docs = db.collection("productos").stream()
    bajos = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        stock = data.get("stock_actual", 0)
        minimo = data.get("stock_minimo", 0)
        if minimo > 0 and stock <= minimo:
            bajos.append(data)
    return sorted(bajos, key=lambda p: p.get("stock_actual", 0))
