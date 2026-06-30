"""
Quick Invoice Generator — Monthly Invoice in One Click

Reads fixed company/client data from .env, asks only for:
- Amount (default: R$ 6.250,00)
- Issue date (default: today)
- Due date (default: 30 days from issue)

Generates PDF + HTML automatically with sequential invoice numbering.

Usage:
    python generate_monthly_invoice.py                    # Interactive prompts
    python generate_monthly_invoice.py --amount 6250     # Skip amount prompt
    python generate_monthly_invoice.py --amount 6250 --no-prompt  # Fully automated
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path


def load_env():
    """Load .env file into environment variables."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("ERROR: .env file not found!")
        print("Copy .env.example to .env and fill in your data.")
        sys.exit(1)

    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)


def get_next_invoice_number() -> str:
    """Get next sequential invoice number by scanning output/ folder.
    
    Looks for pattern INV-NNNN only (ignores old INV-YYYY-NNN format).
    """
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    existing = list(output_dir.glob("INV-*.pdf"))
    if not existing:
        return "INV-0001"

    # Only match our 4-digit sequential pattern: INV-0001, INV-0002, etc.
    numbers = []
    for f in existing:
        match = re.match(r"^INV-(\d{4})$", f.stem)
        if match:
            numbers.append(int(match.group(1)))

    if not numbers:
        return "INV-0001"

    next_num = max(numbers) + 1
    return f"INV-{next_num:04d}"


def prompt_user(amount_arg: str | None = None, no_prompt: bool = False) -> tuple[Decimal, date, date]:
    """Get amount and dates from user (or use defaults)."""
    default_amount = Decimal("6250.00")
    today = date.today()
    default_due = today + timedelta(days=30)

    if no_prompt:
        amount = Decimal(str(amount_arg)) if amount_arg else default_amount
        return amount, today, default_due

    # Amount — always ask (this is what changes each month)
    if amount_arg:
        amount = Decimal(str(amount_arg))
    else:
        print(f"  Enter the invoice amount (numbers only).")
        print(f"  Example: 6250 or 6250.00")
        raw = input(f"\n  Amount: R$ ").strip()
        if raw:
            raw = raw.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".").strip()
            amount = Decimal(raw) if raw else default_amount
        else:
            amount = default_amount

    # Format for confirmation
    amt_show = f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    print(f"  >> {amt_show}")
    print()

    # Issue date — ask with clear format, default to today
    today_str = today.strftime("%m.%d.%Y")
    print(f"  Invoice date. Press ENTER for today ({today_str})")
    print(f"  Or type a date as MM.DD.YYYY (e.g. 06.30.2026)")
    raw_date = input(f"\n  Date: ").strip()
    if raw_date:
        # Accept both dots and slashes
        raw_date = raw_date.replace("/", ".").replace("-", ".")
        parts = raw_date.split(".")
        if len(parts) == 3:
            try:
                issue = date(int(parts[2]), int(parts[0]), int(parts[1]))
            except ValueError:
                print(f"  [!] Invalid date, using today.")
                issue = today
        else:
            issue = today
    else:
        issue = today

    print(f"  >> {issue.strftime('%m.%d.%Y')}")
    print()

    # Due date — auto-calculated, just confirm
    default_due = issue + timedelta(days=30)
    due = default_due
    print(f"  Due date (30 days): {due.strftime('%m.%d.%Y')}")
    print()

    return amount, issue, due


def generate_invoice(amount: Decimal, issue_date: date, due_date: date):
    """Generate the invoice using the main invoice_generator module."""
    from models import Invoice, Party, LineItem
    from renderers import get_renderer

    invoice_number = get_next_invoice_number()

    seller = Party(
        name=os.environ["COMPANY_NAME"],
        address=os.environ.get("BILL_FROM", "").replace("\\n", "\n"),
        tax_id=os.environ["COMPANY_ID"],
        email=os.environ["SUPPORT_EMAIL"],
    )

    buyer = Party(
        name=os.environ.get("BILL_TO", "NATOORA LIMITED").split("\\n")[0],
        address=os.environ.get("BILL_TO", "").replace("\\n", "\n"),
        tax_id="",
        email="",
    )

    items = [
        LineItem(
            description=os.environ["SERVICE_TITLE"] + " - " + os.environ["SERVICE_DESC"],
            quantity=Decimal("1"),
            unit_price=amount,
            unit="service",
            tax_rate=Decimal("0"),
        )
    ]

    notes = (
        f"PAYMENT INFORMATION\n\n"
        f"Bank: {os.environ['BANK_NAME']}\n"
        f"Bank Code: {os.environ['BANK_CODE']}\n"
        f"Branch: {os.environ['BANK_BRANCH']}\n"
        f"Account: {os.environ['BANK_ACCOUNT']}\n"
        f"Beneficiary: {os.environ['BENEFICIARY_NAME']}\n"
        f"Beneficiary CNPJ: {os.environ['BENEFICIARY_CNPJ']}\n\n"
        f"PIX Key: {os.environ['PIX_KEY']}\n\n"
        f"Please make payment by the due date using either the bank account or the PIX key above."
    )

    invoice = Invoice(
        invoice_number=invoice_number,
        issue_date=issue_date,
        due_date=due_date,
        seller=seller,
        buyer=buyer,
        items=items,
        currency=os.environ.get("CURRENCY", "BRL"),
        notes=notes,
        status="sent",
    )

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    # Generate PDF
    pdf_renderer = get_renderer("pdf")
    pdf_path = pdf_renderer.save(invoice, output_dir)

    # Generate HTML (editable source)
    html_renderer = get_renderer("html")
    html_path = html_renderer.save(invoice, output_dir)

    return invoice, pdf_path, html_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate Monthly Invoice (one-click)")
    parser.add_argument("--amount", type=str, default=None, help="Amount in BRL (e.g., 6250)")
    parser.add_argument("--no-prompt", action="store_true", help="Skip all prompts, use defaults")
    args = parser.parse_args()

    load_env()

    company = os.environ['COMPANY_NAME']
    client = os.environ.get('BILL_TO', '').split('\\n')[0]
    service = os.environ['SERVICE_TITLE']

    print()
    print("  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510")
    print("  \u2502         MONTHLY INVOICE GENERATOR            \u2502")
    print("  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518")
    print()
    print(f"  Company:  {company}")
    print(f"  Client:   {client}")
    print(f"  Service:  {service}")
    print()
    print("  " + "\u2500" * 48)
    print()

    amount, issue_date, due_date = prompt_user(args.amount, args.no_prompt)

    print()
    print("  Generating invoice...")
    invoice, pdf_path, html_path = generate_invoice(amount, issue_date, due_date)

    # Format amount for display
    amt_display = f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    print()
    print("  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510")
    print("  \u2502      INVOICE GENERATED SUCCESSFULLY          \u2502")
    print("  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518")
    print()
    print(f"  Invoice #:  {invoice.invoice_number}")
    print(f"  Amount:     {amt_display}")
    print(f"  Issue Date: {issue_date.strftime('%d/%m/%Y')}")
    print(f"  Due Date:   {due_date.strftime('%d/%m/%Y')}")
    print()
    print(f"  PDF:  {pdf_path.name}")
    print(f"  HTML: {html_path.name}")
    print()
    print("  " + "\u2500" * 48)
    print()

    # Open PDF automatically
    if sys.platform == "win32":
        os.startfile(str(pdf_path))


if __name__ == "__main__":
    main()
