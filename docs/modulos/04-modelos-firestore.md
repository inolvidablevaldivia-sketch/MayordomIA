# Módulo: Modelos y Firestore

> **Archivos:** `backend/app/models/schemas.py`, `backend/app/models/firestore.py`  
> **Responsable:** Definición de entidades y operaciones CRUD

---

## Colecciones en Firestore

| Colección | Documento | Descripción |
|-----------|-----------|-------------|
| `unidades` | Una actividad económica | Delirio de Cacao, Fotografía, Casa... |
| `categorias` | Categoría de gasto/ingreso | Insumos, Servicios, Ventas... |
| `productos` | Un producto único | Neucober 404, Caja de bombones... |
| `comercios` | Un local o tienda | Jumbo, La Barata, Lider... |
| `cuentas` | Medio de pago / fuente de dinero | Efectivo, Cta Corriente, Tarjeta Lider... |
| `movimientos` | Una transacción | Compra, venta, uso, merma, devolución |
| `radar_precios` | Precio observado | No afecta inventario ni gastos |
| `auditoria` | Evento de auditoría | Toda operación queda registrada |
| `aprendizaje` | Corrección aprendida | Alias, asociaciones |
| `usuarios` | Usuario de Telegram | ID, nombre, rol, último login |

---

## Operaciones CRUD

Cada colección tiene funciones consistentes:

- `crear_X(data)` → Crea documento con UUID automático
- `obtener_X(id)` → Obtiene un documento por ID
- `listar_X(filtros)` → Lista documentos con filtros
- `actualizar_X(id, data)` → Actualiza campos parciales
- `[soft delete]` → Archivar o marcar como inactivo

---

## Fusión de Productos y Comercios

Cuando existen duplicados:

```python
fusionar_productos(origen_id, destino_id)
```

1. Los aliases del origen se agregan al destino
2. El nombre principal del origen se convierte en alias del destino
3. Los comercios conocidos se combinan
4. El stock se suma
5. El origen se marca como `fusionado_en: destino_id`

Lo mismo aplica para `fusionar_comercios`.

---

## Índices Compuestos Requeridos

Para consultas eficientes, se necesitan los índices definidos en `firestore.indexes.json`:

- `movimientos`: `unidad_id ASC, fecha DESC`
- `movimientos`: `tipo ASC, fecha DESC`
- `movimientos`: `fingerprint ASC, fecha DESC`
- `productos`: `nombre_principal ASC`
- `radar_precios`: `producto_id ASC, fecha DESC`
