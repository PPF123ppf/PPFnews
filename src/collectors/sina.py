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
                "https://news.sina.com.cn/",
                headers=headers,
                timeout=10,
            )
            resp.encoding = resp.apparent_encoding or "utf-8"
            soup = BeautifulSoup(resp.text, "lxml")
            items: List[NewsItem] = []
            seen_titles = set()

            for a_tag in soup.find_all("a", href=True)[:50]:
                href = a_tag.get("href", "")
                title = a_tag.get_text(strip=True)
                if len(title) < 8:
                    continue
                if "sina.com" not in href and "sina.cn" not in href:
                    continue
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                if href.startswith("//"):
                    href = "https:" + href
                elif not href.startswith("http"):
                    continue

                items.append(NewsItem(
                    title=title,
                    source=self.source_name,
                    url=href,
                    category="domestic",
                    hot_score=self.normalize_score(len(items) + 1),
                ))

            return items

        except Exception as e:
            print(f"[新浪新闻] Scrape error: {e}")
            return []
