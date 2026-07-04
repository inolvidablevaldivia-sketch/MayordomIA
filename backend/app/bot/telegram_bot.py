"""
MayordomIA - Bot de Telegram
Interfaz conversacional principal del asistente.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from app.config import settings
from app.ai.gemini import procesar_mensaje, generar_contexto, extraer_de_boleta
from app.core.rules import ejecutar_accion
from app.models.firestore import (
    obtener_o_crear_usuario,
    listar_unidades,
    listar_comercios,
    listar_cuentas,
    obtener_correcciones,
    get_db,
)

logger = logging.getLogger(__name__)

# ─── Historial en memoria (por chat) ─────────────────────────
# En producción, esto debería estar en Firestore o Redis
_historial: dict[str, list[dict]] = {}
_pendientes: dict[str, dict] = {}  # acciones pendientes de confirmación
_correccion_boleta: dict[str, str] = {}  # chat_id → texto OCR esperando corrección


# ══════════════════════════════════════════════════════════════
# INICIALIZACIÓN DEL BOT
# ══════════════════════════════════════════════════════════════

_telegram_app: Application | None = None


def get_telegram_app() -> Application:
    """Obtiene la instancia de la aplicación de Telegram."""
    global _telegram_app
    if _telegram_app is None:
        _telegram_app = (
            Application.builder()
            .token(settings.TELEGRAM_BOT_TOKEN)
            .build()
        )
        _registrar_handlers(_telegram_app)
    return _telegram_app


def _registrar_handlers(app: Application):
    """Registra todos los handlers del bot."""
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("unidades", cmd_unidades))
    app.add_handler(CommandHandler("inventario", cmd_inventario))
    app.add_handler(CommandHandler("cuentas", cmd_cuentas))
    app.add_handler(CommandHandler("reporte", cmd_reporte))
    app.add_handler(CommandHandler("cancelar", cmd_cancelar))

    # Mensajes de texto (principal)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_texto))

    # Fotos (boletas)
    app.add_handler(MessageHandler(filters.PHOTO, manejar_foto))

    # Callbacks de botones inline
    app.add_handler(CallbackQueryHandler(manejar_callback))


# ══════════════════════════════════════════════════════════════
# COMANDOS
# ══════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Bienvenida y registro de usuario."""
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    user_id = str(user.id)

    # Registrar usuario
    usuario = obtener_o_crear_usuario(
        user_id=user_id,
        username=user.username,
        first_name=user.first_name,
    )

    mensaje_bienvenida = (
        f"👋 ¡Hola, {user.first_name or 'usuario'}!\n\n"
        f" Soy **MayordomIA**, tu asistente financiero y administrativo.\n\n"
        f" Puedes hablarme como si fuera una persona:\n\n"
        f" 🛒 *Compré 2 chocolates Neucober a $6.490 en La Barata*\n"
        f" 💰 *Vendí $150.000 en fotografía*\n"
        f" 📊 *¿Cuánto gasté este mes?*\n"
        f" 📡 *Radar: Neucober, 6290, La Barata*\n\n"
        f" También acepto modo rápido:\n"
        f" `2, Neucober 404 1kg, 6490, La Barata`\n\n"
        f" Escribe **/help** para ver todos los comandos.\n"
        f" Escribe **/unidades** para ver tus unidades.\n\n"
        f" ¿En qué puedo ayudarte hoy?"
    )

    await update.message.reply_text(
        mensaje_bienvenida,
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la ayuda del bot."""
    ayuda = (
        "📚 **MayordomIA - Ayuda**\n\n"
        "**Comandos:**\n"
        "/start - Inicio y bienvenida\n"
        "/help - Esta ayuda\n"
        "/unidades - Ver tus unidades\n"
        "/inventario - Ver inventario actual\n"
        "/cuentas - Ver cuentas financieras\n"
        "/reporte - Reporte rápido del mes\n"
        "/cancelar - Cancelar operación pendiente\n\n"
        "**Registros:**\n"
        "• Compras: \"Compré X...\"\n"
        "• Ventas: \"Vendí X...\"\n"
        "• Modo rápido: \"cantidad, producto, precio, comercio\"\n"
        "• Radar: \"Radar: producto, precio, comercio\"\n"
        "• Uso: \"Usé X cantidad de Y\"\n"
        "• Merma: \"Se echaron a perder X...\"\n\n"
        "**Consultas:**\n"
        "• ¿Cuánto gasté este mes?\n"
        "• ¿Cuánto debo en la tarjeta?\n"
        "• ¿Dónde está más barato...?\n"
        "• ¿Cuál es mi utilidad?\n"
        "• ¿Cuánto stock queda de...?\n\n"
        "También puedes enviarme **fotos de boletas** 📸"
    )

    await update.message.reply_text(ayuda, parse_mode="Markdown")


async def cmd_unidades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista las unidades del usuario."""
    unidades = listar_unidades()
    if not unidades:
        await update.message.reply_text(
            "🏢 Aún no tienes Unidades creadas.\n\n"
            "Una Unidad representa una actividad económica: un emprendimiento, tu casa, etc.\n\n"
            "Ejemplo: \"Crear unidad Delirio de Cacao\""
        )
        return

    texto = "🏢 **Tus Unidades**\n\n"
    for u in unidades:
        estado = "🟢" if u.get("estado") == "activa" else "⚫"
        texto += f"{estado} **{u['nombre']}**\n"
        if u.get("descripcion"):
            texto += f"   _{u['descripcion']}_\n"

    await update.message.reply_text(texto, parse_mode="Markdown")


async def cmd_inventario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el inventario actual."""
    db = get_db()
    docs = db.collection("productos").stream()
    productos = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        productos.append(data)

    con_stock = [p for p in productos if p.get("stock_actual", 0) > 0]

    if not con_stock:
        await update.message.reply_text("📦 No hay productos con stock registrado.")
        return

    texto = "📦 **Inventario Actual**\n\n"
    for p in sorted(con_stock, key=lambda x: x.get("stock_actual", 0), reverse=True)[:15]:
        stock_min = p.get("stock_minimo", 0)
        alerta = " ⚠️" if 0 < p.get("stock_actual", 0) <= stock_min else ""
        texto += (
            f"• {p['nombre_principal']}: "
            f"**{p['stock_actual']}** {p.get('unidad_medida', 'unidad')}"
            f"{alerta}\n"
        )

    await update.message.reply_text(texto, parse_mode="Markdown")


async def cmd_cuentas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra las cuentas financieras."""
    cuentas = listar_cuentas()
    if not cuentas:
        await update.message.reply_text(
            "💳 No tienes cuentas financieras registradas.\n\n"
            "Puedes agregar desde el Dashboard Web."
        )
        return

    texto = "💳 **Cuentas Financieras**\n\n"
    for c in cuentas:
        tipo = c.get("tipo", "efectivo")
        saldo = c.get("saldo_actual", 0)
        emoji = {"efectivo": "💵", "cuenta_corriente": "🏦", "cuenta_vista": "🏦",
                  "caja": "📦", "tarjeta_credito": "💳"}.get(tipo, "💰")
        texto += f"{emoji} **{c['nombre']}** ({tipo})\n   Saldo: ${saldo:,.0f}\n"
        if c.get("tarjeta_info"):
            ti = c["tarjeta_info"]
            texto += f"   Cierre: día {ti.get('fecha_cierre', '?')} | Pago: día {ti.get('fecha_pago', '?')}\n"

    await update.message.reply_text(texto, parse_mode="Markdown")


async def cmd_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reporte rápido del mes actual."""
    user_id = str(update.effective_user.id)
    from app.core.rules import _consulta_rentabilidad
    resultado = await _consulta_rentabilidad({})
    await update.message.reply_text(
        resultado.get("respuesta", "📊 No hay datos para mostrar."),
        parse_mode="Markdown",
    )


async def cmd_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela una operación pendiente."""
    chat_id = str(update.effective_chat.id)
    cancelado = False
    if chat_id in _pendientes:
        del _pendientes[chat_id]
        cancelado = True
    if chat_id in _correccion_boleta:
        del _correccion_boleta[chat_id]
        cancelado = True
    if cancelado:
        await update.message.reply_text("❌ Operación cancelada. ¿En qué puedo ayudarte?")
    else:
        await update.message.reply_text("No hay operaciones pendientes para cancelar.")


# ══════════════════════════════════════════════════════════════
# MANEJO DE MENSAJES DE TEXTO
# ══════════════════════════════════════════════════════════════

async def manejar_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa mensajes de texto naturales del usuario."""
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    user_id = str(user.id)
    texto = update.message.text.strip()

    # Registrar usuario
    obtener_o_crear_usuario(user_id, user.username, user.first_name)

    # Enviar "escribiendo..."
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # ─── ¿Es una corrección de boleta? ───
    if chat_id in _correccion_boleta:

                # Si mandó un comando, salir del modo corrección
        if texto.startswith("/"):
            del _correccion_boleta[chat_id]
            await update.message.reply_text("❌ Corrección cancelada. ¿En qué puedo ayudarte?")
            return



        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        try:
            datos_boleta = await extraer_de_boleta(texto)
            if "error" in datos_boleta:
                await update.message.reply_text(
                    f"⚠️ Todavía no pude interpretar la boleta. "
                    f"Intenta escribirlo así:\n\n"
                    f"`Comercio: La Barata\n"
                    f"4x Neucober 404 Morado 1kg $6.390\n"
                    f"2x Neucober 410 Blanco 1kg $9.585\n"
                    f"Total: $44.730`",
                    parse_mode="Markdown",
                )

                # Si el regex tampoco pudo, sacar del modo corrección
                del _correccion_boleta[chat_id]



                return

            items_str = "\n".join([
                f"  • {it.get('cantidad', 1)}x {it.get('producto_nombre', '?')} @ ${it.get('precio_unitario', 0):,.0f}"
                for it in datos_boleta.get("items", [])
            ])

            chat_key = f"boleta_{chat_id}"
            _pendientes[chat_key] = {
                "accion": "registrar_compra",
                "datos": {
                    "tipo": "compra",
                    "items": datos_boleta.get("items", []),
                    "comercio_nombre": datos_boleta.get("comercio_nombre", ""),
                    "total": datos_boleta.get("total", 0),
                    "numero_documento": datos_boleta.get("numero_documento"),
                    "fecha": datos_boleta.get("fecha"),
                },
            }

            keyboard = [[
                InlineKeyboardButton("✅ Sí, registrar", callback_data=f"confirmar_boleta|si|{chat_id}"),
                InlineKeyboardButton("❌ No, cancelar", callback_data=f"confirmar_boleta|no|{chat_id}"),
            ]]

            await update.message.reply_text(
                f"📄 **Boleta interpretada**\n\n"
                f"🏪 {datos_boleta.get('comercio_nombre', 'Desconocido')}\n"
                f"📅 {datos_boleta.get('fecha', '?')}\n\n"
                f"{items_str}\n\n"
                f"💰 Total: **${datos_boleta.get('total', 0):,.0f}**\n\n"
                f"¿Registro esta compra?",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            del _correccion_boleta[chat_id]
            return
        except Exception as e:
            logger.error(f"Error procesando corrección de boleta: {e}")
            del _correccion_boleta[chat_id]

    # ─── Construir contexto actualizado ───
    try:
        unidades = listar_unidades()
        productos_raw = _obtener_todos_los_productos()
        comercios = listar_comercios()
        cuentas = listar_cuentas()
        correcciones = obtener_correcciones()

        contexto = generar_contexto(
            unidades=unidades,
            productos=productos_raw,
            comercios=comercios,
            cuentas=cuentas,
            correcciones=correcciones,
        )
    except Exception as e:
        logger.error(f"Error generando contexto: {e}")
        contexto = "Error cargando datos. Modo conversación básica."

    # ─── Historial de conversación ───
    if chat_id not in _historial:
        _historial[chat_id] = []
    historial = _historial[chat_id]

    # ─── Procesar con IA ───
    try:
        resultado_ia = await procesar_mensaje(
            texto=texto,
            user_id=user_id,
            contexto=contexto,
            historial=historial,
        )
    except Exception as e:
        logger.error(f"Error en IA: {e}")
        await update.message.reply_text(
            "🤖 Lo siento, tuve un problema para entender. ¿Puedes intentarlo de nuevo?",
        )
        return

    # Guardar en historial
    historial.append({"rol": "user", "texto": texto})
    if len(historial) > 50:
        historial = historial[-50:]
    _historial[chat_id] = historial

    # ─── Ejecutar acción ───
    try:
        respuesta = await ejecutar_accion(resultado_ia, user_id)
    except Exception as e:
        logger.error(f"Error ejecutando acción: {e}")
        respuesta = {
            "respuesta": f"❌ Error al procesar: {str(e)}",
            "botones": None,
        }

    # ─── Enviar respuesta ───
    historial.append({"rol": "assistant", "texto": respuesta.get("respuesta", "")})

    # Construir teclado inline si hay botones
    reply_markup = None
    if respuesta.get("botones"):
        keyboard = []
        for btn in respuesta["botones"]:
            keyboard.append([
                InlineKeyboardButton(btn["texto"], callback_data=btn["callback"])
            ])
        reply_markup = InlineKeyboardMarkup(keyboard)

    # Guardar datos pendientes si los hay
    if respuesta.get("accion_pendiente"):
        _pendientes[chat_id] = {
            "accion": respuesta["accion_pendiente"],
            "datos": respuesta.get("datos_pendientes", {}),
        }

    await update.message.reply_text(
        respuesta.get("respuesta", "✅ Procesado."),
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


# ══════════════════════════════════════════════════════════════
# MANEJO DE FOTOS (BOLETAS)
# ══════════════════════════════════════════════════════════════

async def manejar_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa fotos de boletas con OCR y Gemini."""
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    user_id = str(user.id)

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # Obtener la foto de mejor calidad
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    # Descargar imagen
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        img_path = tmp.name

    await update.message.reply_text("🔍 Estoy leyendo la boleta...")

    try:
        # OCR con Tesseract
        import pytesseract
        from PIL import Image

        img = Image.open(img_path)
        texto_ocr = pytesseract.image_to_string(img, lang="spa")

        if not texto_ocr.strip():
            await update.message.reply_text(
                "❌ No pude leer texto en la imagen. ¿Podrías intentar con otra foto más clara?",
            )
            return

        # Enviar a Gemini para estructurar
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        datos_boleta = await extraer_de_boleta(texto_ocr)

        if "error" in datos_boleta:
            # Guardar el texto OCR para que el usuario lo corrija
            _correccion_boleta[chat_id] = texto_ocr
            await update.message.reply_text(
                f"⚠️ Tuve problemas para interpretar la boleta. Esto es lo que leí:\n\n"
                f"```\n{texto_ocr[:500]}\n```\n\n"
                f"**Corrígeme copiando y editando el texto arriba.**\n"
                f"Ejemplo:\n"
                f"`Comercio: La Barata\n"
                f"4x Neucober 404 Morado 1kg $6.390\n"
                f"2x Neucober 410 Blanco 1kg $9.585\n"
                f"Total: $44.730`",
                parse_mode="Markdown",
            )
            return

        # Mostrar lo extraído y pedir confirmación
        items_str = "\n".join([
            f"  • {it.get('cantidad', 1)}x {it.get('producto_nombre', '?')} @ ${it.get('precio_unitario', 0):,.0f}"
            for it in datos_boleta.get("items", [])
        ])

        respuesta = (
            f"📄 **Boleta detectada**\n\n"
            f"🏪 {datos_boleta.get('comercio_nombre', 'Desconocido')}\n"
            f"📅 {datos_boleta.get('fecha', '?')}\n\n"
            f"{items_str}\n\n"
            f"💰 Total: **${datos_boleta.get('total', 0):,.0f}**\n\n"
            f"¿Registro esta compra?"
        )

        # Guardar para confirmación
        chat_key = f"boleta_{chat_id}"
        _pendientes[chat_key] = {
            "accion": "registrar_compra",
            "datos": {
                "tipo": "compra",
                "items": datos_boleta.get("items", []),
                "comercio_nombre": datos_boleta.get("comercio_nombre", ""),
                "total": datos_boleta.get("total", 0),
                "numero_documento": datos_boleta.get("numero_documento"),
                "fecha": datos_boleta.get("fecha"),
            },
        }

        keyboard = [
            [
                InlineKeyboardButton("✅ Sí, registrar", callback_data=f"confirmar_boleta|si|{chat_id}"),
                InlineKeyboardButton("❌ No, cancelar", callback_data=f"confirmar_boleta|no|{chat_id}"),
            ],
            [
                InlineKeyboardButton("✏️ Editar unidad", callback_data=f"editar_boleta|unidad|{chat_id}"),
                InlineKeyboardButton("💳 Editar pago", callback_data=f"editar_boleta|pago|{chat_id}"),
            ],
        ]

        await update.message.reply_text(
            respuesta,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        logger.error(f"Error procesando boleta: {e}")
        await update.message.reply_text(
            f"❌ Error al procesar la boleta: {str(e)}",
        )


# ══════════════════════════════════════════════════════════════
# MANEJO DE CALLBACKS (BOTONES INLINE)
# ══════════════════════════════════════════════════════════════

async def manejar_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa los callbacks de botones inline."""
    query = update.callback_query
    await query.answer()

    data = query.data
    chat_id = str(update.effective_chat.id)
    user_id = str(update.effective_user.id)

    if data.startswith("confirmar_boleta|"):
        await _callback_confirmar_boleta(query, data, chat_id, user_id)
    elif data.startswith("confirmar_duplicado|"):
        await _callback_confirmar_duplicado(query, data, chat_id, user_id)
    elif data.startswith("consultar|"):
        await _callback_consulta(query, data, chat_id, user_id)
    elif data.startswith("corregir_movimiento|"):
        await query.edit_message_text(
            text=f"{query.message.text}\n\n⏳ Función de corrección en desarrollo.",
            parse_mode="Markdown",
        )
    else:
        await query.edit_message_text(
            text=f"{query.message.text}\n\n✅ Acción procesada.",
            parse_mode="Markdown",
        )


async def _callback_confirmar_boleta(query, data: str, chat_id: str, user_id: str):
    """Confirma el registro de una boleta."""
    _, confirmacion, orig_chat = data.split("|")
    chat_key = f"boleta_{orig_chat}"

    if confirmacion == "si":
        datos_pendientes = _pendientes.get(chat_key, {}).get("datos", {})
        if datos_pendientes:
            resultado = await ejecutar_accion(
                {"accion": "registrar_compra", "datos": datos_pendientes},
                user_id,
            )
            await query.edit_message_text(
                text=resultado.get("respuesta", "✅ Boleta registrada."),
                parse_mode="Markdown",
            )
        else:
            await query.edit_message_text("❌ Datos de boleta expirados.")
        if chat_key in _pendientes:
            del _pendientes[chat_key]
    else:
        await query.edit_message_text("❌ Boleta cancelada.")
        if chat_key in _pendientes:
            del _pendientes[chat_key]


async def _callback_confirmar_duplicado(query, data: str, chat_id: str, user_id: str):
    """Confirma o rechaza un duplicado."""
    _, confirmacion, fp = data.split("|")

    if confirmacion == "si":
        datos_pendientes = _pendientes.get(chat_id, {}).get("datos", {})
        if datos_pendientes:
            resultado = await ejecutar_accion(
                {
                    "accion": "confirmar_duplicado",
                    "datos": {"confirmacion": "si", "datos_pendientes": datos_pendientes},
                },
                user_id,
            )
            await query.edit_message_text(
                text=resultado.get("respuesta", "✅ Registrado."),
                parse_mode="Markdown",
            )
        if chat_id in _pendientes:
            del _pendientes[chat_id]
    else:
        await query.edit_message_text("❌ Operación cancelada. No se registró nada.")
        if chat_id in _pendientes:
            del _pendientes[chat_id]


async def _callback_consulta(query, data: str, chat_id: str, user_id: str):
    """Procesa consultas desde botones."""
    _, tipo = data.split("|")
    resultado = await ejecutar_accion(
        {"accion": "consultar", "consulta": tipo},
        user_id,
    )
    await query.edit_message_text(
        text=resultado.get("respuesta", "📊 Consulta procesada."),
        parse_mode="Markdown",
    )


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _obtener_todos_los_productos() -> list[dict]:
    """Obtiene todos los productos de Firestore."""
    try:
        db = get_db()
        docs = db.collection("productos").stream()
        productos = []
        for d in docs:
            data = d.to_dict()
            data["id"] = d.id
            productos.append(data)
        return productos
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════
# ARRANQUE
# ══════════════════════════════════════════════════════════════

async def iniciar_bot():
    """Inicia el bot de Telegram (polling)."""
    app = get_telegram_app()
    logger.info("🤖 MayordomIA Bot iniciado...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("✅ Bot listo. Esperando mensajes...")

    # Mantener vivo
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
