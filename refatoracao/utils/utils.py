from __future__ import annotations

import logging
from pathlib import Path

import requests
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)


def check_internet(timeout: float = 3.0) -> bool:
    """Retorna True quando houver conectividade básica com a internet."""
    try:
        requests.get("https://1.1.1.1", timeout=timeout)
        return True
    except requests.RequestException:
        logger.info("Sem conectividade com a internet.")
        return False


def generate_library_card(username: str, email: str) -> Path:
    """Gera um cartão simples da biblioteca em PDF e retorna o caminho do arquivo."""
    output_path = Path(f"library_card_{username}.pdf")
    page_width, page_height = A4

    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    pdf.setTitle(f"Cartão da Biblioteca - {username}")

    pdf.setFillColor(colors.HexColor("#14324a"))
    pdf.rect(18 * mm, page_height - 72 * mm, 174 * mm, 48 * mm, fill=1, stroke=0)

    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(28 * mm, page_height - 42 * mm, "Cartão da Biblioteca")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(28 * mm, page_height - 53 * mm, f"Usuário: {username}")
    pdf.drawString(28 * mm, page_height - 61 * mm, f"E-mail: {email}")

    pdf.setStrokeColor(colors.white)
    pdf.line(28 * mm, page_height - 66 * mm, 178 * mm, page_height - 66 * mm)

    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawString(28 * mm, page_height - 76 * mm, "Biblioteca LIPS")
    pdf.save()

    logger.info("Cartão da biblioteca gerado em %s", output_path)
    return output_path