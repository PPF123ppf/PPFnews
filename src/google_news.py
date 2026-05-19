import json
from functools import lru_cache
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}


def is_google_news_url(url: str) -> bool:
    parsed = urlparse(url or "")
    return parsed.netloc == "news.google.com" and "/articles/" in parsed.path


def _base64_id(url: str) -> str:
    parsed = urlparse(url)
    return parsed.path.rstrip("/").split("/")[-1]


@lru_cache(maxsize=256)
def decode_google_news_url(url: str) -> str:
    """Decode Google News RSS article URLs into the original publisher URL."""
    if not is_google_news_url(url):
        return url

    article_id = _base64_id(url)
    try:
        params = _get_decoding_params(article_id)
        if not params:
            return url
        decoded_url = _decode_with_params(article_id, params["signature"], params["timestamp"])
        return decoded_url or url
    except Exception as e:
        print(f"[Google News] 解码失败 {url}: {e}")
        return url


def _get_decoding_params(article_id: str) -> dict:
    for prefix in ("articles", "rss/articles"):
        resp = requests.get(
            f"https://news.google.com/{prefix}/{article_id}",
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code != 200:
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        node = soup.select_one("c-wiz div[jscontroller][data-n-a-sg][data-n-a-ts]")
        if node:
            return {
                "signature": node.get("data-n-a-sg", ""),
                "timestamp": node.get("data-n-a-ts", ""),
            }
    return {}


def _decode_with_params(article_id: str, signature: str, timestamp: str) -> str:
    payload = [
        "Fbv4je",
        (
            '["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,'
            f'null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,null,0,0,null,0],'
            f'"{article_id}",{timestamp},"{signature}"]'
        ),
    ]
    resp = requests.post(
        "https://news.google.com/_/DotsSplashUi/data/batchexecute",
        headers={
            **HEADERS,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        },
        data=f"f.req={quote(json.dumps([[payload]]))}",
        timeout=10,
    )
    resp.raise_for_status()

    parsed = json.loads(resp.text.split("\n\n", 1)[1])[:-2]
    return json.loads(parsed[0][2])[1]
