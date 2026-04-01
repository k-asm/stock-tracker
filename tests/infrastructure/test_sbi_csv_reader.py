from pathlib import Path

import pytest

from stock_tracker.infrastructure.csv.sbi_csv_reader import SbiCsvHoldingsRepository

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_sbi.csv"


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
