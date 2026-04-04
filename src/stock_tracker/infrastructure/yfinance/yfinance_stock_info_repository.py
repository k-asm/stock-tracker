from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Optional, Sequence

import yfinance as yf

from ...domain.entities.stock_info import StockInfo
from ...domain.repositories.stock_info_repository import StockInfoRepository
from ...domain.value_objects.money import Currency, Money
from ...domain.value_objects.percentage import Percentage
from ...domain.value_objects.ticker import Ticker

_MAX_WORKERS = 5


class YfinanceStockInfoRepository(StockInfoRepository):
    """
    Fetches financial data from Yahoo Finance via the yfinance library.
    Maps yfinance .info dict keys to StockInfo entity fields.

    - All conversions are None-safe (yfinance returns None frequently for JP stocks)
    - Currency is always JPY for TSE-listed stocks (.T suffix)
    - equity_ratio is derived from balance sheet (not in .info)
    - fetch_many uses ThreadPoolExecutor for parallel fetching
    """

    def fetch(self, ticker: Ticker) -> StockInfo:
        try:
            t = yf.Ticker(ticker.symbol)
            info = t.info or {}
        except Exception:
            return StockInfo(ticker=ticker)

        return self._map_info(ticker, info, t)

    def fetch_many(self, tickers: Sequence[Ticker]) -> Sequence[StockInfo]:
        results: list[StockInfo] = []
        with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
            future_to_ticker = {
                executor.submit(self.fetch, t): t for t in tickers
            }
            for future in as_completed(future_to_ticker):
                try:
                    results.append(future.result())
                except Exception:
                    ticker = future_to_ticker[future]
                    results.append(StockInfo(ticker=ticker))
        return results

    def _map_info(
        self, ticker: Ticker, info: dict[str, Any], yf_ticker: yf.Ticker
    ) -> StockInfo:
        return StockInfo(
            ticker=ticker,
            current_price=self._to_money(
                info.get("currentPrice") or info.get("regularMarketPrice")
            ),
            fifty_two_week_high=self._to_money(info.get("fiftyTwoWeekHigh")),
            fifty_two_week_low=self._to_money(info.get("fiftyTwoWeekLow")),
            trailing_pe=self._to_decimal(info.get("trailingPE")),
            forward_pe=self._to_decimal(info.get("forwardPE")),
            price_to_book=self._to_decimal(info.get("priceToBook")),
            enterprise_to_ebitda=self._to_decimal(info.get("enterpriseToEbitda")),
            trailing_eps=self._to_decimal(info.get("trailingEps")),
            book_value=self._to_decimal(info.get("bookValue")),
            dividend_yield=self._compute_dividend_yield(yf_ticker, info),
            return_on_equity=self._to_percentage(info.get("returnOnEquity")),
            payout_ratio=self._to_percentage(info.get("payoutRatio")),
            operating_margins=self._to_percentage(info.get("operatingMargins")),
            profit_margins=self._to_percentage(info.get("profitMargins")),
            current_ratio=self._to_decimal(info.get("currentRatio")),
            equity_ratio=self._compute_equity_ratio(yf_ticker),
            market_cap=info.get("marketCap"),
            beta=self._to_decimal(info.get("beta")),
            shares_outstanding=info.get("sharesOutstanding"),
        )

    @classmethod
    def _compute_dividend_yield(
        cls, yf_ticker: yf.Ticker, info: dict[str, Any]
    ) -> Optional[Percentage]:
        """
        配当利回り = 年換算配当 ÷ 現在株価

        .info の trailingAnnualDividendYield は株式分割の調整が不完全なため
        .dividends 履歴から直接計算する。

        分割対応:
        - 過去24ヶ月以内に株式分割がある場合、分割日以降の配当のみ使用し
          年換算する（分割前の未調整配当の混入を防ぐ）。
        - 分割がない場合は過去12ヶ月の合計をそのまま使用する。
        """
        try:
            dividends = yf_ticker.dividends
            if dividends is None or dividends.empty:
                return None
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            if not price:
                return None

            now = datetime.now(tz=timezone.utc)

            # 過去24ヶ月以内に分割があれば、分割日以降のみ使用して年換算
            splits = yf_ticker.splits
            cutoff_2y = now - timedelta(days=730)
            recent_splits = splits[splits.index >= cutoff_2y] if splits is not None and not splits.empty else None
            if recent_splits is not None and not recent_splits.empty:
                last_split_date = recent_splits.index[-1]
                post_split = dividends[dividends.index > last_split_date]

                if post_split.empty or post_split.sum() == 0:
                    # 分割直後で実績なし → .dividends は調整済みのため 通常の12ヶ月ウィンドウにフォールバック
                    annual_div = cls._trailing_12m_div(dividends, now)
                else:
                    days_since_split = (now - last_split_date).days
                    if days_since_split <= 0:
                        return None
                    annual_div = Decimal(str(post_split.sum())) * Decimal(365) / Decimal(days_since_split)
            else:
                annual_div = cls._trailing_12m_div(dividends, now)

            if annual_div is None:
                return None
            current_price = Decimal(str(price))
            return Percentage(annual_div / current_price)
        except Exception:
            return None

    @staticmethod
    def _trailing_12m_div(dividends: Any, now: datetime) -> Optional[Decimal]:
        cutoff_1y = now - timedelta(days=365)
        trailing = dividends[dividends.index >= cutoff_1y]
        if trailing.empty:
            return None
        return Decimal(str(trailing.sum()))

    @staticmethod
    def _compute_equity_ratio(yf_ticker: yf.Ticker) -> Optional[Percentage]:
        """
        自己資本比率 = 純資産 / 総資産
        Derived from balance_sheet DataFrame; most recent quarter is column 0.
        """
        try:
            bs = yf_ticker.balance_sheet
            if bs is None or bs.empty:
                return None
            equity_keys = ["Stockholders Equity", "Total Stockholder Equity"]
            asset_keys = ["Total Assets"]
            equity = None
            for key in equity_keys:
                if key in bs.index:
                    equity = bs.loc[key].iloc[0]
                    break
            total_assets = None
            for key in asset_keys:
                if key in bs.index:
                    total_assets = bs.loc[key].iloc[0]
                    break
            if equity is not None and total_assets and total_assets != 0:
                ratio = Decimal(str(equity)) / Decimal(str(total_assets))
                return Percentage(ratio)
        except Exception:
            pass
        return None

    @staticmethod
    def _to_decimal(value: Any) -> Optional[Decimal]:
        if value is None:
            return None
        try:
            d = Decimal(str(value))
            # yfinance sometimes returns NaN as a float
            if d.is_nan() or d.is_infinite():
                return None
            return d
        except Exception:
            return None

    @classmethod
    def _to_money(cls, value: Any) -> Optional[Money]:
        d = cls._to_decimal(value)
        return Money(d, Currency.JPY) if d is not None else None

    @classmethod
    def _to_percentage(cls, value: Any) -> Optional[Percentage]:
        d = cls._to_decimal(value)
        return Percentage(d) if d is not None else None
