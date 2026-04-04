from decimal import Decimal
from pathlib import Path

import pytest

from stock_tracker.infrastructure.csv.sbi_csv_reader import SbiCsvHoldingsRepository

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_sbi.csv"
FIXTURE_FORMAT_B_PATH = Path(__file__).parent / "fixtures" / "sample_sbi_format_b.csv"


# --- Format A ---


def test_load_returns_three_holdings():
    repo = SbiCsvHoldingsRepository()
    holdings = repo.load(str(FIXTURE_PATH))
    assert len(holdings) == 3


def test_first_holding_fields():
    repo = SbiCsvHoldingsRepository()
    holdings = repo.load(str(FIXTURE_PATH))
    toyota = next(h for h in holdings if h.ticker.symbol == "7203.T")
    assert toyota.name == "トヨタ自動車"
    assert toyota.shares == 100
    assert toyota.average_cost.amount == 2000


def test_file_not_found():
    repo = SbiCsvHoldingsRepository()
    with pytest.raises(FileNotFoundError):
        repo.load("/nonexistent/path.csv")


# --- Format B ---


def test_format_b_load_returns_two_holdings():
    repo = SbiCsvHoldingsRepository()
    holdings = repo.load(str(FIXTURE_FORMAT_B_PATH))
    assert len(holdings) == 2


def test_format_b_holding_fields():
    repo = SbiCsvHoldingsRepository()
    holdings = repo.load(str(FIXTURE_FORMAT_B_PATH))
    toyota = next(h for h in holdings if h.ticker.symbol == "7203.T")
    assert toyota.name == "トヨタ自動車"
    assert toyota.shares == Decimal("100")
    assert toyota.average_cost.amount == Decimal("2000")


def test_format_b_ticker_symbols():
    repo = SbiCsvHoldingsRepository()
    holdings = repo.load(str(FIXTURE_FORMAT_B_PATH))
    symbols = {h.ticker.symbol for h in holdings}
    assert symbols == {"7203.T", "9984.T"}


# --- Header detection ---


def test_no_valid_header_raises(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("col1,col2\n1,2\n", encoding="utf-8")
    repo = SbiCsvHoldingsRepository()
    with pytest.raises(ValueError, match="Could not find header row"):
        repo.load(str(bad_csv))


# --- _parse_decimal edge cases ---


def test_parse_decimal_handles_commas(tmp_path):
    """Amounts like "1,234" should parse to Decimal("1234")."""
    csv_content = (
        '銘柄コード,銘柄,保有数量,平均取得単価\n1234,テスト株式会社,"1,000","2,500"\n'
    )
    f = tmp_path / "test.csv"
    f.write_text(csv_content, encoding="utf-8")
    repo = SbiCsvHoldingsRepository()
    holdings = repo.load(str(f))
    assert len(holdings) == 1
    assert holdings[0].shares == Decimal("1000")
    assert holdings[0].average_cost.amount == Decimal("2500")


def test_parse_decimal_skips_dash_rows(tmp_path):
    """Rows where amount is '-' or '―' should be skipped."""
    csv_content = (
        "銘柄コード,銘柄,保有数量,平均取得単価\n"
        "1234,有効株式会社,100,1000\n"
        "5678,無効株式会社,-,1000\n"
    )
    f = tmp_path / "test.csv"
    f.write_text(csv_content, encoding="utf-8")
    repo = SbiCsvHoldingsRepository()
    holdings = repo.load(str(f))
    # Only the valid row
    assert len(holdings) == 1
    assert holdings[0].ticker.symbol == "1234.T"


def test_parse_decimal_skips_zero_shares(tmp_path):
    """Rows with 0 shares should be skipped."""
    csv_content = "銘柄コード,銘柄,保有数量,平均取得単価\n1234,ゼロ株式会社,0,1000\n"
    f = tmp_path / "test.csv"
    f.write_text(csv_content, encoding="utf-8")
    repo = SbiCsvHoldingsRepository()
    holdings = repo.load(str(f))
    assert len(holdings) == 0


def test_parse_decimal_skips_non_digit_code(tmp_path):
    """Rows where code is not all digits (e.g. summary row) should be skipped."""
    csv_content = (
        "銘柄コード,銘柄,保有数量,平均取得単価\n"
        "1234,有効株式会社,100,1000\n"
        "合計,--,200,--\n"
    )
    f = tmp_path / "test.csv"
    f.write_text(csv_content, encoding="utf-8")
    repo = SbiCsvHoldingsRepository()
    holdings = repo.load(str(f))
    assert len(holdings) == 1
