"""候補詳細（D1）。価格比較・プラン・条件・社員の声の3タブ。クーポンと投稿はここから。"""
from __future__ import annotations

import streamlit as st

from auth import require_login
from coupon import acquire, coupon_text, member_link
from dialogs.post import open_post_dialog
from models import CATEGORIES
from posts import list_by_menu, summary
from placeholder import image_url
from pricing import evaluate
from search import get_menu, representative_prices


def render() -> None:


    """候補詳細。価格比較／プラン・条件／社員の声の3タブ。"""
    user = require_login()
    # ① セッションの menu_id からメニューとプランを取る
    menu_id = st.session_state.get("menu_id")
    menu = get_menu(menu_id) if menu_id else None
    if menu is None:
        st.info("候補一覧から選んでください。")
        return
    if st.button("← 一覧に戻る"):
        st.session_state["page"] = "search"; st.rerun()
    h1, h2 = st.columns([1, 3])
    h1.image(image_url(menu.photo_url, menu.name, menu.category), use_container_width=True)
    h2.subheader(f"{menu.name}　{CATEGORIES.get(menu.category, menu.category)}")
    h2.caption(menu.address or "")
    if menu.description:
        h2.write(menu.description)
    # ② 3タブを作る
    tab1, tab2, tab3 = st.tabs(["価格比較", "プラン・条件", "社員の声"])

    market = representative_prices([menu.id]).get(menu.id) if menu.category == "stay" else None
    # ③ 価格比較タブ: プランごとに評価・根拠・クーポン・会員用ページ
    with tab1:
        for p in menu.plans:
            with st.container(border=True):
                st.markdown(f"**{p.name}**")
                if menu.category == "stay":
                    r = evaluate(p, market)
                    st.write(f"元値 {r.list_price:,}円 ／ 福利厚生 {r.benefit_price:,}円 ／ 実勢 {('%s円' % format(r.market_price, ',')) if r.market_price is not None else '—'}")
                    st.markdown(f"判定: **{r.label}**" + (f"　差額 {r.diff:+,}円" if r.diff is not None else ""))
                    with st.expander("根拠"):
                        st.write(r.formula)
                        if r.source:
                            st.write(f"取得元: {r.source}　取得日時: {r.fetched_at}")
                else:
                    st.write(f"福利厚生価格 {p.benefit_price:,}円（元値 {p.list_price:,}円）")
                ct = coupon_text(p)
                if ct:
                    st.info(ct)
                    c1, c2 = st.columns(2)
                    if c1.button("クーポンを取得", key=f"cp-{p.id}"):
                        acquire(user, p); st.success("取得を記録しました。会員用ページで使えます。")
                    if p.member_url and c2.button("会員用ページへ", key=f"ml-{p.id}"):
                        url = member_link(user, p)
                        st.markdown(f"[会員用ページを開く]({url})")
                        st.caption("利用したら感想を残してください。")
                        if st.button("感想を投稿する", key=f"post-{p.id}"):
                            open_post_dialog(user, menu, p)
    # ④ プラン・条件タブ
    with tab2:
        for p in menu.plans:
            st.write(f"- {p.name}: 部屋 {p.room_type or '—'} ／ 食事 {p.meal or '—'} ／ 想定 {p.adults or '—'}名 {p.nights}泊")
        st.write(f"利用回数の上限: {menu.usage_limit or '—'}")
        st.write(f"家族の範囲: {menu.family_scope or '—'}")
        st.write(f"キャンセル条件: {menu.cancel_policy or '—'}")
        if menu.procedure:
            st.write(f"利用手順: {menu.procedure}")
    # ⑤ 社員の声タブ: 一覧・要約・投稿
    with tab3:
        posts = list_by_menu(menu.id)
        s = summary(posts)
        c1, c2 = st.columns([3, 1])
        c1.write(f"{s.count}件" + (f"　平均 ★{s.average}" if s.average else ""))
        if c2.button("投稿する"):
            open_post_dialog(user, menu, None)
        if not posts:
            st.info("まだ声がありません。使ったら最初の一言を残してください。")
        for p in posts:
            with st.container(border=True):
                st.write("★" * p.rating + "☆" * (5 - p.rating) + f"　{p.user_name or '社員'}　{p.created_at.strftime('%Y-%m-%d')}")
                if p.comment:
                    st.write(p.comment)
