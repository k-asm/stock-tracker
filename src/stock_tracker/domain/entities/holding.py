from dataclasses import dataclass
from decimal import Decimal

from ..value_objects.money import Money
from ..value_objects.ticker import Ticker


@dataclass(frozen=True)
class Holding:
    """
    A single stock position in the portfolio as read from SBI CSV.
    Represents what the investor holds - pure domain data,
    no live market information.
    """

    ticker: Ticker
    name: str          # Japanese company name from SBI CSV
    shares: Decimal    # 保有数量
    average_cost: Money  # 平均取得単価 (per share)

    @property
    def total_cost(self) -> Money:
        """評価額(簿価) = shares × average_cost"""
        return Money(self.shares * self.average_cost.amount, self.average_cost.currency)
