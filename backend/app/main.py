"""
MayordomIA - Aplicación Principal
FastAPI + Webhook de Telegram + Dashboard API
"""
from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.APP_LOG_LEVEL, "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("mayordomia")


# ─── Lifespan ────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación."""
    logger.info("🚀 Iniciando MayordomIA...")

    # Iniciar bot de Telegram en segundo plano
    polling_task = None
    if settings.TELEGRAM_BOT_TOKEN:
        try:
            from app.bot.telegram_bot import get_telegram_app
            telegram_app = get_telegram_app()
            await telegram_app.initialize()
            await telegram_app.start()
            polling_task = asyncio.create_task(_polling_loop(telegram_app))
            logger.info("🤖 Bot de Telegram iniciado en modo polling")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo iniciar el bot de Telegram: {e}")
            logger.warning("⚠️ La API y el Dashboard funcionan igual. El bot no está activo.")
    else:
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN no configurado. Bot no iniciado.")

    yield

    # Cleanup
    logger.info("🛑 Apagando MayordomIA...")
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except (asyncio.CancelledError, Exception):
            pass


async def _polling_loop(telegram_app):
    """Loop de polling para el bot de Telegram."""
    try:
        await telegram_app.updater.start_polling(allowed_updates=["message", "callback_query"])
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        await telegram_app.updater.stop()


# ─── App ─────────────────────────────────────────────────────

app = FastAPI(
    title="MayordomIA",
    description="Asistente financiero y administrativo con IA",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "nombre": "MayordomIA",
        "version": "1.0.0",
        "estado": "operativo",
        "lema": "MayordomIA no está diseñado para almacenar datos, sino para comprender la actividad financiera del usuario, aprender de ella y ayudarle a tomar mejores decisiones.",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# ─── Routers ─────────────────────────────────────────────────

from app.routers import unidades, productos, comercios, cuentas, movimientos, consultas, dashboard, categorias

app.include_router(unidades.router, prefix="/api/unidades", tags=["Unidades"])
app.include_router(productos.router, prefix="/api/productos", tags=["Productos"])
app.include_router(comercios.router, prefix="/api/comercios", tags=["Comercios"])
app.include_router(cuentas.router, prefix="/api/cuentas", tags=["Cuentas"])
app.include_router(movimientos.router, prefix="/api/movimientos", tags=["Movimientos"])
app.include_router(consultas.router, prefix="/api/consultas", tags=["Consultas"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(categorias.router, prefix="/api/categorias", tags=["Categorías"])


# ─── Entrypoint ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_DEBUG,
        log_level=settings.APP_LOG_LEVEL.lower(),
    )
