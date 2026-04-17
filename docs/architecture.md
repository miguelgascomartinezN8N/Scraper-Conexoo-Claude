# Arquitectura — Scraper V2

## Diagrama de flujo

```
Petición POST /scrape | /menu/extract | /scrape-rich
            │
            ▼
      main.py (FastAPI, síncrono)
            │
            ▼ por cada dominio
      scraper.py :: scrape_domain()
            │
            ├─► _fetch_http()
            │      requests.get() con User-Agent real
            │      timeout: HTTP_TIMEOUT (default 10s)
            │
            │   HTML obtenido → _extract_all()
            │      ├── extractors/contact.py :: extract_emails()
            │      ├── extractors/contact.py :: extract_phones()
            │      ├── extractors/menu.py :: extract_menu()
            │      ├── extractors/rich.py :: extract_rich()
            │      └── extractors/rich.py :: find_about_url() + fetch
            │
            ▼
      ¿resultado pobre?
      (email=null AND phone=null AND menu<3 items)
            │
            ├── NO → devuelve ScrapeResult, used_playwright=False
            │
            └── SÍ + USE_PLAYWRIGHT=true + browser disponible
                        │
                        ▼
                browser.py :: BrowserManager.get_html()
                        Playwright sync_api, Chromium headless
                        Bloquea: imágenes, fuentes, media, stylesheets
                        Timeout: PLAYWRIGHT_TIMEOUT (default 15s)
                        Semaphore: MAX_CONCURRENT_PLAYWRIGHT (default 3)
                        │
                        ▼
                HTML renderizado → _extract_all() (mismo flujo)
                        │
                        ▼
                devuelve ScrapeResult, used_playwright=True
```

## Decisiones de diseño

### ¿Por qué síncrono?
FastAPI soporta endpoints síncronos (`def` en vez de `async def`). Se eligió síncrono
para evitar complejidad con Playwright, que usa `sync_api`. Mezclar sync/async con
Playwright requiere `asyncio.run()` o `anyio.to_thread`, lo que añade complejidad
innecesaria para este caso de uso.

### ¿Por qué Playwright sync_api?
La API síncrona de Playwright es la opción oficial para scripts Python síncronos.
No requiere un event loop de asyncio corriendo. El semaphore de threading controla
la concurrencia máxima.

### ¿Por qué fallback y no siempre Playwright?
- 70% de webs responden bien a HTTP simple (más rápido, menos memoria)
- Playwright consume ~100MB por instancia de página
- El criterio de fallback cubre los casos donde HTTP falla: webs JS-heavy (Wix, Webflow, React SPA)

### ¿Por qué no persistencia?
Este servicio está diseñado para ser llamado desde n8n workflow por workflow.
n8n gestiona la persistencia (Google Sheets). Añadir base de datos aumentaría
complejidad sin beneficio real para este caso de uso.
