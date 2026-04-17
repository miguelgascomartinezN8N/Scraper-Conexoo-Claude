import re
from typing import Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

NAV_SELECTORS = [
    'nav', 'header nav', '[role="navigation"]',
    '.navbar', '.nav', '.menu', '#menu', '#nav', '#navigation',
]

EXCLUDED_KEYWORDS = re.compile(
    r'^(login|register|signin|sign-in|cart|carrito|search|buscar|'
    r'privacy|cookies|legal|aviso|politica|terms|condiciones)$',
    re.IGNORECASE,
)


def _is_same_domain(url: str, base_url: str) -> bool:
    base_host = urlparse(base_url).netloc
    link_host = urlparse(url).netloc
    return link_host == '' or link_host == base_host


def extract_menu(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, 'lxml')
    links: list[dict] = []
    seen_urls: set[str] = set()

    nav_elements = []
    for selector in NAV_SELECTORS:
        nav_elements.extend(soup.select(selector))

    if not nav_elements:
        nav_elements = [soup]

    for nav in nav_elements:
        for a in nav.find_all('a', href=True):
            href = a['href'].strip()
            text = a.get_text(strip=True)

            if not href or href.startswith('#') or not text or len(text) < 2:
                continue

            absolute_url = urljoin(base_url, href)

            if not _is_same_domain(absolute_url, base_url):
                continue

            if EXCLUDED_KEYWORDS.match(text):
                continue

            path = urlparse(absolute_url).path.rstrip('/')
            last_segment = path.split('/')[-1] if path else ''
            if EXCLUDED_KEYWORDS.match(last_segment):
                continue

            if absolute_url not in seen_urls:
                seen_urls.add(absolute_url)
                links.append({"text": text, "url": absolute_url})

            if len(links) >= 20:
                break

    return links[:20]
