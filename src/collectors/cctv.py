from src.collectors.rss_mixin import RssCollectorMixin
from typing import List
from src.models import NewsItem


class CCTVCollector(RssCollectorMixin):
    source_name = "央视新闻"
    feed_url = "http://news.cctv.com/2019/07/gaoji/cctvnews.xml"

    def fetch(self) -> List[NewsItem]:
        return self._parse_rss()
