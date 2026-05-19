import re
from html import unescape
from typing import Dict, List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.models import NewsItem
from src.translator import translate_to_chinese


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
MIN_SUMMARY_LENGTH = 300
MAX_SUMMARY_LENGTH = 620


def clean_text(value: str) -> str:
    """Convert HTML-ish text to a compact plain-text summary."""
    if not value:
        return ""
    soup = BeautifulSoup(value, "html.parser")
    text = soup.get_text(" ", strip=True)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def clamp_text(value: str, limit: int = MAX_SUMMARY_LENGTH) -> str:
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


def normalize_image_url(image_url: str, base_url: str = "") -> str:
    """Return an absolute HTTP(S) image URL and drop formats that rarely render in WeChat."""
    if not image_url:
        return ""
    absolute_url = urljoin(base_url, image_url.strip())
    parsed = urlparse(absolute_url)
    if parsed.scheme not in ("http", "https"):
        return ""
    if parsed.path.lower().endswith(".svg"):
        return ""
    return absolute_url


def prepare_image_for_push(item: NewsItem) -> None:
    """Normalize image links before optional GitHub Actions image caching."""
    image_url = normalize_image_url(item.image_url, item.image_source_url or item.url)
    if not image_url:
        item.image_url = ""
        item.original_image_url = ""
        return

    item.original_image_url = image_url
    item.image_url = image_url


def _meta_content(soup: BeautifulSoup, *keys: str) -> str:
    for key in keys:
        node = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
        if node and node.get("content"):
            return node["content"].strip()
    return ""


def extract_article_text(soup: BeautifulSoup, limit: int = 1200) -> str:
    """Extract readable article paragraphs so pushed summaries are not too thin."""
    for node in soup(["script", "style", "noscript", "svg"]):
        node.decompose()

    candidates = soup.select(
        "article p, main p, .article p, .content p, .post-content p, "
        ".story-body p, .article-content p, p"
    )
    paragraphs: List[str] = []
    seen = set()
    for node in candidates:
        text = clean_text(node.get_text(" ", strip=True))
        if len(text) < 35:
            continue
        lowered = text.lower()
        if any(skip in lowered for skip in ("cookie", "subscribe", "sign up", "copyright")):
            continue
        if text in seen:
            continue
        seen.add(text)
        paragraphs.append(text)
        if len(" ".join(paragraphs)) >= limit:
            break

    return clamp_text(" ".join(paragraphs), limit)


def expand_short_summary(item: NewsItem) -> str:
    """Add useful context when sources expose only a short blurb."""
    summary = clean_text(item.summary)
    if len(summary) >= MIN_SUMMARY_LENGTH:
        return clamp_text(summary)

    category = "国际新闻" if item.category == "international" else "国内新闻"
    context = (
        f"这条{category}来自{item.source}，标题为“{item.title}”。"
        "目前可抓取到的公开正文信息有限，但它进入今日 TOP 列表，说明相关议题正在获得较高关注。"
        "阅读时建议重点看三点：事件本身出现了什么新进展，相关机构或当事方是否已经回应，"
        "以及这件事接下来可能带来的政策、市场或社会影响。"
    )
    combined = f"{summary} {context}".strip() if summary else context
    return clamp_text(combined)


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

    article_text = extract_article_text(soup)
    summary = article_text if len(article_text) > len(clean_text(description)) else clean_text(description)

    final_url = resp.url or url
    absolute_image_url = normalize_image_url(image_url, final_url)
    return {
        "summary": summary,
        "image_url": absolute_image_url,
        "image_source_url": final_url,
    }


def enrich_items(items: List[NewsItem]) -> List[NewsItem]:
    """Fill missing summaries/images after ranking, limiting network work to pushed items."""
    for item in items:
        metadata: Dict[str, str] = fetch_article_metadata(item.url)

        metadata_summary = metadata.get("summary", "")
        if not item.summary or len(clean_text(item.summary)) < 180:
            item.summary = metadata_summary or item.summary
        elif metadata_summary and len(metadata_summary) > len(clean_text(item.summary)):
            item.summary = metadata.get("summary", "")

        if not item.image_url:
            item.image_url = metadata.get("image_url", "")
            item.image_source_url = metadata.get("image_source_url", "")

        if item.category == "international":
            item.title = translate_to_chinese(item.title)
            item.summary = clamp_text(translate_to_chinese(item.summary))

        item.summary = expand_short_summary(item) or (
            f"{item.title}。该条来自{item.source}，当前热度排名靠前，"
            "反映了今天较高的公共关注度，建议结合来源链接查看完整背景。"
        )
        prepare_image_for_push(item)

    return items
