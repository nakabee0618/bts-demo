"""候補一覧（一覧モジュール）。お得な順に並べ、カードで価格と判定を表示する。並び替えは お得順／価格順／評価順。"""
from __future__ import annotations

import streamlit as st

from models import CATEGORIES, Menu
from placeholder import image_url
from pricing import PriceResult, best_result
from search import Condition, is_new, rating_summary, representative_prices

SORTS = {"お得順": "diff", "価格が安い順": "price", "評価が高い順": "rating"}


def sort_key(item: tuple[Menu, PriceResult | None], mode: str, ratings: dict):
    """並べ替えのキー。お得順は差額の大きい順（比較できないものは末尾）。"""
    m, r = item
    if mode == "price":
        return min(p.benefit_price for p in m.plans)
    if mode == "rating":
        return -(ratings.get(m.id, (0, 0))[1])
    return -(r.diff if r and r.diff is not None else -10**9)


def render_results(menus: list[Menu], cond: Condition) -> None:
    """候補一覧の本体。検索画面から呼ばれる。"""
    if not menus:
        st.info("条件に合う施設が見つかりません。エリアや予算を変えてみてください。")
        return
    # ① 実勢価格と口コミの要約をまとめて取る
    prices = representative_prices([m.id for m in menus])
    ratings = rating_summary([m.id for m in menus])
    items = [(m, best_result(m.plans, prices.get(m.id)) if m.category == "stay" else None) for m in menus]
    # ② 並び替え
    c1, c2 = st.columns([3, 1])
    c1.caption(f"{len(items)}件（宿泊は一般サイトの価格と比較）")
    mode = SORTS[c2.selectbox("並び替え", list(SORTS), label_visibility="collapsed")]
    items.sort(key=lambda it: sort_key(it, mode, ratings))
    # ③ カードを描画し、ボタンで詳細へ
    for m, r in items:
        with st.container(border=True):
            c0, c1, c2 = st.columns([1, 3, 1])
            c0.image(image_url(m.photo_url, m.name, m.category, width=200, height=120), use_container_width=True)
            cat_color = {"stay": "violet", "meal": "orange", "leisure": "green"}.get(m.category, "gray")
            badges = f":{cat_color}-badge[{CATEGORIES.get(m.category, m.category)}]"
            if is_new(m.content_updated_at):
                badges += " :red-badge[新着]"
            if r is not None and r.market_price is not None and r.diff <= 0:
                badges += " :red-badge[一般サイトの方が安い]"
            elif r is not None and r.market_price is None:
                badges += " :gray-badge[一般サイトの価格なし]"
            if any(p.coupon_code for p in m.plans):
                badges += " :blue-badge[クーポンあり]"
            cnt, avg = ratings.get(m.id, (0, None))
            c1.markdown(f"#### {m.name}")
            c1.markdown(badges + (f"　★{avg}（{cnt}件）" if cnt else ""))
            if r is not None and r.market_price is not None:
                if r.diff > 0:
                    c1.markdown(f"### :green[{r.diff:,}円お得]" + ("　:gray[目安]" if r.reference else ""))
                    c1.markdown(f"福利厚生 **{r.benefit_price:,}円**　:gray[（一般サイト {r.market_price:,}円）]")
                else:
                    c1.markdown(f"福利厚生 **{r.benefit_price:,}円**　:gray[（一般サイト {r.market_price:,}円）]")
            else:
                cheapest = min(m.plans, key=lambda p: p.benefit_price)
                c1.markdown(f"福利厚生 **{cheapest.benefit_price:,}円〜**")
            if c2.button("詳細を見る", key=f"detail-{m.id}"):
                st.session_state["menu_id"] = m.id
                st.session_state["page"] = "detail"
                st.rerun()
