# extractors/multipage.py
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

CANDIDATE_PATHS = [
    '/contact', '/contacto', '/about', '/sobre-nosotros',
    '/advertise', '/publicidad', '/anunciate', '/media-kit',
    '/mediakit', '/colabora', '/work-with-us',
]

LEAD_CALIENTE_RE = re.compile(
    r'/(advertise|publicidad|anunciate|media[-_]?kit|mediakit|colabora|work[-_]with[-_]us)',
    re.IGNORECASE,
)


@dataclass
class PageResult:
    url: str
    html: str
    is_lead_caliente: bool = False


def _same_domain(url: str, base_url: str) -> bool:
    base_host = urlparse(base_url).netloc.lstrip('www.')
    url_host = urlparse(url).netloc.lstrip('www.')
    return url_host == base_host or url_host.endswith('.' + base_host)


def crawl_pages(
    base_url: str,
    menu_links: list[str],
    session: requests.Session,
    timeout: int = 5,
    max_pages: int = 5,
) -> tuple[list[PageResult], Optional[str]]:
    """
    Fetches up to max_pages candidate sub-pages from the site.

    Returns (pages, pagina_publicidad_url).
    Only visits URLs that appear in menu_links or match CANDIDATE_PATHS.
    """
    visited: set[str] = set()
    results: list[PageResult] = []
    pagina_publicidad_url: Optional[str] = None

    # Build candidate set: menu links that match known paths
    menu_set = {u.rstrip('/') for u in menu_links if _same_domain(u, base_url)}
    candidates: list[str] = []

    for path in CANDIDATE_PATHS:
        full = urljoin(base_url, path)
        full_clean = full.rstrip('/')
        if full_clean in menu_set or any(full_clean == m.rstrip('/') for m in menu_set):
            candidates.append(full)

    # Also add menu links that match lead_caliente pattern even if not in our list
    for url in menu_set:
        path = urlparse(url).path
        if LEAD_CALIENTE_RE.search(path) and url not in candidates:
            candidates.append(url)

    for url in candidates:
        if len(results) >= max_pages:
            break
        url_clean = url.rstrip('/')
        if url_clean in visited:
            continue
        visited.add(url_clean)

        try:
            resp = session.get(
                url,
                timeout=timeout,
                headers={'User-Agent': 'n8n/1.0'},
                allow_redirects=True,
            )
            if resp.status_code != 200:
                continue
        except Exception:
            continue

        path = urlparse(url).path
        is_lc = bool(LEAD_CALIENTE_RE.search(path))
        if is_lc and pagina_publicidad_url is None:
            pagina_publicidad_url = url

        results.append(PageResult(url=url, html=resp.text, is_lead_caliente=is_lc))

    return results, pagina_publicidad_url
