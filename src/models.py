from dataclasses import dataclass, field
from typing import List


@dataclass
class NewsItem:
    title: str
    source: str
    url: str
    summary: str = ""
    category: str = "domestic"  # "domestic" | "international"
    hot_score: int = 0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "summary": self.summary[:100] if self.summary else "",
            "category": self.category,
            "hot_score": self.hot_score,
        }


@dataclass
class PushConfig:
    serverchan_key: str = ""
    pushplus_token: str = ""
