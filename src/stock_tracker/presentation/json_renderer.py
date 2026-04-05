import json
import sys
from collections.abc import Sequence
from decimal import Decimal

from rich.console import Console

from ..application.dtos.portfolio_row_dto import PortfolioRowDTO


def _json_default(obj: object) -> object:
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class JsonRenderer:
    """
    Renders PortfolioRowDTOs as JSON to stdout.
    Status messages are written to stderr to keep stdout clean for piping.
    Decimal values are serialized as strings to preserve precision.
    Only depends on PortfolioRowDTO — no domain types cross this boundary.
    """

    def __init__(self) -> None:
        self._console = Console(stderr=True)

    def status(self, message: str):
        return self._console.status(message)

    def render(self, rows: Sequence[PortfolioRowDTO]) -> None:
        data = [vars(row) for row in rows]
        sys.stdout.write(
            json.dumps(data, ensure_ascii=False, indent=2, default=_json_default)
        )
        sys.stdout.write("\n")
