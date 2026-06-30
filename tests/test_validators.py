"""Unit tests for invoice validators."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validators import InvoiceValidator


def get_valid_data() -> dict:
    """Return minimal valid invoice data."""
    return {
        "invoice_number": "INV-001",
        "issue_date": "2024-03-15",
        "due_date": "2024-04-15",
        "currency": "BRL",
        "seller": {"name": "Seller Co", "address": "Address 1", "email": "a@b.com"},
        "buyer": {"name": "Buyer Co", "address": "Address 2", "email": "c@d.com"},
        "items": [
            {"description": "Service", "quantity": 10, "unit_price": 100.0, "tax_rate": 0.05}
        ],
    }


validator = InvoiceValidator()


def test_valid_invoice():
    """Valid data produces no errors."""
    errors = validator.validate(get_valid_data())
    assert errors == [], f"Unexpected errors: {errors}"


def test_missing_required_fields():
    """Missing required fields are detected."""
    errors = validator.validate({})
    assert len(errors) >= 5  # All required fields missing
    field_names = [e.field for e in errors]
    assert "invoice_number" in field_names
    assert "items" in field_names


def test_invalid_date_format():
    """Invalid date format is rejected."""
    data = get_valid_data()
    data["issue_date"] = "15/03/2024"  # Wrong format
    errors = validator.validate(data)
    assert any(e.field == "issue_date" for e in errors)


def test_due_date_before_issue():
    """Due date before issue date is rejected."""
    data = get_valid_data()
    data["issue_date"] = "2024-04-15"
    data["due_date"] = "2024-03-15"
    errors = validator.validate(data)
    assert any(e.field == "due_date" for e in errors)


def test_empty_items():
    """Empty items list is rejected."""
    data = get_valid_data()
    data["items"] = []
    errors = validator.validate(data)
    assert any(e.field == "items" for e in errors)


def test_negative_quantity():
    """Negative quantity is rejected."""
    data = get_valid_data()
    data["items"][0]["quantity"] = -5
    errors = validator.validate(data)
    assert any("quantity" in e.field for e in errors)


def test_invalid_tax_rate():
    """Tax rate > 1 is rejected."""
    data = get_valid_data()
    data["items"][0]["tax_rate"] = 5.0  # Should be 0.05, not 5
    errors = validator.validate(data)
    assert any("tax_rate" in e.field for e in errors)


def test_invalid_email():
    """Invalid email format detected."""
    data = get_valid_data()
    data["seller"]["email"] = "not-an-email"
    errors = validator.validate(data)
    assert any("email" in e.field for e in errors)


def test_unsupported_currency():
    """Unsupported currency is rejected."""
    data = get_valid_data()
    data["currency"] = "XYZ"
    errors = validator.validate(data)
    assert any(e.field == "currency" for e in errors)


def test_missing_item_description():
    """Item without description is rejected."""
    data = get_valid_data()
    data["items"][0]["description"] = ""
    errors = validator.validate(data)
    assert any("description" in e.field for e in errors)


if __name__ == "__main__":
    tests = [
        test_valid_invoice,
        test_missing_required_fields,
        test_invalid_date_format,
        test_due_date_before_issue,
        test_empty_items,
        test_negative_quantity,
        test_invalid_tax_rate,
        test_invalid_email,
        test_unsupported_currency,
        test_missing_item_description,
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
