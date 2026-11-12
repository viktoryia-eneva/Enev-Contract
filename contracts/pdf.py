from io import BytesIO
from pathlib import Path
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import translation
from xhtml2pdf import pisa

FONTS_DIR = Path(__file__).resolve().parent / "fonts"

def render_contract_pdf(contract):
    """Build the contract PDF, save it in contract.pdf and return the bytes."""
    trip = contract.trip
    travelers = list(contract.travelers.all())
    
    balance = contract.price - (contract.deposit or 0)
    
    context = {
        "contract": contract,
        "trip": trip,
        "travelers": travelers,
        "balance": balance,
        "font_regular": (FONTS_DIR / "DejaVuSans.ttf").as_posix(),
        "font_bold": (FONTS_DIR / "DejaVuSans-Bold.ttf").as_posix(),
    }
    
    with translation.override("bg"):
        html = render_to_string("contracts/contract_pdf.html", context)
        
        buffer = BytesIO()
        result = pisa.CreatePDF(html, dest = buffer, encoding="utf-8")
        if result.err:
            raise RuntimeError("PDF generation failed")
        pdf_bytes = buffer.getvalue()
        
        if contract.pdf:
            contract.pdf.delete(save=False)
    
        contract.pdf.save(f"contract_{contract.number}.pdf", ContentFile(pdf_bytes), save=True)
    
    return pdf_bytes