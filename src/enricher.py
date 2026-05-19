import re
from html import unescape
from typing import Dict, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.models import NewsItem


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def clean_text(value: str) -> str:
    """Convert HTML-ish text to a compact plain-text summary."""
    if not value:
        return ""
    soup = BeautifulSoup(value, "html.parser")
    text = soup.get_text(" ", strip=True)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def clamp_text(value: str, limit: int = 220) -> str:
    text = clean_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def extract_image_from_html(html: str, base_url: str = "") -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    img = soup.find("img")
    if not img:
        return ""
    src = img.get("src") or img.get("data-src") or img.get("data-original")
    return urljoin(base_url, src) if src else ""


def _meta_content(soup: BeautifulSoup, *keys: str) -> str:
    for key in keys:
        node = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
        if node and node.get("content"):
            return node["content"].strip()
    return ""


def fetch_article_metadata(url: str, timeout: int = 8) -> Dict[str, str]:
    """Fetch article page metadata for summary and a directly related image."""
    if not url or not url.startswith(("http://", "https://")):
        return {}

    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
    except Exception as e:
        print(f"[内容补全] 获取页面失败 {url}: {e}")
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")
    description = _meta_content(
        soup,
        "og:description",
        "twitter:description",
        "description",
    )
    image_url = _meta_content(
        soup,
        "og:image",
        "og:image:url",
        "twitter:image",
        "twitter:image:src",
    )

    if not image_url:
        image_link = soup.find("link", attrs={"rel": lambda rel: rel and "image_src" in rel})
        if image_link and image_link.get("href"):
            image_url = image_link["href"].strip()

    if not image_url:
        article_img = soup.select_one("article img, main img")
        if article_img:
            image_url = (
                article_img.get("src")
                or article_img.get("data-src")
                or article_img.get("data-original")
                or ""
            ).strip()

    final_url = resp.url or url
    return {
        "summary": clean_text(description),
        "image_url": urljoin(final_url, image_url) if image_url else "",
        "image_source_url": final_url,
    }


def enrich_items(items: List[NewsItem]) -> List[NewsItem]:
    """Fill missing summaries/images after ranking, limiting network work to pushed items."""
    for item in items:
        metadata: Dict[str, str] = {}
        if not item.summary or not item.image_url:
            metadata = fetch_article_metadata(item.url)

        if not item.summary:
            item.summary = metadata.get("summary", "")
        if not item.image_url:
            item.image_url = metadata.get("image_url", "")
            item.image_source_url = metadata.get("image_source_url", "")

        item.summary = clamp_text(item.summary) or (
            f"{item.title}。该条来自{item.source}，当前热度排名靠前，"
            "反映了今天较高的公共关注度，建议结合来源链接查看完整背景。"
        )

    return items
