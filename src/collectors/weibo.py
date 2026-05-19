import requests
from typing import List
from src.models import NewsItem
from src.collectors.base import BaseCollector


class WeiboCollector(BaseCollector):
    source_name = "微博热搜"

    def fetch(self) -> List[NewsItem]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://weibo.com/",
        }
        try:
            resp = requests.get(
                "https://weibo.com/ajax/side/hotSearch",
                headers=headers,
                timeout=10,
            )
            data = resp.json()
            realtime = data.get("data", {}).get("realtime", [])
            items: List[NewsItem] = []

            for i, item in enumerate(realtime[:20]):
                word = item.get("word", "").strip()
                if not word:
                    continue
                score = item.get("raw_hot_score", 0) or self.normalize_score(i + 1)
                items.append(NewsItem(
                    title=word,
                    source=self.source_name,
                    url=f"https://s.weibo.com/weibo?q={word}",
                    category="domestic",
                    hot_score=int(score),
                ))

            return items

        except Exception as e:
            print(f"[微博热搜] Scrape error: {e}")
            return []
