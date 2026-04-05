from decimal import Decimal
from typing import Any

from ...domain.value_objects.money import Currency, Money
from ...domain.value_objects.percentage import Percentage


def to_decimal(value: Any) -> Decimal | None:
    """yfinance の生値を Decimal に変換する。None / NaN / Inf はすべて None を返す。"""
    if value is None:
        return None
    try:
        d = Decimal(str(value))
        # yfinance sometimes returns NaN as a float
        if d.is_nan() or d.is_infinite():
            return None
        return d
    except Exception:
        return None


def to_money(value: Any) -> Money | None:
    d = to_decimal(value)
    return Money(d, Currency.JPY) if d is not None else None


def to_percentage(value: Any) -> Percentage | None:
    d = to_decimal(value)
    return Percentage(d) if d is not None else None
