from pydantic import BaseModel
from typing import Optional


class ScrapeRequest(BaseModel):
    domains: list[str]
    extract_emails: bool = True
    extract_phones: bool = True
    search_depth: int = 10
    timeout: int = 10


class MenuRequest(BaseModel):
    domains: list[str]
    timeout: int = 5


class RichRequest(BaseModel):
    domains: list[str]
    timeout: int = 15


class ContactItem(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None


class ScrapeResult(BaseModel):
    domain: str
    status: str
    contacts: list[ContactItem] = []
    emails_adicionales: list[str] = []
    telefonos_adicionales: list[str] = []
    used_playwright: bool = False
    processing_time: float = 0.0


class ScrapeResponse(BaseModel):
    request_id: str
    results: list[ScrapeResult]


class MenuLink(BaseModel):
    text: str
    url: str


class MenuResult(BaseModel):
    domain: str
    menu_links: list[MenuLink] = []


class MenuResponse(BaseModel):
    results: list[MenuResult]


class RichResult(BaseModel):
    domain: str
    status: str
    titulo_web: Optional[str] = None
    meta_descripcion: Optional[str] = None
    descripcion_negocio: Optional[str] = None
    texto_about: Optional[str] = None
    email_principal: Optional[str] = None
    emails_adicionales: list[str] = []
    telefono_principal: Optional[str] = None
    telefonos_adicionales: list[str] = []
    formulario_contacto_url: Optional[str] = None
    menu_links: list[MenuLink] = []
    used_playwright: bool = False
    processing_time: float = 0.0


class RichResponse(BaseModel):
    results: list[RichResult]


class HealthResponse(BaseModel):
    status: str
    version: str
    playwright: bool
