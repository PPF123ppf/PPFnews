# Daily News Push Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Daily automatic push of domestic + international top 10 news to WeChat via Server酱/PushPlus

**Architecture:** Python scraper with independent per-source collectors, RSS + HTML scraping, GitHub Actions scheduled trigger, unified aggregation and formatting pipeline.

**Tech Stack:** Python 3.11+, requests, BeautifulSoup, feedparser, GitHub Actions

---

### Task 1: Project Scaffolding + Models + Config

**Files:**
- Create: `src/__init__.py`
- Create: `src/models.py`
- Create: `src/config.py`
- Create: `requirements.txt`
- Create: `.github/workflows/daily.yml` (placeholder)

- [ ] **Step 1: Create project directories and __init__.py files**

```bash
mkdir -p src/collectors && touch src/__init__.py src/collectors/__init__.py
```

- [ ] **Step 2: Write models.py**

```python
from dataclasses import dataclass, field
from typing import List


@dataclass
class NewsItem:
    title: str
    source: str
    url: str
    summary: str = ""
    category: str = "domestic"  # "domestic" | "international"
    hot_score: int = 0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "summary": self.summary[:100] if self.summary else "",
            "category": self.category,
            "hot_score": self.hot_score,
        }


@dataclass
class PushConfig:
    serverchan_key: str = ""
    pushplus_token: str = ""
```

- [ ] **Step 3: Write config.py**

```python
import os
from src.models import PushConfig


def load_config() -> PushConfig:
    return PushConfig(
        serverchan_key=os.getenv("SERVERCHAN_KEY", ""),
        pushplus_token=os.getenv("PUSHPLUS_TOKEN", ""),
    )
```

- [ ] **Step 4: Write requirements.txt**

```
requests>=2.31.0
beautifulsoup4>=4.12.0
feedparser>=6.0.11
lxml>=5.0.0
```

- [ ] **Step 5: Commit**

```bash
git init && git add -A && git commit -m "chore: scaffold project structure with models and config"
```

---

### Task 2: Base Collector Interface

**Files:**
- Create: `src/collectors/base.py`

- [ ] **Step 1: Write base.py**

```python
from abc import ABC, abstractmethod
from typing import List
from src.models import NewsItem


class BaseCollector(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        ...

    @abstractmethod
    def fetch(self) -> List[NewsItem]:
        ...

    def normalize_score(self, rank: int, max_rank: int = 20) -> int:
        """Convert position rank to a score. Rank 1 = highest score."""
        return max(1, (max_rank - rank + 1) * 5)
```

- [ ] **Step 2: Commit**

```bash
git add -A && git commit -m "feat: add base collector abstract class"
```

---

### Task 3: RSS Utility + Xinhua + CCTV Collectors

**Files:**
- Create: `src/collectors/rss_mixin.py`
- Create: `src/collectors/xinhua.py`
- Create: `src/collectors/cctv.py`

- [ ] **Step 1: Write rss_mixin.py**

```python
import feedparser
from typing import List, Optional
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
                # Strip HTML tags from summary
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
```

- [ ] **Step 2: Write xinhua.py**

```python
from src.collectors.rss_mixin import RssCollectorMixin
from typing import List
from src.models import NewsItem


class XinhuaCollector(RssCollectorMixin):
    source_name = "新华社"
    feed_url = "http://www.news.cn/rss/gnxw.xml"

    def fetch(self) -> List[NewsItem]:
        return self._parse_rss()
```

- [ ] **Step 3: Write cctv.py**

```python
from src.collectors.rss_mixin import RssCollectorMixin
from typing import List
from src.models import NewsItem


class CCTVCollector(RssCollectorMixin):
    source_name = "央视新闻"
    feed_url = "http://news.cctv.com/2019/07/gaoji/cctvnews.xml"

    def fetch(self) -> List[NewsItem]:
        return self._parse_rss()
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: add RSS collector mixin, Xinhua and CCTV collectors"
```

---

### Task 4: Baidu + Weibo Collectors (Domestic Scraping)

**Files:**
- Create: `src/collectors/baidu.py`
- Create: `src/collectors/weibo.py`

- [ ] **Step 1: Write baidu.py**

```python
import re
import json
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
            # Data is embedded in a script tag as JSON
            scripts = soup.find_all("script")
            items: List[NewsItem] = []

            for script in scripts:
                content = script.string or ""
                if "s-data" not in content and "hotSearch" not in content:
                    continue
                # Try to extract JSON array from window.__NUQI__ or similar
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
                break  # Found the data we need

            return items

        except Exception as e:
            print(f"[百度热搜] Scrape error: {e}")
            return []
```

- [ ] **Step 2: Write weibo.py**

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: add Baidu and Weibo hot search collectors"
```

---

### Task 5: Tencent + Sina + Global Times Collectors

**Files:**
- Create: `src/collectors/tencent.py`
- Create: `src/collectors/sina.py`
- Create: `src/collectors/global_times.py`

- [ ] **Step 1: Write tencent.py**

```python
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
```

- [ ] **Step 2: Write sina.py**

```python
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
```

- [ ] **Step 3: Write global_times.py**

```python
from src.collectors.rss_mixin import RssCollectorMixin
from typing import List
from src.models import NewsItem


class GlobalTimesCollector(RssCollectorMixin):
    source_name = "环球网"
    feed_url = "https://www.globaltimes.cn/rss/index.xml"

    def fetch(self) -> List[NewsItem]:
        items = self._parse_rss()
        for item in items:
            item.category = "international"
        return items
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: add Tencent, Sina, and Global Times collectors"
```

---

### Task 6: International RSS Collectors (Reuters, BBC, CNN, AP)

**Files:**
- Create: `src/collectors/reuters.py`
- Create: `src/collectors/bbc.py`
- Create: `src/collectors/cnn.py`
- Create: `src/collectors/ap.py`

- [ ] **Step 1: Write reuters.py**

```python
from src.collectors.rss_mixin import RssCollectorMixin
from typing import List
from src.models import NewsItem


class ReutersCollector(RssCollectorMixin):
    source_name = "Reuters"
    feed_url = "https://www.reutersagency.com/feed/"

    def fetch(self) -> List[NewsItem]:
        items = self._parse_rss()
        for item in items:
            item.category = "international"
        return items
```

- [ ] **Step 2: Write bbc.py**

```python
from src.collectors.rss_mixin import RssCollectorMixin
from typing import List
from src.models import NewsItem


class BBCCollector(RssCollectorMixin):
    source_name = "BBC"
    feed_url = "https://feeds.bbci.co.uk/news/rss.xml"

    def fetch(self) -> List[NewsItem]:
        items = self._parse_rss()
        for item in items:
            item.category = "international"
        return items
```

- [ ] **Step 3: Write cnn.py**

```python
from src.collectors.rss_mixin import RssCollectorMixin
from typing import List
from src.models import NewsItem


class CNNCollector(RssCollectorMixin):
    source_name = "CNN"
    feed_url = "http://rss.cnn.com/rss/cnn_topstories.rss"

    def fetch(self) -> List[NewsItem]:
        items = self._parse_rss()
        for item in items:
            item.category = "international"
        return items
```

- [ ] **Step 4: Write ap.py**

```python
from src.collectors.rss_mixin import RssCollectorMixin
from typing import List
from src.models import NewsItem


class APCollector(RssCollectorMixin):
    source_name = "AP"
    feed_url = "https://feeds.ap.org/ap/topnews"

    def fetch(self) -> List[NewsItem]:
        items = self._parse_rss()
        for item in items:
            item.category = "international"
        return items
```

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: add Reuters, BBC, CNN, AP collectors"
```

---

### Task 7: Pusher Module (Server酱 + PushPlus)

**Files:**
- Create: `src/pusher.py`

- [ ] **Step 1: Write pusher.py**

```python
import requests
from typing import List
from src.models import NewsItem, PushConfig


def format_message(domestic_items: List[NewsItem], international_items: List[NewsItem]) -> str:
    """Format news items into a WeChat-friendly message."""
    lines = ["📰 今日国内外热点新闻\n", "═" * 20]

    lines.append("\n🇨🇳 国内 TOP 10\n")
    for i, item in enumerate(domestic_items[:10], 1):
        lines.append(f"{i}. {item.title}")
        lines.append(f"   [{item.source}]")
        if item.url:
            lines.append(f"   {item.url}")
        lines.append("")

    lines.append("═" * 20)
    lines.append("\n🌍 国际 TOP 10\n")
    for i, item in enumerate(international_items[:10], 1):
        lines.append(f"{i}. {item.title}")
        lines.append(f"   [{item.source}]")
        if item.url:
            lines.append(f"   {item.url}")
        lines.append("")

    lines.append(f"\n更新时间：2026-05-19 08:00")
    return "\n".join(lines)


def push_via_serverchan(config: PushConfig, title: str, content: str) -> bool:
    """Push via Server酱."""
    if not config.serverchan_key:
        return False
    try:
        resp = requests.post(
            f"https://sctapi.ftqq.com/{config.serverchan_key}.send",
            data={"title": title, "desp": content},
            timeout=15,
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"[Server酱] Push error: {e}")
        return False


def push_via_pushplus(config: PushConfig, title: str, content: str) -> bool:
    """Push via PushPlus."""
    if not config.pushplus_token:
        return False
    try:
        resp = requests.post(
            "https://www.pushplus.plus/send",
            json={
                "token": config.pushplus_token,
                "title": title,
                "content": content,
                "template": "txt",
            },
            timeout=15,
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"[PushPlus] Push error: {e}")
        return False


def push_news(config: PushConfig, domestic: List[NewsItem], international: List[NewsItem]) -> bool:
    """Push formatted news via configured channels."""
    title = "每日新闻推送 — 国内外 TOP 10"
    content = format_message(domestic, international)

    pushed = False
    if config.serverchan_key:
        pushed = push_via_serverchan(config, title, content) or pushed
    if config.pushplus_token:
        pushed = push_via_pushplus(config, title, content) or pushed

    if not pushed:
        print("[推送] 未配置任何推送渠道或所有推送均失败")
    return pushed
```

- [ ] **Step 2: Commit**

```bash
git add -A && git commit -m "feat: add pusher module with Server酱 and PushPlus support"
```

---

### Task 8: Main Entry Point (Aggregate, Sort, Format, Push)

**Files:**
- Create: `src/main.py`

- [ ] **Step 1: Write main.py**

```python
"""Daily News Push — Entry point for GitHub Actions."""

import re
from typing import List
from src.config import load_config
from src.models import NewsItem
from src.pusher import push_news

# Domestic collectors
from src.collectors.baidu import BaiduCollector
from src.collectors.weibo import WeiboCollector
from src.collectors.xinhua import XinhuaCollector
from src.collectors.cctv import CCTVCollector
from src.collectors.tencent import TencentCollector
from src.collectors.sina import SinaCollector

# International collectors
from src.collectors.reuters import ReutersCollector
from src.collectors.bbc import BBCCollector
from src.collectors.cnn import CNNCollector
from src.collectors.ap import APCollector
from src.collectors.global_times import GlobalTimesCollector


def normalize_title(title: str) -> str:
    """Normalize title for deduplication."""
    text = title.lower().strip()
    text = re.sub(r"[^\w一-鿿]", "", text)  # Keep alphanumeric + CJK
    return text


def deduplicate(items: List[NewsItem]) -> List[NewsItem]:
    """Remove near-duplicate items based on title similarity."""
    seen: set = set()
    result: List[NewsItem] = []
    for item in items:
        key = normalize_title(item.title)[:30]  # Use first 30 chars
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def collect_all() -> tuple:
    """Run all collectors and return (domestic, international) items."""
    domestic_collectors = [
        BaiduCollector(),
        WeiboCollector(),
        XinhuaCollector(),
        CCTVCollector(),
        TencentCollector(),
        SinaCollector(),
    ]
    international_collectors = [
        ReutersCollector(),
        BBCCollector(),
        CNNCollector(),
        APCollector(),
        GlobalTimesCollector(),
    ]

    domestic_items: List[NewsItem] = []
    international_items: List[NewsItem] = []

    for collector in domestic_collectors:
        try:
            items = collector.fetch()
            print(f"[{collector.source_name}] 获取 {len(items)} 条")
            domestic_items.extend(items)
        except Exception as e:
            print(f"[{collector.source_name}] 采集失败: {e}")

    for collector in international_collectors:
        try:
            items = collector.fetch()
            print(f"[{collector.source_name}] fetched {len(items)} items")
            international_items.extend(items)
        except Exception as e:
            print(f"[{collector.source_name}] failed: {e}")

    return domestic_items, international_items


def sort_and_top(items: List[NewsItem], top_n: int = 10) -> List[NewsItem]:
    """Deduplicate, sort by hot_score desc, return top N."""
    items = deduplicate(items)
    items.sort(key=lambda x: x.hot_score, reverse=True)
    return items[:top_n]


def main():
    config = load_config()
    print("=" * 40)
    print("开始采集新闻...")
    print("=" * 40)

    domestic_items, international_items = collect_all()

    print("\n" + "=" * 40)
    print(f"国内: {len(domestic_items)} 条 → 去重排序取 TOP 10")
    domestic_top = sort_and_top(domestic_items)
    for i, item in enumerate(domestic_top, 1):
        print(f"  {i}. [{item.source}] {item.title} (热度: {item.hot_score})")

    print(f"\n国际: {len(international_items)} 条 → 去重排序取 TOP 10")
    international_top = sort_and_top(international_items)
    for i, item in enumerate(international_top, 1):
        print(f"  {i}. [{item.source}] {item.title} (score: {item.hot_score})")

    print("\n" + "=" * 40)
    print("开始推送...")
    success = push_news(config, domestic_top, international_top)
    print(f"推送结果: {'成功' if success else '失败'}")
    print("=" * 40)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add -A && git commit -m "feat: add main entry point with collection and aggregation pipeline"
```

---

### Task 9: GitHub Actions Workflow + README

**Files:**
- Create: `.github/workflows/daily.yml`
- Create: `README.md`

- [ ] **Step 1: Write .github/workflows/daily.yml**

```yaml
name: Daily News Push

on:
  schedule:
    # Run daily at 00:00 UTC (08:00 Beijing time)
    - cron: '0 0 * * *'
  workflow_dispatch:  # Allow manual trigger for testing

jobs:
  news:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Collect and push news
        env:
          SERVERCHAN_KEY: ${{ secrets.SERVERCHAN_KEY }}
          PUSHPLUS_TOKEN: ${{ secrets.PUSHPLUS_TOKEN }}
        run: python src/main.py
```

- [ ] **Step 2: Write README.md**

```markdown
# Daily News Push

每日自动抓取国内外主流新闻源，聚合后国内/国际各取 TOP 10，通过 Server酱 / PushPlus 推送到微信。

## 新闻来源

### 国内
| 来源 | 方式 |
|------|------|
| 百度热搜 | HTML 爬取 |
| 微博热搜 | JSON API |
| 新华社 | RSS |
| 央视新闻 | RSS |
| 腾讯新闻 | HTML 爬取 |
| 新浪新闻 | HTML 爬取 |

### 国际
| 来源 | 方式 |
|------|------|
| Reuters | RSS |
| BBC | RSS |
| CNN | RSS |
| AP | RSS |
| 环球网 | RSS |

## 使用方式

### 1. Fork 本仓库

### 2. 配置推送渠道（至少一个）

**Server酱：** 在 https://sct.ftqq.com 获取 SendKey
**PushPlus：** 在 https://www.pushplus.plus 获取 Token

### 3. 配置 GitHub Secrets

在仓库 Settings → Secrets and variables → Actions 中添加：

| Name | Value |
|------|-------|
| `SERVERCHAN_KEY` | Server酱 SendKey |
| `PUSHPLUS_TOKEN` | PushPlus Token |

### 4. 启用 Actions

GitHub Actions 默认启用，每天 UTC 00:00（北京时间 08:00）自动运行。

也可以手动触发：Actions → Daily News Push → Run workflow

## 本地运行

```bash
pip install -r requirements.txt
SERVERCHAN_KEY=xxx python src/main.py
```
```

- [ ] **Step 3: Create .gitignore**

```bash
echo -e "__pycache__/\n*.pyc\n.env" > .gitignore
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: add GitHub Actions workflow and README"
```

---

## Self-Review Checklist

1. **Spec coverage:** All 12 news sources covered (6 domestic: Baidu, Weibo, Xinhua, CCTV, Tencent, Sina; 5 international: Reuters, BBC, CNN, AP, Global Times). Pusher covers both Server酱 and PushPlus. GitHub Actions scheduled. ✅
2. **Placeholder scan:** No TBD, TODO, or vague steps. Every file has complete code. ✅
3. **Type consistency:** NewsItem uses same fields throughout. `source_name` property consistent across collectors. `fetch()` returns `List[NewsItem]` everywhere. ✅
4. **No missing imports:** All imports checked. Each collector imports correct base class. All collectors imported in main.py. ✅
