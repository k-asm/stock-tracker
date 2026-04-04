import csv
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional, Sequence

from ...domain.entities.holding import Holding
from ...domain.repositories.holdings_repository import HoldingsRepository
from ...domain.value_objects.money import Currency, Money
from ...domain.value_objects.ticker import Ticker

# SBI Securities CSV column headers — two known export formats:
#
# Format A (保有証券一覧): "銘柄コード", "銘柄", "保有数量", "平均取得単価"
# Format B (ポートフォリオ一覧): "銘柄（コード）" contains "XXXX 銘柄名",
#                               "数量", "取得単価"
#
# The parser auto-detects which format is in use from the header row.

_HEADER_FORMAT_A = "銘柄コード"
_HEADER_FORMAT_B = "銘柄（コード）"

# Format A column names
_A_CODE = "銘柄コード"
_A_NAME = "銘柄"
_A_SHARES = "保有数量"
_A_AVG_COST = "平均取得単価"

# Format B column names
_B_CODE_NAME = "銘柄（コード）"   # "XXXX 銘柄名" combined
_B_SHARES = "数量"
_B_AVG_COST = "取得単価"

# Regex to extract 4-digit stock code from "XXXX 銘柄名"
_CODE_RE = re.compile(r"^(\d{4})\s+(.+)$")

# Encodings to try in order
_ENCODINGS = ["cp932", "utf-8-sig", "utf-8"]


class SbiCsvHoldingsRepository(HoldingsRepository):
    """
    Reads SBI Securities portfolio export CSV.

    Supports two export formats from SBI Securities:
    - Format A: 保有証券一覧 (銘柄コード / 銘柄 / 保有数量 / 平均取得単価)
    - Format B: ポートフォリオ一覧 (銘柄（コード） / 数量 / 取得単価)

    Encoding: CP932 (Shift-JIS), with UTF-8 fallback.
    """

    def load(self, source: str) -> Sequence[Holding]:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"SBI CSV not found: {source}")

        raw = self._read_file(path)
        lines = raw.splitlines()

        header_idx, fmt = self._find_header_row(lines)
        if header_idx is None:
            raise ValueError(
                f"Could not find header row in {source}. "
                "Make sure this is a valid SBI Securities portfolio CSV export."
            )

        data_text = "\n".join(lines[header_idx:])
        reader = csv.DictReader(data_text.splitlines())

        holdings = []
        for row in reader:
            holding = (
                self._parse_row_format_a(row)
                if fmt == "A"
                else self._parse_row_format_b(row)
            )
            if holding is not None:
                holdings.append(holding)
        return holdings

    def _read_file(self, path: Path) -> str:
        for encoding in _ENCODINGS:
            try:
                return path.read_text(encoding=encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        raise ValueError(
            f"Could not decode {path} with any of {_ENCODINGS}. "
            "Please check the file encoding."
        )

    def _find_header_row(
        self, lines: list[str]
    ) -> tuple[Optional[int], Optional[str]]:
        for i, line in enumerate(lines):
            # Check Format B before Format A: "銘柄コード" is a substring of "銘柄（コード）"
            if _HEADER_FORMAT_B in line:
                return i, "B"
            if _HEADER_FORMAT_A in line:
                return i, "A"
        return None, None

    def _parse_row_format_a(self, row: dict) -> Optional[Holding]:
        code = row.get(_A_CODE, "").strip()
        if not code or not code.isdigit():
            return None
        name = row.get(_A_NAME, "").strip()
        shares = self._parse_decimal(row.get(_A_SHARES, ""))
        avg_cost = self._parse_decimal(row.get(_A_AVG_COST, ""))
        return self._build_holding(code, name, shares, avg_cost)

    def _parse_row_format_b(self, row: dict) -> Optional[Holding]:
        code_name = row.get(_B_CODE_NAME, "").strip()
        m = _CODE_RE.match(code_name)
        if not m:
            return None
        code = m.group(1)
        name = m.group(2).strip()
        shares = self._parse_decimal(row.get(_B_SHARES, ""))
        avg_cost = self._parse_decimal(row.get(_B_AVG_COST, ""))
        return self._build_holding(code, name, shares, avg_cost)

    @staticmethod
    def _build_holding(
        code: str,
        name: str,
        shares: Optional[Decimal],
        avg_cost: Optional[Decimal],
    ) -> Optional[Holding]:
        if shares is None or avg_cost is None or shares == 0:
            return None
        return Holding(
            ticker=Ticker.from_sbi_code(code),
            name=name,
            shares=shares,
            average_cost=Money(avg_cost, Currency.JPY),
        )

    @staticmethod
    def _parse_decimal(value: str) -> Optional[Decimal]:
        cleaned = (
            value.strip()
            .replace(",", "")
            .replace("円", "")
            .replace("株", "")
            .replace("口", "")
        )
        if not cleaned or cleaned in ("-", "―", "－"):
            return None
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None
