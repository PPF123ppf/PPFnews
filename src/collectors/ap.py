from src.collectors.rss_mixin import GoogleNewsRssMixin
from typing import List
from src.models import NewsItem


class APCollector(GoogleNewsRssMixin):
    source_name = "AP"
    search_query = "apnews.com+top+news"

    def fetch(self) -> List[NewsItem]:
        items = self._parse_rss()
        for item in items:
            item.category = "international"
        return items
