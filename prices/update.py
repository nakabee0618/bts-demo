"""対象メニューの実勢価格をまとめて取得し、market_prices と fetch_logs に保存する（B2）。

使い方: python -m prices.update [--checkin 2026-11-22] [--nights 1] [--adults 2]
- 宿泊（category=stay）で hotel_ref のあるメニューが対象
- 連続 STOP_AFTER 回失敗したら停止し、fetch_logs に stopped=true を残す
- 取得した価格は「代表日程」として保存する（is_representative=true）
"""
from __future__ import annotations

import argparse
import time
import tomllib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from supabase import create_client

from prices.rakuten import fetch_price

ROOT = Path(__file__).resolve().parent.parent
STOP_AFTER = 5
RETRY = 2
INTERVAL_SEC = 1.0


def next_saturday(today: date | None = None) -> date:


    """次の土曜の日付（代表日程の既定）。"""
    d = today or date.today()
    return d + timedelta(days=(5 - d.weekday()) % 7 or 7)


def main() -> None:


    """対象メニューの実勢価格を取得し、market_prices と fetch_logs に保存する。"""
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkin", type=date.fromisoformat, default=next_saturday())
    ap.add_argument("--nights", type=int, default=1)
    ap.add_argument("--adults", type=int, default=2)
    args = ap.parse_args()

    # ① 接続情報と楽天のアプリIDを読む
    secrets = tomllib.loads((ROOT / ".streamlit" / "secrets.toml").read_text(encoding="utf-8"))
    c = create_client(secrets["supabase"]["url"], secrets["supabase"]["anon_key"]).schema("bts")
    app_id = secrets.get("rakuten", {}).get("application_id", "")

    # ② 対象（宿泊で hotel_ref のあるメニュー）を取り、取得ログを開始する
    menus = c.table("menus").select("id,tenant_id,hotel_ref,name").eq("category", "stay").not_.is_("hotel_ref", "null").is_("deleted_at", "null").execute().data
    if not menus:
        print("対象がありません"); return
    tenant_id = menus[0]["tenant_id"]
    log = c.table("fetch_logs").insert({"tenant_id": tenant_id, "started_at": datetime.now(timezone.utc).isoformat(), "target_count": len(menus)}).execute().data[0]

    # ③ 1件ずつ取得。失敗は再試行、連続失敗で停止
    ok = ng = streak = 0
    stopped = False
    for m in menus:
        fetched = None
        for _ in range(RETRY + 1):
            try:
                fetched = fetch_price(m["hotel_ref"], args.checkin, args.nights, args.adults, app_id)
                break
            except Exception as e:
                last = e
                time.sleep(INTERVAL_SEC)
        if fetched is None:
            ng += 1; streak += 1
            print(f"  失敗 {m['name']}: {last}")
            if streak >= STOP_AFTER:
                stopped = True; print("連続失敗のため停止"); break
            continue
        streak = 0; ok += 1
        # ④ 代表日程のフラグを付け替えて保存する
        c.table("market_prices").update({"is_representative": False}).eq("menu_id", m["id"]).execute()
        c.table("market_prices").insert({
            "menu_id": m["id"], "hotel_ref": m["hotel_ref"], "checkin": args.checkin.isoformat(), "nights": args.nights,
            "adults": args.adults, "children": 0, "price": fetched.price, "source": fetched.source, "source_url": fetched.source_url,
            "fetched_at": datetime.now(timezone.utc).isoformat(), "is_representative": True,
        }).execute()
        print(f"  {m['name']}: {fetched.price:,}円 ({fetched.source})")
        time.sleep(INTERVAL_SEC)

    # ⑤ 取得ログを締める
    c.table("fetch_logs").update({"finished_at": datetime.now(timezone.utc).isoformat(), "success_count": ok, "fail_count": ng, "stopped": stopped}).eq("id", log["id"]).execute()
    print(f"完了: 成功 {ok} / 失敗 {ng} / 停止 {stopped}")


if __name__ == "__main__":
    main()
