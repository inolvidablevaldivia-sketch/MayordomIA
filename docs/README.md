# Documentación Técnica de MayordomIA

## Índice de Documentos

| Documento | Contenido |
|-----------|-----------|
| [Módulo IA (Gemini)](modulos/01-ia-gemini.md) | Prompt del sistema, procesamiento NL, extracción de boletas, fingerprints |
| [Motor de Reglas](modulos/02-motor-reglas.md) | Ejecución de acciones, flujo de compra, consultas, aprendizaje |
| [Bot de Telegram](modulos/03-bot-telegram.md) | Handlers, comandos, flujo de mensajes, OCR de boletas, callbacks |
| [Modelos y Firestore](modulos/04-modelos-firestore.md) | Colecciones, CRUD, fusión de entidades, índices |

---

## Diagrama de Flujo Completo

```
┌──────────────────────────────────────────────────────────────┐
│                        USUARIO                                │
│  "Compré 2 chocolates a $6.490 en La Barata"                 │
└───────────────────────────┬──────────────────────────────────┘
                            │ (Telegram)
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                     BOT DE TELEGRAM                           │
│  • Recibe el texto                                           │
│  • Construye contexto (unidades, productos, etc.)            │
│  • Envía a Gemini                                            │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                     GEMINI (IA)                               │
│  • Entiende: "compré" = acción registrar_compra             │
│  • Extrae: items=[{nombre:"chocolate", cantidad:2,           │
│             precio:3245}], comercio="La Barata"               │
│  • Devuelve JSON con acción + datos + mensaje                │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                   MOTOR DE REGLAS                             │
│  1. Busca/Crea comercio "La Barata"                          │
│  2. Busca/Crea producto "chocolate" (o alias)                │
│  3. Busca cuenta "efectivo"                                  │
│  4. Genera fingerprint                                       │
│  5. Verifica duplicados                                      │
│  6. Crea movimiento en Firestore                             │
│  7. Actualiza stock (+2 chocolates)                          │
│  8. Actualiza saldo cuenta (-$6.490)                         │
│  9. Registra evento de auditoría                             │
│  10. Devuelve respuesta formateada                           │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                     FIRESTORE                                 │
│  movimientos/{id}: {tipo:"compra", items:[...], total:6490}  │
│  productos/{id}: {stock_actual: 12 + 2 = 14}                │
│  cuentas/{id}: {saldo_actual: 100000 - 6490 = 93510}        │
│  auditoria/{id}: {tipo:"creacion", entidad:"movimiento"}     │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              RESPUESTA AL USUARIO                             │
│  🛒 Compra registrada                                        │
│    • 2x chocolate @ $3.245 = $6.490                          │
│  💰 Total: $6.490                                            │
│  🏪 La Barata                                                │
│  📦 Unidad: Casa                                             │
│  💳 Efectivo                                                 │
│  [✏️ Corregir] [📋 Ver inventario]                            │
└──────────────────────────────────────────────────────────────┘
```

---

## Estados y Transiciones

### Estado de un Movimiento

```
                    ┌─────────────┐
        compra con  │             │  compra con
        tarjeta ───→│ COMPROMETIDO│←─── pago diferido
                    │             │
                    └──────┬──────┘
                           │ pago realizado
                           ▼
                    ┌─────────────┐
                    │   PAGADO    │
                    └─────────────┘
```

### Ciclo de Vida de una Unidad

```
CREADA → ACTIVA ←→ ARCHIVADA
           │            │
           └── REACTIVAR ──┘
```

---

## Reglas de Seguridad

En desarrollo se usa modo prueba (acceso total). Para producción, `firestore.rules` define:
- Solo usuarios autenticados pueden leer/escribir
- Cada usuario solo ve sus datos (por implementar multi-tenant)
