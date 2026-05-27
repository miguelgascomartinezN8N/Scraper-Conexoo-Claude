import re
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import settings
from extractors.jsonld import extract_jsonld
from extractors.social import extract_social_links

ABOUT_PATHS = re.compile(
    r'/(about|quienes-somos|sobre-nosotros|nosotros|empresa|who-we-are|sobre-mi)/?$',
    re.IGNORECASE,
)
CONTACT_PATHS = re.compile(
    r'/(contacto|contact|contactanos|contact-us|escribenos)/?$',
    re.IGNORECASE,
)

try:
    from langdetect import detect as _langdetect_detect
    _LANGDETECT_AVAILABLE = True
except ImportError:
    _LANGDETECT_AVAILABLE = False


def _clean_title(raw: str) -> str:
    raw = raw.strip()
    parts = re.split(r'\s*[\|\-–—]\s*', raw)
    return parts[0].strip() if parts else raw


def _get_visible_text(soup: BeautifulSoup) -> str:
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        tag.decompose()
    text = soup.get_text(separator=' ', strip=True)
    return re.sub(r'\s+', ' ', text).strip()


def _detect_language(soup: BeautifulSoup, visible_text: str) -> Optional[str]:
    html_tag = soup.find('html')
    if html_tag and html_tag.get('lang'):
        lang = str(html_tag['lang']).strip().split('-')[0].lower()
        if len(lang) == 2:
            return lang

    meta_lang = soup.find('meta', attrs={'http-equiv': re.compile(r'content-language', re.I)})
    if meta_lang and meta_lang.get('content'):
        lang = str(meta_lang['content']).strip().split('-')[0].lower()
        if len(lang) == 2:
            return lang

    if _LANGDETECT_AVAILABLE and visible_text:
        try:
            return _langdetect_detect(visible_text[:800])
        except Exception:
            pass

    return None


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

    # ── Título ──────────────────────────────────────────────────────────────
    titulo_web = None
    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        titulo_web = _clean_title(title_tag.string)

    # ── Meta description ────────────────────────────────────────────────────
    meta_descripcion = None
    meta = soup.find('meta', attrs={'name': 'description'})
    if meta and meta.get('content'):
        meta_descripcion = meta['content'].strip()
    if not meta_descripcion:
        og = soup.find('meta', attrs={'property': 'og:description'})
        if og and og.get('content'):
            meta_descripcion = og['content'].strip()

    # ── Open Graph extras (A2.5) ─────────────────────────────────────────────
    nombre_sitio_og = None
    og_site = soup.find('meta', attrs={'property': 'og:site_name'})
    if og_site and og_site.get('content'):
        nombre_sitio_og = og_site['content'].strip()

    autor_meta = None
    meta_author = soup.find('meta', attrs={'name': 'author'})
    if meta_author and meta_author.get('content'):
        autor_meta = meta_author['content'].strip()

    # ── Visible text ────────────────────────────────────────────────────────
    soup2 = BeautifulSoup(html, 'lxml')
    visible_text = _get_visible_text(soup2)
    texto_homepage = visible_text[:settings.rich_text_max_chars] if visible_text else None

    # ── Idioma (A2.3) ────────────────────────────────────────────────────────
    idioma = _detect_language(soup, visible_text)

    # ── Formulario contacto ──────────────────────────────────────────────────
    formulario_contacto_url = None
    for a in soup.find_all('a', href=True):
        absolute = urljoin(base_url, a['href'].strip())
        if CONTACT_PATHS.search(urlparse(absolute).path):
            formulario_contacto_url = absolute
            break

    # ── Descripcion negocio ──────────────────────────────────────────────────
    parts = []
    if titulo_web:
        parts.append(titulo_web)
    if meta_descripcion:
        parts.append(meta_descripcion)
    if texto_homepage:
        first_para = next(
            (s for s in texto_homepage.split('.') if len(s.strip()) > 30),
            texto_homepage[:200],
        )
        parts.append(first_para.strip())
    descripcion_negocio = ' '.join(parts)[:600] if parts else None

    # ── JSON-LD (A2.1) ───────────────────────────────────────────────────────
    jsonld_data = extract_jsonld(soup)
    tipo_schema = jsonld_data['tipo_schema']
    pais = jsonld_data['pais_jsonld']

    # ── Redes sociales (A2.2) ────────────────────────────────────────────────
    redes_sociales = dict(jsonld_data['redes_sociales'])
    redes_from_links = extract_social_links(soup, base_url)
    for plat, url in redes_from_links.items():
        if plat not in redes_sociales:
            redes_sociales[plat] = url

    # ── Owner (A2.1 fallback) ────────────────────────────────────────────────
    nombre_owner = jsonld_data['nombre_owner'] or autor_meta

    return {
        "titulo_web": titulo_web,
        "meta_descripcion": meta_descripcion,
        "texto_homepage": texto_homepage,
        "descripcion_negocio": descripcion_negocio,
        "formulario_contacto_url": formulario_contacto_url,
        # A2
        "idioma": idioma,
        "nombre_owner": nombre_owner,
        "tipo_schema": tipo_schema,
        "redes_sociales": redes_sociales,
        "pais": pais,
        "nombre_sitio_og": nombre_sitio_og,
        "autor_meta": autor_meta,
    }
