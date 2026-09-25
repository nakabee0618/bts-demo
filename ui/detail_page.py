"""候補詳細（D1）。価格比較・プラン・条件・社員の声の3タブ。クーポンと投稿はここから。"""
from __future__ import annotations

import streamlit as st

from auth import require_login
from coupon import acquire, member_link
from dialogs.post import open_post_dialog
from models import CATEGORIES
from posts import list_by_menu, summary
from placeholder import image_url
from pricing import evaluate
from search import get_menu, representative_prices, spots_by_area


def render() -> None:


    """候補詳細。価格比較／プラン・条件／社員の声の3タブ。"""
    user = require_login()
    # ① セッションの menu_id からメニューとプランを取る
    menu_id = st.session_state.get("menu_id")
    menu = get_menu(menu_id) if menu_id else None
    if menu is None:
        st.info("一覧から施設を選んでください。")
        return
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
    # ② 3タブを作る
    tab1, tab2, tab3, tab4 = st.tabs(["価格比較", "プラン・条件", "口コミ", "周辺"])

    market = representative_prices([menu.id]).get(menu.id) if menu.category == "stay" else None
    # ③ 価格比較タブ: プランごとの価格・クーポン・予約ページ
    with tab1:
        for p in menu.plans:
            with st.container(border=True):
                st.markdown(f"**{p.name}**" + (f"　:gray[{p.room_type or ''} {p.meal or ''}]" if p.room_type or p.meal else ""))
                if menu.category == "stay":
                    r = evaluate(p, market)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("福利厚生価格", f"{r.benefit_price:,}円")
                    if r.market_price is not None:
                        m2.metric("一般サイトの価格", f"{r.market_price:,}円")
                        m3.metric("差額", f"{r.diff:+,}円")
                        m3.caption(":green[お得]" if r.diff > 0 else ":red[一般サイトの方が安い]")
                        st.caption(f"一般サイトの価格は{r.fetched_at[:10].replace('-', '/')}時点" + ("（楽天トラベル）" if r.source == "rakuten_api" else "（お試し版のため仮の値）") + ("　※人数・泊数を換算した目安" if r.reference else ""))
                    else:
                        m2.metric("一般サイトの価格", "—")
                        m3.metric("差額", "—")
                        m3.caption("一般サイトの価格を調べられませんでした")
                else:
                    st.write(f"福利厚生価格 {p.benefit_price:,}円")
                if p.coupon_code:
                    with st.container(border=True):
                        k1, k2 = st.columns([1, 1], vertical_alignment="center")
                        k1.markdown(":blue-badge[クーポン]")
                        k1.markdown(f"予約ページでこのコードを入力すると、福利厚生価格 **{p.benefit_price:,}円** になります")
                        k2.caption("クーポンコード（右端のアイコンでコピー）")
                        k2.code(p.coupon_code, language=None)
                        b1, b2 = st.columns([1, 1])
                        if not st.session_state.get(f"opened-{p.id}"):
                            # 使ったこと・予約ページへ進んだことを1回の操作で記録する
                            if b1.button("クーポンを使って予約する", key=f"cp-{p.id}", type="primary", use_container_width=True):
                                acquire(user, p)
                                if p.member_url:
                                    member_link(user, p)
                                st.session_state[f"opened-{p.id}"] = True
                                st.rerun()
                        else:
                            if p.member_url:
                                b1.link_button("予約ページを開く", p.member_url, type="primary", use_container_width=True)
                            if b2.button("口コミを書く", key=f"post-{p.id}", use_container_width=True):
                                open_post_dialog(user, menu, p)
                            st.caption("コードは予約ページで入力してください。「クーポン使用履歴」からいつでも見られます")
    # ④ プラン・条件タブ
    with tab2:
        for p in menu.plans:
            st.write(f"- {p.name}: 部屋 {p.room_type or '—'} ／ 食事 {p.meal or '—'} ／ {p.adults or 2}名・{p.nights}泊の料金")
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
        if c2.button("口コミを書く"):
            open_post_dialog(user, menu, None)
        if not posts:
            st.info("まだ口コミがありません。利用したら最初の口コミを書いてみてください。")
        for p in posts:
            with st.container(border=True):
                st.write("★" * p.rating + "☆" * (5 - p.rating) + f"　{p.user_name or '社員'}　{p.created_at.strftime('%Y/%m/%d')}")
                if p.comment:
                    st.write(p.comment)
                if p.photo_url:
                    st.image(p.photo_url, width=280)
    # ⑥ 周辺タブ: 公開情報から集めた食事・レジャー
    with tab4:
        spots = spots_by_area(menu.area_id)
        if not spots:
            st.info("周辺の情報はまだありません。")
        for kind, label in (("meal", "食事"), ("leisure", "レジャー")):
            items = [sp for sp in spots if sp["kind"] == kind]
            if items:
                st.markdown(f"**{label}**")
                for sp in items:
                    st.write(f"- [{sp['name']}]({sp['url']})　:gray[{sp.get('description') or ''}]")
        st.caption("公開情報をもとにした案内です。宿の比較には使っていません。")
