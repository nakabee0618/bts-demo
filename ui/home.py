"""検索前の画面（一覧モジュール）。お得ランキング・新着・最近の口コミを見せる。"""
from __future__ import annotations

import streamlit as st

from models import User
from placeholder import image_url
from pricing import best_result
from search import all_stay_menus, is_new, recent_posts, representative_prices


def render_home(user: User) -> None:
    """検索フォームの下に出す。検索したら消える。件数が少なくても見劣りしないよう、数の集計は出さない。"""
    # ① お得ランキング（宿泊の差額トップ5）
    menus = all_stay_menus(user.tenant_id)
    prices = representative_prices([m.id for m in menus])
    ranked = [(m, best_result(m.plans, prices.get(m.id))) for m in menus]
    ranked = [(m, r) for m, r in ranked if r and r.diff is not None and r.diff > 0]
    ranked.sort(key=lambda x: -x[1].diff)
    st.markdown("#### お得ランキング")
    cols = st.columns(5)
    for i, (m, r) in enumerate(ranked[:5]):
        with cols[i]:
            # 施設名は長さがまちまちで折り返すため、ボタンより下に置いて位置を揃える
            st.image(image_url(m.photo_url, m.name, m.category, width=200, height=120), use_container_width=True)
            st.markdown(f"**{i+1}位**　:green[**{r.diff:,}円お得**]")
            if st.button("詳細を見る", key=f"rank-{m.id}", use_container_width=True):
                st.session_state["menu_id"] = m.id; st.session_state["page"] = "detail"; st.rerun()
            st.caption(m.name)
    # ② 新着メニュー
    new = [m for m in menus if is_new(m.content_updated_at)]
    if new:
        st.markdown("#### 新着")
        st.write("　".join(f":red-badge[新着] {m.name}" for m in new[:5]))
    # ③ 最近の口コミ
    posts = recent_posts(user.tenant_id, 3)
    if posts:
        st.markdown("#### 最近の口コミ")
        for p in posts:
            with st.container(border=True):
                st.write("★" * int(p["rating"]) + "☆" * (5 - int(p["rating"])) + f"　**{p['menu_name']}**　{(p.get('users') or {}).get('name', '社員')}")
                if p.get("comment"):
                    st.write(p["comment"])
                if p.get("photo_url"):
                    st.image(p["photo_url"], width=200)
