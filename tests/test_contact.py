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


def test_email_data_mail_attribute():
    html = '<span data-mail="via-datamail@empresa.com">email</span>'
    principal, adicionales = extract_emails(html)
    assert principal == "via-datamail@empresa.com"


def test_email_excludes_no_reply_with_dash():
    html = "<p>no-reply@empresa.com</p>"
    principal, adicionales = extract_emails(html)
    assert principal is None


def test_email_priority_contacto_over_generic():
    html = "<p>otro@empresa.com y contacto@empresa.com</p>"
    principal, adicionales = extract_emails(html)
    assert principal == "contacto@empresa.com"


def test_email_priority_hola_over_generic():
    html = "<p>otro@empresa.com y hola@empresa.com</p>"
    principal, adicionales = extract_emails(html)
    assert principal == "hola@empresa.com"


def test_phone_movil_context():
    html = "<p>Móvil: 612 345 678</p>"
    principal, adicionales = extract_phones(html)
    assert principal is not None


def test_phone_llamar_context():
    html = "<p>Llámanos: 912 345 678</p>"
    principal, adicionales = extract_phones(html)
    assert principal is not None


def test_phone_celular_context():
    html = "<p>Celular: 612 345 678</p>"
    principal, adicionales = extract_phones(html)
    assert principal is not None


def test_phone_adicionales_capped_at_3():
    html = """
    <p>Tel: <a href="tel:+34911111111">111</a></p>
    <p>Móvil: <a href="tel:+34622222222">222</a></p>
    <p>Fax: <a href="tel:+34933333333">333</a></p>
    <p>Otro: <a href="tel:+34944444444">444</a></p>
    """
    principal, adicionales = extract_phones(html)
    assert principal is not None
    assert len(adicionales) <= 3
