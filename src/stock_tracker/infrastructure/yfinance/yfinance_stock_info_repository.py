from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import yfinance as yf

from ...domain.entities.stock_info import StockInfo
from ...domain.repositories.stock_info_repository import StockInfoRepository
from ...domain.value_objects.ticker import Ticker
from .yfinance_calculators import compute_dividend_yield, compute_equity_ratio
from .yfinance_converters import to_decimal, to_money, to_percentage

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
            future_to_ticker = {executor.submit(self.fetch, t): t for t in tickers}
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
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        return StockInfo(
            ticker=ticker,
            current_price=to_money(price),
            fifty_two_week_high=to_money(info.get("fiftyTwoWeekHigh")),
            fifty_two_week_low=to_money(info.get("fiftyTwoWeekLow")),
            trailing_pe=to_decimal(info.get("trailingPE")),
            forward_pe=to_decimal(info.get("forwardPE")),
            price_to_book=to_decimal(info.get("priceToBook")),
            enterprise_to_ebitda=to_decimal(info.get("enterpriseToEbitda")),
            trailing_eps=to_decimal(info.get("trailingEps")),
            book_value=to_decimal(info.get("bookValue")),
            dividend_yield=compute_dividend_yield(
                yf_ticker.dividends, yf_ticker.splits, price
            ),
            return_on_equity=to_percentage(info.get("returnOnEquity")),
            payout_ratio=to_percentage(info.get("payoutRatio")),
            operating_margins=to_percentage(info.get("operatingMargins")),
            profit_margins=to_percentage(info.get("profitMargins")),
            current_ratio=to_decimal(info.get("currentRatio")),
            equity_ratio=compute_equity_ratio(yf_ticker.balance_sheet),
            market_cap=info.get("marketCap"),
            beta=to_decimal(info.get("beta")),
            shares_outstanding=info.get("sharesOutstanding"),
        )
