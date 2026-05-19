from src.collectors.rss_mixin import RssCollectorMixin
from typing import List
from src.models import NewsItem


class GlobalTimesCollector(RssCollectorMixin):
    source_name = "环球网"
    feed_url = "https://www.globaltimes.cn/rss/index.xml"

    def fetch(self) -> List[NewsItem]:
        items = self._parse_rss()
        for item in items:
            item.category = "international"
        return items
