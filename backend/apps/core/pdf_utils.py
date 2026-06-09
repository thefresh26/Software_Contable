"""
Utilidad de generación de PDF.
Intenta WeasyPrint; si las libs del sistema (GTK/Pango) no están disponibles
cae a xhtml2pdf que funciona en Windows sin dependencias nativas.
"""
import io
from django.template.loader import render_to_string
from django.http import HttpResponse


def render_pdf(template_name: str, context: dict, base_url: str = None) -> bytes:
    """Renderiza un template HTML a bytes PDF."""
    html_str = render_to_string(template_name, context)

    # Intentar WeasyPrint (mejor calidad, requiere GTK en Windows)
    try:
        from weasyprint import HTML
        return HTML(string=html_str, base_url=base_url).write_pdf()
    except OSError:
        pass  # librerías nativas no disponibles — caer a xhtml2pdf

    # Fallback: xhtml2pdf (funciona en Windows sin deps)
    from xhtml2pdf import pisa
    buf = io.BytesIO()
    status = pisa.CreatePDF(html_str, dest=buf, encoding='utf-8')
    if status.err:
        raise RuntimeError(f'xhtml2pdf error: {status.err}')
    return buf.getvalue()


def pdf_response(pdf_bytes: bytes, filename: str) -> HttpResponse:
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
