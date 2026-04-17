import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from browser import browser_manager
from config import settings
from models import (
    ScrapeRequest, ScrapeResponse, ScrapeResult as ScrapeResultModel, ContactItem,
    MenuRequest, MenuResponse, MenuResult, MenuLink,
    RichRequest, RichResponse, RichResult,
    HealthResponse,
)
from scraper import scrape_domain

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    browser_manager.start(max_concurrent=settings.max_concurrent_playwright)
    yield
    browser_manager.stop()


app = FastAPI(
    title="Scraper V2",
    version="2.0.0",
    description="API de scraping para outreach — emails, teléfonos, menú y contexto para IA",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        playwright=browser_manager.available,
    )


@app.post("/scrape", response_model=ScrapeResponse)
def scrape(request: ScrapeRequest):
    if not request.domains:
        raise HTTPException(status_code=400, detail="Lista de dominios vacía")
    if len(request.domains) > settings.max_domains_per_request:
        raise HTTPException(
            status_code=400,
            detail=f"Máximo {settings.max_domains_per_request} dominios por petición",
        )

    results = []
    for domain in request.domains:
        sr = scrape_domain(domain, timeout=request.timeout)
        contacts = []
        if sr.email_principal:
            contacts.append(ContactItem(email=sr.email_principal))
        if sr.telefono_principal:
            contacts.append(ContactItem(phone=sr.telefono_principal))

        results.append(ScrapeResultModel(
            domain=sr.domain,
            status=sr.status,
            contacts=contacts,
            emails_adicionales=sr.emails_adicionales,
            telefonos_adicionales=sr.telefonos_adicionales,
            used_playwright=sr.used_playwright,
            processing_time=sr.processing_time,
        ))

    return ScrapeResponse(request_id=f"req_{uuid.uuid4().hex[:12]}", results=results)


@app.post("/menu/extract", response_model=MenuResponse)
def menu_extract(request: MenuRequest):
    if not request.domains:
        raise HTTPException(status_code=400, detail="Lista de dominios vacía")
    if len(request.domains) > settings.max_domains_per_request:
        raise HTTPException(status_code=400, detail=f"Máximo {settings.max_domains_per_request} dominios por petición")

    results = []
    for domain in request.domains:
        sr = scrape_domain(domain, timeout=request.timeout)
        results.append(MenuResult(
            domain=sr.domain,
            menu_links=[MenuLink(**lnk) for lnk in sr.menu_links],
        ))

    return MenuResponse(results=results)


@app.post("/scrape-rich", response_model=RichResponse)
def scrape_rich(request: RichRequest):
    if not request.domains:
        raise HTTPException(status_code=400, detail="Lista de dominios vacía")
    if len(request.domains) > settings.max_domains_per_request:
        raise HTTPException(status_code=400, detail=f"Máximo {settings.max_domains_per_request} dominios por petición")

    results = []
    for domain in request.domains:
        sr = scrape_domain(domain, timeout=request.timeout)
        results.append(RichResult(
            domain=sr.domain,
            status=sr.status,
            titulo_web=sr.titulo_web,
            meta_descripcion=sr.meta_descripcion,
            descripcion_negocio=sr.descripcion_negocio,
            texto_about=sr.texto_about,
            email_principal=sr.email_principal,
            emails_adicionales=sr.emails_adicionales,
            telefono_principal=sr.telefono_principal,
            telefonos_adicionales=sr.telefonos_adicionales,
            formulario_contacto_url=sr.formulario_contacto_url,
            menu_links=[MenuLink(**lnk) for lnk in sr.menu_links],
            used_playwright=sr.used_playwright,
            processing_time=sr.processing_time,
        ))

    return RichResponse(results=results)
