from src.collectors.rss_mixin import GoogleNewsRssMixin
from typing import List
from src.models import NewsItem


class CCTVCollector(GoogleNewsRssMixin):
    source_name = "央视新闻"
    search_query = "site:news.cctv.com 中国 when:2d"
    language = "zh-CN"
    country = "CN"
    ceid = "CN:zh-Hans"

    def fetch(self) -> List[NewsItem]:
        return self._parse_rss()
