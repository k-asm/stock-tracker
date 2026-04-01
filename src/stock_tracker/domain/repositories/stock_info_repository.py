from abc import ABC, abstractmethod
from typing import Sequence

from ..entities.stock_info import StockInfo
from ..value_objects.ticker import Ticker


class StockInfoRepository(ABC):
    """
    Port for fetching live financial data.
    Implementations: YfinanceStockInfoRepository, FileCacheStockInfoRepository.
    """

    @abstractmethod
    def fetch(self, ticker: Ticker) -> StockInfo:
        """
        Fetch financial metrics for a single ticker.
        Returns StockInfo with None fields for unavailable data.
        Never raises for missing data — only raises for network/IO errors.
        """
        ...

    def fetch_many(self, tickers: Sequence[Ticker]) -> Sequence[StockInfo]:
        """
        Default: fetch sequentially. Override for batching or concurrency.
        """
        return [self.fetch(t) for t in tickers]
