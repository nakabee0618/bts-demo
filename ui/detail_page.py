"""候補詳細の枠（共通）。見出しとタブの切り替えだけを持ち、各タブの中身は担当ごとのファイルに任せる。"""
from __future__ import annotations

import streamlit as st

from auth import require_login
from models import CATEGORIES
from placeholder import image_url
from search import get_menu
from ui.price_tab import render_price_tab
from ui.review_tab import render_review_tab
from ui.spots_tab import render_spots_tab


def render() -> None:
    """候補詳細。価格比較／プラン・条件／口コミ／周辺の4タブ。app.py から呼ばれる。"""
    user = require_login()
    # ① セッションの menu_id からメニューとプランを取る
    menu_id = st.session_state.get("menu_id")
    menu = get_menu(menu_id) if menu_id else None
    if menu is None:
        st.info("一覧から施設を選んでください。")
        return
    # ② 見出し（戻る・画像・施設名・バッジ・住所・説明）
    if st.button("← 一覧に戻る"):
        st.session_state["page"] = "search"; st.rerun()
    h1, h2 = st.columns([1, 3])
    h1.image(image_url(menu.photo_url, menu.name, menu.category), use_container_width=True)
    h2.subheader(menu.name)
    cat_color = {"stay": "violet", "meal": "orange", "leisure": "green"}.get(menu.category, "gray")
    h2.markdown(f":{cat_color}-badge[{CATEGORIES.get(menu.category, menu.category)}]" + (" :blue-badge[クーポンあり]" if any(p.coupon_code for p in menu.plans) else ""))
    h2.caption(menu.address or "")
    if menu.description:
        h2.write(menu.description)
    # ③ 4タブ。中身はそれぞれの担当ファイルが描く
    tab1, tab2, tab3, tab4 = st.tabs(["価格比較", "プラン・条件", "口コミ", "周辺"])
    with tab1:
        render_price_tab(user, menu)
    with tab2:
        _render_conditions(menu)
    with tab3:
        render_review_tab(user, menu)
    with tab4:
        render_spots_tab(menu)


def _render_conditions(menu) -> None:
    """プラン・条件タブ。プランの内容と利用条件を並べる。"""
    for p in menu.plans:
        st.write(f"- {p.name}: 部屋 {p.room_type or '—'} ／ 食事 {p.meal or '—'} ／ {p.adults or 2}名・{p.nights}泊の料金")
    st.write(f"利用回数の上限: {menu.usage_limit or '—'}")
    st.write(f"家族の範囲: {menu.family_scope or '—'}")
    st.write(f"キャンセル条件: {menu.cancel_policy or '—'}")
    if menu.procedure:
        st.write(f"利用手順: {menu.procedure}")
