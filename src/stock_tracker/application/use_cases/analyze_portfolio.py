from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from ...domain.entities.holding import Holding
from ...domain.entities.stock_info import StockInfo
from ...domain.repositories.holdings_repository import HoldingsRepository
from ...domain.repositories.stock_info_repository import StockInfoRepository
from ...domain.value_objects.percentage import Percentage
from ..dtos.portfolio_row_dto import PortfolioRowDTO


@dataclass
class AnalyzePortfolioRequest:
    source: str  # CSV file path


class AnalyzePortfolioUseCase:
    """
    Orchestrates portfolio analysis:
    1. Load holdings from repository (CSV adapter)
    2. Fetch live data for each ticker (yfinance adapter, optionally cached)
    3. Compute derived metrics (gain/loss, current value)
    4. Return list of PortfolioRowDTOs for the presentation layer

    Both repositories are injected (Dependency Inversion).
    No imports from infrastructure or presentation.
    """

    def __init__(
        self,
        holdings_repo: HoldingsRepository,
        stock_info_repo: StockInfoRepository,
    ) -> None:
        self._holdings_repo = holdings_repo
        self._stock_info_repo = stock_info_repo

    def execute(self, request: AnalyzePortfolioRequest) -> Sequence[PortfolioRowDTO]:
        holdings = self._holdings_repo.load(request.source)
        tickers = [h.ticker for h in holdings]
        stock_infos = {
            si.ticker.symbol: si for si in self._stock_info_repo.fetch_many(tickers)
        }

        return [
            self._build_row(holding, stock_infos.get(holding.ticker.symbol))
            for holding in holdings
        ]

    def _build_row(self, holding: Holding, info: StockInfo | None) -> PortfolioRowDTO:
        current_price = (
            info.current_price.amount if info and info.current_price else None
        )
        current_value = (
            holding.shares * current_price if current_price is not None else None
        )
        gain_loss = (
            current_value - holding.total_cost.amount
            if current_value is not None
            else None
        )
        gain_loss_pct = (
            gain_loss / holding.total_cost.amount * Decimal("100")
            if gain_loss is not None and holding.total_cost.amount != 0
            else None
        )

        def pct(p: Percentage | None) -> Decimal | None:
            return p.as_percent if p else None

        def money_amount(m) -> Decimal | None:
            return m.amount if m else None

        return PortfolioRowDTO(
            ticker_symbol=holding.ticker.symbol,
            company_name=holding.name,
            shares=holding.shares,
            average_cost=holding.average_cost.amount,
            total_cost=holding.total_cost.amount,
            current_price=current_price,
            current_value=current_value,
            gain_loss=gain_loss,
            gain_loss_pct=gain_loss_pct,
            trailing_pe=info.trailing_pe if info else None,
            forward_pe=info.forward_pe if info else None,
            price_to_book=info.price_to_book if info else None,
            enterprise_to_ebitda=info.enterprise_to_ebitda if info else None,
            trailing_eps=info.trailing_eps if info else None,
            book_value=info.book_value if info else None,
            dividend_yield_pct=pct(info.dividend_yield if info else None),
            return_on_equity_pct=pct(info.return_on_equity if info else None),
            payout_ratio_pct=pct(info.payout_ratio if info else None),
            operating_margins_pct=pct(info.operating_margins if info else None),
            profit_margins_pct=pct(info.profit_margins if info else None),
            current_ratio=info.current_ratio if info else None,
            equity_ratio_pct=pct(info.equity_ratio if info else None),
            market_cap=info.market_cap if info else None,
            fifty_two_week_high=money_amount(
                info.fifty_two_week_high if info else None
            ),
            fifty_two_week_low=money_amount(info.fifty_two_week_low if info else None),
            beta=info.beta if info else None,
        )
