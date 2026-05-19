from dataclasses import dataclass
from typing import List


@dataclass
class NewsItem:
    title: str
    source: str
    url: str
    summary: str = ""
    image_url: str = ""
    image_source_url: str = ""
    original_image_url: str = ""
    published_at: str = ""
    category: str = "domestic"  # "domestic" | "international"
    hot_score: int = 0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "summary": self.summary[:600] if self.summary else "",
            "image_url": self.image_url,
            "image_source_url": self.image_source_url,
            "original_image_url": self.original_image_url,
            "published_at": self.published_at,
            "category": self.category,
            "hot_score": self.hot_score,
        }


@dataclass
class PushConfig:
    serverchan_key: str = ""
    pushplus_token: str = ""
