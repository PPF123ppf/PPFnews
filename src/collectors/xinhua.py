from src.collectors.rss_mixin import GoogleNewsRssMixin
from typing import List
from src.models import NewsItem


class XinhuaCollector(GoogleNewsRssMixin):
    source_name = "新华社"
    search_query = "site:xinhuanet.com"

    def fetch(self) -> List[NewsItem]:
        return self._parse_rss()
