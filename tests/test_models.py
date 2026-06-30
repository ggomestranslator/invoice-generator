"""Unit tests for invoice data models."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decimal import Decimal
from datetime import date

from models import Party, LineItem, Invoice, format_currency


def test_line_item_subtotal():
    """Test basic subtotal calculation."""
    item = LineItem(
        description="Test",
        quantity=Decimal("10"),
        unit_price=Decimal("100.00"),
    )
    assert item.subtotal == Decimal("1000.00")
    assert item.tax_amount == Decimal("0")
    assert item.total == Decimal("1000.00")


def test_line_item_with_tax():
    """Test line item with tax."""
    item = LineItem(
        description="Service",
        quantity=Decimal("5"),
        unit_price=Decimal("200.00"),
        tax_rate=Decimal("0.10"),
    )
    assert item.subtotal == Decimal("1000.00")
    assert item.tax_amount == Decimal("100.00")
    assert item.total == Decimal("1100.00")


def test_line_item_with_discount():
    """Test line item with discount applied before tax."""
    item = LineItem(
        description="Product",
        quantity=Decimal("2"),
        unit_price=Decimal("500.00"),
        tax_rate=Decimal("0.05"),
        discount_pct=Decimal("0.10"),
    )
    assert item.subtotal == Decimal("1000.00")
    assert item.discount_amount == Decimal("100.00")
    assert item.taxable_amount == Decimal("900.00")
    assert item.tax_amount == Decimal("45.00")
    assert item.total == Decimal("945.00")


def test_invoice_totals():
    """Test invoice aggregate calculations."""
    invoice = Invoice(
        invoice_number="TEST-001",
        issue_date=date(2024, 1, 1),
        due_date=date(2024, 2, 1),
        seller=Party(name="Seller", address="Address 1"),
        buyer=Party(name="Buyer", address="Address 2"),
        items=[
            LineItem(description="A", quantity=Decimal("1"), unit_price=Decimal("100"), tax_rate=Decimal("0.10")),
            LineItem(description="B", quantity=Decimal("2"), unit_price=Decimal("50"), tax_rate=Decimal("0.05")),
        ],
    )
    assert invoice.subtotal == Decimal("200.00")
    assert invoice.total_tax == Decimal("15.00")
    assert invoice.grand_total == Decimal("215.00")


def test_invoice_overdue():
    """Test overdue detection."""
    invoice = Invoice(
        invoice_number="TEST-002",
        issue_date=date(2020, 1, 1),
        due_date=date(2020, 2, 1),
        seller=Party(name="S", address="A"),
        buyer=Party(name="B", address="A"),
        items=[LineItem(description="X", quantity=Decimal("1"), unit_price=Decimal("100"))],
        status="sent",
    )
    assert invoice.is_overdue is True

    invoice.status = "paid"
    assert invoice.is_overdue is False


def test_format_currency_brl():
    """Test BRL formatting."""
    assert format_currency(Decimal("1234.56"), "BRL") == "R$ 1.234,56"
    assert format_currency(Decimal("0.50"), "BRL") == "R$ 0,50"


def test_format_currency_usd():
    """Test USD formatting."""
    assert format_currency(Decimal("1234.56"), "USD") == "$ 1,234.56"


def test_format_currency_large_number():
    """Test formatting with large numbers."""
    result = format_currency(Decimal("1000000.00"), "BRL")
    assert "R$" in result
    assert "1.000.000" in result


if __name__ == "__main__":
    tests = [
        test_line_item_subtotal,
        test_line_item_with_tax,
        test_line_item_with_discount,
        test_invoice_totals,
        test_invoice_overdue,
        test_format_currency_brl,
        test_format_currency_usd,
        test_format_currency_large_number,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
            print(f"  ✅ {test.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {test.__name__}: {e}")

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
