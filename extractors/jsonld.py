# extractors/jsonld.py
import json
import re
from typing import Optional

from bs4 import BeautifulSoup

SOCIAL_PLATFORMS = re.compile(
    r'(twitter\.com|x\.com|linkedin\.com|instagram\.com|facebook\.com|'
    r'youtube\.com|tiktok\.com|mastodon\.social|bsky\.app)',
    re.IGNORECASE,
)


def _flatten_graph(ld: object) -> list[dict]:
    """Convierte @graph o un único objeto en una lista de nodos."""
    if isinstance(ld, list):
        out = []
        for item in ld:
            out.extend(_flatten_graph(item))
        return out
    if isinstance(ld, dict):
        if '@graph' in ld:
            return _flatten_graph(ld['@graph'])
        return [ld]
    return []


def _get_name(node: dict) -> Optional[str]:
    return node.get('name') or node.get('legalName')


def _get_same_as_socials(node: dict) -> dict[str, str]:
    same_as = node.get('sameAs', [])
    if isinstance(same_as, str):
        same_as = [same_as]
    result: dict[str, str] = {}
    for url in same_as:
        if not isinstance(url, str):
            continue
        m = SOCIAL_PLATFORMS.search(url)
        if m:
            platform = m.group(1).lower().replace('.com', '').replace('.social', '').replace('.app', '')
            if platform not in result:
                result[platform] = url
    return result


def extract_jsonld(soup: BeautifulSoup) -> dict:
    """
    Extrae datos estructurados de todos los <script type="application/ld+json">.

    Retorna:
        nombre_owner   str | None   – Organization.name o Person.name
        tipo_schema    str | None   – primer @type no trivial encontrado
        redes_sociales dict         – {plataforma: url} de sameAs
        pais_jsonld    str | None   – address.addressCountry
    """
    nombre_owner: Optional[str] = None
    tipo_schema: Optional[str] = None
    redes_sociales: dict[str, str] = {}
    pais_jsonld: Optional[str] = None

    for script in soup.find_all('script', type='application/ld+json'):
        raw = script.string or ''
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue

        nodes = _flatten_graph(data)
        for node in nodes:
            if not isinstance(node, dict):
                continue

            node_type = node.get('@type', '')
            if isinstance(node_type, list):
                node_type = node_type[0] if node_type else ''

            if tipo_schema is None and node_type not in ('', 'WebPage', 'BreadcrumbList'):
                tipo_schema = node_type

            if nombre_owner is None and node_type in (
                'Organization', 'LocalBusiness', 'Corporation',
                'NewsMediaOrganization', 'Blog', 'Person',
            ):
                nombre_owner = _get_name(node)

            if not redes_sociales:
                redes_sociales = _get_same_as_socials(node)
            else:
                redes_sociales.update(_get_same_as_socials(node))

            if pais_jsonld is None:
                addr = node.get('address', {})
                if isinstance(addr, dict):
                    pais_jsonld = addr.get('addressCountry')
                elif isinstance(addr, str):
                    pais_jsonld = addr

    return {
        'nombre_owner': nombre_owner or None,
        'tipo_schema': tipo_schema or None,
        'redes_sociales': redes_sociales,
        'pais_jsonld': pais_jsonld or None,
    }
