import json
from collections.abc import Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from ...domain.entities.stock_info import StockInfo
from ...domain.repositories.stock_info_repository import StockInfoRepository
from ...domain.value_objects.money import Currency, Money
from ...domain.value_objects.percentage import Percentage
from ...domain.value_objects.ticker import Ticker

DEFAULT_TTL_MINUTES = 15


class FileCacheStockInfoRepository(StockInfoRepository):
    """
    Decorator pattern: wraps another StockInfoRepository with file-based JSON caching.
    Cache files stored in ~/.cache/stock-tracker/<ticker>.json
    Skips cache if TTL expired.

    Usage:
        inner = YfinanceStockInfoRepository()
        cached = FileCacheStockInfoRepository(inner, ttl_minutes=15)
    """

    def __init__(
        self,
        inner: StockInfoRepository,
        cache_dir: Path | None = None,
        ttl_minutes: int = DEFAULT_TTL_MINUTES,
    ) -> None:
        self._inner = inner
        self._cache_dir = cache_dir or Path.home() / ".cache" / "stock-tracker"
        self._ttl = timedelta(minutes=ttl_minutes)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, ticker: Ticker) -> StockInfo:
        cache_path = self._cache_path(ticker)
        cached = self._load_cache(cache_path, ticker)
        if cached is not None:
            return cached
        result = self._inner.fetch(ticker)
        self._write_cache(cache_path, result)
        return result

    def fetch_many(self, tickers: Sequence[Ticker]) -> Sequence[StockInfo]:
        # Check cache first; only fetch uncached tickers from inner repo
        cached_results: dict[str, StockInfo] = {}
        uncached: list[Ticker] = []

        for ticker in tickers:
            cache_path = self._cache_path(ticker)
            cached = self._load_cache(cache_path, ticker)
            if cached is not None:
                cached_results[ticker.symbol] = cached
            else:
                uncached.append(ticker)

        if uncached:
            fetched = self._inner.fetch_many(uncached)
            for info in fetched:
                self._write_cache(self._cache_path(info.ticker), info)
                cached_results[info.ticker.symbol] = info

        return [cached_results[t.symbol] for t in tickers if t.symbol in cached_results]

    def _cache_path(self, ticker: Ticker) -> Path:
        safe_name = ticker.symbol.replace(".", "_")
        return self._cache_dir / f"{safe_name}.json"

    def _load_cache(self, path: Path, ticker: Ticker) -> StockInfo | None:
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cached_at = datetime.fromisoformat(data["_cached_at"])
            if datetime.now() - cached_at > self._ttl:
                return None
            return self._deserialize(data, ticker)
        except Exception:
            return None

    def _write_cache(self, path: Path, info: StockInfo) -> None:
        try:
            data = self._serialize(info)
            data["_cached_at"] = datetime.now().isoformat()
            path.write_text(
                json.dumps(data, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
        except Exception:
            pass  # Cache write failure is non-fatal

    @staticmethod
    def _serialize(info: StockInfo) -> dict[str, Any]:
        def d(v: Decimal | None) -> str | None:
            return str(v) if v is not None else None

        def pct(v: Percentage | None) -> str | None:
            return str(v.value) if v is not None else None

        def money(v: Money | None) -> str | None:
            return str(v.amount) if v is not None else None

        return {
            "ticker": info.ticker.symbol,
            "current_price": money(info.current_price),
            "fifty_two_week_high": money(info.fifty_two_week_high),
            "fifty_two_week_low": money(info.fifty_two_week_low),
            "trailing_pe": d(info.trailing_pe),
            "forward_pe": d(info.forward_pe),
            "price_to_book": d(info.price_to_book),
            "enterprise_to_ebitda": d(info.enterprise_to_ebitda),
            "trailing_eps": d(info.trailing_eps),
            "book_value": d(info.book_value),
            "dividend_yield": pct(info.dividend_yield),
            "return_on_equity": pct(info.return_on_equity),
            "payout_ratio": pct(info.payout_ratio),
            "operating_margins": pct(info.operating_margins),
            "profit_margins": pct(info.profit_margins),
            "current_ratio": d(info.current_ratio),
            "equity_ratio": pct(info.equity_ratio),
            "market_cap": info.market_cap,
            "beta": d(info.beta),
            "shares_outstanding": info.shares_outstanding,
        }

    @staticmethod
    def _deserialize(data: dict[str, Any], ticker: Ticker) -> StockInfo:
        def d(v: str | None) -> Decimal | None:
            return Decimal(v) if v is not None else None

        def pct(v: str | None) -> Percentage | None:
            return Percentage(Decimal(v)) if v is not None else None

        def money(v: str | None) -> Money | None:
            return Money(Decimal(v), Currency.JPY) if v is not None else None

        return StockInfo(
            ticker=ticker,
            current_price=money(data.get("current_price")),
            fifty_two_week_high=money(data.get("fifty_two_week_high")),
            fifty_two_week_low=money(data.get("fifty_two_week_low")),
            trailing_pe=d(data.get("trailing_pe")),
            forward_pe=d(data.get("forward_pe")),
            price_to_book=d(data.get("price_to_book")),
            enterprise_to_ebitda=d(data.get("enterprise_to_ebitda")),
            trailing_eps=d(data.get("trailing_eps")),
            book_value=d(data.get("book_value")),
            dividend_yield=pct(data.get("dividend_yield")),
            return_on_equity=pct(data.get("return_on_equity")),
            payout_ratio=pct(data.get("payout_ratio")),
            operating_margins=pct(data.get("operating_margins")),
            profit_margins=pct(data.get("profit_margins")),
            current_ratio=d(data.get("current_ratio")),
            equity_ratio=pct(data.get("equity_ratio")),
            market_cap=data.get("market_cap"),
            beta=d(data.get("beta")),
            shares_outstanding=data.get("shares_outstanding"),
        )
