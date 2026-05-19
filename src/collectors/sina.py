import requests
from typing import List
from bs4 import BeautifulSoup
from src.models import NewsItem
from src.collectors.base import BaseCollector


class SinaCollector(BaseCollector):
    source_name = "新浪新闻"

    def fetch(self) -> List[NewsItem]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        try:
            resp = requests.get(
                "https://news.sina.com.cn/hotnews/",
                headers=headers,
                timeout=10,
            )
            soup = BeautifulSoup(resp.text, "lxml")
            items: List[NewsItem] = []

            for i, a_tag in enumerate(soup.select("a[href*='sina.com']")[:15]):
                title = a_tag.get_text(strip=True)
                href = a_tag.get("href", "")
                if len(title) < 8:
                    continue
                items.append(NewsItem(
                    title=title,
                    source=self.source_name,
                    url=href if href.startswith("http") else f"https:{href}",
                    category="domestic",
                    hot_score=self.normalize_score(i + 1),
                ))

            return items

        except Exception as e:
            print(f"[新浪新闻] Scrape error: {e}")
            return []
