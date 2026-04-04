from decimal import Decimal

from stock_tracker.domain.entities.holding import Holding
from stock_tracker.domain.value_objects.money import Currency, Money
from stock_tracker.domain.value_objects.ticker import Ticker


class TestHolding:
    def _make(self, shares: int, cost: int) -> Holding:
        return Holding(
            ticker=Ticker.from_sbi_code("7203"),
            name="トヨタ自動車",
            shares=Decimal(shares),
            average_cost=Money(Decimal(cost), Currency.JPY),
        )

    def test_total_cost_is_shares_times_average_cost(self):
        holding = self._make(shares=100, cost=2000)
        assert holding.total_cost.amount == Decimal("200000")

    def test_total_cost_currency_matches_average_cost(self):
        holding = self._make(shares=50, cost=3000)
        assert holding.total_cost.currency == Currency.JPY

    def test_total_cost_fractional_shares(self):
        holding = Holding(
            ticker=Ticker.from_sbi_code("7203"),
            name="テスト",
            shares=Decimal("1.5"),
            average_cost=Money(Decimal("1000"), Currency.JPY),
        )
        assert holding.total_cost.amount == Decimal("1500")
