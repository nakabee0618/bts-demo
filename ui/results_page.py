"""候補一覧（C3）。得な順に並べ、カードで4価格と判定を表示する。"""
from __future__ import annotations

import streamlit as st

from models import CATEGORIES, Menu
from placeholder import image_url
from pricing import PriceResult, best_result
from search import Condition, representative_prices


def sort_key(item: tuple[Menu, PriceResult | None]):


    """並べ替えのキー。差額の大きい順、比較不可は末尾。"""
    r = item[1]
    return -(r.diff if r and r.diff is not None else -10**9)


def render_results(menus: list[Menu], cond: Condition) -> None:


    """候補一覧。得な順のカードと詳細へのボタン。"""
    if not menus:
        st.info("条件に合うメニューがありません。エリアや予算を変えてみてください。")
        return
    # ① 代表日程の実勢価格をまとめて取る
    prices = representative_prices([m.id for m in menus])
    # ② 宿泊は代表の結果を計算し、差額の大きい順に並べる
    items = [(m, best_result(m.plans, prices.get(m.id)) if m.category == "stay" else None) for m in menus]
    items.sort(key=sort_key)
    st.caption(f"{len(items)}件。得な順に並んでいます（宿泊のみ実勢価格と比較）")
    # ③ カードを描画し、ボタンで詳細へ
    for m, r in items:
        with st.container(border=True):
            c0, c1, c2 = st.columns([1, 3, 1])
            c0.image(image_url(m.photo_url, m.name, m.category, width=200, height=120), use_container_width=True)
            c1.markdown(f"**{m.name}**　{CATEGORIES.get(m.category, m.category)}")
            if r is not None:
                c1.write(f"元値 {r.list_price:,}円 ／ 福利厚生 {r.benefit_price:,}円 ／ 実勢 {('%s円' % format(r.market_price, ',')) if r.market_price is not None else '—'}")
                if r.diff is not None:
                    color = "green" if r.judgement == "good" else "red"
                    c1.markdown(f":{color}[**{r.label}**]　差額 {r.diff:+,}円")
                else:
                    c1.markdown(f":gray[**{r.label}**]")
            else:
                cheapest = min(m.plans, key=lambda p: p.benefit_price)
                c1.write(f"福利厚生価格 {cheapest.benefit_price:,}円〜（比較なし）")
            if c2.button("詳細を見る", key=f"detail-{m.id}"):
                st.session_state["menu_id"] = m.id
                st.session_state["page"] = "detail"
                st.rerun()
