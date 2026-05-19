import feedparser
from datetime import datetime, timezone, timedelta
from typing import List
from urllib.parse import quote
from src.models import NewsItem
from src.collectors.base import BaseCollector
from src.enricher import clean_text, extract_image_from_html


class RssCollectorMixin(BaseCollector):
    """Mixin for RSS-based collectors. Override feed_url and source_name."""

    feed_url: str = ""
    max_age_hours: int = 48
    strip_source_suffix: bool = False

    def _parse_rss(self, max_items: int = 15) -> List[NewsItem]:
        """Parse RSS feed and return news items."""
        if not self.feed_url:
            return []

        try:
            feed = feedparser.parse(self.feed_url)
            items: List[NewsItem] = []

            for entry in feed.entries:
                published_at = self._entry_published_at(entry)
                if published_at and not self._is_recent(published_at):
                    continue

                title = self._clean_title(entry.get("title", "").strip())
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
                    published_at=published_at.isoformat() if published_at else "",
                    category="domestic",
                    hot_score=self.normalize_score(len(items) + 1),
                ))
                if len(items) >= max_items:
                    break

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

    def _clean_title(self, title: str) -> str:
        if not self.strip_source_suffix:
            return title
        return title.rsplit(" - ", 1)[0].strip() if " - " in title else title

    def _entry_published_at(self, entry) -> datetime | None:
        parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if not parsed:
            return None
        return datetime(*parsed[:6], tzinfo=timezone.utc)

    def _is_recent(self, published_at: datetime) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.max_age_hours)
        return published_at >= cutoff


class GoogleNewsRssMixin(RssCollectorMixin):
    """Mixin for Google News RSS filtered by site. Override search_query."""

    search_query: str = ""
    language: str = "en-US"
    country: str = "US"
    ceid: str = "US:en"
    strip_source_suffix: bool = True

    def _parse_rss(self, max_items: int = 15) -> List[NewsItem]:
        if not self.search_query:
            return []
        self.feed_url = (
            f"https://news.google.com/rss/search?q={quote(self.search_query)}"
            f"&hl={self.language}&gl={self.country}&ceid={self.ceid}"
        )
        return super()._parse_rss(max_items)
