"""Daily News Push — Entry point for GitHub Actions."""

import re
from typing import List
from src.config import load_config
from src.enricher import enrich_items
from src.image_cache import cache_images_for_push, commit_cached_images
from src.models import NewsItem
from src.pusher import push_news
from src.quality import print_quality_report, select_quality_top

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
        XinhuaCollector(),
        CCTVCollector(),
        TencentCollector(),
        SinaCollector(),
        BaiduCollector(),
        WeiboCollector(),
    ]
    international_collectors = [
        ReutersCollector(),
        APCollector(),
        BBCCollector(),
        CNNCollector(),
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


def source_balanced_candidates(items: List[NewsItem], limit: int = 30) -> List[NewsItem]:
    """Build a diverse candidate pool before expensive enrichment and quality scoring."""
    items = deduplicate(items)
    grouped: dict[str, List[NewsItem]] = {}
    for item in items:
        grouped.setdefault(item.source, []).append(item)

    for source_items in grouped.values():
        source_items.sort(key=lambda x: x.hot_score, reverse=True)

    result: List[NewsItem] = []
    while len(result) < limit and any(grouped.values()):
        active_sources = sorted(
            (source for source, source_items in grouped.items() if source_items),
            key=lambda source: grouped[source][0].hot_score,
            reverse=True,
        )
        for source in active_sources:
            if len(result) >= limit:
                break
            result.append(grouped[source].pop(0))

    return result


def main():
    config = load_config()
    print("=" * 40)
    print("开始采集新闻...")
    print("=" * 40)

    domestic_items, international_items = collect_all()

    print("\n" + "=" * 40)
    print(f"国内: {len(domestic_items)} 条 → 构建候选池 → 质量评分取 TOP 10")
    domestic_candidates = source_balanced_candidates(domestic_items, limit=18)
    print(f"国内候选池: {len(domestic_candidates)} 条，补全文字概括和相关图片...")
    domestic_candidates = enrich_items(domestic_candidates)
    domestic_top, domestic_report = select_quality_top(domestic_candidates, top_n=10)
    print_quality_report("国内", domestic_report, domestic_top)
    for i, item in enumerate(domestic_top, 1):
        print(f"  {i}. [{item.source}] {item.title} (热度: {item.hot_score})")

    print(f"\n国际: {len(international_items)} 条 → 构建候选池 → 质量评分取 TOP 10")
    international_candidates = source_balanced_candidates(international_items, limit=18)
    print(f"国际候选池: {len(international_candidates)} 条，补全文字概括和相关图片...")
    international_candidates = enrich_items(international_candidates)
    international_top, international_report = select_quality_top(international_candidates, top_n=10)
    print_quality_report("国际", international_report, international_top)
    for i, item in enumerate(international_top, 1):
        print(f"  {i}. [{item.source}] {item.title} (score: {item.hot_score})")

    print("\n缓存新闻图片...")
    cached_images = cache_images_for_push(domestic_top + international_top)
    commit_cached_images(cached_images)

    print("\n" + "=" * 40)
    print("开始推送...")
    success = push_news(config, domestic_top, international_top)
    print(f"推送结果: {'成功' if success else '失败'}")
    print("=" * 40)


if __name__ == "__main__":
    main()
