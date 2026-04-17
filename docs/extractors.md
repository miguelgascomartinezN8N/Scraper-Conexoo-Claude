# Extractores — Documentación Técnica

## contact.py

### Extracción de emails

Orden de búsqueda:

1. **`mailto:` en href** — `<a href="mailto:usuario@dominio.com">` — máxima fiabilidad
2. **Atributos `data-email` / `data-mail`** — técnica anti-scraping común
3. **Regex estándar** sobre `get_text()` — patrón `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-zA-Z]{2,}`
4. **Emails ofuscados `[at][dot]`** — `usuario [at] empresa [dot] com` → `usuario@empresa.com`
5. **Emails ofuscados `(at)`** — `usuario(at)empresa.com`

**Prioridad `email_principal`:** `info@` > `contacto@` > `contact@` > `hola@` > `hello@` > `consultas@` > primer email válido encontrado.

**Filtros de exclusión:** `noreply`, `no-reply`, dominios de ejemplo (`example.com`, `test.com`), redes sociales (facebook, twitter, instagram, linkedin, youtube, tiktok).

**`emails_adicionales`:** hasta 5, deduplicados.

### Extracción de teléfonos

**Siempre válidos (sin contexto):**
- `<a href="tel:+34912345678">` — extracción directa del atributo

**Válidos con contexto (±80 chars):**
- Regex multi-formato detecta el número
- Se valida que haya keyword cercana: `teléfono`, `tel`, `telf`, `phone`, `móvil`, `celular`, `whatsapp`, `llamar`, `llámanos`, `contacto`
- Sin keyword → descartado (evita falsos positivos con IVAs, referencias, códigos postales)

**Normalización:** se eliminan espacios, guiones, paréntesis y puntos.

---

## menu.py

Selectores probados en orden: `nav`, `header nav`, `[role="navigation"]`, `.navbar`, `.nav`, `.menu`, `#menu`, `#nav`, `#navigation`.

Si no encuentra ninguno → escanea todo el documento.

**Filtros:**
- Links externos (fuera del dominio base)
- Anchors puros (`href="#"`)
- Textos de 1 carácter
- Keywords excluidas en texto y URL: `login`, `register`, `cart`, `search`, `privacy`, `cookies`, `legal`

**Límite:** 20 items máximo, URLs absolutas siempre.

---

## rich.py

### Título
Toma `<title>` y limpia el primer separador (`|`, `-`, `–`, `—`).  
Ejemplo: `"Empresa SL | Marketing Digital"` → `"Empresa SL"`

### Meta description
1. `<meta name="description" content="...">`
2. Fallback: `<meta property="og:description" content="...">`

### Texto homepage
Elimina `<script>`, `<style>`, `<nav>`, `<header>`, `<footer>`, `<aside>` del DOM.
Extrae texto visible con `get_text(separator=' ', strip=True)`.
Limita a `RICH_TEXT_MAX_CHARS` (default: 800 chars).

### Texto about
Escanea todos los `<a href>` buscando rutas que macheen:
`/about`, `/quienes-somos`, `/sobre-nosotros`, `/nosotros`, `/empresa`, `/who-we-are`
Si encuentra una, hace petición HTTP adicional y extrae el primer párrafo > 80 chars (máx `ABOUT_TEXT_MAX_CHARS`: 300 chars).

### descripcion_negocio
Concatena: `titulo_web` + `meta_descripcion` + primer párrafo de `texto_homepage`.
Límite: 600 caracteres. Listo para enviar directamente a la IA.
