from pydantic import BaseModel, Field
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
    # A2 — nuevos campos
    idioma: Optional[str] = None
    nombre_owner: Optional[str] = None
    tipo_schema: Optional[str] = None
    redes_sociales: dict[str, str] = Field(default_factory=dict)
    pais: Optional[str] = None
    # A3 — señales editoriales
    pagina_publicidad_url: Optional[str] = None
    lead_caliente: bool = False
    ads_partners: list[str] = Field(default_factory=list)
    rss_url: Optional[str] = None
    ultimo_post_fecha: Optional[str] = None
    paginas_visitadas: list[str] = Field(default_factory=list)


class RichResponse(BaseModel):
    results: list[RichResult]


# A4 — endpoint único
class PublisherRequest(BaseModel):
    domains: list[str]
    timeout: int = 15
    crawl: bool = True


class PublisherResponse(BaseModel):
    results: list[RichResult]


class HealthResponse(BaseModel):
    status: str
    version: str
    playwright: bool
