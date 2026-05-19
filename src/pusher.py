import requests
from typing import List
from datetime import datetime, timezone, timedelta
from src.models import NewsItem, PushConfig
from src.enricher import clamp_text


BEIJING_TZ = timezone(timedelta(hours=8))


def format_message(domestic_items: List[NewsItem], international_items: List[NewsItem]) -> str:
    """Format news items into a Markdown message with summaries and images."""
    updated_at = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M")
    lines = [
        "# 今日国内外热点新闻",
        "",
        f"> 更新时间：{updated_at}（北京时间）",
        "",
        "今日推送不再只给链接；每条包含文字概括、相关图片和来源。",
    ]

    lines.extend(_format_section("国内 TOP 10", domestic_items[:10]))
    lines.extend(_format_section("国际 TOP 10", international_items[:10]))

    return "\n".join(lines)


def _format_section(title: str, items: List[NewsItem]) -> List[str]:
    lines = ["", f"## {title}", ""]
    for i, item in enumerate(items, 1):
        lines.extend(_format_item(i, item))
    return lines


def _format_item(index: int, item: NewsItem) -> List[str]:
    summary = clamp_text(item.summary, limit=620) or (
        f"{item.title}。该条来自{item.source}，目前热度较高，"
        "可通过来源链接查看完整报道和后续进展。"
    )
    lines = [
        f"### {index}. {item.title}",
        "",
        f"**来源：** {item.source}",
        "",
        f"**内容概括：** {summary}",
        "",
    ]

    if item.image_url:
        lines.extend([
            "**相关图片：**",
            "",
            f"![{item.title}]({item.image_url})",
            "",
        ])
        if item.image_source_url:
            lines.extend([f"图片来源：{item.image_source_url}", ""])
        if item.original_image_url and item.original_image_url != item.image_url:
            lines.extend([f"原图链接：{item.original_image_url}", ""])
    else:
        lines.extend(["**相关图片：** 未获取到可可靠引用的相关图片。", ""])

    if item.url:
        lines.extend([f"**原文链接：** {item.url}", ""])

    return lines


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
                "template": "markdown",
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
