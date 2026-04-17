import re
from typing import Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from config import settings

ABOUT_PATHS = re.compile(
    r'/(about|quienes-somos|sobre-nosotros|nosotros|empresa|who-we-are|sobre-mi)/?$',
    re.IGNORECASE,
)
CONTACT_PATHS = re.compile(
    r'/(contacto|contact|contactanos|contact-us|escribenos)/?$',
    re.IGNORECASE,
)
TITLE_SEPARATOR_RE = re.compile(r'\s*[\|\-–—]\s*.*$')


def _clean_title(raw: str) -> str:
    raw = raw.strip()
    parts = re.split(r'\s*[\|\-–—]\s*', raw)
    return parts[0].strip() if parts else raw


def _get_visible_text(soup: BeautifulSoup) -> str:
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        tag.decompose()
    text = soup.get_text(separator=' ', strip=True)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def find_about_url(html: str, base_url: str) -> Optional[str]:
    soup = BeautifulSoup(html, 'lxml')
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        absolute = urljoin(base_url, href)
        path = urlparse(absolute).path
        if ABOUT_PATHS.search(path):
            return absolute
    return None


def extract_rich(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, 'lxml')

    titulo_web = None
    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        titulo_web = _clean_title(title_tag.string)

    meta_descripcion = None
    meta = soup.find('meta', attrs={'name': 'description'})
    if meta and meta.get('content'):
        meta_descripcion = meta['content'].strip()
    if not meta_descripcion:
        og = soup.find('meta', attrs={'property': 'og:description'})
        if og and og.get('content'):
            meta_descripcion = og['content'].strip()

    visible_text = _get_visible_text(BeautifulSoup(html, 'lxml'))  # separate parse: _get_visible_text mutates soup via decompose
    texto_homepage = visible_text[:settings.rich_text_max_chars] if visible_text else None

    formulario_contacto_url = None
    for a in soup.find_all('a', href=True):
        absolute = urljoin(base_url, a['href'].strip())
        if CONTACT_PATHS.search(urlparse(absolute).path):
            formulario_contacto_url = absolute
            break

    parts = []
    if titulo_web:
        parts.append(titulo_web)
    if meta_descripcion:
        parts.append(meta_descripcion)
    if texto_homepage:
        first_para = next(
            (s for s in texto_homepage.split('.') if len(s.strip()) > 30),
            texto_homepage[:200]
        )
        parts.append(first_para.strip())

    descripcion_negocio = ' '.join(parts)[:600] if parts else None

    return {
        "titulo_web": titulo_web,
        "meta_descripcion": meta_descripcion,
        "texto_homepage": texto_homepage,
        "descripcion_negocio": descripcion_negocio,
        "formulario_contacto_url": formulario_contacto_url,
    }
