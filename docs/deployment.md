# Deployment Guide — Scraper V2

## Render (pruebas)

1. Fork o sube el repo a GitHub (solo el directorio `scraper-v2/`)
2. En Render: New → Web Service → Connect repo
3. **Runtime:** Docker
4. **Plan:** Starter ($7/mes) — el Free tier (512MB RAM) no es suficiente para Playwright
5. **Variables de entorno** (en Render dashboard):
   ```
   USE_PLAYWRIGHT=true
   HTTP_TIMEOUT=10
   PLAYWRIGHT_TIMEOUT=15
   ```
6. Deploy → copiar la URL pública (ej: `https://scraper-v2.onrender.com`)

## VPS con Docker

### Requisitos
- Docker y Docker Compose instalados
- Puerto 8000 abierto o proxy inverso (nginx)

### docker-compose.yml
```yaml
version: "3.9"
services:
  scraper:
    build: .
    ports:
      - "8000:8000"
    environment:
      - USE_PLAYWRIGHT=true
      - HTTP_TIMEOUT=10
      - PLAYWRIGHT_TIMEOUT=15
      - MAX_CONCURRENT_PLAYWRIGHT=3
    restart: unless-stopped
```

### Comandos
```bash
# Build y arrancar
docker compose up -d --build

# Ver logs
docker compose logs -f scraper

# Reiniciar
docker compose restart scraper

# Parar
docker compose down
```

### Actualizar
```bash
git pull
docker compose up -d --build
```

## Actualizar n8n tras el despliegue

En el workflow **Scraping webs Outreach V2**, actualizar las URLs en:
- Nodo **Scrape Contact**: `https://TU-URL/scrape`
- Nodo **Scrape Menu**: `https://TU-URL/menu/extract`

Para el endpoint nuevo `/scrape-rich`, añadir un nodo HTTP Request Tool apuntando a `https://TU-URL/scrape-rich`.
