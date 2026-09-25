"""検索（C2）。条件を検証し、メニューとプランを絞り込む。DBアクセスは repository 関数にまとめる。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from db import table
from models import Area, MarketPrice, Menu, Plan


@dataclass
class Condition:
    area_id: Optional[str]
    category: Optional[str]
    checkin: Optional[date]
    adults: int
    budget: Optional[int]


def validate(cond: Condition) -> Optional[str]:
    """入力の検証。問題があれば理由、なければ None。"""
    # ① 人数は1以上
    if cond.adults < 1:
        return "人数は1人以上で入力してください"
    # ② 日程は今日以降
    if cond.checkin and cond.checkin < date.today():
        return "宿泊日は今日以降を選んでください"
    # ③ 予算は0以上
    if cond.budget is not None and cond.budget < 0:
        return "予算は0以上で入力してください"
    return None


def list_areas() -> list[Area]:


    """エリアの一覧（表示順）。"""
    rows = table("areas").select("id,code,name,sort").order("sort").execute().data
    return [Area.from_row(r) for r in rows]


def search(tenant_id: str, cond: Condition) -> list[Menu]:
    """条件に合うメニュー（プラン付き）を返す。予算はプランの福利厚生価格で判定する。"""
    # ① メニューをテナント・エリア・カテゴリで絞る
    q = table("menus").select("*").eq("tenant_id", tenant_id).is_("deleted_at", "null")
    if cond.area_id:
        q = q.eq("area_id", cond.area_id)
    if cond.category:
        q = q.eq("category", cond.category)
    menus = [Menu.from_row(r) for r in q.order("name").execute().data]
    if not menus:
        return []
    # ② 該当メニューのプランをまとめて取り、予算（福利厚生価格）で絞る
    ids = [m.id for m in menus]
    plan_rows = table("plans").select("*").in_("menu_id", ids).is_("deleted_at", "null").execute().data
    by_menu: dict[str, list[Plan]] = {}
    for r in plan_rows:
        p = Plan.from_row(r)
        if cond.budget is not None and p.benefit_price > cond.budget:
            continue
        by_menu.setdefault(p.menu_id, []).append(p)
    # ③ プランが残ったメニューだけを返す
    result = []
    for m in menus:
        m.plans = by_menu.get(m.id, [])
        if m.plans:
            result.append(m)
    return result


def representative_prices(menu_ids: list[str]) -> dict[str, MarketPrice]:
    """メニューごとの代表日程の実勢価格。なければ含まれない。"""
    if not menu_ids:
        return {}
    rows = table("market_prices").select("*").in_("menu_id", menu_ids).eq("is_representative", True).execute().data
    return {r["menu_id"]: MarketPrice.from_row(r) for r in rows}


def get_menu(menu_id: str) -> Optional[Menu]:


    """メニュー1件とそのプラン（福利厚生価格の安い順）。"""
    rows = table("menus").select("*").eq("id", menu_id).limit(1).execute().data
    if not rows:
        return None
    m = Menu.from_row(rows[0])
    m.plans = [Plan.from_row(r) for r in table("plans").select("*").eq("menu_id", menu_id).is_("deleted_at", "null").order("benefit_price").execute().data]
    return m


NEW_DAYS = 14


def is_new(content_updated_at: Optional[str]) -> bool:
    """内容の更新日が NEW_DAYS 日以内なら新着。"""
    if not content_updated_at:
        return False
    return date.fromisoformat(str(content_updated_at)[:10]) >= date.today() - timedelta(days=NEW_DAYS)


def spots_by_area(area_id: Optional[str]) -> list[dict]:
    """エリアの周辺情報（食事・レジャー）。共通＋自テナントのもの。"""
    if not area_id:
        return []
    return table("spots").select("*").eq("area_id", area_id).order("kind").execute().data


def rating_summary(menu_ids: list[str]) -> dict[str, tuple[int, float]]:
    """メニューごとの口コミ件数と平均。並び替え（評価順）と一覧表示に使う。"""
    if not menu_ids:
        return {}
    rows = table("posts").select("menu_id, rating").in_("menu_id", menu_ids).eq("hidden", False).is_("deleted_at", "null").execute().data
    acc: dict[str, list[int]] = {}
    for r in rows:
        acc.setdefault(r["menu_id"], []).append(int(r["rating"]))
    return {k: (len(v), round(sum(v) / len(v), 1)) for k, v in acc.items()}


def all_stay_menus(tenant_id: str) -> list[Menu]:
    """ランキング用: 宿泊メニュー全件（プラン付き）。"""
    return search(tenant_id, Condition(None, "stay", None, 2, None))


def recent_posts(tenant_id: str, limit: int = 3) -> list[dict]:
    """最近の口コミ（施設名つき）。"""
    rows = table("posts").select("*, users(name)").eq("tenant_id", tenant_id).eq("hidden", False).is_("deleted_at", "null").order("created_at", desc=True).limit(limit).execute().data
    ids = list({r["menu_id"] for r in rows})
    names = {m["id"]: m["name"] for m in table("menus").select("id,name").in_("menu_id" if False else "id", ids).execute().data} if ids else {}
    for r in rows:
        r["menu_name"] = names.get(r["menu_id"], "")
    return rows


def monthly_usage(tenant_id: str) -> dict[str, int]:
    """今月のクーポン利用数と口コミ数。"""
    start = date.today().replace(day=1).isoformat()
    coupons = table("activity_logs").select("id, occurred_at").eq("tenant_id", tenant_id).eq("kind", "coupon").execute().data
    posts = table("posts").select("id, created_at").eq("tenant_id", tenant_id).is_("deleted_at", "null").execute().data
    return {"coupons": sum(1 for r in coupons if str(r["occurred_at"])[:10] >= start), "posts": sum(1 for r in posts if str(r["created_at"])[:10] >= start)}
