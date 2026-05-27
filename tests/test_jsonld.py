# tests/test_jsonld.py
from bs4 import BeautifulSoup
from extractors.jsonld import extract_jsonld


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, 'lxml')


def test_organization_name():
    html = '''<script type="application/ld+json">
    {"@type": "Organization", "name": "Acme Corp", "url": "https://acme.com"}
    </script>'''
    result = extract_jsonld(_soup(html))
    assert result['nombre_owner'] == 'Acme Corp'


def test_graph_extracts_org():
    html = '''<script type="application/ld+json">
    {"@graph": [{"@type": "WebSite", "name": "Blog Ejemplo"},
                {"@type": "Organization", "name": "Empresa SL"}]}
    </script>'''
    result = extract_jsonld(_soup(html))
    assert result['nombre_owner'] is not None


def test_same_as_social_links():
    html = '''<script type="application/ld+json">
    {"@type": "Organization", "name": "Co", "sameAs": [
      "https://twitter.com/empresa",
      "https://linkedin.com/company/empresa",
      "https://www.facebook.com/empresa"
    ]}
    </script>'''
    result = extract_jsonld(_soup(html))
    assert 'twitter' in result['redes_sociales'] or 'x' in result['redes_sociales']
    assert 'linkedin' in result['redes_sociales']
    assert 'facebook' in result['redes_sociales']


def test_malformed_json_ignored():
    html = '<script type="application/ld+json">NOT JSON AT ALL{{{</script>'
    result = extract_jsonld(_soup(html))
    assert result['nombre_owner'] is None
    assert result['redes_sociales'] == {}


def test_address_country():
    html = '''<script type="application/ld+json">
    {"@type": "LocalBusiness", "name": "Tienda", "address": {"addressCountry": "ES"}}
    </script>'''
    result = extract_jsonld(_soup(html))
    assert result['pais_jsonld'] == 'ES'


def test_tipo_schema_detected():
    html = '''<script type="application/ld+json">
    {"@type": "NewsMediaOrganization", "name": "Diario"}
    </script>'''
    result = extract_jsonld(_soup(html))
    assert result['tipo_schema'] == 'NewsMediaOrganization'


def test_multiple_scripts_merged():
    html = '''
    <script type="application/ld+json">{"@type": "WebSite", "name": "W"}</script>
    <script type="application/ld+json">{"@type": "Organization", "name": "Org X",
      "sameAs": ["https://instagram.com/orgx"]}</script>
    '''
    result = extract_jsonld(_soup(html))
    assert result['nombre_owner'] == 'Org X'
    assert 'instagram' in result['redes_sociales']


def test_no_json_ld_returns_empty():
    html = '<html><body><p>Sin schema</p></body></html>'
    result = extract_jsonld(_soup(html))
    assert result['nombre_owner'] is None
    assert result['redes_sociales'] == {}
    assert result['tipo_schema'] is None
