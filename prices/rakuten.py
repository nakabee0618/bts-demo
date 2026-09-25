"""実勢価格の取得（B2）。楽天トラベルAPI（空室検索）で宿の最安料金を取る。

- アプリIDが未設定、または hotel_ref が楽天のホテル番号（数字）でない場合はダミー価格を返す
- 失敗時は例外を投げ、呼び出し側（update.py）が再試行と停止を判断する
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

import requests

API_URL = "https://app.rakuten.co.jp/services/api/Travel/VacantHotelSearch/20170426"
TIMEOUT = 10


@dataclass
class Fetched:
    price: int
    source: str
    source_url: Optional[str]


def is_rakuten_ref(hotel_ref: Optional[str]) -> bool:


    """hotel_ref が楽天のホテル番号（数字）かどうか。"""
    return bool(hotel_ref) and hotel_ref.isdigit()


def fetch_price(hotel_ref: str, checkin: date, nights: int, adults: int, application_id: str = "") -> Fetched:
    """宿・日程・人数で最安の総額を返す。APIが使えない条件ではダミー。"""
    # ① アプリIDがない、または楽天のホテル番号でなければダミー価格
    if not application_id or not is_rakuten_ref(hotel_ref):
        return dummy_price(hotel_ref, checkin, nights, adults)
    # ② 空室検索APIを呼ぶ（宿・日程・人数）
    params = {
        "applicationId": application_id,
        "format": "json",
        "hotelNo": hotel_ref,
        "checkinDate": checkin.isoformat(),
        "checkoutDate": (checkin + timedelta(days=nights)).isoformat(),
        "adultNum": adults,
        "responseType": "small",
    }
    r = requests.get(API_URL, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    # ③ 応答から部屋ごとの合計料金を集め、最安を取る
    prices = []
    for h in data.get("hotels", []):
        for part in h.get("hotel", []):
            for rp in part.get("roomInfo", []) if isinstance(part, dict) else []:
                total = (rp.get("dailyCharge") or {}).get("total")
                if total:
                    prices.append(int(total))
    # ④ 価格がなければ失敗として例外にする
    if not prices:
        raise ValueError("no vacant room / price")
    url = next((p["hotelBasicInfo"]["hotelInformationUrl"] for h in data.get("hotels", []) for p in h.get("hotel", []) if "hotelBasicInfo" in p), None)
    return Fetched(min(prices), "rakuten_api", url)


def dummy_price(hotel_ref: Optional[str], checkin: date, nights: int, adults: int) -> Fetched:
    """決定的なダミー価格。同じ入力なら同じ値。土曜は2割高。"""
    # ① 宿IDから決定的な基準価格を作る（16,000〜41,000円）
    seed = int(hashlib.md5(f"{hotel_ref}".encode()).hexdigest(), 16)
    base = 16000 + (seed % 26) * 1000          # 16,000〜41,000円（2名1泊）
    # ② 1人あたり×人数×泊数。土曜は2割高
    per_adult = base / 2
    price = per_adult * adults * nights
    if checkin.weekday() == 5:
        price *= 1.2
    return Fetched(int(round(price / 100) * 100), "dummy", None)
