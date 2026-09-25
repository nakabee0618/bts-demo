"""周辺情報のクローリング（価格取得モジュール）。

観光情報サイトなどの公開ページから、食事・レジャーの名称・説明・URLを集めて spots に保存する。
- 対象ページは crawl_targets.csv（area_code, kind, url）で指定する
- ページ構造はサイトごとに違うため、抽出は「見出しとリンク」の汎用ルール。精度が要る場合はサイトごとの関数を足す
- 使い方: python -m prices.crawl_spots
- 取得間隔を空け、robots.txt と利用規約を確認してから使う
"""
from __future__ import annotations

import csv
import re
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path

import requests
from supabase import create_client

ROOT = Path(__file__).resolve().parent.parent
INTERVAL_SEC = 2.0
TIMEOUT = 10
HEADERS = {"User-Agent": "bts-app-crawler/0.1 (team project)"}


def fetch_html(url: str) -> str:
    """ページを取得して文字列で返す。失敗は例外。"""
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return r.text


def extract_spots(html: str, base_url: str, limit: int = 20) -> list[dict]:
    """見出し（h2/h3）とその直後のリンクから、名称・説明・URLを抜く汎用ルール。"""
    spots = []
    # ① 見出しの文字列と、見出し以降のリンクを拾う
    for m in re.finditer(r"<h[23][^>]*>(.*?)</h[23]>(.*?)(?=<h[23][^>]*>|</body>|$)", html, flags=re.S | re.I):
        name = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if not name or len(name) > 40:
            continue
        body = m.group(2)[:600]
        link = re.search(r'href="([^"]+)"', body)
        url = link.group(1) if link else base_url
        if url.startswith("/"):
            url = re.match(r"https?://[^/]+", base_url).group(0) + url
        desc = re.sub(r"<[^>]+>", " ", body)
        desc = re.sub(r"\s+", " ", desc).strip()[:80]
        spots.append({"name": name, "description": desc, "url": url})
        if len(spots) >= limit:
            break
    return spots


def main() -> None:
    """crawl_targets.csv の各ページを取得し、spots に保存する。"""
    secrets = tomllib.loads((ROOT / ".streamlit" / "secrets.toml").read_text(encoding="utf-8"))
    c = create_client(secrets["supabase"]["url"], secrets["supabase"]["anon_key"]).schema("bts")
    areas = {a["code"]: a["id"] for a in c.table("areas").select("id,code").is_("tenant_id", "null").execute().data}
    targets_path = ROOT / "seed" / "crawl_targets.csv"
    if not targets_path.exists():
        print("seed/crawl_targets.csv がありません（area_code, kind, url）"); return
    with open(targets_path, newline="", encoding="utf-8") as f:
        targets = list(csv.DictReader(f))
    # ② 1ページずつ取得し、抽出して保存
    for t in targets:
        try:
            html = fetch_html(t["url"])
        except Exception as e:
            print(f"  失敗 {t['url']}: {e}"); time.sleep(INTERVAL_SEC); continue
        spots = extract_spots(html, t["url"])
        for s in spots:
            c.table("spots").insert({"tenant_id": None, "area_id": areas.get(t["area_code"]), "kind": t["kind"], "name": s["name"], "description": s["description"], "url": s["url"], "source": t["url"], "fetched_at": datetime.now(timezone.utc).isoformat()}).execute()
        print(f"  {t['area_code']}/{t['kind']}: {len(spots)}件")
        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
