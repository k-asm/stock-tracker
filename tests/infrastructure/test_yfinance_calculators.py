from datetime import UTC, datetime

import pandas as pd
import pytest

from stock_tracker.infrastructure.yfinance.yfinance_calculators import (
    compute_dividend_yield,
    compute_equity_ratio,
)


def _make_dividends(entries: list[tuple[str, float]]) -> pd.Series:
    index = pd.to_datetime([e[0] for e in entries], utc=True)
    values = [e[1] for e in entries]
    return pd.Series(values, index=index, name="Dividends", dtype=float)


def _make_splits(entries: list[tuple[str, float]]) -> pd.Series:
    index = pd.to_datetime([e[0] for e in entries], utc=True)
    values = [e[1] for e in entries]
    return pd.Series(values, index=index, name="Stock Splits", dtype=float)


def _empty_splits() -> pd.Series:
    return pd.Series([], dtype=float, name="Stock Splits")


NOW = datetime(2026, 4, 5, tzinfo=UTC)


class TestComputeDividendYield:
    def test_no_splits_trailing_12m(self):
        """分割なし: 過去12ヶ月の合計を使う"""
        dividends = _make_dividends(
            [
                ("2025-04-10", 20.0),  # 12ヶ月以内
                ("2025-09-29", 20.0),  # 12ヶ月以内
            ]
        )
        result = compute_dividend_yield(
            dividends, _empty_splits(), price=2000.0, now=NOW
        )
        assert result is not None
        assert float(result.value) == pytest.approx(40 / 2000, rel=1e-6)

    def test_no_splits_excludes_older_than_12m(self):
        """12ヶ月より古い配当は含まれない"""
        dividends = _make_dividends(
            [
                ("2024-09-28", 20.0),  # 12ヶ月超 → 除外
                ("2025-09-29", 20.0),  # 12ヶ月以内
            ]
        )
        result = compute_dividend_yield(
            dividends, _empty_splits(), price=2000.0, now=NOW
        )
        assert result is not None
        assert float(result.value) == pytest.approx(20 / 2000, rel=1e-6)

    def test_split_post_data_sufficient_annualizes(self):
        """分割後180日以上: 分割後配当を年換算する"""
        split_date = "2025-09-01"
        # days_since_split = 2026-04-05 - 2025-09-01 = 216日
        dividends = _make_dividends(
            [
                ("2025-03-28", 50.0),  # 分割前
                ("2025-11-28", 12.0),  # 分割後
                ("2026-03-30", 12.0),  # 分割後
            ]
        )
        splits = _make_splits([(split_date, 4.0)])
        result = compute_dividend_yield(dividends, splits, price=600.0, now=NOW)
        assert result is not None
        days = (NOW - pd.Timestamp(split_date, tz=UTC)).days
        expected = 24 * 365 / days / 600
        assert float(result.value) == pytest.approx(expected, rel=1e-4)

    def test_split_post_data_insufficient_falls_back_to_trailing_12m(self):
        """
        分割後180日未満: 年換算誤差が大きいため trailing 12m にフォールバック
        (8001.T のケース: 97日で1回分を年換算すると約2倍になる問題)
        """
        split_date = "2025-12-29"
        dividends = _make_dividends(
            [
                ("2025-09-29", 20.0),  # 分割前（yfinance 調整済み）
                ("2026-03-30", 22.0),  # 分割後
            ]
        )
        splits = _make_splits([(split_date, 5.0)])
        result = compute_dividend_yield(dividends, splits, price=2042.0, now=NOW)
        assert result is not None
        # trailing 12m = 20 + 22 = 42
        assert float(result.value) == pytest.approx(42 / 2042, rel=1e-4)

    def test_split_date_entry_excluded_in_fallback(self):
        """
        分割日当日のエントリ（未調整の疑い）は trailing 12m から除外される
        (5401.T のケース: 分割日と同日の 60円エントリが未調整)
        """
        split_date_short = "2026-01-01"
        dividends = _make_dividends(
            [
                ("2025-09-29", 16.0),  # 分割前（調整済み）
                ("2026-01-01", 60.0),  # 分割日当日（未調整の疑い）→ 除外される
                ("2026-03-30", 12.0),  # 分割後
            ]
        )
        splits = _make_splits([(split_date_short, 5.0)])
        result = compute_dividend_yield(dividends, splits, price=600.0, now=NOW)
        assert result is not None
        # 2026-01-01 は除外, trailing 12m = 2025-09-29(16) + 2026-03-30(12) = 28
        assert float(result.value) == pytest.approx(28 / 600, rel=1e-4)

    def test_no_post_split_dividends_falls_back_to_trailing_12m(self):
        """分割直後で実績なし: trailing 12m にフォールバック"""
        split_date = "2026-03-01"
        dividends = _make_dividends(
            [
                ("2025-09-29", 20.0),
                ("2025-03-28", 20.0),
            ]
        )
        splits = _make_splits([(split_date, 3.0)])
        result = compute_dividend_yield(dividends, splits, price=1000.0, now=NOW)
        assert result is not None
        assert float(result.value) == pytest.approx(20 / 1000, rel=1e-4)

    def test_empty_dividends_returns_none(self):
        dividends = _make_dividends([])
        result = compute_dividend_yield(
            dividends, _empty_splits(), price=1000.0, now=NOW
        )
        assert result is None

    def test_zero_price_returns_none(self):
        dividends = _make_dividends([("2025-09-29", 20.0)])
        result = compute_dividend_yield(dividends, _empty_splits(), price=0.0, now=NOW)
        assert result is None


class TestComputeEquityRatio:
    def _make_bs(self, equity: float, total_assets: float) -> pd.DataFrame:
        return pd.DataFrame(
            {pd.Timestamp("2025-12-31"): [equity, total_assets]},
            index=["Stockholders Equity", "Total Assets"],
        )

    def test_basic(self):
        bs = self._make_bs(equity=500_000, total_assets=1_000_000)
        result = compute_equity_ratio(bs)
        assert result is not None
        assert float(result.value) == pytest.approx(0.5, rel=1e-6)

    def test_none_balance_sheet_returns_none(self):
        assert compute_equity_ratio(None) is None

    def test_empty_balance_sheet_returns_none(self):
        assert compute_equity_ratio(pd.DataFrame()) is None

    def test_zero_total_assets_returns_none(self):
        bs = self._make_bs(equity=100, total_assets=0)
        assert compute_equity_ratio(bs) is None
