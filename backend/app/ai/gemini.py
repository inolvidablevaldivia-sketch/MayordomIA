"""
MayordomIA - Integracion con Gemini (IA conversacional)
El motor que comprende el lenguaje natural del usuario.
"""
from __future__ import annotations

import json
import hashlib
import logging
from datetime import datetime
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

_gemini_client = None


def _get_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _gemini_client


SYSTEM_PROMPT = """Eres MayordomIA, un asistente financiero y administrativo personal.

Tu funcion es ayudar al usuario a gestionar sus finanzas personales y multiples emprendimientos desde una conversacion natural.

## FILOSOFIA
- Conversacional: entiendes lenguaje natural, como si hablaras con una persona.
- Modo rapido: aceptas datos separados por comas (cantidad, producto, precio, comercio).
- Aprendes: cada correccion que el usuario haga la recuerdas para siempre.
- Solo preguntas cuando hay incertidumbre real.
- NUNCA tomas decisiones que impliquen riesgo financiero sin confirmacion.
- Siempre pides confirmacion ante posible DUPLICACION de gastos/ingresos.

## TUS CAPACIDADES
1. Registrar COMPRAS, USOS, VENTAS, MERMAS, DEVOLUCIONES
2. Consultar saldos, gastos, ingresos, inventario
3. Comparar precios entre comercios (Radar)
4. Generar reportes (diario, semanal, mensual, anual, por unidad, por categoria)
5. Responder sobre estado de cuentas y tarjetas

## DATOS DEL USUARIO
{contexto}

## REGLAS
- Cuando el usuario escriba un registro, extrae: tipo de movimiento, productos, cantidades, precios, comercio, unidad, medio de pago, fecha.
- Si falta informacion ESENCIAL, pregunta SOLO lo indispensable usando botones.
- Si detectas posible duplicado, pregunta ANTES de registrar.
- Los precios en CLP (pesos chilenos) pueden escribirse como: $150.000, 150000, 150k.
- El usuario puede escribir "2, Neucober 404 1kg, 6490, La Barata" (modo rapido).
- Si el usuario dice "Quedan 8" refiriendose a un producto, calcula la diferencia con el stock anterior.
- Si el usuario dice "Radar" seguido de producto, precio, comercio, registra en radar.

## FORMATO DE RESPUESTA INTERNA
Cuando necesites ejecutar una accion, responde con un JSON valido dentro de ```json ... ```:

Para registrar compra:
```json
{{"accion": "registrar_compra", "datos": {{"tipo": "compra", "items": [{{"producto_nombre": "...", "cantidad": 1.0, "precio_unitario": 1000}}], "comercio_nombre": "...", "unidad_nombre": "...", "total": 1000, "medio_pago": "efectivo"}}, "mensaje": "Registrando compra..."}}
```

Responde SIEMPRE con un JSON de accion + un mensaje amigable para el usuario.
"""


def generar_contexto(unidades, productos, comercios, cuentas, correcciones):
    ctx_parts = []
    if unidades:
        ctx_parts.append("## UNIDADES DEL USUARIO")
        for u in unidades:
            ctx_parts.append(f"- {u['nombre']} (ID: {u['id']}) [{u.get('estado', 'activa')}]")
    if productos:
        ctx_parts.append("\n## PRODUCTOS CONOCIDOS")
        for p in productos[:30]:
            aliases = ", ".join(p.get("aliases", []))
            alias_str = f" | Aliases: {aliases}" if aliases else ""
            ctx_parts.append(
                f"- {p['nombre_principal']} | Stock: {p.get('stock_actual', 0)} {p.get('unidad_medida', 'unidad')}"
                f" | Ultimo precio: ${p.get('ultimo_precio') or 'N/A'}{alias_str}"
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
                tarjeta = f" | Cierre: dia {ti.get('fecha_cierre', '?')} | Pago: dia {ti.get('fecha_pago', '?')}"
            ctx_parts.append(f"- {c['nombre']} ({tipo}) | Saldo: ${saldo:,.0f}{tarjeta}")
    if correcciones:
        ctx_parts.append("\n## CORRECCIONES APRENDIDAS (Alias)")
        for corr in correcciones[:20]:
            ctx_parts.append(
                f"- \"{corr['texto_original']}\" -> \"{corr['texto_corregido']}\" "
                f"({corr['tipo']}, usado {corr.get('contador_usos', 1)}x)"
            )
    return "\n".join(ctx_parts) if ctx_parts else "No hay datos registrados aun."


async def procesar_mensaje(texto, user_id, contexto, historial=None):
    client = _get_client()
    full_prompt = SYSTEM_PROMPT.replace("{contexto}", contexto)
    user_message = f"Usuario ({user_id}): {texto}"
    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[{"role": "user", "parts": [{"text": full_prompt + "\n\n---\n\n" + user_message}]}],
            config={"temperature": 0.3, "top_p": 0.9, "max_output_tokens": 1024},
        )
        return _parsear_respuesta(response.text.strip())
    except Exception as e:
        return {"accion": "error", "mensaje": "Lo siento, tuve un problema al procesar tu mensaje.", "error": str(e)}


def _parsear_respuesta(texto):
    if "```json" in texto:
        start = texto.index("```json") + 7
        end = texto.index("```", start)
        json_str = texto[start:end].strip()
        try:
            accion_data = json.loads(json_str)
            mensaje_amigable = texto[: texto.index("```json")].strip()
            if not mensaje_amigable:
                mensaje_amigable = texto[end + 3:].strip()
            accion_data["mensaje"] = accion_data.get("mensaje", mensaje_amigable)
            return accion_data
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass
    return {"accion": "conversar", "mensaje": texto}


async def extraer_de_boleta(texto_ocr):
    """Extrae info de boleta. Intento 1: Gemini. Intento 2: Regex."""
    import re

    # Intento 1: Gemini
    try:
        client = _get_client()
        prompt = (
            'Devuelve SOLO JSON sin markdown:\n'
            '{"comercio_nombre":"Nombre","fecha":"YYYY-MM-DD",'
            '"items":[{"producto_nombre":"X","cantidad":1,"precio_unitario":1000,"subtotal":1000}],'
            '"total":44730,"numero_documento":"123"}\n\n'
            'Agrupa productos iguales, precio_unitario=subtotal/cantidad, '
            'ignora NETO/IVA/VUELTO/RUT/direcciones/URLs.\n\n'
            f'Texto:\n{texto_ocr}'
        )
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config={"temperature": 0.0, "max_output_tokens": 2048},
        )
        resp_text = response.text.strip()
        if resp_text.startswith("```"):
            resp_text = resp_text.split("```")[1]
            if resp_text.startswith("json"):
                resp_text = resp_text[4:]
            resp_text = resp_text.strip()
        result = json.loads(resp_text)
        if result.get("items"):
            return result
    except Exception:
        pass

    # Intento 2: Regex (no depende de IA)
    items = []
    comercio = None
    fecha = None
    total = 0.0
    num_doc = None

    for pat in [
        r'Comercio\s*:?\s*(.+)',
        r'SOCIEDAD COMERCIAL\s+(.+)',
        r'(LA BARATA|JUMBO|LIDER|UNIMARC|SANTA ISABEL|TOTTUS|MAYORISTA\s*\d+)',
    ]:
        m = re.search(pat, texto_ocr, re.IGNORECASE)
        if m:
            comercio = (m.group(1) if m.lastindex else m.group(0)).strip()
            break

    fm = re.search(r'Fecha\s*:?\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', texto_ocr)
    if fm:
        d, mo, y = int(fm.group(1)), int(fm.group(2)), int(fm.group(3))
        if y < 100:
            y += 2000
        fecha = f"{y:04d}-{mo:02d}-{d:02d}"

    dm = re.search(r'(?:N\*|N)\s*(\d+)', texto_ocr)
    if dm:
        num_doc = dm.group(1)

    for m in re.finditer(
        r'(\d+)\s+([A-Za-z][A-Za-z0-9\s\.\-]{2,}?)\s+\$\s*([\d\.]+)',
        texto_ocr,
    ):
        cant = float(m.group(1))
        nombre = m.group(2).strip()
        for bad in [
            'CANT', 'ITEM', 'SUBTOTAL', 'NETO', 'IVA', 'VUELTO', 'TOTAL',
            'RUT', 'Giro:', 'Direccion:', 'Comuna:', 'Ciudad:', 'Fono:',
            'COMPROBANTE', 'VENTA', 'SOCIEDAD', 'COMERCIAL', 'LIMITADA',
            'LACTEOS', 'ABARROTES', 'HUEVOS', 'VALDIVIA',
        ]:
            nombre = nombre.replace(bad, '')
        nombre = ' '.join(nombre.split())
        if len(nombre) < 5 or '.CL' in nombre.upper() or 'WWW.' in nombre.upper():
            continue
        subtotal = float(m.group(3).replace('.', ''))
        items.append({
            "producto_nombre": nombre.strip(),
            "cantidad": cant,
            "precio_unitario": round(subtotal / cant),
            "subtotal": subtotal,
        })

    tm = re.search(r'TOTAL\s*:?\s*\$\s*([\d\.]+)', texto_ocr)
    if tm:
        total = float(tm.group(1).replace('.', ''))

    if items:
        return {
            "comercio_nombre": comercio or "Desconocido",
            "fecha": fecha,
            "items": items,
            "total": total or sum(i["subtotal"] for i in items),
            "numero_documento": num_doc,
            "moneda": "CLP",
        }

    return {"error": "no se pudo extraer", "raw_text": texto_ocr[:500]}


def generar_fingerprint(comercio, fecha, total, items, numero_documento=None):
    partes = [comercio.strip().lower(), fecha[:10], str(round(total))]
    if numero_documento:
        partes.append(numero_documento.strip())
    items_str = sorted([
        f"{i.get('producto_nombre', '')}:{i.get('cantidad', 0)}"
        for i in items
    ])
    partes.extend(items_str)
    return hashlib.sha256("|".join(partes).encode()).hexdigest()[:16]
