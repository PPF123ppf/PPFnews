from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from src.enricher import clean_text, looks_mojibake
from src.google_news import is_google_news_url
from src.models import NewsItem


SOURCE_PRIORITY: Dict[str, int] = {
    "新华社": 45,
    "央视新闻": 42,
    "Reuters": 45,
    "AP": 43,
    "BBC": 40,
    "CNN": 38,
    "环球网": 32,
    "腾讯新闻": 28,
    "新浪新闻": 24,
    "百度热搜": 18,
    "微博热搜": 16,
}


def quality_score(item: NewsItem) -> int:
    score = SOURCE_PRIORITY.get(item.source, 10)
    summary = clean_text(item.summary)
    title = clean_text(item.title)

    score += min(item.hot_score, 100) // 5
    if item.published_at:
        score += _freshness_score(item.published_at)
    if len(summary) >= 300:
        score += 18
    elif len(summary) >= 160:
        score += 10
    elif len(summary) < 80:
        score -= 20
    if item.image_url:
        score += 8
    if item.url and not is_google_news_url(item.url):
        score += 8
    if looks_mojibake(summary) or looks_mojibake(title):
        score -= 80
    if _is_bad_url(item.url):
        score -= 25
    if _looks_low_value_title(title):
        score -= 18

    return score


def _freshness_score(value: str) -> int:
    try:
        published = datetime.fromisoformat(value)
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
    except ValueError:
        return 0
    hours = (datetime.now(timezone.utc) - published.astimezone(timezone.utc)).total_seconds() / 3600
    if hours <= 12:
        return 18
    if hours <= 24:
        return 12
    if hours <= 48:
        return 6
    return -30


def _is_bad_url(url: str) -> bool:
    parsed = urlparse(url or "")
    return "comment" in parsed.netloc or "comment" in parsed.path or parsed.netloc == "news.google.com"


def _looks_low_value_title(title: str) -> bool:
    lowered = title.lower()
    low_value_markers = ("观看：", "watch:", "视频", "直播", "comment")
    return any(marker in lowered for marker in low_value_markers)


def select_quality_top(
    items: List[NewsItem],
    top_n: int = 10,
    max_per_source: int = 2,
) -> Tuple[List[NewsItem], Dict[str, object]]:
    scored = sorted(
        ((quality_score(item), item) for item in items),
        key=lambda pair: pair[0],
        reverse=True,
    )
    selected: List[NewsItem] = []
    source_counts: Counter = Counter()
    rejected: Counter = Counter()

    for score, item in scored:
        if len(selected) >= top_n:
            break
        if score < 45:
            rejected["low_score"] += 1
            continue
        if source_counts[item.source] >= max_per_source:
            rejected["source_cap"] += 1
            continue
        if looks_mojibake(item.title) or looks_mojibake(item.summary):
            rejected["mojibake"] += 1
            continue
        if _is_bad_url(item.url):
            rejected["bad_url"] += 1
            continue
        selected.append(item)
        source_counts[item.source] += 1

    if len(selected) < top_n:
        for score, item in scored:
            if len(selected) >= top_n:
                break
            if item in selected or score < 35:
                continue
            if looks_mojibake(item.title) or looks_mojibake(item.summary):
                continue
            selected.append(item)
            source_counts[item.source] += 1

    report = {
        "candidates": len(items),
        "selected": len(selected),
        "source_counts": dict(source_counts),
        "rejected": dict(rejected),
        "image_count": sum(1 for item in selected if item.image_url),
        "google_news_urls": sum(1 for item in selected if is_google_news_url(item.url)),
        "mojibake_count": sum(
            1 for item in selected if looks_mojibake(item.title) or looks_mojibake(item.summary)
        ),
        "top_scores": [(score, item.source, item.title[:40]) for score, item in scored[:10]],
    }
    return selected, report


def print_quality_report(label: str, report: Dict[str, object], items: List[NewsItem]) -> None:
    print(f"\n[质量报告] {label}")
    print(f"  候选数: {report['candidates']} | 入选数: {report['selected']}")
    print(f"  入选来源: {report['source_counts']}")
    print(f"  丢弃原因: {report['rejected']}")
    print(f"  入选图片数: {report['image_count']}")
    print(f"  Google News 聚合链接残留: {report['google_news_urls']}")
    print(f"  乱码残留: {report['mojibake_count']}")
    for i, item in enumerate(items, 1):
        print(
            f"  {i}. [{item.source}] score={quality_score(item)} "
            f"image={'Y' if item.image_url else 'N'} {item.title}"
        )
