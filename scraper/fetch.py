#!/usr/bin/env python3
"""ヤフオクの落札相場（closedsearch）を取得して docs/data/ に保存する。

標準ライブラリのみで動作。GitHub Actions から 1 日 3 回（朝・昼・晩）実行される想定。
"""
import json
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYWORDS = ROOT / "scraper" / "keywords.json"
DATA_DIR = ROOT / "docs" / "data"
HISTORY = DATA_DIR / "history.json"
LATEST = DATA_DIR / "latest.json"

JST = timezone(timedelta(hours=9))
URL = "https://auctions.yahoo.co.jp/closedsearch/closedsearch"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0 Safari/537.36")
MAX_HISTORY = 3 * 365 * 2  # 約2年分


def slot_of(now):
    h = now.hour
    if h < 10:
        return "朝"
    if h < 16:
        return "昼"
    return "晩"


def fetch_listing(query):
    qs = urllib.parse.urlencode({"p": query, "n": 100, "b": 1})
    req = urllib.request.Request(f"{URL}?{qs}", headers={
        "User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})
    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                html = r.read().decode("utf-8", "replace")
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
            if not m:
                raise RuntimeError("__NEXT_DATA__ が見つかりません（ページ構造が変わった可能性）")
            data = json.loads(m.group(1))
            return data["props"]["pageProps"]["initialState"]["search"]["items"]["listing"]
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(5 * (attempt + 1))
    raise last_err


def summarize(kw, listing):
    stats = (listing.get("metadata") or {}).get("statistics") or {}
    items = [i for i in listing.get("items") or [] if (i.get("price") or 0) > 0]
    prices = [i["price"] for i in items]
    return {
        "yahooAvg": stats.get("avgPrice"),          # ヤフオク公式の相場平均（過去約120日）
        "yahooMin": stats.get("minPrice"),
        "yahooMax": stats.get("maxPrice"),
        "total": listing.get("totalResultsAvailable"),
        "recentCount": len(prices),                 # 直近の落札 最大100件
        "recentAvg": round(statistics.mean(prices)) if prices else None,
        "recentMedian": round(statistics.median(prices)) if prices else None,
    }, [{
        "title": i.get("title"),
        "price": i.get("price"),
        "bids": i.get("bidCount"),
        "endTime": i.get("endTime"),
        "image": i.get("imageUrl"),
        "url": f"https://auctions.yahoo.co.jp/jp/auction/{i.get('auctionId')}",
    } for i in items[:20]]


def main():
    keywords = json.loads(KEYWORDS.read_text(encoding="utf-8"))
    now = datetime.now(JST)
    history = json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() else []

    entry = {"time": now.isoformat(timespec="seconds"), "slot": slot_of(now), "data": {}}
    latest = {"updated": entry["time"], "slot": entry["slot"], "keywords": keywords, "items": {}}
    errors = []
    for n, kw in enumerate(keywords):
        if n:
            time.sleep(3)  # サーバーに負荷をかけないよう間隔をあける
        try:
            summary, items = summarize(kw, fetch_listing(kw["query"]))
            entry["data"][kw["id"]] = summary
            latest["items"][kw["id"]] = items
            print(f"[OK] {kw['label']}: 相場平均 ¥{summary['yahooAvg']:,} / 直近平均 ¥{summary['recentAvg']:,}")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{kw['label']}: {e}")
            print(f"[NG] {kw['label']}: {e}", file=sys.stderr)

    if not entry["data"]:
        sys.exit("すべてのキーワードで取得に失敗しました")

    history.append(entry)
    history = history[-MAX_HISTORY:]
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=1), encoding="utf-8")
    LATEST.write_text(json.dumps(latest, ensure_ascii=False, indent=1), encoding="utf-8")
    if errors:
        print("一部失敗:", *errors, sep="\n  ", file=sys.stderr)


if __name__ == "__main__":
    main()
