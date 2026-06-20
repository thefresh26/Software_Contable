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

    # Intentar WeasyPrint (mejor calidad, requiere GTK/Pango en el sistema)
    try:
        from weasyprint import HTML
        return HTML(string=html_str, base_url=base_url).write_pdf()
    except Exception:
        pass  # cualquier fallo de WeasyPrint (OSError, ImportError, etc.) → xhtml2pdf

    # Fallback: xhtml2pdf (funciona sin dependencias nativas del sistema)
    from xhtml2pdf import pisa
    buf = io.BytesIO()
    pisa.CreatePDF(html_str, dest=buf, encoding='utf-8')
    pdf_bytes = buf.getvalue()
    if not pdf_bytes:
        raise RuntimeError('PDF generation failed: output is empty')
    return pdf_bytes


def pdf_response(pdf_bytes: bytes, filename: str) -> HttpResponse:
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
