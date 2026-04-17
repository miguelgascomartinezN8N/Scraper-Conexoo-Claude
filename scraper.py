import time
import logging
from typing import Optional
from urllib.parse import urlparse
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup

from config import settings
from browser import browser_manager
from extractors.contact import extract_emails, extract_phones
from extractors.menu import extract_menu
from extractors.rich import extract_rich, find_about_url

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


@dataclass
class ScrapeResult:
    domain: str
    status: str
    email_principal: Optional[str] = None
    emails_adicionales: list = field(default_factory=list)
    telefono_principal: Optional[str] = None
    telefonos_adicionales: list = field(default_factory=list)
    menu_links: list = field(default_factory=list)
    titulo_web: Optional[str] = None
    meta_descripcion: Optional[str] = None
    descripcion_negocio: Optional[str] = None
    texto_about: Optional[str] = None
    formulario_contacto_url: Optional[str] = None
    used_playwright: bool = False
    processing_time: float = 0.0


def _is_poor_result(
    email: Optional[str], phone: Optional[str], menu: list
) -> bool:
    return email is None and phone is None and len(menu) < 3


def _fetch_http(url: str, timeout: int) -> Optional[str]:
    try:
        r = requests.get(
            url, timeout=timeout, headers=HEADERS,
            allow_redirects=True, verify=False
        )
        r.raise_for_status()
        return r.text
    except Exception as e:
        logger.warning(f"HTTP failed for {url}: {e}")
        return None


def _fetch_about_text(about_url: str, timeout: int) -> Optional[str]:
    html = _fetch_http(about_url, timeout)
    if not html:
        return None
    soup = BeautifulSoup(html, 'lxml')
    for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
        tag.decompose()
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        if len(text) > 80:
            return text[:settings.about_text_max_chars]
    return None


def _extract_all(html: str, base_url: str, timeout: int) -> dict:
    email_p, emails_add = extract_emails(html)
    phone_p, phones_add = extract_phones(html)
    menu = extract_menu(html, base_url)
    rich = extract_rich(html, base_url)

    about_url = find_about_url(html, base_url)
    texto_about = None
    if about_url:
        texto_about = _fetch_about_text(about_url, timeout)

    return {
        "email_principal": email_p,
        "emails_adicionales": emails_add,
        "telefono_principal": phone_p,
        "telefonos_adicionales": phones_add,
        "menu_links": menu,
        "texto_about": texto_about,
        **rich,
    }


def scrape_domain(domain: str, timeout: int = 10) -> ScrapeResult:
    start = time.time()

    if not domain.startswith(("http://", "https://")):
        url = f"https://{domain}"
    else:
        url = domain

    clean_domain = urlparse(url).netloc or domain
    used_playwright = False
    data: dict = {}

    html = _fetch_http(url, timeout)
    if html:
        data = _extract_all(html, url, timeout)

    if settings.use_playwright and browser_manager.available and (
        not html
        or _is_poor_result(
            data.get("email_principal"),
            data.get("telefono_principal"),
            data.get("menu_links", []),
        )
    ):
        pw_html = browser_manager.get_html(url, settings.playwright_timeout)
        if pw_html:
            data = _extract_all(pw_html, url, timeout)
            used_playwright = True

    if not html and not used_playwright:
        status = "error"
    elif data.get("email_principal") or data.get("telefono_principal"):
        status = "success"
    else:
        status = "no_contacts"

    return ScrapeResult(
        domain=clean_domain,
        status=status,
        email_principal=data.get("email_principal"),
        emails_adicionales=data.get("emails_adicionales", []),
        telefono_principal=data.get("telefono_principal"),
        telefonos_adicionales=data.get("telefonos_adicionales", []),
        menu_links=data.get("menu_links", []),
        titulo_web=data.get("titulo_web"),
        meta_descripcion=data.get("meta_descripcion"),
        descripcion_negocio=data.get("descripcion_negocio"),
        texto_about=data.get("texto_about"),
        formulario_contacto_url=data.get("formulario_contacto_url"),
        used_playwright=used_playwright,
        processing_time=round(time.time() - start, 2),
    )
