from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class PortfolioRowDTO:
    """
    Flat data transfer object representing one row in the output table.
    All values are Python primitives ready for formatting — no domain
    objects cross this boundary into the presentation layer.

    Monetary values are plain Decimal (JPY).
    Percentage values are already multiplied by 100 (e.g. 2.5 means 2.5%).
    """

    # Identity
    ticker_symbol: str    # "7203.T"
    company_name: str     # トヨタ自動車

    # Holdings (from CSV)
    shares: Decimal
    average_cost: Decimal          # 平均取得単価 (JPY)
    total_cost: Decimal            # 評価額 簿価 (JPY)

    # Live price
    current_price: Optional[Decimal]
    current_value: Optional[Decimal]    # shares × current_price
    gain_loss: Optional[Decimal]        # current_value - total_cost
    gain_loss_pct: Optional[Decimal]    # gain_loss / total_cost × 100

    # Valuation
    trailing_pe: Optional[Decimal]
    forward_pe: Optional[Decimal]
    price_to_book: Optional[Decimal]
    enterprise_to_ebitda: Optional[Decimal]

    # Per-share
    trailing_eps: Optional[Decimal]
    book_value: Optional[Decimal]

    # Yield / Returns (display as %, e.g. 2.5 means 2.5%)
    dividend_yield_pct: Optional[Decimal]
    return_on_equity_pct: Optional[Decimal]
    payout_ratio_pct: Optional[Decimal]

    # Margins (display as %)
    operating_margins_pct: Optional[Decimal]
    profit_margins_pct: Optional[Decimal]

    # Balance Sheet
    current_ratio: Optional[Decimal]
    equity_ratio_pct: Optional[Decimal]   # 自己資本比率

    # Size / Range
    market_cap: Optional[int]
    fifty_two_week_high: Optional[Decimal]
    fifty_two_week_low: Optional[Decimal]

    # Additional
    beta: Optional[Decimal]
