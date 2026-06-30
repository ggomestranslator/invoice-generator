"""
Renderers — Invoice Generator

Output renderers for different formats (HTML, Markdown, PDF).
Each renderer implements the same interface for consistency.
"""

from __future__ import annotations

import html as html_lib
from pathlib import Path
from typing import Protocol

from models import Invoice, format_currency
from templates.invoice_html import render_html_template
from templates.invoice_md import render_md_template


class Renderer(Protocol):
    """Protocol for invoice renderers."""

    def render(self, invoice: Invoice) -> str:
        """Render invoice to string content."""
        ...

    def save(self, invoice: Invoice, output_path: Path) -> Path:
        """Render and save to file. Returns path to saved file."""
        ...


class HTMLRenderer:
    """Renders invoice as a styled HTML document."""

    def render(self, invoice: Invoice) -> str:
        """Generate complete HTML document."""
        return render_html_template(invoice)

    def save(self, invoice: Invoice, output_path: Path) -> Path:
        """Save HTML file."""
        content = self.render(invoice)
        file_path = output_path / f"{invoice.invoice_number}.html"
        file_path.write_text(content, encoding="utf-8")
        return file_path


class MarkdownRenderer:
    """Renders invoice as Markdown (ideal for version control and plain text)."""

    def render(self, invoice: Invoice) -> str:
        """Generate Markdown document."""
        return render_md_template(invoice)

    def save(self, invoice: Invoice, output_path: Path) -> Path:
        """Save Markdown file."""
        content = self.render(invoice)
        file_path = output_path / f"{invoice.invoice_number}.md"
        file_path.write_text(content, encoding="utf-8")
        return file_path


class PDFRenderer:
    """Renders invoice as a professional SaaS-grade PDF with modern minimalist design."""

    def render(self, invoice: Invoice) -> str:
        return ""

    def save(self, invoice: Invoice, output_path: Path) -> Path:
        try:
            from fpdf import FPDF
        except ImportError:
            raise RuntimeError("PDF generation requires 'fpdf2'. Install: pip install fpdf2")

        import os

        # --- Design tokens ---
        MARGIN = 14          # ~40px margins
        TEXT_PRIMARY = (17, 17, 17)       # #111111
        TEXT_SECONDARY = (85, 85, 85)     # #555555
        TEXT_MUTED = (130, 130, 130)      # #828282
        DIVIDER_COLOR = (221, 221, 221)   # #DDDDDD
        LINK_COLOR = (37, 99, 235)        # Blue for hyperlinks
        SECTION_GAP = 9      # ~32px between sections
        ELEMENT_GAP = 3      # ~10px between elements
        DIVIDER_GAP = 6      # space above/below dividers

        pdf = FPDF()
        pdf.set_margins(MARGIN, MARGIN, MARGIN)
        pdf.set_auto_page_break(auto=True, margin=MARGIN)
        pdf.add_page()

        fonts_dir = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
        if os.path.exists(os.path.join(fonts_dir, "arial.ttf")):
            pdf.add_font("F", "", fname=os.path.join(fonts_dir, "arial.ttf"))
            pdf.add_font("F", "B", fname=os.path.join(fonts_dir, "arialbd.ttf"))
            pdf.add_font("F", "I", fname=os.path.join(fonts_dir, "ariali.ttf"))
            f = "F"
        else:
            f = "Helvetica"

        W = 210 - 2 * MARGIN  # usable content width

        def divider():
            """Thin gray horizontal divider with spacing."""
            pdf.ln(DIVIDER_GAP)
            pdf.set_draw_color(*DIVIDER_COLOR)
            pdf.set_line_width(0.3)
            pdf.line(MARGIN, pdf.get_y(), 210 - MARGIN, pdf.get_y())
            pdf.ln(DIVIDER_GAP)

        # ============================================================
        # 1. HEADER
        # ============================================================
        y_header = pdf.get_y()

        # Left side: Company + CNPJ (stacked tight)
        pdf.set_font(f, "B", 16)
        pdf.set_text_color(*TEXT_PRIMARY)
        pdf.cell(W * 0.55, 7, invoice.seller.name, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font(f, "", 9)
        pdf.set_text_color(*TEXT_SECONDARY)
        if invoice.seller.tax_id:
            pdf.cell(W * 0.55, 4, f"CNPJ: {invoice.seller.tax_id}", new_x="LMARGIN", new_y="NEXT")
        y_left_end = pdf.get_y()

        # Right side: Invoice # + Dates (positioned at same y as header start)
        pdf.set_y(y_header)
        pdf.set_x(MARGIN + W * 0.55)
        pdf.set_font(f, "B", 22)
        pdf.set_text_color(*TEXT_PRIMARY)
        pdf.cell(W * 0.45, 9, f"Invoice #{invoice.invoice_number}", align="R", new_x="LMARGIN", new_y="NEXT")

        pdf.set_x(MARGIN + W * 0.55)
        pdf.set_font(f, "", 9)
        pdf.set_text_color(*TEXT_SECONDARY)
        pdf.cell(W * 0.45, 4.5, f"Creation date: {invoice.issue_date.strftime('%Y-%m-%d')}", align="R", new_x="LMARGIN", new_y="NEXT")

        pdf.set_x(MARGIN + W * 0.55)
        pdf.cell(W * 0.45, 4.5, f"Due date: {invoice.due_date.strftime('%Y-%m-%d')}", align="R", new_x="LMARGIN", new_y="NEXT")
        y_right_end = pdf.get_y()

        pdf.set_y(max(y_left_end, y_right_end))
        divider()

        # ============================================================
        # 2. BILLING SECTION — Two columns
        # ============================================================
        y_billing = pdf.get_y()
        col_right_x = MARGIN + W / 2 + 4

        # Bill From (left)
        pdf.set_font(f, "B", 10)
        pdf.set_text_color(*TEXT_PRIMARY)
        pdf.cell(W / 2, 5.5, "Bill From:", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(ELEMENT_GAP)
        pdf.set_font(f, "", 9)
        pdf.set_text_color(*TEXT_SECONDARY)
        for line in invoice.seller.address.replace("\\n", "\n").split("\n"):
            line = line.strip()
            if line:
                pdf.cell(W / 2, 4.5, line, new_x="LMARGIN", new_y="NEXT")
        y_from_end = pdf.get_y()

        # Bill To (right)
        pdf.set_y(y_billing)
        pdf.set_x(col_right_x)
        pdf.set_font(f, "B", 10)
        pdf.set_text_color(*TEXT_PRIMARY)
        pdf.cell(W / 2, 5.5, "Bill To:")
        pdf.set_y(pdf.get_y() + 5.5 + ELEMENT_GAP)
        pdf.set_font(f, "", 9)
        pdf.set_text_color(*TEXT_SECONDARY)
        for line in invoice.buyer.address.replace("\\n", "\n").split("\n"):
            line = line.strip()
            if line:
                pdf.set_x(col_right_x)
                pdf.cell(W / 2, 4.5, line)
                pdf.set_y(pdf.get_y() + 4.5)
        y_to_end = pdf.get_y()

        pdf.set_y(max(y_from_end, y_to_end))
        divider()

        # ============================================================
        # 3. SERVICES
        # ============================================================
        pdf.set_font(f, "B", 13)
        pdf.set_text_color(*TEXT_PRIMARY)
        pdf.cell(0, 7, "Services", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(ELEMENT_GAP + 2)

        for item in invoice.items:
            parts = item.description.split(" - ", 1)
            title = parts[0].strip()
            desc = parts[1].strip() if len(parts) > 1 else ""

            # Service title — bold, slightly larger
            pdf.set_font(f, "B", 10)
            pdf.set_text_color(*TEXT_PRIMARY)
            pdf.cell(0, 5.5, title, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

            # Full description — regular, gray, increased line spacing
            if desc:
                pdf.set_font(f, "", 9)
                pdf.set_text_color(*TEXT_SECONDARY)
                pdf.multi_cell(W, 5, desc, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(ELEMENT_GAP)

        divider()

        # ============================================================
        # 4. TOTAL — right-aligned, large, bold, BRL formatted
        # ============================================================
        pdf.ln(SECTION_GAP)
        pdf.set_font(f, "B", 22)
        pdf.set_text_color(*TEXT_PRIMARY)
        total_formatted = format_currency(invoice.grand_total, invoice.currency)
        pdf.cell(0, 10, f"Total {invoice.currency} {total_formatted}", align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(SECTION_GAP)

        divider()

        # ============================================================
        # 5. PAYMENT DETAILS — two-column key:value layout
        # ============================================================
        pdf.ln(2)
        pdf.set_font(f, "B", 10)
        pdf.set_text_color(*TEXT_PRIMARY)
        pdf.cell(0, 5.5, "Pay to banking details below:", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(ELEMENT_GAP + 2)

        label_w = 68
        if invoice.notes:
            notes_text = invoice.notes.replace("\\n", "\n")
            for line in notes_text.split("\n"):
                line = line.strip()
                if not line or line == "PAYMENT INFORMATION":
                    continue
                if ":" in line and not line.startswith("If ") and not line.startswith("Please"):
                    label, _, value = line.partition(":")
                    # Label: semi-bold, darker
                    pdf.set_font(f, "B", 9)
                    pdf.set_text_color(*TEXT_SECONDARY)
                    pdf.cell(label_w, 5.5, f"{label.strip()}:")
                    # Value: regular, primary color
                    pdf.set_font(f, "", 9)
                    pdf.set_text_color(*TEXT_PRIMARY)
                    pdf.cell(0, 5.5, value.strip(), new_x="LMARGIN", new_y="NEXT")
                else:
                    # Freeform text lines (Please make payment...)
                    pdf.ln(ELEMENT_GAP + 1)
                    pdf.set_font(f, "", 9)
                    pdf.set_text_color(*TEXT_SECONDARY)
                    pdf.multi_cell(W, 5, line)

        # ============================================================
        # 6. FOOTER — contact with hyperlinked email
        # ============================================================
        pdf.ln(SECTION_GAP + 4)
        divider()
        pdf.ln(2)

        email = invoice.seller.email or ""
        pdf.set_font(f, "", 9)
        pdf.set_text_color(*TEXT_MUTED)
        pdf.cell(pdf.get_string_width("Questions? Send an email to "), 5, "Questions? Send an email to ")

        # Email as blue hyperlink
        pdf.set_font(f, "", 9)
        pdf.set_text_color(*LINK_COLOR)
        email_w = pdf.get_string_width(email)
        pdf.cell(email_w, 5, email, link=f"mailto:{email}")

        pdf.set_text_color(*TEXT_MUTED)
        pdf.cell(5, 5, ".")

        file_path = output_path / f"{invoice.invoice_number}.pdf"
        pdf.output(str(file_path))
        return file_path


def get_renderer(format_name: str) -> Renderer:
    """Factory function to get renderer by format name."""
    renderers = {
        "html": HTMLRenderer(),
        "md": MarkdownRenderer(),
        "markdown": MarkdownRenderer(),
        "pdf": PDFRenderer(),
    }
    renderer = renderers.get(format_name.lower())
    if renderer is None:
        valid = list(renderers.keys())
        raise ValueError(f"Unsupported format '{format_name}'. Valid: {valid}")
    return renderer
