# 🤖 MayordomIA

> *"MayordomIA no está diseñado para almacenar datos, sino para comprender la actividad financiera del usuario, aprender de ella y ayudarle a tomar mejores decisiones."*

**MayordomIA** es un asistente financiero y administrativo basado en Inteligencia Artificial. Administra finanzas personales y múltiples emprendimientos mediante conversaciones naturales desde **Telegram**. Incluye un **Dashboard Web** para administración completa.

---

## 📋 Índice

1. [¿Cómo funciona? (Explicación detallada)](#-cómo-funciona-explicación-detallada)
2. [Arquitectura](#-arquitectura)
3. [Requisitos Previos y Setup](#-requisitos-previos-y-setup)
4. [Estructura del Proyecto](#-estructura-del-proyecto)
5. [Uso del Bot de Telegram](#-uso-del-bot-de-telegram)
6. [Dashboard Web](#-dashboard-web)
7. [API Reference](#-api-reference)
8. [Filosofía y Reglas](#-filosofía-y-reglas)
9. [Documentación Técnica](#-documentación-técnica)

---

## 🧠 ¿Cómo funciona? (Explicación detallada)

Cuando escribes `"Compré 2 chocolates Neucober a $6.490 en La Barata"` en Telegram, esto ocurre dentro de MayordomIA:

### Paso 1: El Bot recibe tu mensaje
El bot de Telegram captura el texto, registra tu usuario en Firestore y muestra "escribiendo...".

### Paso 2: Se construye el CONTEXTO
Antes de llamar a la IA, el bot consulta Firestore y arma un resumen de **todo lo que sabe de ti**:

```
UNIDADES: Delirio de Cacao, Fotografía Inolvidable, Casa
PRODUCTOS: Neucober 404 1kg (Stock: 5kg, Último precio: $6.200)
           Caja bombones (Stock: 12, Aliases: ["caja de bombones"])
COMERCIOS: La Barata, Jumbo, Lider, Mayorista 10
CUENTAS: Efectivo ($150.000), Tarjeta Lider (-$45.000)
CORRECCIONES: "Chocolate Cobertura" → "Neucober 404 1kg" (usada 3 veces)
```

Este contexto permite que la IA "sepa" quién eres y qué tienes, sin que se lo repitas.

### Paso 3: Gemini (IA) analiza tu mensaje
El texto + contexto + historial se envía a **Gemini 2.0 Flash**. Gemini devuelve:

```json
{
  "accion": "registrar_compra",
  "datos": {
    "items": [{"producto_nombre": "Neucober 404 1kg", "cantidad": 2, "precio_unitario": 3245}],
    "comercio_nombre": "La Barata",
    "total": 6490,
    "medio_pago": "efectivo"
  },
  "mensaje": "¡Registrada!"
}
```

### Paso 4: El Motor de Reglas ejecuta (11 operaciones)

1. **Busca/Crea comercio** → "La Barata" (lo crea si no existe)
2. **Resuelve Unidad** → "Casa" por defecto
3. **Resuelve productos** → Busca "Neucober" por nombre Y aliases. **Aquí las correcciones aprendidas evitan preguntar**
4. **Resuelve cuenta** → Busca "efectivo" entre tus cuentas
5. **Calcula total** → $3.245 × 2 = $6.490
6. **Genera fingerprint** → Hash SHA256 de comercio+fecha+total+productos
7. **Verifica duplicados** → Busca misma huella en últimas 24h. Si existe, **pregunta antes de registrar**
8. **Registra movimiento** → `movimientos/{id}` en Firestore
9. **Actualiza stock** → Neucober: 5 + 2 = 7 kg
10. **Actualiza saldo** → Efectivo: $150.000 - $6.490 = $143.510
11. **Audita** → `auditoria/{id}` con qué pasó, quién, cuándo

### Paso 5: Respuesta al usuario
```
🛒 Compra registrada
  • 2x Neucober 404 1kg @ $3.245 = $6.490

💰 Total: $6.490
🏪 La Barata
📦 Unidad: Casa
💳 Efectivo

[✏️ Corregir] [📋 Ver inventario]
```

### ¿Cómo APRENDE?

Cuando escribes `"Chocolate Cobertura = Neucober 404 1kg"`:
1. Se guarda en `aprendizaje/{id}` con contador de usos
2. Se agrega como **alias** del producto Neucober
3. La próxima vez, el contexto incluye la corrección → **la IA no vuelve a preguntar**

### ¿Cómo detecta DUPLICADOS?

Cada compra genera un **fingerprint** = SHA256(comercio|fecha|total|productos|cantidades|n° doc).  
Si existe la misma huella en 24h, pregunta antes de registrar.

### Flujo visual

```
Tú escribes           IA entiende           Motor ejecuta          Firestore guarda
───────────────    ─────────────────    ───────────────────     ──────────────────
"Compré 2...   →  accion: compra    →  1. Busca comercio  →  movimientos/{id}
 $6.490 en..."    items: [chocolate]    2. Busca producto  →  productos/{id}
                  total: 6490           3. Calcula total   →  cuentas/{id}
                  comercio: La Barata   4. Verifica dups   →  auditoria/{id}
                                        5. Actualiza stock
                                        6. Actualiza saldo
                                        7. Audita
```

---

## 🏗 Arquitectura

```
Usuario → Telegram → Gemini (IA) → Motor de Reglas → Firestore → Dashboard Web
```

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| **Bot** | python-telegram-bot | Framework más completo para Telegram |
| **IA** | Google Gemini 2.0 Flash | Rápido, excelente español, gratuito |
| **Backend** | Python 3.12 + FastAPI | Mejor ecosistema IA, Firebase SDK oficial |
| **DB** | Firebase Firestore | NoSQL serverless, sin operaciones |
| **Dashboard** | Next.js 14 + TailwindCSS | Moderno, SSR, gran DX |
| **OCR** | Tesseract | Open source, soporte español |
| **Infra** | Docker Compose | Portabilidad, fácil despliegue |

---

## 📦 Requisitos Previos y Setup

### 1. Bot de Telegram (~5 min)
- Busca `@BotFather` en Telegram
- Envía `/newbot`, sigue las instrucciones
- Guarda el **token**

### 2. Google Gemini API Key (~3 min)
- Ve a [Google AI Studio](https://aistudio.google.com/)
- Crea una API Key (gratis)
- Guarda el key

### 3. Firebase Firestore (~10 min)
- Ve a [Firebase Console](https://console.firebase.google.com/)
- Crea proyecto → Firestore Database (modo prueba)
- Configuración → Cuentas de servicio → Generar clave privada
- Descarga el JSON

### Configurar .env

```bash
cd backend && cp .env.example .env
```

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
GEMINI_API_KEY=AIza...
FIREBASE_PROJECT_ID=mayordomia-xxxxx
FIREBASE_PRIVATE_KEY_ID=abc123...
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEv...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxx@....iam.gserviceaccount.com
FIREBASE_CLIENT_ID=123456789
FIREBASE_CLIENT_CERT_URL=https://...
```

### Ejecutar

```bash
# Docker (recomendado)
docker compose up

# O manual:
make run          # Backend + Dashboard en paralelo
make run-backend  # Solo backend
make run-dashboard # Solo dashboard

# O paso a paso:
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

cd dashboard && npm install && npm run dev
```

### Verificar
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:3000
- Health: http://localhost:8000/health

---

## 📁 Estructura del Proyecto

```
mayordomia/
├── backend/                          # Python / FastAPI
│   ├── app/
│   │   ├── main.py                   # App principal, routers
│   │   ├── config.py                 # Lee .env
│   │   ├── bot/telegram_bot.py       # Bot Telegram (7 comandos + IA)
│   │   ├── ai/gemini.py              # Gemini: prompt, NL, fingerprint
│   │   ├── core/rules.py             # Motor de reglas (11 operaciones)
│   │   ├── models/
│   │   │   ├── schemas.py            # Modelos Pydantic (10 entidades)
│   │   │   └── firestore.py          # CRUD Firestore (10 colecciones)
│   │   └── routers/                  # 7 routers REST
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── dashboard/                        # Next.js / TailwindCSS
│   ├── src/app/                      # 8 páginas
│   ├── src/components/layout/        # Sidebar
│   └── src/lib/api.ts               # Cliente API
├── docs/                             # Documentación técnica
│   └── modulos/                      # Docs por módulo
├── firestore/
│   ├── firestore.rules
│   └── firestore.indexes.json
├── docker-compose.yml
├── Makefile                          # Comandos rápidos
├── .gitignore
└── README.md
```

---

## 💬 Uso del Bot de Telegram

### Comandos
| Comando | Función |
|---------|---------|
| `/start` | Bienvenida + registro |
| `/help` | Guía completa |
| `/unidades` | Ver tus unidades |
| `/inventario` | Stock actual + alertas |
| `/cuentas` | Saldos de cuentas |
| `/reporte` | Reporte del mes |
| `/cancelar` | Cancelar pendiente |

### Registros

**Modo conversacional:**
```
Compré 2 chocolates Neucober 404 1kg a $6.490 en La Barata
Vendí $150.000 en fotografía
Usé 500g de chocolate para producción
Se echaron a perder 3 cajas de bombones
```

**Modo rápido (comas):**
```
2, Neucober 404 1kg, 6490, La Barata
```

**Radar (no afecta inventario):**
```
Radar
Neucober
6290
La Barata
```

### Consultas
```
¿Cuánto gasté este mes?
¿Cuánto gastó Delirio?
¿Cuál es mi utilidad global?
¿Cuánto debo en la Tarjeta Lider?
¿Dónde está más barato el Neucober?
¿Cuánto stock queda de chocolate?
¿Qué productos debo comprar?
```

### Boletas
Envía una foto de la boleta y la IA la procesa con OCR + Gemini.

### Correcciones (Aprendizaje)
```
Chocolate Cobertura = Chocolate Neucober 404 1kg
```

---

## 🖥 Dashboard Web

| Página | Funcionalidades |
|--------|----------------|
| **Dashboard** | KPIs, entidades, alertas stock bajo, últimos movimientos |
| **Unidades** | CRUD, colores, archivar |
| **Categorías** | Vista por unidad |
| **Productos** | CRUD, aliases, stock, fusión de duplicados |
| **Comercios** | CRUD, fusión |
| **Cuentas** | CRUD + tarjetas de crédito (cierre, pago, cupo) |
| **Reportes** | Gastos, rentabilidad, inventario |
| **Configuración** | Conexiones, import/export |

---

## 📡 API Reference

`http://localhost:8000/api/`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/unidades` | Listar unidades |
| POST | `/unidades` | Crear unidad |
| PUT/DELETE | `/unidades/:id` | Editar/Archivar |
| GET | `/productos?buscar=` | Buscar productos |
| POST | `/productos/fusionar` | Fusionar productos |
| GET | `/comercios` | Listar comercios |
| POST | `/comercios/fusionar` | Fusionar comercios |
| GET | `/cuentas` | Listar cuentas |
| GET | `/movimientos?unidad_id=&tipo=` | Listar movimientos |
| GET | `/consultas/gastos?unidad=` | Gastos del mes |
| GET | `/consultas/inventario` | Estado inventario |
| GET | `/consultas/deudas` | Estado tarjetas |
| GET | `/consultas/precios?producto=` | Radar precios |
| GET | `/consultas/rentabilidad` | Rentabilidad |
| GET | `/dashboard/resumen` | Dashboard home |

---

## 🧠 Filosofía y Reglas

1. **Conversacional** — lenguaje natural, como hablar con una persona
2. **Modo rápido** — datos por comas para velocidad
3. **Aprendizaje continuo** — cada corrección se recuerda
4. **Solo pregunta con incertidumbre** — mientras más sabe, menos pregunta
5. **Nunca decide riesgos** — confirma antes de duplicar
6. **Todo queda registrado** — sin eliminaciones físicas, solo auditoría
7. **IA desacoplada** — se puede cambiar Gemini por otro modelo

---

## 📚 Documentación Técnica

Documentación detallada en `docs/`:

| Documento | Contenido |
|-----------|-----------|
| [IA Gemini](docs/modulos/01-ia-gemini.md) | Prompt del sistema, NL, fingerprints |
| [Motor de Reglas](docs/modulos/02-motor-reglas.md) | 11 operaciones, consultas, aprendizaje |
| [Bot Telegram](docs/modulos/03-bot-telegram.md) | Handlers, comandos, OCR, callbacks |
| [Modelos Firestore](docs/modulos/04-modelos-firestore.md) | Colecciones, CRUD, fusión, índices |
| [Docs General](docs/README.md) | Diagramas de flujo, estados, seguridad |

---

## 🔜 Roadmap

- [ ] Reportes automáticos (lunes, inicio de mes, año)
- [ ] Exportación Google Sheets
- [ ] Gráficos avanzados con Recharts
- [ ] Importación masiva Excel/CSV
- [ ] Audio (notas de voz)
- [ ] Multi-usuario con roles
- [ ] Notificaciones proactivas de stock bajo
- [ ] API SII (boletas electrónicas chilenas)
- [ ] PWA para acceso móvil

---

## 👤 Autor

**Daniel Rojas** — Idea original y especificación funcional

---

*"El objetivo es dejar de tomar decisiones por intuición y comenzar a decidir utilizando información real."*
