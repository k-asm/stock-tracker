from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

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
    current_price: Optional[Money] = None           # 現在値 (currentPrice)
    fifty_two_week_high: Optional[Money] = None     # 52週高値
    fifty_two_week_low: Optional[Money] = None      # 52週安値

    # --- Valuation ---
    trailing_pe: Optional[Decimal] = None           # PER (実績)
    forward_pe: Optional[Decimal] = None            # PER (予想)
    price_to_book: Optional[Decimal] = None         # PBR
    enterprise_to_ebitda: Optional[Decimal] = None  # EV/EBITDA

    # --- Per-Share ---
    trailing_eps: Optional[Decimal] = None          # EPS
    book_value: Optional[Decimal] = None            # BPS

    # --- Yield / Returns ---
    dividend_yield: Optional[Percentage] = None     # 配当利回り
    return_on_equity: Optional[Percentage] = None   # ROE
    payout_ratio: Optional[Percentage] = None       # 配当性向

    # --- Margins ---
    operating_margins: Optional[Percentage] = None  # 営業利益率
    profit_margins: Optional[Percentage] = None     # 純利益率

    # --- Balance Sheet / Liquidity ---
    current_ratio: Optional[Decimal] = None         # 流動比率
    equity_ratio: Optional[Percentage] = None       # 自己資本比率 (derived)

    # --- Size ---
    market_cap: Optional[int] = None                # 時価総額 (raw yen)

    # --- Additional ---
    beta: Optional[Decimal] = None                  # ベータ値
    shares_outstanding: Optional[int] = None        # 発行済株式数
