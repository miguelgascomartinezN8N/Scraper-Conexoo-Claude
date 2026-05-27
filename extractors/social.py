# extractors/social.py
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

SOCIAL_PATTERNS: dict[str, re.Pattern] = {
    'twitter':   re.compile(r'https?://(?:www\.)?(twitter|x)\.com/(?!intent|share|home|search|hashtag|status)[^/\s"\'?#]+', re.IGNORECASE),
    'linkedin':  re.compile(r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[^/\s"\'?#]+', re.IGNORECASE),
    'instagram': re.compile(r'https?://(?:www\.)?instagram\.com/[^/\s"\'?#]+', re.IGNORECASE),
    'facebook':  re.compile(r'https?://(?:www\.)?facebook\.com/(?!sharer|share|dialog)[^/\s"\'?#]+', re.IGNORECASE),
    'youtube':   re.compile(r'https?://(?:www\.)?youtube\.com/(?:channel|c|user|@)[^/\s"\'?#]+', re.IGNORECASE),
    'tiktok':    re.compile(r'https?://(?:www\.)?tiktok\.com/@[^/\s"\'?#]+', re.IGNORECASE),
    'mastodon':  re.compile(r'https?://mastodon\.[a-z]+/@[^/\s"\'?#]+', re.IGNORECASE),
    'bluesky':   re.compile(r'https?://bsky\.app/profile/[^/\s"\'?#]+', re.IGNORECASE),
}


def _own_domain(url: str, base_url: str) -> bool:
    """True si la URL pertenece al mismo dominio que base_url."""
    try:
        base_host = urlparse(base_url).netloc.lower().lstrip('www.')
        link_host = urlparse(url).netloc.lower().lstrip('www.')
        return base_host and base_host in link_host
    except Exception:
        return False


def extract_social_links(soup: BeautifulSoup, base_url: str) -> dict[str, str]:
    """
    Detecta perfiles de redes sociales en todos los <a href> del documento.

    Excluye links al propio dominio (típicos de menús "síguenos").
    Retorna {plataforma: url_completa} — un perfil por red.
    """
    result: dict[str, str] = {}

    for a in soup.find_all('a', href=True):
        href = str(a['href']).strip()
        if not href.startswith('http'):
            continue
        if _own_domain(href, base_url):
            continue
        for platform, pattern in SOCIAL_PATTERNS.items():
            if platform not in result and pattern.match(href):
                result[platform] = href
                break

    return result
