from src.collectors.rss_mixin import RssCollectorMixin
from typing import List
from src.models import NewsItem


class CNNCollector(RssCollectorMixin):
    source_name = "CNN"
    feed_url = "http://rss.cnn.com/rss/cnn_topstories.rss"

    def fetch(self) -> List[NewsItem]:
        items = self._parse_rss()
        for item in items:
            item.category = "international"
        return items
