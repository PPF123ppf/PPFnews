import feedparser
from typing import List
from urllib.parse import quote
from src.models import NewsItem
from src.collectors.base import BaseCollector
from src.enricher import clean_text, extract_image_from_html


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
                summary_html = entry.get("summary", "") or entry.get("description", "")
                image_url = self._extract_entry_image(entry, summary_html)

                items.append(NewsItem(
                    title=title,
                    source=self.source_name,
                    url=link,
                    summary=clean_text(summary_html),
                    image_url=image_url,
                    image_source_url=link if image_url else "",
                    category="domestic",
                    hot_score=self.normalize_score(i + 1),
                ))

            return items

        except Exception as e:
            print(f"[{self.source_name}] RSS parse error: {e}")
            return []

    def _extract_entry_image(self, entry, summary_html: str) -> str:
        """Extract image URLs exposed by common RSS media fields."""
        for field in ("media_content", "media_thumbnail"):
            for media in entry.get(field, []) or []:
                url = media.get("url")
                if url:
                    return url

        for link in entry.get("links", []) or []:
            if str(link.get("type", "")).startswith("image/") and link.get("href"):
                return link["href"]

        for enclosure in entry.get("enclosures", []) or []:
            if str(enclosure.get("type", "")).startswith("image/") and enclosure.get("href"):
                return enclosure["href"]

        return extract_image_from_html(summary_html, entry.get("link", ""))


class GoogleNewsRssMixin(RssCollectorMixin):
    """Mixin for Google News RSS filtered by site. Override search_query."""

    search_query: str = ""

    def _parse_rss(self, max_items: int = 15) -> List[NewsItem]:
        if not self.search_query:
            return []
        self.feed_url = (
            f"https://news.google.com/rss/search?q={quote(self.search_query)}"
            f"&hl=en-US&gl=US&ceid=US:en"
        )
        return super()._parse_rss(max_items)
