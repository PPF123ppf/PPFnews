from src.collectors.rss_mixin import GoogleNewsRssMixin
from typing import List
from src.models import NewsItem


class SinaCollector(GoogleNewsRssMixin):
    source_name = "新浪新闻"
    search_query = "sina.com.cn"

    def fetch(self) -> List[NewsItem]:
        return self._parse_rss()
