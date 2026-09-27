import os
import re
import time
import logging
from fpdf import FPDF

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORTS_DIR = os.path.join(BASE_DIR, "static", "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)


def _sanitize_pdf_text(text: str) -> str:
    """Replaces non-latin1 / fancy unicode characters for standard FPDF core fonts."""
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "--",
        "\u2026": "...",
        "\u2022": "*",
        "\u2605": "*",
        "\u2728": "*",
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    # Remove any lingering unencodable characters
    return text.encode("latin-1", "replace").decode("latin-1")


class ComicPDF(FPDF):
    def __init__(self, comic_title: str = "ComicCraft Comic"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.comic_title = comic_title
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(120, 120, 120)
        safe_title = _sanitize_pdf_text(f"COMICCRAFT: {self.comic_title}")
        self.cell(0, 8, safe_title, border=0, new_x="LMARGIN", new_y="NEXT", align="R")
        self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def save_pdf(layout: list[dict], title: str = "ComicCraft Comic") -> str:
    """
    Uses FPDF to compile the full comic (images + narration) into a multi-page PDF,
    one panel per page. Saves to static/exports/ with a timestamped filename.
    Returns the file path.
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    clean_title = re.sub(r"[^a-zA-Z0-9_\-]", "_", title[:25]).strip("_") or "comic"
    filename = f"{clean_title}_{timestamp}.pdf"
    disk_path = os.path.join(EXPORTS_DIR, filename)
    relative_web_path = f"/static/exports/{filename}"

    pdf = ComicPDF(comic_title=title)

    for panel in layout:
        pdf.add_page()

        panel_num = panel.get("panel_number", 1)
        panel_title = _sanitize_pdf_text(panel.get("title", f"Panel {panel_num}"))
        scene_desc = _sanitize_pdf_text(panel.get("scene_description", ""))
        panel_text = _sanitize_pdf_text(panel.get("text", ""))
        img_path = panel.get("image_path", "")

        # 1. Panel Header Badge
        pdf.set_fill_color(255, 215, 0)
        pdf.set_text_color(20, 20, 20)
        pdf.set_font("Helvetica", "B", 14)
        header_text = f" PANEL {panel_num}: {panel_title} "
        pdf.cell(0, 10, header_text, border=1, new_x="LMARGIN", new_y="NEXT", align="C", fill=True)
        pdf.ln(4)

        # 2. Embed Image
        # Resolve web path to disk path
        local_img = None
        if img_path.startswith("/static/"):
            rel = img_path.replace("/static/", "", 1)
            candidate = os.path.join(BASE_DIR, "static", rel)
            if os.path.exists(candidate):
                local_img = candidate
        elif os.path.exists(img_path):
            local_img = img_path

        if local_img and os.path.exists(local_img):
            # Page width is 210mm, margins 10mm each side -> 190mm usable width
            img_w = 140
            x_pos = (210 - img_w) / 2
            y_pos = pdf.get_y()
            pdf.image(local_img, x=x_pos, y=y_pos, w=img_w, h=img_w)
            pdf.set_y(y_pos + img_w + 5)
        else:
            pdf.ln(5)

        # 3. Scene Description (italic)
        if scene_desc:
            pdf.set_font("Helvetica", "I", 10)
            pdf.set_text_color(90, 90, 90)
            pdf.multi_cell(0, 5, f"Scene: {scene_desc}", border=0, align="C")
            pdf.ln(3)

        # 4. Narration & Dialogue Box
        if panel_text:
            pdf.set_fill_color(248, 249, 250)
            pdf.set_draw_color(200, 200, 200)
            pdf.set_text_color(30, 30, 30)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, panel_text, border=1, fill=True, align="L")
            pdf.ln(4)

    pdf.output(disk_path)
    logger.info(f"Comic PDF successfully saved to {disk_path}")

    return relative_web_path
