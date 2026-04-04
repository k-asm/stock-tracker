from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Percentage:
    """
    Represents a ratio stored as a decimal fraction (0.05 = 5%).
    yfinance returns ratios like dividendYield as 0.025 meaning 2.5%.
    """

    value: Decimal  # stored as fraction, e.g. 0.025

    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, "value", Decimal(str(self.value)))

    @property
    def as_percent(self) -> Decimal:
        return self.value * 100

    def __str__(self) -> str:
        return f"{self.as_percent:.2f}%"
