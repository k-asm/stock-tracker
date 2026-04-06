from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pandas as pd

from ...domain.value_objects.percentage import Percentage


def compute_dividend_yield(
    dividends: pd.Series,
    splits: pd.Series,
    price: float,
    now: datetime | None = None,
) -> Percentage | None:
    """
    配当利回り = 年換算配当 ÷ 現在株価

    .info の trailingAnnualDividendYield は株式分割の調整が不完全なため
    .dividends 履歴から直接計算する。

    分割対応:
    - 過去24ヶ月以内に株式分割がある場合:
        - 分割後データが180日以上 → 分割後配当を年換算
        - 分割後データが180日未満 → 年換算誤差が大きいため
          分割日当日エントリを除いた trailing 12m にフォールバック
        - 分割後実績なし（分割直後）→ trailing 12m にフォールバック
    - 分割なし → 過去12ヶ月の合計
    """
    try:
        if dividends is None or dividends.empty:
            return None
        if not price:
            return None

        if now is None:
            now = datetime.now(tz=UTC)

        cutoff_2y = now - timedelta(days=730)
        recent_splits = (
            splits[splits.index >= cutoff_2y]
            if splits is not None and not splits.empty
            else None
        )

        if recent_splits is not None and not recent_splits.empty:
            last_split_date = recent_splits.index[-1]
            post_split = dividends[dividends.index > last_split_date]

            post_split_sum = post_split.sum()
            if post_split.empty or post_split_sum == 0:
                # 分割直後で実績なし → .dividends は調整済みのため 12m にフォールバック
                annual_div = _trailing_12m_div(dividends, now)
            else:
                days_since_split = (now - last_split_date).days
                if days_since_split <= 0:
                    return None
                if days_since_split < 180:
                    # 分割後データが1支払期間未満（半期払いなら約180日）のため
                    # 年換算すると誤差が大きい（例: 97日で1回分を年換算→約2倍）。
                    # .dividends は分割調整済みのため trailing 12m を使う。
                    # 分割日当日のエントリは未調整の疑いがあるため除外する。
                    divs_excl_split_date = dividends[
                        ~dividends.index.isin(recent_splits.index)
                    ]
                    annual_div = _trailing_12m_div(divs_excl_split_date, now)
                else:
                    annual_div = (
                        Decimal(str(post_split_sum))
                        * Decimal(365)
                        / Decimal(days_since_split)
                    )
        else:
            annual_div = _trailing_12m_div(dividends, now)

        if annual_div is None:
            return None
        return Percentage(annual_div / Decimal(str(price)))
    except Exception:
        return None


def compute_equity_ratio(balance_sheet: Any) -> Percentage | None:
    """
    自己資本比率 = 純資産 / 総資産
    balance_sheet は yf.Ticker.balance_sheet（DataFrame）を想定。
    最新四半期は列 0。
    """
    try:
        if balance_sheet is None or balance_sheet.empty:
            return None
        equity = _get_first_bs_value(
            balance_sheet, ["Stockholders Equity", "Total Stockholder Equity"]
        )
        total_assets = _get_first_bs_value(balance_sheet, ["Total Assets"])
        if equity is not None and total_assets and total_assets != 0:
            ratio = Decimal(str(equity)) / Decimal(str(total_assets))
            return Percentage(ratio)
    except Exception:
        pass
    return None


def _get_first_bs_value(balance_sheet: Any, keys: list[str]) -> Any:
    for key in keys:
        if key in balance_sheet.index:
            return balance_sheet.loc[key].iloc[0]
    return None


def _trailing_12m_div(dividends: pd.Series, now: datetime) -> Decimal | None:
    cutoff_1y = now - timedelta(days=365)
    trailing = dividends[dividends.index >= cutoff_1y]
    if trailing.empty:
        return None
    return Decimal(str(trailing.sum()))
