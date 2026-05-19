from src.collectors.rss_mixin import RssCollectorMixin
from typing import List
from src.models import NewsItem


class APCollector(RssCollectorMixin):
    source_name = "AP"
    feed_url = "https://feeds.ap.org/ap/topnews"

    def fetch(self) -> List[NewsItem]:
        items = self._parse_rss()
        for item in items:
            item.category = "international"
        return items
