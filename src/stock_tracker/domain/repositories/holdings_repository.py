from abc import ABC, abstractmethod
from collections.abc import Sequence

from ..entities.holding import Holding


class HoldingsRepository(ABC):
    """
    Port: reads portfolio holdings from some persistent source.
    Domain layer defines the interface; infrastructure provides the adapter.
    """

    @abstractmethod
    def load(self, source: str) -> Sequence[Holding]:
        """
        Load all holdings from the given source identifier.
        For CSV implementations, source is a file path string.
        Raises: FileNotFoundError, ValueError on parse errors.
        """
        ...
