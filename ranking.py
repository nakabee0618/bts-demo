"""お得ランキングと新着（差額計算・ランキング表示モジュール）。検索前の画面と一覧で使う。"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from models import Menu
from pricing import PriceResult, best_result
from search import Condition, representative_prices, search

NEW_DAYS = 14


def is_new(content_updated_at: Optional[str]) -> bool:
    """内容の更新日が NEW_DAYS 日以内なら新着。"""
    if not content_updated_at:
        return False
    return date.fromisoformat(str(content_updated_at)[:10]) >= date.today() - timedelta(days=NEW_DAYS)


def all_stay_menus(tenant_id: str) -> list[Menu]:
    """ランキング用: 宿泊メニュー全件（プラン付き）。"""
    return search(tenant_id, Condition(None, "stay", None, 2, None))


def top_deals(tenant_id: str, limit: int = 5) -> list[tuple[Menu, PriceResult]]:
    """差額の大きい順に上位を返す。得でないもの・比較できないものは入れない。"""
    # ① 宿泊メニューと一般サイトの価格をまとめて取る
    menus = all_stay_menus(tenant_id)
    prices = representative_prices([m.id for m in menus])
    # ② メニューごとに最も得なプランを選び、得なものだけ残す
    ranked = [(m, best_result(m.plans, prices.get(m.id))) for m in menus]
    ranked = [(m, r) for m, r in ranked if r and r.diff is not None and r.diff > 0]
    # ③ 差額の大きい順に並べて上位を返す
    ranked.sort(key=lambda x: -x[1].diff)
    return ranked[:limit]


def new_menus(tenant_id: str, limit: int = 5) -> list[Menu]:
    """新着のメニュー（宿泊）。"""
    return [m for m in all_stay_menus(tenant_id) if is_new(m.content_updated_at)][:limit]
