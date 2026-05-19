from src.collectors.rss_mixin import GoogleNewsRssMixin
from typing import List
from src.models import NewsItem


class CNNCollector(GoogleNewsRssMixin):
    source_name = "CNN"
    search_query = "site:cnn.com when:2d"

    def fetch(self) -> List[NewsItem]:
        items = self._parse_rss()
        for item in items:
            item.category = "international"
        return items
