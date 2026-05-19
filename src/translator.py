from typing import Dict, List

import requests


TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"
TRANSLATE_CACHE: Dict[str, str] = {}


def _split_text(text: str, chunk_size: int = 1800) -> List[str]:
    chunks: List[str] = []
    current = ""
    for sentence in text.replace("\n", " ").split(". "):
        sentence = sentence.strip()
        if not sentence:
            continue
        if current and len(current) + len(sentence) + 2 > chunk_size:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current}. {sentence}" if current else sentence
    if current:
        chunks.append(current)
    return chunks or [text]


def translate_to_chinese(text: str, timeout: int = 10) -> str:
    """Translate text into Simplified Chinese using Google's public translate endpoint."""
    text = (text or "").strip()
    if not text:
        return ""
    if text in TRANSLATE_CACHE:
        return TRANSLATE_CACHE[text]

    translated_chunks: List[str] = []
    for chunk in _split_text(text):
        try:
            resp = requests.get(
                TRANSLATE_URL,
                params={
                    "client": "gtx",
                    "sl": "auto",
                    "tl": "zh-CN",
                    "dt": "t",
                    "q": chunk,
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            translated = "".join(part[0] for part in data[0] if part and part[0])
            translated_chunks.append(translated.strip())
        except Exception as e:
            print(f"[翻译] 翻译失败，保留原文: {e}")
            translated_chunks.append(chunk)

    result = " ".join(part for part in translated_chunks if part).strip()
    TRANSLATE_CACHE[text] = result
    return result
