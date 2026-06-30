"""Markdown template for invoice rendering."""

from __future__ import annotations

from models import Invoice, format_currency


def render_md_template(invoice: Invoice) -> str:
    """Render invoice as Markdown document."""
    # Items table
    items_rows = ""
    for item in invoice.items:
        items_rows += (
            f"| {item.description} | {item.quantity} {item.unit} | "
            f"{format_currency(item.unit_price, invoice.currency)} | "
            f"{item.tax_rate * 100:.1f}% | "
            f"{format_currency(item.total, invoice.currency)} |\n"
        )

    discount_line = ""
    if invoice.total_discount > 0:
        discount_line = f"| **Discount** | **-{format_currency(invoice.total_discount, invoice.currency)}** |\n"

    notes_section = ""
    if invoice.notes:
        notes_section = f"""
---

## Notes

{invoice.notes}
"""

    return f"""# Invoice {invoice.invoice_number}

**Status:** {invoice.status.upper()} | **Currency:** {invoice.currency}

---

## Details

| | From | Bill To |
|---|---|---|
| **Name** | {invoice.seller.name} | {invoice.buyer.name} |
| **Address** | {invoice.seller.address} | {invoice.buyer.address} |
| **Tax ID** | {invoice.seller.tax_id} | {invoice.buyer.tax_id} |
| **Email** | {invoice.seller.email} | {invoice.buyer.email} |

**Issue Date:** {invoice.issue_date.strftime('%d/%m/%Y')} | **Due Date:** {invoice.due_date.strftime('%d/%m/%Y')}

---

## Items

| Description | Quantity | Unit Price | Tax | Total |
|-------------|:--------:|-----------:|:---:|------:|
{items_rows}

---

## Totals

| | Amount |
|---|---:|
| Subtotal | {format_currency(invoice.subtotal, invoice.currency)} |
| Tax | {format_currency(invoice.total_tax, invoice.currency)} |
{discount_line}| **TOTAL** | **{format_currency(invoice.grand_total, invoice.currency)}** |
{notes_section}
---

*Automatically generated document — Invoice Generator v1.0*
"""
