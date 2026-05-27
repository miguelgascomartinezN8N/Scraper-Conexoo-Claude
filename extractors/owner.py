# extractors/owner.py
import re
from typing import Optional

from bs4 import BeautifulSoup

COPYRIGHT_RE = re.compile(
    r'©\s*(?:\d{4}\s*)?([A-ZÁÉÍÓÚÀÂÈÊÎÔÙÛÄËÏÖÜ][A-Za-záéíóúàâèêîôùûäëïöüÁÉÍÓÚÀÂÈÊÎÔÙÛÄËÏÖÜ\s&.,\'-]{2,59})',
    re.UNICODE,
)
SELF_INTRO_RE = re.compile(
    r'(?:Soy|I am|I\'m|Je suis|Sou|Mi nombre es|My name is|Me llamo|Je m\'appelle)\s+'
    r'([A-ZÁÉÍÓÚÀÈÊÙÄËÖÜ][a-záéíóúàèêùäëöü]+(?:\s+[A-ZÁÉÍÓÚÀÈÊÙÄËÖÜ][a-záéíóúàèêùäëöü]+)?)',
    re.UNICODE,
)

DISCARD_NAMES = {
    'wordpress', 'powered by', 'copyright', 'all rights reserved',
    'todos los derechos', 'rights reserved', 'blogger', 'drupal',
    'joomla', 'wix', 'squarespace', 'shopify', 'magento',
}


def _is_valid_name(name: str) -> bool:
    name = name.strip()
    if len(name) < 3 or len(name) > 60:
        return False
    lower = name.lower()
    if any(discard in lower for discard in DISCARD_NAMES):
        return False
    # Must have at least one letter
    if not re.search(r'[A-Za-záéíóúàèêùäëöü]', name):
        return False
    return True


def extract_owner(
    soup: BeautifulSoup,
    about_text: str = '',
    jsonld_nombre: Optional[str] = None,
) -> Optional[str]:
    """
    Heuristic fallback for nombre_owner when JSON-LD didn't provide one.

    Priority:
    1. JSON-LD (already resolved upstream — passed in for convenience)
    2. Footer copyright pattern
    3. Self-intro pattern in about_text
    4. <meta name="author">
    """
    if jsonld_nombre and _is_valid_name(jsonld_nombre):
        return jsonld_nombre

    # Footer copyright
    footer = soup.find('footer')
    footer_text = footer.get_text(' ', strip=True) if footer else ''
    if not footer_text:
        # Fallback: last 500 chars of body text
        body = soup.find('body')
        footer_text = (body.get_text(' ', strip=True) if body else '')[-500:]

    for m in COPYRIGHT_RE.finditer(footer_text):
        candidate = m.group(1).strip().rstrip('.,;')
        if _is_valid_name(candidate):
            return candidate

    # Self-intro in about_text
    for m in SELF_INTRO_RE.finditer(about_text):
        candidate = m.group(1).strip()
        if _is_valid_name(candidate):
            return candidate

    # <meta name="author">
    meta = soup.find('meta', attrs={'name': 'author'})
    if meta and meta.get('content'):
        candidate = str(meta['content']).strip()
        if _is_valid_name(candidate):
            return candidate

    return None
