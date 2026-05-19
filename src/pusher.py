import requests
from typing import List
from datetime import datetime, timezone, timedelta
from html import escape
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


def format_html_message(domestic_items: List[NewsItem], international_items: List[NewsItem]) -> str:
    """Format news items as PushPlus HTML; images render more reliably than Markdown."""
    updated_at = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M")
    parts = [
        "<article style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.65;color:#1f2933;\">",
        "<h1 style=\"font-size:22px;margin:0 0 8px;\">今日国内外热点新闻</h1>",
        f"<p style=\"color:#667085;margin:0 0 16px;\">更新时间：{escape(updated_at)}（北京时间）</p>",
        "<p style=\"margin:0 0 18px;\">每条新闻包含中文内容概括、相关图片和来源链接。</p>",
    ]
    parts.extend(_format_html_section("国内 TOP 10", domestic_items[:10]))
    parts.extend(_format_html_section("国际 TOP 10", international_items[:10]))
    parts.append("</article>")
    return "\n".join(parts)


def _format_html_section(title: str, items: List[NewsItem]) -> List[str]:
    parts = [f"<h2 style=\"font-size:18px;margin:24px 0 12px;border-left:4px solid #2563eb;padding-left:8px;\">{escape(title)}</h2>"]
    for i, item in enumerate(items, 1):
        parts.extend(_format_html_item(i, item))
    return parts


def _format_html_item(index: int, item: NewsItem) -> List[str]:
    summary = clamp_text(item.summary, limit=620) or (
        f"{item.title}。该条来自{item.source}，目前热度较高，"
        "可通过来源链接查看完整报道和后续进展。"
    )
    parts = [
        "<section style=\"margin:0 0 22px;padding:14px;border:1px solid #e5e7eb;border-radius:12px;background:#ffffff;\">",
        f"<h3 style=\"font-size:17px;margin:0 0 8px;\">{index}. {escape(item.title)}</h3>",
        f"<p style=\"margin:0 0 8px;color:#475467;\"><strong>来源：</strong>{escape(item.source)}</p>",
        f"<p style=\"margin:0 0 12px;\"><strong>内容概括：</strong>{escape(summary)}</p>",
    ]

    if item.image_url:
        parts.extend([
            "<div style=\"margin:12px 0;\">",
            (
                f"<img src=\"{escape(item.image_url, quote=True)}\" alt=\"{escape(item.title, quote=True)}\" "
                "style=\"display:block;width:100%;max-width:680px;height:auto;border-radius:10px;border:1px solid #e5e7eb;\" />"
            ),
            "</div>",
        ])
        if item.original_image_url and item.original_image_url != item.image_url:
            parts.append(
                f"<p style=\"font-size:13px;color:#667085;margin:6px 0;\">"
                f"若图片未显示，可点原图链接：<a href=\"{escape(item.original_image_url, quote=True)}\">查看原图</a></p>"
            )
    else:
        parts.append("<p style=\"color:#667085;margin:8px 0;\">相关图片：未获取到可可靠引用的相关图片。</p>")

    if item.url:
        parts.append(f"<p style=\"margin:8px 0 0;\"><a href=\"{escape(item.url, quote=True)}\">查看原文</a></p>")

    parts.append("</section>")
    return parts


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
        print(f"[Server酱] HTTP {resp.status_code}: {resp.text[:300]}")
        if resp.status_code != 200:
            return False
        try:
            data = resp.json()
            errno = data.get("errno")
            code = data.get("code")
            return errno in (0, None) and code in (0, None)
        except ValueError:
            return True
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
                "template": "html",
            },
            timeout=15,
        )
        print(f"[PushPlus] HTTP {resp.status_code}: {resp.text[:500]}")
        if resp.status_code != 200:
            return False
        try:
            data = resp.json()
        except ValueError:
            return False
        code = data.get("code")
        success = code == 200
        if not success:
            print(f"[PushPlus] Business failure: {data}")
        return success
    except Exception as e:
        print(f"[PushPlus] Push error: {e}")
        return False


def push_news(config: PushConfig, domestic: List[NewsItem], international: List[NewsItem]) -> bool:
    """Push formatted news via configured channels."""
    title = "每日新闻推送 — 国内外 TOP 10"

    pushed = False
    if config.pushplus_token:
        pushed = push_via_pushplus(config, title, format_html_message(domestic, international)) or pushed
    if not pushed and config.serverchan_key:
        print("[推送] PushPlus 未确认成功，尝试 Server酱备用渠道")
        pushed = push_via_serverchan(config, title, format_message(domestic, international)) or pushed

    if not pushed:
        print("[推送] 未配置任何推送渠道或所有推送均失败")
    return pushed
