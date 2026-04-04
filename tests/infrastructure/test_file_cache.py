import json
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from stock_tracker.domain.entities.stock_info import StockInfo
from stock_tracker.domain.value_objects.money import Currency, Money
from stock_tracker.domain.value_objects.percentage import Percentage
from stock_tracker.domain.value_objects.ticker import Ticker
from stock_tracker.infrastructure.cache.file_cache_stock_info_repository import (
    FileCacheStockInfoRepository,
)


def _ticker(code: str) -> Ticker:
    return Ticker.from_sbi_code(code)


def _make_stock_info(code: str, price: int = 1000) -> StockInfo:
    return StockInfo(
        ticker=_ticker(code),
        current_price=Money(Decimal(price), Currency.JPY),
        trailing_pe=Decimal("15.5"),
        dividend_yield=Percentage(Decimal("0.025")),
    )


@pytest.fixture()
def cache_dir(tmp_path: Path) -> Path:
    return tmp_path / "cache"


@pytest.fixture()
def inner_repo():
    return MagicMock()


def make_repo(
    inner_repo,
    cache_dir: Path,
    ttl_minutes: int = 15,
) -> FileCacheStockInfoRepository:
    return FileCacheStockInfoRepository(
        inner_repo, cache_dir=cache_dir, ttl_minutes=ttl_minutes
    )


class TestFetch:
    def test_cache_miss_calls_inner_and_writes_cache(self, inner_repo, cache_dir):
        info = _make_stock_info("7203")
        inner_repo.fetch.return_value = info
        repo = make_repo(inner_repo, cache_dir)

        result = repo.fetch(_ticker("7203"))

        inner_repo.fetch.assert_called_once_with(_ticker("7203"))
        assert result.ticker.symbol == "7203.T"
        cache_file = cache_dir / "7203_T.json"
        assert cache_file.exists()

    def test_cache_hit_does_not_call_inner(self, inner_repo, cache_dir):
        info = _make_stock_info("7203")
        inner_repo.fetch.return_value = info
        repo = make_repo(inner_repo, cache_dir)

        repo.fetch(_ticker("7203"))  # populates cache
        inner_repo.reset_mock()
        result = repo.fetch(_ticker("7203"))  # should hit cache

        inner_repo.fetch.assert_not_called()
        assert result.current_price.amount == Decimal("1000")

    def test_expired_cache_calls_inner_again(self, inner_repo, cache_dir):
        info = _make_stock_info("7203")
        inner_repo.fetch.return_value = info
        repo = make_repo(inner_repo, cache_dir, ttl_minutes=1)

        # Write a cache file with an old timestamp
        cache_file = cache_dir / "7203_T.json"
        old_time = (datetime.now() - timedelta(minutes=5)).isoformat()
        data = FileCacheStockInfoRepository._serialize(info)
        data["_cached_at"] = old_time
        cache_file.write_text(json.dumps(data, default=str), encoding="utf-8")

        repo.fetch(_ticker("7203"))

        inner_repo.fetch.assert_called_once()

    def test_corrupt_cache_file_falls_through_to_inner(self, inner_repo, cache_dir):
        info = _make_stock_info("7203")
        inner_repo.fetch.return_value = info
        repo = make_repo(inner_repo, cache_dir)

        (cache_dir / "7203_T.json").write_text("not valid json", encoding="utf-8")

        result = repo.fetch(_ticker("7203"))

        inner_repo.fetch.assert_called_once()
        assert result.ticker.symbol == "7203.T"

    def test_cache_preserves_all_fields(self, inner_repo, cache_dir):
        info = StockInfo(
            ticker=_ticker("7203"),
            current_price=Money(Decimal("2500"), Currency.JPY),
            fifty_two_week_high=Money(Decimal("3000"), Currency.JPY),
            fifty_two_week_low=Money(Decimal("2000"), Currency.JPY),
            trailing_pe=Decimal("12.3"),
            price_to_book=Decimal("1.5"),
            dividend_yield=Percentage(Decimal("0.03")),
            return_on_equity=Percentage(Decimal("0.15")),
            market_cap=5_000_000_000,
            beta=Decimal("0.9"),
        )
        inner_repo.fetch.return_value = info
        repo = make_repo(inner_repo, cache_dir)

        repo.fetch(_ticker("7203"))
        inner_repo.reset_mock()
        result = repo.fetch(_ticker("7203"))

        assert result.current_price.amount == Decimal("2500")
        assert result.fifty_two_week_high.amount == Decimal("3000")
        assert result.fifty_two_week_low.amount == Decimal("2000")
        assert result.trailing_pe == Decimal("12.3")
        assert result.price_to_book == Decimal("1.5")
        assert result.dividend_yield.value == Decimal("0.03")
        assert result.return_on_equity.value == Decimal("0.15")
        assert result.market_cap == 5_000_000_000
        assert result.beta == Decimal("0.9")


class TestFetchMany:
    def test_all_cache_miss_calls_inner(self, inner_repo, cache_dir):
        tickers = [_ticker("7203"), _ticker("9984")]
        infos = [_make_stock_info("7203"), _make_stock_info("9984")]
        inner_repo.fetch_many.return_value = infos
        repo = make_repo(inner_repo, cache_dir)

        results = repo.fetch_many(tickers)

        inner_repo.fetch_many.assert_called_once_with(tickers)
        assert len(results) == 2

    def test_all_cache_hit_does_not_call_inner(self, inner_repo, cache_dir):
        tickers = [_ticker("7203"), _ticker("9984")]
        infos = [_make_stock_info("7203"), _make_stock_info("9984")]
        inner_repo.fetch_many.return_value = infos
        repo = make_repo(inner_repo, cache_dir)

        repo.fetch_many(tickers)  # populate cache
        inner_repo.reset_mock()
        results = repo.fetch_many(tickers)

        inner_repo.fetch_many.assert_not_called()
        assert len(results) == 2

    def test_partial_cache_hit_only_fetches_uncached(self, inner_repo, cache_dir):
        # Pre-cache 7203
        cached_info = _make_stock_info("7203", price=2500)
        inner_repo.fetch.return_value = cached_info
        repo = make_repo(inner_repo, cache_dir)
        repo.fetch(_ticker("7203"))
        inner_repo.reset_mock()

        # Now fetch_many for 7203 (cached) + 9984 (not cached)
        uncached_info = _make_stock_info("9984", price=7200)
        inner_repo.fetch_many.return_value = [uncached_info]

        results = repo.fetch_many([_ticker("7203"), _ticker("9984")])

        inner_repo.fetch_many.assert_called_once_with([_ticker("9984")])
        assert len(results) == 2
        prices = {r.ticker.symbol: r.current_price.amount for r in results}
        assert prices["7203.T"] == Decimal("2500")
        assert prices["9984.T"] == Decimal("7200")

    def test_preserves_input_order(self, inner_repo, cache_dir):
        tickers = [_ticker("9984"), _ticker("7203"), _ticker("6758")]
        infos = [
            _make_stock_info("9984", price=7200),
            _make_stock_info("7203", price=2500),
            _make_stock_info("6758", price=12000),
        ]
        inner_repo.fetch_many.return_value = infos
        repo = make_repo(inner_repo, cache_dir)

        results = repo.fetch_many(tickers)

        symbols = [r.ticker.symbol for r in results]
        assert symbols == ["9984.T", "7203.T", "6758.T"]
