from src.collectors.rss_mixin import GoogleNewsRssMixin
from typing import List
from src.models import NewsItem


class ReutersCollector(GoogleNewsRssMixin):
    source_name = "Reuters"
    search_query = "reuters"

    def fetch(self) -> List[NewsItem]:
        items = self._parse_rss()
        for item in items:
            item.category = "international"
        return items
