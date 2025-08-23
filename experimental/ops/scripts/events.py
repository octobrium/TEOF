#!/usr/bin/env python3
import json, re, time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from xml.etree import ElementTree as ET

UA = {"User-Agent": "teof/events"}

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def http_get(url, timeout=8):
    req = Request(url, headers=UA)
    with urlopen(req, timeout=timeout) as r:
        return r.read()

def rss_items(xml_bytes):
    try:
        root = ET.fromstring(xml_bytes)
        for it in root.iter():
            tag = it.tag.lower()
            if tag.endswith("item") or tag.endswith("entry"):
                title = (it.findtext("title") or "").strip()
                link = (it.findtext("link") or "").strip()
                if not link:
                    ln = it.find("link")
                    if ln is not None and ln.get("href"):
                        link = ln.get("href")
                yield {"title": title, "link": link}
    except Exception:
        return

def load_cfg(path):
    try:
        return json.loads(open(path, "r", encoding="utf-8").read())
    except Exception:
        return {"feeds": [], "rules": []}

def scan(cfg):
    out = []
    rules = cfg.get("rules", [])
    for f in cfg.get("feeds", []):
        url = f.get("url")
        if not url:
            continue
        try:
            raw = http_get(url)
            items = list(rss_items(raw))
            for it in items:
                title = it.get("title","")
                for r in rules:
                    pat = r.get("pattern")
                    if not pat:
                        continue
                    if re.search(pat, title, flags=re.I):
                        out.append({
                            "label": f"EVT {r.get('tag','event')} ({r.get('severity','info')})",
                            "value": title,
                            "timestamp_utc": now_iso(),
                            "source": it.get("link") or url,
                            "provenance": "auto:rss",
                            "volatile": True,
                            "stale_labeled": False,
                            "meta": {"feed": url, "rule": r}
                        })
                        break
        except Exception:
            continue
        time.sleep(0.2)
    return out

def main():
    cfg = load_cfg("config/events.json")
    print(json.dumps(scan(cfg), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
