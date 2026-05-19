from src.collectors.rss_mixin import RssCollectorMixin
from typing import List
from src.models import NewsItem


class ReutersCollector(RssCollectorMixin):
    source_name = "Reuters"
    feed_url = "https://www.reutersagency.com/feed/"

    def fetch(self) -> List[NewsItem]:
        items = self._parse_rss()
        for item in items:
            item.category = "international"
        return items
