"""
MayordomIA - Integración con Gemini (IA conversacional)
El motor que comprende el lenguaje natural del usuario.
"""
from __future__ import annotations

import json
import hashlib
from datetime import datetime
from typing import Any

from app.config import settings

# ─── Cliente Gemini ──────────────────────────────────────────
_gemini_client = None


def _get_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _gemini_client


# ══════════════════════════════════════════════════════════════
# PROMPT DEL SISTEMA
# ══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Eres MayordomIA, un asistente financiero y administrativo personal.

Tu función es ayudar al usuario a gestionar sus finanzas personales y múltiples emprendimientos desde una conversación natural.

## FILOSOFÍA
- Conversacional: entiendes lenguaje natural, como si hablaras con una persona.
- Modo rápido: aceptas datos separados por comas (cantidad, producto, precio, comercio).
- Aprendes: cada corrección que el usuario haga la recuerdas para siempre.
- Solo preguntas cuando hay incertidumbre real.
- NUNCA tomas decisiones que impliquen riesgo financiero sin confirmación.
- Siempre pides confirmación ante posible DUPLICACIÓN de gastos/ingresos.

## TUS CAPACIDADES
1. Registrar COMPRAS, USOS, VENTAS, MERMAS, DEVOLUCIONES
2. Consultar saldos, gastos, ingresos, inventario
3. Comparar precios entre comercios (Radar)
4. Generar reportes (diario, semanal, mensual, anual, por unidad, por categoría)
5. Responder sobre estado de cuentas y tarjetas

## DATOS DEL USUARIO
{contexto}

## REGLAS
- Cuando el usuario escriba un registro, extrae: tipo de movimiento, productos, cantidades, precios, comercio, unidad, medio de pago, fecha.
- Si falta información ESENCIAL, pregunta SOLO lo indispensable usando botones.
- Si detectas posible duplicado, pregunta ANTES de registrar.
- Los precios en CLP (pesos chilenos) pueden escribirse como: $150.000, 150000, 150k.
- El usuario puede escribir "2, Neucober 404 1kg, 6490, La Barata" (modo rápido: cantidad, producto, precio, comercio).
- Si el usuario dice "Quedan 8" refiriéndose a un producto, calcula la diferencia con el stock anterior.
- Si el usuario dice "Radar" seguido de producto, precio, comercio, registra en radar (no afecta inventario).

## FORMATO DE RESPUESTA INTERNA
Cuando necesites ejecutar una acción, responde con un JSON válido dentro de ```json ... ```:

Para registrar compra:
```json
{{"accion": "registrar_compra", "datos": {{"tipo": "compra", "items": [{{"producto_nombre": "...", "cantidad": 1.0, "precio_unitario": 1000}}], "comercio_nombre": "...", "unidad_nombre": "...", "total": 1000, "medio_pago": "efectivo"}}, "mensaje": "Registrando compra..."}}
```

Para consultar:
```json
{{"accion": "consultar", "consulta": "gastos_mes", "filtros": {{"unidad": null, "mes": "actual"}}, "mensaje": "Buscando información..."}}
```

Para radar:
```json
{{"accion": "registrar_radar", "datos": {{"producto_nombre": "...", "precio": 6290, "comercio_nombre": "..."}}, "mensaje": "Precio registrado en radar."}}
```

Si es solo conversación (sin acción):
```json
{{"accion": "conversar", "mensaje": "Tu respuesta aquí"}}
```

Responde SIEMPRE con un JSON de acción + un mensaje amigable para el usuario.
"""


# ══════════════════════════════════════════════════════════════
# FUNCIONES PRINCIPALES
# ══════════════════════════════════════════════════════════════

def generar_contexto(
    unidades: list[dict],
    productos: list[dict],
    comercios: list[dict],
    cuentas: list[dict],
    correcciones: list[dict],
) -> str:
    """Genera el contexto actual para el prompt de la IA."""
    ctx_parts = []

    if unidades:
        ctx_parts.append("## UNIDADES DEL USUARIO")
        for u in unidades:
            ctx_parts.append(f"- {u['nombre']} (ID: {u['id']}) [{u.get('estado', 'activa')}]")

    if productos:
        ctx_parts.append("\n## PRODUCTOS CONOCIDOS")
        for p in productos[:30]:  # limitar para no exceder contexto
            aliases = ", ".join(p.get("aliases", []))
            alias_str = f" | Aliases: {aliases}" if aliases else ""
            ctx_parts.append(
                f"- {p['nombre_principal']} | Stock: {p.get('stock_actual', 0)} {p.get('unidad_medida', 'unidad')}"
                f" | Último precio: ${p.get('ultimo_precio') or 'N/A'}{alias_str}"
            )

    if comercios:
        ctx_parts.append("\n## COMERCIOS CONOCIDOS")
        for c in comercios[:20]:
            ctx_parts.append(f"- {c['nombre']} (ID: {c['id']})")

    if cuentas:
        ctx_parts.append("\n## CUENTAS FINANCIERAS")
        for c in cuentas:
            tipo = c.get("tipo", "efectivo")
            saldo = c.get("saldo_actual", 0)
            tarjeta = ""
            if c.get("tarjeta_info"):
                ti = c["tarjeta_info"]
                tarjeta = f" | Cierre: día {ti.get('fecha_cierre', '?')} | Pago: día {ti.get('fecha_pago', '?')}"
            ctx_parts.append(f"- {c['nombre']} ({tipo}) | Saldo: ${saldo:,.0f}{tarjeta}")

    if correcciones:
        ctx_parts.append("\n## CORRECCIONES APRENDIDAS (Alias)")
        for corr in correcciones[:20]:
            ctx_parts.append(
                f"- \"{corr['texto_original']}\" → \"{corr['texto_corregido']}\" "
                f"({corr['tipo']}, usado {corr.get('contador_usos', 1)}x)"
            )

    return "\n".join(ctx_parts) if ctx_parts else "No hay datos registrados aún. Ayuda al usuario a crear su primera Unidad."


async def procesar_mensaje(
    texto: str,
    user_id: str,
    contexto: str,
    historial: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Procesa un mensaje del usuario con Gemini y devuelve la acción a ejecutar.

    Returns:
        dict con: accion, datos, mensaje, botones_sugeridos
    """
    client = _get_client()

    # Construir historial de conversación
    messages = []
    if historial:
        for h in historial[-10:]:  # últimos 10 mensajes
            messages.append({"role": h.get("rol", "user"), "parts": [h["texto"]]})

    # Prompt completo
    full_prompt = SYSTEM_PROMPT.replace("{contexto}", contexto)

    # Mensaje del usuario
    user_message = f"Usuario ({user_id}): {texto}"

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[
                {"role": "user", "parts": [full_prompt + "\n\n---\n\n" + user_message]}
            ],
            config={
                "temperature": 0.3,
                "top_p": 0.9,
                "max_output_tokens": 1024,
            },
        )

        respuesta_texto = response.text.strip()

        # Intentar extraer el JSON de acción
        return _parsear_respuesta(respuesta_texto)

    except Exception as e:
        return {
            "accion": "error",
            "mensaje": f"Lo siento, tuve un problema al procesar tu mensaje. ¿Podrías intentarlo de nuevo?",
            "error": str(e),
        }


def _parsear_respuesta(texto: str) -> dict[str, Any]:
    """Extrae el JSON de acción de la respuesta de Gemini."""
    # Buscar bloque JSON
    if "```json" in texto:
        start = texto.index("```json") + 7
        end = texto.index("```", start)
        json_str = texto[start:end].strip()
        try:
            accion_data = json.loads(json_str)
            # Extraer mensaje amigable (lo que está fuera del JSON)
            mensaje_amigable = texto[: texto.index("```json")].strip()
            if not mensaje_amigable:
                mensaje_amigable = texto[end + 3:].strip()
            accion_data["mensaje"] = accion_data.get("mensaje", mensaje_amigable)
            return accion_data
        except json.JSONDecodeError:
            pass

    # Si no hay JSON, intentar parsear como JSON puro
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass

    # Fallback: conversación simple
    return {
        "accion": "conversar",
        "mensaje": texto,
    }


async def extraer_de_boleta(texto_ocr: str) -> dict[str, Any]:
    """
    Extrae información estructurada de una boleta/factura usando OCR previo.
    Soporta texto OCR sucio y correcciones manuales del usuario.
    """
    client = _get_client()

    prompt = f"""Eres un extractor de datos de boletas chilenas. Tu tarea es extraer información estructurada incluso si el texto tiene errores de OCR.

Analiza el siguiente texto y devuelve un JSON con:

- comercio_nombre: nombre del local o comercio (ej: "La Barata", "Jumbo", "Lider")
- fecha: en formato ISO (YYYY-MM-DD). Si no hay fecha, usa null.
- items: lista de productos. Para cada uno: {{"producto_nombre": "...", "cantidad": 1.0, "precio_unitario": 1000, "subtotal": 1000}}
- total: el TOTAL final de la boleta (número, sin signo $)
- numero_documento: número de boleta si es visible, si no, null
- moneda: "CLP"

REGLAS IMPORTANTES:
1. AGRUPA productos repetidos (ej: si aparece "NEUCOBER 404" dos veces, súmalos en cantidad)
2. IGNORA líneas que no sean productos (direcciones, RUT, "NETO", "IVA", "VUELTO", "www.", etc.)
3. El PRECIO UNITARIO se calcula como subtotal / cantidad
4. Si el texto está muy dañado, haz tu mejor esfuerzo con lo que haya
5. Nombres de productos: limpia prefijos como números sueltos, normaliza mayúsculas
6. Si ves "NEUCOBER", "NENICOBER", "NEUCABER" o similares, normaliza a "Neucober"
7. SIEMPRE responde con JSON válido. Si no puedes extraer items, usa lista vacía [].

Texto a analizar:
{texto_ocr}

Responde SOLO con JSON válido, sin markdown, sin explicaciones."""

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[prompt],
            config={"temperature": 0.1, "max_output_tokens": 2048},
        )
        texto = response.text.strip()
        # Limpiar markdown si viene envuelto
        if texto.startswith("```"):
            partes = texto.split("```")
            texto = partes[1] if len(partes) > 1 else partes[0]
            if texto.startswith("json"):
                texto = texto[4:]
            texto = texto.strip()

        result = json.loads(texto)

        # Validar que tiene estructura mínima
        if "items" not in result:
            result["items"] = []
        if "total" not in result:
            result["total"] = 0

        return result

    except json.JSONDecodeError:
        # Intentar de nuevo con un prompt más simple
        try:
            response2 = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[prompt + "\n\nIMPORTANTE: Responde SOLO con JSON. Nada de texto adicional."],
                config={"temperature": 0.0, "max_output_tokens": 2048},
            )
            texto2 = response2.text.strip()
            if texto2.startswith("```"):
                texto2 = texto2.split("```")[1]
                if texto2.startswith("json"):
                    texto2 = texto2[4:]
            return json.loads(texto2.strip())
        except Exception:
            return {"error": "no se pudo parsear", "raw_text": texto_ocr}

    except Exception as e:
        return {"error": str(e), "raw_text": texto_ocr}


# ══════════════════════════════════════════════════════════════
# FINGERPRINT (Detección de Duplicados)
# ══════════════════════════════════════════════════════════════

def generar_fingerprint(
    comercio: str,
    fecha: str,
    total: float,
    items: list[dict],
    numero_documento: str | None = None,
) -> str:
    """
    Genera un fingerprint único para detectar duplicados.

    La huella considera: comercio + fecha + total + productos + cantidades + N° doc.
    """
    partes = [
        comercio.strip().lower(),
        fecha[:10],  # solo fecha sin hora
        str(round(total)),
    ]
    if numero_documento:
        partes.append(numero_documento.strip())

    # Items ordenados para consistencia
    items_str = sorted([
        f"{i.get('producto_nombre', '')}:{i.get('cantidad', 0)}"
        for i in items
    ])
    partes.extend(items_str)

    fingerprint = hashlib.sha256("|".join(partes).encode()).hexdigest()[:16]
    return fingerprint
