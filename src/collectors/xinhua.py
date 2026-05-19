from src.collectors.rss_mixin import RssCollectorMixin
from typing import List
from src.models import NewsItem


class XinhuaCollector(RssCollectorMixin):
    source_name = "新华社"
    feed_url = "http://www.news.cn/rss/gnxw.xml"

    def fetch(self) -> List[NewsItem]:
        return self._parse_rss()
