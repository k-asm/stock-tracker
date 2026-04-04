from dataclasses import dataclass


@dataclass(frozen=True)
class Ticker:
    """
    Yahoo Finance ticker symbol for Japanese stocks.
    SBI CSV provides a 4-digit code; this VO appends ".T" for TSE.
    Example: "7203" → Ticker("7203.T")
    """

    symbol: str  # e.g. "7203.T"

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("Ticker symbol cannot be empty")

    @classmethod
    def from_sbi_code(cls, code: str) -> Ticker:
        """Converts SBI 4-digit code to Yahoo Finance symbol."""
        return cls(f"{code.strip()}.T")
