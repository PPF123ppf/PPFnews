from src.collectors.rss_mixin import GoogleNewsRssMixin
from typing import List
from src.models import NewsItem


class GlobalTimesCollector(GoogleNewsRssMixin):
    source_name = "环球网"
    search_query = "site:globaltimes.cn when:2d"

    def fetch(self) -> List[NewsItem]:
        items = self._parse_rss()
        for item in items:
            item.category = "international"
        return items
