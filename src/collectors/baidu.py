import requests
from typing import List
from src.models import NewsItem
from src.collectors.base import BaseCollector


class BaiduCollector(BaseCollector):
    source_name = "百度热搜"

    def fetch(self) -> List[NewsItem]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://top.baidu.com/board?tab=realtime",
        }
        try:
            resp = requests.get(
                "https://top.baidu.com/api/board?tab=realtime",
                headers=headers,
                timeout=10,
            )
            data = resp.json()
            cards = data.get("data", {}).get("cards", [])
            items: List[NewsItem] = []

            for card in cards:
                for i, item in enumerate(card.get("content", [])[:20]):
                    word = item.get("word", "").strip()
                    if not word:
                        continue
                    url = item.get("url", "") or item.get("query", "")
                    if url and not url.startswith("http"):
                        url = "https://www.baidu.com/s?wd=" + word
                    score = int(item.get("hotScore", 0)) or self.normalize_score(i + 1)
                    items.append(NewsItem(
                        title=word,
                        source=self.source_name,
                        url=url,
                        summary=item.get("desc", "").strip(),
                        image_url=item.get("img", "") or item.get("image", ""),
                        image_source_url=url if item.get("img") or item.get("image") else "",
                        category="domestic",
                        hot_score=score,
                    ))

            return items

        except Exception as e:
            print(f"[百度热搜] API error: {e}")
            return []
