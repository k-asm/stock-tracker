from decimal import Decimal
from unittest.mock import MagicMock

from stock_tracker.application.use_cases.analyze_portfolio import (
    AnalyzePortfolioRequest,
    AnalyzePortfolioUseCase,
)
from stock_tracker.domain.entities.holding import Holding
from stock_tracker.domain.entities.stock_info import StockInfo
from stock_tracker.domain.value_objects.money import Currency, Money
from stock_tracker.domain.value_objects.ticker import Ticker


def _make_holding(code: str, shares: int, cost: int) -> Holding:
    return Holding(
        ticker=Ticker.from_sbi_code(code),
        name=f"Company {code}",
        shares=Decimal(shares),
        average_cost=Money(Decimal(cost), Currency.JPY),
    )


def _make_stock_info(code: str, price: int) -> StockInfo:
    return StockInfo(
        ticker=Ticker.from_sbi_code(code),
        current_price=Money(Decimal(price), Currency.JPY),
    )


def test_execute_computes_gain_loss():
    holdings_repo = MagicMock()
    holdings_repo.load.return_value = [_make_holding("7203", 100, 2000)]

    stock_info_repo = MagicMock()
    stock_info_repo.fetch_many.return_value = [_make_stock_info("7203", 2500)]

    use_case = AnalyzePortfolioUseCase(holdings_repo, stock_info_repo)
    rows = use_case.execute(AnalyzePortfolioRequest(source="dummy.csv"))

    assert len(rows) == 1
    row = rows[0]
    assert row.current_price == Decimal("2500")
    assert row.current_value == Decimal("250000")
    assert row.gain_loss == Decimal("50000")
    assert row.gain_loss_pct == Decimal("25")


def test_execute_handles_missing_stock_info():
    holdings_repo = MagicMock()
    holdings_repo.load.return_value = [_make_holding("9999", 10, 1000)]

    stock_info_repo = MagicMock()
    stock_info_repo.fetch_many.return_value = [
        StockInfo(ticker=Ticker.from_sbi_code("9999"))  # all None
    ]

    use_case = AnalyzePortfolioUseCase(holdings_repo, stock_info_repo)
    rows = use_case.execute(AnalyzePortfolioRequest(source="dummy.csv"))

    assert len(rows) == 1
    assert rows[0].current_price is None
    assert rows[0].gain_loss is None
