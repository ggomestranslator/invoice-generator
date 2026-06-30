"""HTML template for invoice rendering."""

from __future__ import annotations

from models import Invoice, format_currency


def render_html_template(invoice: Invoice) -> str:
    """Render invoice as complete HTML document with inline CSS."""
    items_rows = ""
    for item in invoice.items:
        items_rows += f"""
            <tr>
                <td>{item.description}</td>
                <td class="center">{item.quantity} {item.unit}</td>
                <td class="right">{format_currency(item.unit_price, invoice.currency)}</td>
                <td class="center">{item.tax_rate * 100:.1f}%</td>
                <td class="right">{format_currency(item.total, invoice.currency)}</td>
            </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Invoice {invoice.invoice_number}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 40px; color: #333; max-width: 800px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 40px; border-bottom: 3px solid #2563eb; padding-bottom: 20px; }}
        .header h1 {{ color: #2563eb; font-size: 2rem; }}
        .invoice-meta {{ text-align: right; }}
        .invoice-meta p {{ margin: 4px 0; }}
        .invoice-number {{ font-size: 1.2rem; font-weight: 700; color: #1e40af; }}
        .parties {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-bottom: 30px; }}
        .party h3 {{ color: #6b7280; font-size: 0.85rem; text-transform: uppercase; margin-bottom: 8px; }}
        .party .name {{ font-weight: 700; font-size: 1.1rem; }}
        .party p {{ margin: 3px 0; color: #4b5563; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #f3f4f6; color: #374151; padding: 12px; text-align: left; font-size: 0.85rem; text-transform: uppercase; }}
        td {{ padding: 12px; border-bottom: 1px solid #e5e7eb; }}
        .center {{ text-align: center; }}
        .right {{ text-align: right; }}
        .totals {{ margin-top: 20px; display: flex; justify-content: flex-end; }}
        .totals table {{ width: 300px; }}
        .totals td {{ padding: 8px 12px; }}
        .totals .grand-total {{ font-size: 1.3rem; font-weight: 700; color: #2563eb; border-top: 2px solid #2563eb; }}
        .notes {{ margin-top: 30px; padding: 15px; background: #f9fafb; border-radius: 8px; border-left: 4px solid #2563eb; }}
        .notes h4 {{ color: #6b7280; margin-bottom: 5px; }}
        .footer {{ margin-top: 40px; text-align: center; color: #9ca3af; font-size: 0.8rem; }}
        .status {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
        .status-draft {{ background: #fef3c7; color: #92400e; }}
        .status-sent {{ background: #dbeafe; color: #1e40af; }}
        .status-paid {{ background: #d1fae5; color: #065f46; }}
        .status-overdue {{ background: #fee2e2; color: #991b1b; }}
        @media print {{ body {{ padding: 20px; }} }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>INVOICE</h1>
            <span class="status status-{invoice.status}">{invoice.status}</span>
        </div>
        <div class="invoice-meta">
            <p class="invoice-number">{invoice.invoice_number}</p>
            <p><strong>Issue Date:</strong> {invoice.issue_date.strftime('%d/%m/%Y')}</p>
            <p><strong>Due Date:</strong> {invoice.due_date.strftime('%d/%m/%Y')}</p>
        </div>
    </div>

    <div class="parties">
        <div class="party">
            <h3>From</h3>
            <p class="name">{invoice.seller.name}</p>
            <p>{invoice.seller.address}</p>
            <p>CNPJ: {invoice.seller.tax_id}</p>
            <p>{invoice.seller.email}</p>
        </div>
        <div class="party">
            <h3>Bill To</h3>
            <p class="name">{invoice.buyer.name}</p>
            <p>{invoice.buyer.address}</p>
            <p>CNPJ: {invoice.buyer.tax_id}</p>
            <p>{invoice.buyer.email}</p>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Description</th>
                <th class="center">Quantity</th>
                <th class="right">Unit Price</th>
                <th class="center">Tax</th>
                <th class="right">Total</th>
            </tr>
        </thead>
        <tbody>
            {items_rows}
        </tbody>
    </table>

    <div class="totals">
        <table>
            <tr>
                <td>Subtotal:</td>
                <td class="right">{format_currency(invoice.subtotal, invoice.currency)}</td>
            </tr>
            <tr>
                <td>Tax:</td>
                <td class="right">{format_currency(invoice.total_tax, invoice.currency)}</td>
            </tr>
            {"<tr><td>Discount:</td><td class='right'>-" + format_currency(invoice.total_discount, invoice.currency) + "</td></tr>" if invoice.total_discount > 0 else ""}
            <tr>
                <td class="grand-total">TOTAL:</td>
                <td class="right grand-total">{format_currency(invoice.grand_total, invoice.currency)}</td>
            </tr>
        </table>
    </div>

    {"<div class='notes'><h4>Notes</h4><p>" + invoice.notes.replace(chr(10), '<br>') + "</p></div>" if invoice.notes else ""}

    <div class="footer">
        <p>Automatically generated document — Invoice Generator v1.0</p>
    </div>
</body>
</html>"""
