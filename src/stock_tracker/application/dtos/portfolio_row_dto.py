from dataclasses import dataclass
from decimal import Decimal


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
    ticker_symbol: str  # "7203.T"
    company_name: str  # トヨタ自動車

    # Holdings (from CSV)
    shares: Decimal
    average_cost: Decimal  # 平均取得単価 (JPY)
    total_cost: Decimal  # 評価額 簿価 (JPY)

    # Live price
    current_price: Decimal | None
    current_value: Decimal | None  # shares × current_price
    gain_loss: Decimal | None  # current_value - total_cost
    gain_loss_pct: Decimal | None  # gain_loss / total_cost × 100

    # Valuation
    trailing_pe: Decimal | None
    forward_pe: Decimal | None
    price_to_book: Decimal | None
    enterprise_to_ebitda: Decimal | None

    # Per-share
    trailing_eps: Decimal | None
    book_value: Decimal | None

    # Yield / Returns (display as %, e.g. 2.5 means 2.5%)
    dividend_yield_pct: Decimal | None
    return_on_equity_pct: Decimal | None
    payout_ratio_pct: Decimal | None

    # Margins (display as %)
    operating_margins_pct: Decimal | None
    profit_margins_pct: Decimal | None

    # Balance Sheet
    current_ratio: Decimal | None
    equity_ratio_pct: Decimal | None  # 自己資本比率

    # Size / Range
    market_cap: int | None
    fifty_two_week_high: Decimal | None
    fifty_two_week_low: Decimal | None

    # Additional
    beta: Decimal | None
