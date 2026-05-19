from abc import ABC, abstractmethod
from typing import List
from src.models import NewsItem


class BaseCollector(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        ...

    @abstractmethod
    def fetch(self) -> List[NewsItem]:
        ...

    def normalize_score(self, rank: int, max_rank: int = 20) -> int:
        """Convert position rank to a score. Rank 1 = highest score."""
        return max(1, (max_rank - rank + 1) * 5)
