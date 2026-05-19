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

            for i, link in enumerate(soup.select("a[href*='news.qq.com']")[:15]):
                title = link.get_text(strip=True)
                href = link.get("href", "")
                if len(title) < 8:
                    continue
                if href and not href.startswith("http"):
                    href = "https:" + href if href.startswith("//") else "https://news.qq.com" + href
                items.append(NewsItem(
                    title=title,
                    source=self.source_name,
                    url=href,
                    category="domestic",
                    hot_score=self.normalize_score(i + 1),
                ))

            return items

        except Exception as e:
            print(f"[腾讯新闻] Scrape error: {e}")
            return []
