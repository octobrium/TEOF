#!/usr/bin/env python3
# Lightweight, deterministic text extraction with graceful fallbacks.

from __future__ import annotations
import re, json, hashlib
from dataclasses import dataclass
from typing import List, Optional, Tuple

# Soft deps (each optional)
try:
    import requests  # type: ignore
except Exception:
    requests = None  # type: ignore

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:
    BeautifulSoup = None  # type: ignore

try:
    from readability import Document  # type: ignore
except Exception:
    Document = None  # type: ignore

try:
    import trafilatura  # type: ignore
except Exception:
    trafilatura = None  # type: ignore


@dataclass
class ExtractResult:
    url: str
    title: str
    text: str
    links: List[str]
    meta: dict
    extractor: str
    confidence: float
    sha256: str


def _sha256_bytes(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()


def _links_from_html(html: str) -> List[str]:
    if not BeautifulSoup:
        return []
    soup = BeautifulSoup(html, "lxml")
    out = []
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if href and href.startswith(("http://", "https://")):
            out.append(href.strip())
    # Dedup, preserve order
    seen, uniq = set(), []
    for h in out:
        if h not in seen:
            uniq.append(h); seen.add(h)
    return uniq[:64]


def _clean_whitespace(s: str) -> str:
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\r?\n\s*\n\s*\n+", "\n\n", s)
    return s.strip()


def fetch_url(url: str, timeout: int = 15) -> Tuple[str, bytes]:
    if not requests:
        raise RuntimeError("requests not installed (pip install requests)")
    headers = {
        "User-Agent": "TEOF-Extractor/1.0 (+deterministic; provenance)"
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    content = r.content or b""
    # Try to decode as utf-8 with fallback
    try:
        html = content.decode("utf-8")
    except UnicodeDecodeError:
        html = content.decode("latin-1", errors="replace")
    return html, content


def extract(url: str) -> ExtractResult:
    """
    Deterministic extractor chain:
      1) trafilatura (if available)
      2) readability-lxml (if available)
      3) vanilla BeautifulSoup fallback
    """
    html, raw = fetch_url(url)
    links = _links_from_html(html)
    title = ""
    text = ""
    extractor = "none"
    confidence = 0.2

    # 1) trafilatura
    if trafilatura:
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                txt = trafilatura.extract(downloaded, include_links=False) or ""
                if txt.strip():
                    text = _clean_whitespace(txt)
                    title = trafilatura.extract_metadata(downloaded).title or ""
                    extractor = "trafilatura"
                    confidence = 0.9
        except Exception:
            pass

    # 2) readability
    if not text and Document and BeautifulSoup:
        try:
            doc = Document(html)
            title = (doc.short_title() or "").strip()
            article_html = doc.summary(html_partial=True)
            soup = BeautifulSoup(article_html, "lxml")
            txt = soup.get_text("\n")
            if txt:
                text = _clean_whitespace(txt)
                extractor = "readability"
                confidence = 0.8
        except Exception:
            pass

    # 3) soup fallback
    if not text and BeautifulSoup:
        try:
            soup = BeautifulSoup(html, "lxml")
            # Prefer <article>, fallback to body text
            article = soup.find("article") or soup.body
            if article:
                txt = article.get_text("\n")
                text = _clean_whitespace(txt)
                extractor = "bs4"
                confidence = 0.6
            # title
            if not title:
                t = soup.find("title")
                if t and t.text:
                    title = t.text.strip()
        except Exception:
            pass

    # Guard
    title = title or ""
    text = text or ""

    meta = {
        "content_sha256": _sha256_bytes(raw),
        "length": len(text),
        "has_title": bool(title),
    }
    return ExtractResult(
        url=url,
        title=title,
        text=text,
        links=links,
        meta=meta,
        extractor=extractor,
        confidence=confidence,
        sha256=_sha256_bytes(text.encode("utf-8")),
    )


if __name__ == "__main__":
    import argparse, sys, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    args = ap.parse_args()
    try:
        res = extract(args.url)
        print(json.dumps(res.__dict__, indent=2))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
