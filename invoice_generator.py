"""
Invoice Generator — Main Application

CLI application for generating invoices from JSON/YAML data.
Supports multiple output formats: HTML, Markdown, PDF.

Usage:
    python invoice_generator.py --sample --format md
    python invoice_generator.py --input examples/sample_invoice.json --format html
    python invoice_generator.py --input examples/ --format html --output output/
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from models import Invoice, Party, LineItem
from validators import InvoiceValidator
from renderers import get_renderer

logger = logging.getLogger(__name__)


# =============================================================================
# Data Loading
# =============================================================================


def load_invoice_data(file_path: Path) -> dict:
    """Load invoice data from JSON or YAML file."""
    suffix = file_path.suffix.lower()

    if suffix == ".json":
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    elif suffix in (".yaml", ".yml"):
        try:
            import yaml
            with open(file_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except ImportError:
            raise RuntimeError("YAML support requires 'pyyaml'. Install: pip install pyyaml")
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .json or .yaml")


def parse_invoice(data: dict) -> Invoice:
    """Parse validated data into Invoice model."""
    seller = Party(
        name=data["seller"]["name"],
        address=data["seller"]["address"],
        tax_id=data["seller"].get("tax_id", ""),
        email=data["seller"].get("email", ""),
        phone=data["seller"].get("phone", ""),
    )

    buyer = Party(
        name=data["buyer"]["name"],
        address=data["buyer"]["address"],
        tax_id=data["buyer"].get("tax_id", ""),
        email=data["buyer"].get("email", ""),
        phone=data["buyer"].get("phone", ""),
    )

    items = []
    for item_data in data["items"]:
        items.append(LineItem(
            description=item_data["description"],
            quantity=Decimal(str(item_data["quantity"])),
            unit_price=Decimal(str(item_data["unit_price"])),
            unit=item_data.get("unit", "un"),
            tax_rate=Decimal(str(item_data.get("tax_rate", 0))),
            discount_pct=Decimal(str(item_data.get("discount_pct", 0))),
        ))

    return Invoice(
        invoice_number=data["invoice_number"],
        issue_date=datetime.strptime(data["issue_date"], "%Y-%m-%d").date(),
        due_date=datetime.strptime(data["due_date"], "%Y-%m-%d").date(),
        seller=seller,
        buyer=buyer,
        items=items,
        currency=data.get("currency", "BRL"),
        notes=data.get("notes", ""),
        payment_terms=data.get("payment_terms", ""),
        status=data.get("status", "draft"),
    )


# =============================================================================
# Sample Data
# =============================================================================


def create_sample_invoice() -> Invoice:
    """Create a sample invoice for demonstration."""
    return Invoice(
        invoice_number="INV-2024-SAMPLE",
        issue_date=date.today(),
        due_date=date(2024, 12, 31),
        seller=Party(
            name="Acme Tech Solutions Ltda",
            address="Av. Paulista, 1000 - São Paulo, SP",
            tax_id="12.345.678/0001-90",
            email="financeiro@acmetech.com.br",
        ),
        buyer=Party(
            name="Cliente Demo Ltda",
            address="Rua Augusta, 500 - São Paulo, SP",
            tax_id="98.765.432/0001-10",
            email="compras@demo.com",
        ),
        items=[
            LineItem(
                description="Consultoria em Arquitetura AI",
                quantity=Decimal("40"),
                unit_price=Decimal("350.00"),
                unit="horas",
                tax_rate=Decimal("0.05"),
            ),
            LineItem(
                description="Implementação RAG Pipeline",
                quantity=Decimal("1"),
                unit_price=Decimal("12000.00"),
                unit="projeto",
                tax_rate=Decimal("0.05"),
                discount_pct=Decimal("0.10"),
            ),
        ],
        currency="BRL",
        notes="Pagamento via PIX ou transferência bancária.",
        status="draft",
    )


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Invoice Generator — Gera invoices em HTML, Markdown ou PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python invoice_generator.py --sample --format md
  python invoice_generator.py --input examples/sample_invoice.json --format html
  python invoice_generator.py --input examples/ --format html --output output/
        """,
    )
    parser.add_argument("--input", "-i", help="JSON/YAML file or directory with invoice data")
    parser.add_argument("--output", "-o", default="output", help="Output directory (default: output/)")
    parser.add_argument("--format", "-f", default="md", choices=["html", "md", "markdown", "pdf"],
                        help="Output format (default: md)")
    parser.add_argument("--sample", action="store_true", help="Generate a sample invoice")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of file")
    parser.add_argument("--validate-only", action="store_true", help="Only validate input, don't generate")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    # Determine input
    if args.sample:
        invoices = [create_sample_invoice()]
    elif args.input:
        input_path = Path(args.input)
        if input_path.is_file():
            files = [input_path]
        elif input_path.is_dir():
            files = list(input_path.glob("*.json")) + list(input_path.glob("*.yaml"))
            if not files:
                print(f"Error: No JSON/YAML files found in {input_path}")
                sys.exit(1)
        else:
            print(f"Error: Path not found: {input_path}")
            sys.exit(1)

        # Load and validate
        validator = InvoiceValidator()
        invoices = []

        for file in files:
            logger.info("Loading: %s", file.name)
            data = load_invoice_data(file)

            errors = validator.validate(data)
            if errors:
                print(f"\n❌ Validation errors in {file.name}:")
                for err in errors:
                    print(f"  • {err.field}: {err.message}")
                if args.validate_only:
                    continue
                sys.exit(1)

            if args.validate_only:
                print(f"  ✅ {file.name} — valid")
                continue

            invoices.append(parse_invoice(data))

        if args.validate_only:
            print("\nValidation complete.")
            sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)

    # Render
    renderer = get_renderer(args.format)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    for invoice in invoices:
        if args.stdout:
            print(renderer.render(invoice))
        else:
            saved_path = renderer.save(invoice, output_dir)
            print(f"✅ Generated: {saved_path}")
            print(f"   Total: {invoice.grand_total} {invoice.currency} | Items: {len(invoice.items)}")


if __name__ == "__main__":
    main()
