"""
Data Models — Invoice Generator

Defines the core domain models using dataclasses.
All monetary calculations use Decimal for precision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


@dataclass
class Party:
    """Represents a seller or buyer entity."""
    name: str
    address: str
    tax_id: str = ""
    email: str = ""
    phone: str = ""


@dataclass
class LineItem:
    """A single item/service on the invoice."""
    description: str
    quantity: Decimal
    unit_price: Decimal
    unit: str = "un"
    tax_rate: Decimal = Decimal("0")
    discount_pct: Decimal = Decimal("0")

    @property
    def subtotal(self) -> Decimal:
        """Quantity × unit price before tax."""
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def discount_amount(self) -> Decimal:
        """Discount applied to subtotal."""
        return (self.subtotal * self.discount_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def taxable_amount(self) -> Decimal:
        """Subtotal after discount."""
        return self.subtotal - self.discount_amount

    @property
    def tax_amount(self) -> Decimal:
        """Tax calculated on taxable amount."""
        return (self.taxable_amount * self.tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def total(self) -> Decimal:
        """Final line total including tax."""
        return self.taxable_amount + self.tax_amount


@dataclass
class Invoice:
    """Complete invoice document."""
    invoice_number: str
    issue_date: date
    due_date: date
    seller: Party
    buyer: Party
    items: list[LineItem]
    currency: str = "BRL"
    notes: str = ""
    payment_terms: str = ""
    status: str = "draft"  # draft, sent, paid, overdue

    @property
    def subtotal(self) -> Decimal:
        """Sum of all line subtotals before tax."""
        return sum((item.taxable_amount for item in self.items), Decimal("0"))

    @property
    def total_tax(self) -> Decimal:
        """Sum of all tax amounts."""
        return sum((item.tax_amount for item in self.items), Decimal("0"))

    @property
    def total_discount(self) -> Decimal:
        """Sum of all discounts."""
        return sum((item.discount_amount for item in self.items), Decimal("0"))

    @property
    def grand_total(self) -> Decimal:
        """Final invoice total."""
        return self.subtotal + self.total_tax

    @property
    def is_overdue(self) -> bool:
        """Check if invoice is past due date."""
        return date.today() > self.due_date and self.status != "paid"


# =============================================================================
# Currency Formatting
# =============================================================================

CURRENCY_SYMBOLS = {
    "BRL": "R$",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
}

CURRENCY_LOCALE = {
    "BRL": {"decimal": ",", "thousands": "."},
    "USD": {"decimal": ".", "thousands": ","},
    "EUR": {"decimal": ",", "thousands": "."},
    "GBP": {"decimal": ".", "thousands": ","},
}


def format_currency(amount: Decimal, currency: str = "BRL") -> str:
    """Format amount with currency symbol and locale-appropriate separators."""
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    locale = CURRENCY_LOCALE.get(currency, CURRENCY_LOCALE["USD"])

    # Format with 2 decimal places
    abs_amount = abs(amount)
    int_part = int(abs_amount)
    dec_part = int((abs_amount - int_part) * 100)

    # Add thousands separators
    int_str = f"{int_part:,}".replace(",", locale["thousands"])
    formatted = f"{symbol} {int_str}{locale['decimal']}{dec_part:02d}"

    if amount < 0:
        formatted = f"-{formatted}"

    return formatted
