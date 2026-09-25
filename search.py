"""検索（C2）。条件を検証し、メニューとプランを絞り込む。DBアクセスは repository 関数にまとめる。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
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
