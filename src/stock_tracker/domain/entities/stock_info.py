from dataclasses import dataclass
from decimal import Decimal

from ..value_objects.money import Money
from ..value_objects.percentage import Percentage
from ..value_objects.ticker import Ticker


@dataclass(frozen=True)
class StockInfo:
    """
    Live financial data for a single stock fetched from a market data source.
    All fields are Optional because yfinance frequently returns None for
    Japanese stocks (data availability varies by company and listing).

    Field naming follows yfinance .info keys for traceability.
    """

    ticker: Ticker

    # --- Price ---
    current_price: Money | None = None  # 現在値 (currentPrice)
    fifty_two_week_high: Money | None = None  # 52週高値
    fifty_two_week_low: Money | None = None  # 52週安値

    # --- Valuation ---
    trailing_pe: Decimal | None = None  # PER (実績)
    forward_pe: Decimal | None = None  # PER (予想)
    price_to_book: Decimal | None = None  # PBR
    enterprise_to_ebitda: Decimal | None = None  # EV/EBITDA

    # --- Per-Share ---
    trailing_eps: Decimal | None = None  # EPS
    book_value: Decimal | None = None  # BPS

    # --- Yield / Returns ---
    dividend_yield: Percentage | None = None  # 配当利回り
    return_on_equity: Percentage | None = None  # ROE
    payout_ratio: Percentage | None = None  # 配当性向

    # --- Margins ---
    operating_margins: Percentage | None = None  # 営業利益率
    profit_margins: Percentage | None = None  # 純利益率

    # --- Balance Sheet / Liquidity ---
    current_ratio: Decimal | None = None  # 流動比率
    equity_ratio: Percentage | None = None  # 自己資本比率 (derived)

    # --- Size ---
    market_cap: int | None = None  # 時価総額 (raw yen)

    # --- Additional ---
    beta: Decimal | None = None  # ベータ値
    shares_outstanding: int | None = None  # 発行済株式数
