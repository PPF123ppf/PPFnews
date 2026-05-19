import requests
from typing import List
from bs4 import BeautifulSoup
from src.models import NewsItem
from src.collectors.base import BaseCollector


class TencentCollector(BaseCollector):
    source_name = "腾讯新闻"

    def fetch(self) -> List[NewsItem]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        try:
            resp = requests.get(
                "https://news.qq.com/",
                headers=headers,
                timeout=10,
            )
            soup = BeautifulSoup(resp.text, "lxml")
            items: List[NewsItem] = []

            # Try multiple selectors to find news links
            seen_urls = set()
            for link in soup.find_all("a", href=True)[:50]:
                href = link.get("href", "")
                title = link.get_text(strip=True)
                if len(title) < 8:
                    continue
                # Accept any link that looks like a news article
                if any(k in href for k in ["news.qq.com", "new.qq.com", "view.inews.qq.com"]):
                    if href in seen_urls:
                        continue
                    seen_urls.add(href)
                    if not href.startswith("http"):
                        href = "https:" + href
                    items.append(NewsItem(
                        title=title,
                        source=self.source_name,
                        url=href,
                        category="domestic",
                        hot_score=self.normalize_score(len(items) + 1),
                    ))

            return items

        except Exception as e:
            print(f"[腾讯新闻] Scrape error: {e}")
            return []
