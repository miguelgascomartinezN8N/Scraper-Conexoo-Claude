# tests/test_contact.py
import pytest
from extractors.contact import extract_emails, extract_phones


# ── EMAIL TESTS ────────────────────────────────────────────────────────────────

def test_email_standard_regex():
    html = "<p>Escríbenos a info@empresa.com para más info.</p>"
    principal, adicionales = extract_emails(html)
    assert principal == "info@empresa.com"
    assert adicionales == []


def test_email_mailto_href():
    html = '<a href="mailto:contacto@empresa.com">Contactar</a>'
    principal, adicionales = extract_emails(html)
    assert principal == "contacto@empresa.com"


def test_email_obfuscated_at_dot():
    html = "<p>Escríbenos: usuario [at] empresa [dot] com</p>"
    principal, adicionales = extract_emails(html)
    assert principal == "usuario@empresa.com"


def test_email_obfuscated_at_parenthesis():
    html = "<p>usuario(at)empresa.com para contactar</p>"
    principal, adicionales = extract_emails(html)
    assert principal == "usuario@empresa.com"


def test_email_data_email_attribute():
    html = '<span data-email="oculto@empresa.com">email protegido</span>'
    principal, adicionales = extract_emails(html)
    assert principal == "oculto@empresa.com"


def test_email_priority_info_over_other():
    html = "<p>otro@empresa.com o info@empresa.com</p>"
    principal, adicionales = extract_emails(html)
    assert principal == "info@empresa.com"
    assert "otro@empresa.com" in adicionales


def test_email_excludes_noreply():
    html = "<p>noreply@empresa.com</p>"
    principal, adicionales = extract_emails(html)
    assert principal is None


def test_email_excludes_social():
    html = "<p>usuario@facebook.com</p>"
    principal, adicionales = extract_emails(html)
    assert principal is None


def test_email_multiple_adicionales_max_5():
    emails = " ".join([f"email{i}@empresa.com" for i in range(7)])
    html = f"<p>{emails}</p>"
    principal, adicionales = extract_emails(html)
    assert len(adicionales) <= 5


# ── PHONE TESTS ────────────────────────────────────────────────────────────────

def test_phone_tel_href_no_context_needed():
    html = '<a href="tel:+34912345678">Llamar</a>'
    principal, adicionales = extract_phones(html)
    assert principal == "+34912345678"


def test_phone_with_context_keyword():
    html = "<p>Teléfono: 912 345 678</p>"
    principal, adicionales = extract_phones(html)
    assert principal is not None
    assert "912345678" in principal.replace(" ", "")


def test_phone_without_context_rejected():
    html = "<p>Referencia pedido: 912345678</p>"
    principal, adicionales = extract_phones(html)
    assert principal is None


def test_phone_international_format():
    html = "<p>Llámanos al +34 912 345 678</p>"
    principal, adicionales = extract_phones(html)
    assert principal is not None
    assert "+34" in principal


def test_phone_whatsapp_context():
    html = "<p>WhatsApp: 612 345 678</p>"
    principal, adicionales = extract_phones(html)
    assert principal is not None


def test_phone_multiple_adicionales():
    html = "<p>Tel: 912345678 y móvil: 612345678</p>"
    principal, adicionales = extract_phones(html)
    assert principal is not None
    assert len(adicionales) <= 3
