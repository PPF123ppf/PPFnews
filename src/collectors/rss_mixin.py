import feedparser
from typing import List
from src.models import NewsItem
from src.collectors.base import BaseCollector


class RssCollectorMixin(BaseCollector):
    """Mixin for RSS-based collectors. Override feed_url and source_name."""

    feed_url: str = ""

    def _parse_rss(self, max_items: int = 15) -> List[NewsItem]:
        """Parse RSS feed and return news items."""
        if not self.feed_url:
            return []

        try:
            feed = feedparser.parse(self.feed_url)
            items: List[NewsItem] = []

            for i, entry in enumerate(feed.entries[:max_items]):
                title = entry.get("title", "").strip()
                if not title:
                    continue

                link = entry.get("link", "")
                summary = entry.get("summary", "") or entry.get("description", "")
                summary = summary.replace("<p>", " ").replace("</p>", " ") \
                    .replace("<br>", " ").replace("<br/>", " ") \
                    .replace("<![CDATA[", "").replace("]]>", "")

                items.append(NewsItem(
                    title=title,
                    source=self.source_name,
                    url=link,
                    summary=summary.strip(),
                    category="domestic",
                    hot_score=self.normalize_score(i + 1),
                ))

            return items

        except Exception as e:
            print(f"[{self.source_name}] RSS parse error: {e}")
            return []


class GoogleNewsRssMixin(RssCollectorMixin):
    """Mixin for Google News RSS filtered by site. Override search_query."""

    search_query: str = ""

    def _parse_rss(self, max_items: int = 15) -> List[NewsItem]:
        if not self.search_query:
            return []
        self.feed_url = (
            f"https://news.google.com/rss/search?q={self.search_query}"
            f"&hl=en-US&gl=US&ceid=US:en"
        )
        return super()._parse_rss(max_items)
