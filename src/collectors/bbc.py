from src.collectors.rss_mixin import RssCollectorMixin
from typing import List
from src.models import NewsItem


class BBCCollector(RssCollectorMixin):
    source_name = "BBC"
    feed_url = "https://feeds.bbci.co.uk/news/rss.xml"

    def fetch(self) -> List[NewsItem]:
        items = self._parse_rss()
        for item in items:
            item.category = "international"
        return items
