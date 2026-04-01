from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class Currency(Enum):
    JPY = "JPY"
    USD = "USD"


@dataclass(frozen=True)
class Money:
    """
    Immutable monetary value with currency.
    Uses Decimal to avoid float precision issues in financial calculations.
    """

    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))
