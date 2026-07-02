# Módulo: Bot de Telegram

> **Archivo:** `backend/app/bot/telegram_bot.py`  
> **Responsable:** Interfaz conversacional del usuario

---

## Arquitectura del Bot

```
Usuario (Telegram)
  ↓ mensaje de texto/foto
python-telegram-bot (polling)
  ↓ handlers registrados
  ├── /start, /help, /unidades, etc. → Comandos directos
  ├── Texto libre → IA (Gemini) → Motor de Reglas → Respuesta
  ├── Fotos → OCR (Tesseract) → Gemini (extracción) → Confirmación
  └── Botones inline → Callbacks → Ejecución de acciones
```

---

## Comandos Disponibles

| Comando | Función |
|---------|---------|
| `/start` | Bienvenida y registro de usuario |
| `/help` | Guía completa de uso |
| `/unidades` | Lista las unidades activas |
| `/inventario` | Muestra productos con stock > 0 y alertas |
| `/cuentas` | Lista cuentas financieras con saldos |
| `/reporte` | Reporte rápido del mes |
| `/cancelar` | Cancela operación pendiente (duplicado, boleta) |

---

## Flujo de un Mensaje de Texto

1. El usuario escribe algo
2. Se muestra "escribiendo..." (feedback visual)
3. Se construye el **contexto** (unidades, productos, comercios, cuentas, correcciones)
4. Se envía a Gemini con el **historial** reciente (últimos 10 mensajes)
5. Gemini devuelve una acción
6. El motor de reglas ejecuta la acción
7. Se envía la respuesta al usuario con botones inline si corresponde

---

## Manejo de Fotos (Boletas)

1. El usuario envía una foto
2. Se descarga la imagen en máxima calidad
3. **Tesseract OCR** extrae el texto (español)
4. El texto se envía a **Gemini** para estructurarlo
5. Se muestra lo detectado y se pide confirmación con botones
6. Si el usuario confirma, se registra la compra

---

## Estados y Memoria

### Historial de conversación (`_historial`)
Diccionario en memoria `{chat_id: [{rol, texto}, ...]}`.  
En producción, debe migrarse a Firestore o Redis.

### Operaciones pendientes (`_pendientes`)
Cuando se detecta un duplicado o una boleta, los datos quedan pendientes hasta que el usuario confirma/cancela.

---

## Callbacks de Botones

| Prefijo | Acción |
|---------|--------|
| `confirmar_boleta\|` | Confirma/cancela boleta OCR |
| `confirmar_duplicado\|` | Confirma/cancela duplicado |
| `consultar\|` | Ejecuta consulta desde botón |
| `corregir_movimiento\|` | Inicia corrección (en desarrollo) |
| `editar_boleta\|` | Editar unidad/pago de boleta |
