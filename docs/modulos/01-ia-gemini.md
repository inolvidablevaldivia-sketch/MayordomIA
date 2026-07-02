# Módulo: IA (Gemini)

> **Archivo:** `backend/app/ai/gemini.py`  
> **Responsable:** Comprensión de lenguaje natural y decisiones de la IA

---

## Propósito

Este módulo es el **cerebro** de MayordomIA. Se comunica con Google Gemini para:

1. Entender el lenguaje natural del usuario
2. Decidir qué acción ejecutar (registrar compra, consultar, corregir, etc.)
3. Extraer datos de boletas/facturas mediante OCR
4. Generar fingerprints para detección de duplicados

---

## Funciones Principales

### `procesar_mensaje(texto, user_id, contexto, historial) → dict`

**Qué hace:**  
Envía el mensaje del usuario a Gemini junto con el contexto del sistema (unidades, productos, comercios, cuentas, correcciones aprendidas) y el historial reciente de la conversación.

**Cómo funciona:**
1. Construye un prompt con el `SYSTEM_PROMPT` reemplazando `{contexto}` por los datos reales del usuario
2. Envía el mensaje a Gemini con `temperature=0.3` (balance entre creatividad y precisión)
3. Gemini devuelve una respuesta que incluye un bloque JSON con la acción a ejecutar
4. El parser extrae ese JSON y el mensaje amigable para el usuario

**Ejemplo de flujo:**
```
Usuario: "Compré 2 chocolates a $6.490 en La Barata"
         ↓
Gemini analiza y decide: accion = "registrar_compra"
         ↓
Devuelve JSON con items, comercio, total, etc.
         ↓
El motor de reglas ejecuta la compra
```

### `extraer_de_boleta(texto_ocr) → dict`

Extrae información estructurada de una boleta usando OCR previo. Gemini recibe el texto extraído por Tesseract y devuelve un JSON con:
- `comercio_nombre`
- `fecha` (ISO)  
- `items` (producto, cantidad, precio)
- `total`
- `numero_documento`

### `generar_fingerprint(comercio, fecha, total, items, numero_documento) → str`

Genera un hash SHA256 truncado a 16 caracteres que sirve como huella digital única de una compra. Se usa para detectar duplicados.

**Componentes de la huella:**
- Comercio (normalizado a minúsculas)
- Fecha (solo YYYY-MM-DD)
- Total redondeado
- Número de documento (si existe)
- Items ordenados alfabéticamente (producto:cantidad)

---

## Prompt del Sistema

El `SYSTEM_PROMPT` le da personalidad y reglas a la IA:

```markdown
Eres MayordomIA, un asistente financiero y administrativo personal.

FILOSOFÍA:
- Conversacional: entiendes lenguaje natural
- Modo rápido: aceptas "2, producto, precio, comercio"
- Aprendes: cada corrección la recuerdas para siempre
- Solo preguntas con incertidumbre real
- NUNCA decides riesgos sin confirmación
- Confirmas ante posible DUPLICACIÓN

CAPACIDADES:
1. Registrar COMPRAS, USOS, VENTAS, MERMAS, DEVOLUCIONES
2. Consultar saldos, gastos, ingresos, inventario
3. Comparar precios (Radar)
4. Reportes (diario, semanal, mensual, anual)
5. Estado de cuentas y tarjetas
```

---

## Formato de Comunicación

La IA devuelve sus decisiones en bloques JSON:

```json
{
  "accion": "registrar_compra | consultar | conversar | corregir | ...",
  "datos": { ... },
  "mensaje": "texto amigable para el usuario"
}
```

El parser (`_parsear_respuesta`) extrae este JSON incluso si Gemini lo envuelve en markdown o texto adicional.

---

## Por qué Gemini

- **Rápido** (Flash es el modelo más rápido de Google)
- **Excelente en español** (entiende modismos chilenos, CLP, etc.)
- **Barato** (capa gratuita generosa: ~1,500 requests/día)
- **Desacoplable** (el motor de IA está aislado; se puede cambiar a GPT-4, Claude, etc.)

---

## Posibles Mejoras

- [ ] Modo "rápido local" sin llamar a Gemini para registros simples
- [ ] Caché de respuestas frecuentes
- [ ] Fine-tuning con datos históricos del usuario
- [ ] Soporte multimodal (procesar imágenes directamente sin OCR previo)
