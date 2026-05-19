from src.collectors.rss_mixin import GoogleNewsRssMixin
from typing import List
from src.models import NewsItem


class TencentCollector(GoogleNewsRssMixin):
    source_name = "腾讯新闻"
    search_query = "site:news.qq.com 中国 when:2d"
    language = "zh-CN"
    country = "CN"
    ceid = "CN:zh-Hans"

    def fetch(self) -> List[NewsItem]:
        return self._parse_rss()
