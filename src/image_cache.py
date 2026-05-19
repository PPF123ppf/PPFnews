import os
import re
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Iterable, List
from urllib.parse import quote

import requests

from src.models import NewsItem


BEIJING_TZ = timezone(timedelta(hours=8))
MAX_IMAGE_BYTES = 5 * 1024 * 1024
IMAGE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def should_cache_images() -> bool:
    """Only publish image cache URLs when running inside GitHub Actions."""
    return bool(os.getenv("GITHUB_ACTIONS") and os.getenv("GITHUB_REPOSITORY"))


def _safe_filename(value: str, fallback: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-").lower()
    return value[:50] or fallback


def _extension_from_content_type(content_type: str) -> str:
    content_type = content_type.lower()
    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    if "gif" in content_type:
        return ".gif"
    return ".jpg"


def _raw_github_url(path: Path) -> str:
    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.getenv("GITHUB_REF_NAME", "main")
    relative = path.as_posix()
    quoted_path = "/".join(quote(part) for part in relative.split("/"))
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{quoted_path}"


def _download_image(url: str, dest_without_ext: Path) -> Path | None:
    try:
        resp = requests.get(url, headers=IMAGE_HEADERS, timeout=20, stream=True)
        resp.raise_for_status()
    except Exception as e:
        print(f"[图片缓存] 下载失败 {url}: {e}")
        return None

    content_type = resp.headers.get("content-type", "")
    if "image" not in content_type.lower():
        print(f"[图片缓存] 非图片响应 {url}: {content_type}")
        return None

    dest = dest_without_ext.with_suffix(_extension_from_content_type(content_type))
    dest.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    with dest.open("wb") as fh:
        for chunk in resp.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            written += len(chunk)
            if written > MAX_IMAGE_BYTES:
                print(f"[图片缓存] 图片超过 5MB，跳过 {url}")
                try:
                    dest.unlink(missing_ok=True)
                except TypeError:
                    if dest.exists():
                        dest.unlink()
                return None
            fh.write(chunk)

    return dest


def cache_images_for_push(items: Iterable[NewsItem]) -> List[Path]:
    """Download pushed news images into the repo and replace URLs with GitHub raw URLs."""
    if not should_cache_images():
        return []

    date_dir = datetime.now(BEIJING_TZ).strftime("%Y%m%d")
    cached_paths: List[Path] = []
    for index, item in enumerate(items, 1):
        image_url = item.original_image_url or item.image_url
        if not image_url:
            continue

        category = _safe_filename(item.category, "news")
        source = _safe_filename(item.source, "source")
        dest_without_ext = Path("assets") / "news" / date_dir / f"{index:02d}-{category}-{source}"
        cached = _download_image(image_url, dest_without_ext)
        if not cached:
            continue

        item.original_image_url = image_url
        item.image_url = _raw_github_url(cached)
        cached_paths.append(cached)

    return cached_paths


def commit_cached_images(paths: List[Path]) -> None:
    """Commit and push cached images before sending the message that references them."""
    if not paths or not should_cache_images():
        return

    try:
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
        subprocess.run(
            ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
            check=True,
        )
        subprocess.run(["git", "add", "assets/news"], check=True)
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"])
        if diff.returncode == 0:
            return
        subprocess.run(
            ["git", "commit", "-m", "chore: cache news images [skip ci]"],
            check=True,
        )
        subprocess.run(["git", "push"], check=True)
    except Exception as e:
        print(f"[图片缓存] 提交图片缓存失败，继续使用原图片链接: {e}")
