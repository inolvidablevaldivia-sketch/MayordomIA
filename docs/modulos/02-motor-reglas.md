# Módulo: Motor de Reglas

> **Archivo:** `backend/app/core/rules.py`  
> **Responsable:** Ejecutar la lógica de negocio determinada por la IA

---

## Propósito

El motor de reglas es el **ejecutor**. Recibe la acción decidida por Gemini y la transforma en operaciones concretas en Firestore. Es el puente entre "lo que la IA entendió" y "lo que realmente pasa en la base de datos".

---

## Acciones Soportadas

| Acción | Descripción | Afecta |
|--------|-------------|--------|
| `registrar_compra` | Registra una compra en Firestore | Stock (+), Saldo (-), Productos, Comercios |
| `registrar_venta` | Registra un ingreso por venta | Stock (-), Saldo (+), Productos |
| `registrar_uso` | Descuenta stock sin transacción financiera | Stock (-) |
| `registrar_merma` | Registra pérdida de producto | Stock (-) |
| `registrar_radar` | Registra precio observado (no afecta inventario) | Radar, Producto (mejor precio) |
| `consultar` | Responde consultas (gastos, inventario, deudas, precios, rentabilidad) | Solo lectura |
| `confirmar_duplicado` | Confirma/rechaza una compra duplicada detectada | Movimiento |
| `corregir` | Guarda una corrección de aprendizaje | Aprendizaje, Alias |
| `crear_unidad` | Crea una nueva unidad económica | Unidades |
| `crear_producto` | Crea un nuevo producto | Productos |
| `conversar` | Solo responde texto, sin acción | Nada |

---

## Flujo de una Compra (caso completo)

```
1. Resolver/Crear Comercio → Si no existe, se crea automáticamente
2. Resolver Unidad → Busca por nombre; si no, usa la primera activa
3. Resolver/Crear Productos → Cada ítem se busca por nombre/alias
4. Resolver Cuenta Financiera → Busca por nombre o tipo
5. Calcular Total → Suma de subtotales si no se especificó
6. Generar Fingerprint → Hash para detectar duplicados
7. Verificar Duplicados → Si existe en últimas 24h, pregunta
8. Registrar Movimiento → Crea documento en Firestore
9. Actualizar Stock → Incrementa el stock de cada producto
10. Actualizar Saldo → Descuenta de la cuenta (si es pago inmediato)
11. Auditoría → Registra evento
12. Responder al Usuario → Mensaje formateado con detalles
```

---

## Consultas Inteligentes

### Gastos del mes
Calcula total de compras filtrado por unidad (opcional) y mes actual.

### Inventario
Agrupa productos en 3 categorías:
- **Con stock** (> 0)
- **Bajo mínimo** (0 < stock ≤ stock_minimo)
- **Sin stock** (= 0 y tiene mínimo definido)

### Deudas
Filtra cuentas tipo `tarjeta_credito` activas y muestra saldo usado y fechas de cierre/pago.

### Precios (Radar)
Muestra mejor precio histórico, último precio, precio promedio y los últimos registros de radar.

### Rentabilidad
Por cada unidad: `ingresos (ventas) - gastos (compras)`. Incluye total global.

---

## Sistema de Aprendizaje

Cuando el usuario corrige algo (ej: "Chocolate Cobertura = Chocolate Neucober 404 1kg"):

1. Se guarda la corrección en la colección `aprendizaje` con contador de usos
2. Se agrega el texto original como alias del producto corregido
3. La próxima vez que la IA reciba "Chocolate Cobertura", el contexto incluirá esta corrección
4. **La IA no vuelve a preguntar**

---

## Consideraciones de Diseño

- **Sin eliminaciones físicas**: todo se marca o se actualiza (soft delete)
- **Auditoría completa**: cada operación genera un evento en `auditoria`
- **Idempotencia**: el fingerprint evita duplicados
- **Defaults inteligentes**: si falta info, usa valores por defecto razonables
