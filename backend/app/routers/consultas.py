"""Router de Consultas Inteligentes"""
from datetime import datetime
from fastapi import APIRouter, Query
from app.core.rules import (
    _consulta_gastos, _consulta_inventario, _consulta_deudas,
    _consulta_precios, _consulta_rentabilidad,
)

router = APIRouter()


@router.get("/gastos")
def get_gastos(unidad: str | None = None):
    """Consulta gastos del mes actual."""
    import asyncio
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(
        _consulta_gastos({"unidad": unidad})
    )
    loop.close()
    return result


@router.get("/inventario")
def get_inventario():
    import asyncio
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(_consulta_inventario({}))
    loop.close()
    return result


@router.get("/deudas")
def get_deudas():
    import asyncio
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(_consulta_deudas({}))
    loop.close()
    return result


@router.get("/precios")
def get_precios(producto: str = Query(...)):
    import asyncio
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(
        _consulta_precios({"producto": producto})
    )
    loop.close()
    return result


@router.get("/rentabilidad")
def get_rentabilidad():
    import asyncio
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(_consulta_rentabilidad({}))
    loop.close()
    return result
