from decimal import Decimal

import pytest

from stock_tracker.domain.value_objects.money import Currency, Money
from stock_tracker.domain.value_objects.percentage import Percentage
from stock_tracker.domain.value_objects.ticker import Ticker


class TestTicker:
    def test_from_sbi_code_appends_dot_t(self):
        ticker = Ticker.from_sbi_code("7203")
        assert ticker.symbol == "7203.T"

    def test_from_sbi_code_strips_whitespace(self):
        ticker = Ticker.from_sbi_code("  9984  ")
        assert ticker.symbol == "9984.T"

    def test_empty_symbol_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            Ticker("")

    def test_direct_construction(self):
        ticker = Ticker("7203.T")
        assert ticker.symbol == "7203.T"

    def test_frozen(self):
        ticker = Ticker.from_sbi_code("7203")
        with pytest.raises((AttributeError, TypeError)):
            ticker.symbol = "other"  # type: ignore[misc]


class TestMoney:
    def test_stores_decimal(self):
        m = Money(Decimal("1500"), Currency.JPY)
        assert m.amount == Decimal("1500")
        assert m.currency == Currency.JPY

    def test_coerces_int_to_decimal(self):
        m = Money(2000, Currency.JPY)  # type: ignore[arg-type]
        assert isinstance(m.amount, Decimal)
        assert m.amount == Decimal("2000")

    def test_coerces_float_to_decimal(self):
        m = Money(10.5, Currency.JPY)  # type: ignore[arg-type]
        assert isinstance(m.amount, Decimal)
        assert m.amount == Decimal("10.5")

    def test_frozen(self):
        m = Money(Decimal("100"), Currency.JPY)
        with pytest.raises((AttributeError, TypeError)):
            m.amount = Decimal("999")  # type: ignore[misc]

    def test_equality(self):
        a = Money(Decimal("500"), Currency.JPY)
        b = Money(Decimal("500"), Currency.JPY)
        assert a == b

    def test_inequality_different_currency(self):
        jpy = Money(Decimal("500"), Currency.JPY)
        usd = Money(Decimal("500"), Currency.USD)
        assert jpy != usd


class TestPercentage:
    def test_as_percent_multiplies_by_100(self):
        p = Percentage(Decimal("0.025"))
        assert p.as_percent == Decimal("2.5")

    def test_str_formats_with_two_decimals(self):
        p = Percentage(Decimal("0.025"))
        assert str(p) == "2.50%"

    def test_coerces_float_to_decimal(self):
        p = Percentage(0.05)  # type: ignore[arg-type]
        assert isinstance(p.value, Decimal)
        assert p.value == Decimal("0.05")

    def test_zero(self):
        p = Percentage(Decimal("0"))
        assert p.as_percent == Decimal("0")
        assert str(p) == "0.00%"

    def test_frozen(self):
        p = Percentage(Decimal("0.1"))
        with pytest.raises((AttributeError, TypeError)):
            p.value = Decimal("0.9")  # type: ignore[misc]
