"""Unit tests for invoice renderers."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decimal import Decimal
from datetime import date

from models import Party, LineItem, Invoice
from renderers import get_renderer, HTMLRenderer, MarkdownRenderer


def create_test_invoice() -> Invoice:
    """Create a test invoice for renderer testing."""
    return Invoice(
        invoice_number="TEST-RENDER-001",
        issue_date=date(2024, 6, 15),
        due_date=date(2024, 7, 15),
        seller=Party(name="Test Seller", address="Seller Address", tax_id="11.111.111/0001-11", email="s@test.com"),
        buyer=Party(name="Test Buyer", address="Buyer Address", tax_id="22.222.222/0001-22", email="b@test.com"),
        items=[
            LineItem(description="Item One", quantity=Decimal("5"), unit_price=Decimal("100.00"), tax_rate=Decimal("0.10")),
            LineItem(description="Item Two", quantity=Decimal("2"), unit_price=Decimal("250.00"), unit="un"),
        ],
        currency="BRL",
        notes="Test notes here",
        status="draft",
    )


def test_html_renderer_produces_html():
    """HTML renderer produces valid HTML with required elements."""
    invoice = create_test_invoice()
    renderer = HTMLRenderer()
    output = renderer.render(invoice)

    assert "<!DOCTYPE html>" in output
    assert "TEST-RENDER-001" in output
    assert "Test Seller" in output
    assert "Test Buyer" in output
    assert "Item One" in output
    assert "Item Two" in output
    assert "R$" in output


def test_markdown_renderer_produces_md():
    """Markdown renderer produces valid Markdown."""
    invoice = create_test_invoice()
    renderer = MarkdownRenderer()
    output = renderer.render(invoice)

    assert "# Invoice TEST-RENDER-001" in output
    assert "Test Seller" in output
    assert "Test Buyer" in output
    assert "Item One" in output
    assert "|" in output  # Tables


def test_html_contains_totals():
    """HTML output contains correct totals."""
    invoice = create_test_invoice()
    renderer = HTMLRenderer()
    output = renderer.render(invoice)

    # Item 1: 5 * 100 = 500, tax 10% = 50, total = 550
    # Item 2: 2 * 250 = 500, tax 0% = 0, total = 500
    # Grand total = 1050
    assert "1.050" in output or "1050" in output


def test_markdown_contains_notes():
    """Markdown output includes notes section."""
    invoice = create_test_invoice()
    renderer = MarkdownRenderer()
    output = renderer.render(invoice)

    assert "Test notes here" in output
    assert "Notes" in output


def test_get_renderer_factory():
    """Factory returns correct renderer types."""
    assert isinstance(get_renderer("html"), HTMLRenderer)
    assert isinstance(get_renderer("md"), MarkdownRenderer)
    assert isinstance(get_renderer("markdown"), MarkdownRenderer)


def test_get_renderer_invalid():
    """Factory raises for invalid format."""
    try:
        get_renderer("invalid")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unsupported format" in str(e)


def test_html_renderer_save(tmp_path=None):
    """HTML renderer saves file correctly."""
    import tempfile
    output_dir = Path(tempfile.mkdtemp())
    invoice = create_test_invoice()
    renderer = HTMLRenderer()

    saved = renderer.save(invoice, output_dir)
    assert saved.exists()
    assert saved.suffix == ".html"
    assert "TEST-RENDER-001" in saved.name

    content = saved.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content

    # Cleanup
    saved.unlink()
    output_dir.rmdir()


if __name__ == "__main__":
    tests = [
        test_html_renderer_produces_html,
        test_markdown_renderer_produces_md,
        test_html_contains_totals,
        test_markdown_contains_notes,
        test_get_renderer_factory,
        test_get_renderer_invalid,
        test_html_renderer_save,
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
        except Exception as e:
            failed += 1
            print(f"  ❌ {test.__name__}: {type(e).__name__}: {e}")

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
