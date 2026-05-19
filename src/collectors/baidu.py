import re
import requests
from typing import List
from bs4 import BeautifulSoup
from src.models import NewsItem
from src.collectors.base import BaseCollector


class BaiduCollector(BaseCollector):
    source_name = "百度热搜"

    def fetch(self) -> List[NewsItem]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        try:
            resp = requests.get(
                "https://top.baidu.com/board?tab=realtime",
                headers=headers,
                timeout=10,
            )
            soup = BeautifulSoup(resp.text, "lxml")
            scripts = soup.find_all("script")
            items: List[NewsItem] = []

            for script in scripts:
                content = script.string or ""
                if "s-data" not in content and "hotSearch" not in content:
                    continue
                matches = re.findall(r'"word":"(.*?)"', content)
                match_urls = re.findall(r'"url":"(.*?)"', content)
                match_score = re.findall(r'"score":"?(\d+)"?', content)

                for i, word in enumerate(matches[:20]):
                    url = match_urls[i] if i < len(match_urls) else ""
                    if url and not url.startswith("http"):
                        url = "https://top.baidu.com" + url
                    score = int(match_score[i]) if i < len(match_score) else self.normalize_score(i + 1)
                    items.append(NewsItem(
                        title=word,
                        source=self.source_name,
                        url=url,
                        category="domestic",
                        hot_score=score,
                    ))
                break

            return items

        except Exception as e:
            print(f"[百度热搜] Scrape error: {e}")
            return []
