# API Reference — Scraper V2

Base URL: `http://localhost:8000`

---

## GET /health

Verifica el estado del servicio.

**Response:**
```json
{ "status": "healthy", "version": "2.0.0", "playwright": true }
```

---

## POST /scrape

Extrae emails y teléfonos de una lista de dominios.

**Request:**
```json
{
  "domains": ["empresa.com"],
  "extract_emails": true,
  "extract_phones": true,
  "search_depth": 10,
  "timeout": 10
}
```

**Response:**
```json
{
  "request_id": "req_abc123",
  "results": [{
    "domain": "empresa.com",
    "status": "success",
    "contacts": [
      { "email": "info@empresa.com", "phone": null },
      { "email": null, "phone": "+34912345678" }
    ],
    "emails_adicionales": ["otro@empresa.com"],
    "telefonos_adicionales": [],
    "used_playwright": false,
    "processing_time": 1.23
  }]
}
```

**Status values:** `success` | `no_contacts` | `error`

**curl:**
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{"domains": ["empresa.com"]}'
```

---

## POST /menu/extract

Extrae el menú de navegación principal.

**Request:**
```json
{ "domains": ["empresa.com"], "timeout": 5 }
```

**Response:**
```json
{
  "results": [{
    "domain": "empresa.com",
    "menu_links": [
      { "text": "Inicio", "url": "https://empresa.com/" },
      { "text": "Servicios", "url": "https://empresa.com/servicios" }
    ]
  }]
}
```

**curl:**
```bash
curl -X POST http://localhost:8000/menu/extract \
  -H "Content-Type: application/json" \
  -d '{"domains": ["empresa.com"]}'
```

---

## POST /scrape-rich

Extrae todo: contacto + menú + contexto para IA (título, meta, descripción).

**Request:**
```json
{ "domains": ["empresa.com"], "timeout": 15 }
```

**Response:**
```json
{
  "results": [{
    "domain": "empresa.com",
    "status": "success",
    "titulo_web": "Empresa SL",
    "meta_descripcion": "Agencia de marketing digital.",
    "descripcion_negocio": "Empresa SL. Agencia de marketing digital. Ofrecemos SEO y publicidad.",
    "email_principal": "info@empresa.com",
    "emails_adicionales": [],
    "telefono_principal": "+34912345678",
    "telefonos_adicionales": [],
    "formulario_contacto_url": "https://empresa.com/contacto",
    "menu_links": [],
    "used_playwright": false,
    "processing_time": 2.1
  }]
}
```

**curl:**
```bash
curl -X POST http://localhost:8000/scrape-rich \
  -H "Content-Type: application/json" \
  -d '{"domains": ["empresa.com"]}'
```
