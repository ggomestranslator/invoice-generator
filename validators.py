"""
Validators — Invoice Generator

Input validation with clear error messages.
Validates structure, required fields, and business rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass
class ValidationError:
    """A single validation error."""
    field: str
    message: str
    value: Any = None


class InvoiceValidator:
    """Validates invoice input data before model creation."""

    def validate(self, data: dict) -> list[ValidationError]:
        """Validate raw invoice data. Returns list of errors (empty = valid)."""
        errors = []

        # Required top-level fields
        required = ["invoice_number", "issue_date", "due_date", "seller", "buyer", "items"]
        for field_name in required:
            if field_name not in data:
                errors.append(ValidationError(field_name, f"Required field '{field_name}' is missing"))

        if errors:
            return errors  # Can't validate further without required fields

        # Invoice number format
        inv_num = data.get("invoice_number", "")
        if not inv_num or len(inv_num) < 3:
            errors.append(ValidationError("invoice_number", "Must be at least 3 characters"))

        # Dates
        errors.extend(self._validate_dates(data))

        # Parties
        errors.extend(self._validate_party(data.get("seller", {}), "seller"))
        errors.extend(self._validate_party(data.get("buyer", {}), "buyer"))

        # Items
        errors.extend(self._validate_items(data.get("items", [])))

        # Currency
        currency = data.get("currency", "BRL")
        valid_currencies = ["BRL", "USD", "EUR", "GBP"]
        if currency not in valid_currencies:
            errors.append(ValidationError(
                "currency", f"Unsupported currency '{currency}'. Valid: {valid_currencies}"
            ))

        return errors

    def _validate_dates(self, data: dict) -> list[ValidationError]:
        """Validate date fields."""
        errors = []

        issue_date = self._parse_date(data.get("issue_date"))
        due_date = self._parse_date(data.get("due_date"))

        if issue_date is None:
            errors.append(ValidationError("issue_date", "Invalid date format. Use YYYY-MM-DD"))
        if due_date is None:
            errors.append(ValidationError("due_date", "Invalid date format. Use YYYY-MM-DD"))

        if issue_date and due_date and due_date < issue_date:
            errors.append(ValidationError("due_date", "Due date cannot be before issue date"))

        return errors

    def _validate_party(self, party: dict, prefix: str) -> list[ValidationError]:
        """Validate seller/buyer data."""
        errors = []

        if not isinstance(party, dict):
            errors.append(ValidationError(prefix, "Must be an object with name and address"))
            return errors

        if not party.get("name"):
            errors.append(ValidationError(f"{prefix}.name", "Name is required"))
        if not party.get("address"):
            errors.append(ValidationError(f"{prefix}.address", "Address is required"))

        email = party.get("email", "")
        if email and "@" not in email:
            errors.append(ValidationError(f"{prefix}.email", f"Invalid email: '{email}'"))

        return errors

    def _validate_items(self, items: list) -> list[ValidationError]:
        """Validate line items."""
        errors = []

        if not items:
            errors.append(ValidationError("items", "At least one item is required"))
            return errors

        if not isinstance(items, list):
            errors.append(ValidationError("items", "Items must be a list"))
            return errors

        for i, item in enumerate(items):
            prefix = f"items[{i}]"

            if not isinstance(item, dict):
                errors.append(ValidationError(prefix, "Each item must be an object"))
                continue

            if not item.get("description"):
                errors.append(ValidationError(f"{prefix}.description", "Description is required"))

            # Quantity
            qty = item.get("quantity")
            if qty is None:
                errors.append(ValidationError(f"{prefix}.quantity", "Quantity is required"))
            elif not isinstance(qty, (int, float)) or qty <= 0:
                errors.append(ValidationError(f"{prefix}.quantity", "Must be a positive number"))

            # Unit price
            price = item.get("unit_price")
            if price is None:
                errors.append(ValidationError(f"{prefix}.unit_price", "Unit price is required"))
            elif not isinstance(price, (int, float)) or price < 0:
                errors.append(ValidationError(f"{prefix}.unit_price", "Must be a non-negative number"))

            # Tax rate
            tax = item.get("tax_rate", 0)
            if not isinstance(tax, (int, float)) or tax < 0 or tax > 1:
                errors.append(ValidationError(f"{prefix}.tax_rate", "Must be between 0 and 1 (e.g., 0.05 = 5%)"))

            # Discount
            discount = item.get("discount_pct", 0)
            if not isinstance(discount, (int, float)) or discount < 0 or discount > 1:
                errors.append(ValidationError(f"{prefix}.discount_pct", "Must be between 0 and 1"))

        return errors

    @staticmethod
    def _parse_date(value: Any) -> date | None:
        """Parse date from string or return None."""
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return None
        return None
