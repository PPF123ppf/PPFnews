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
