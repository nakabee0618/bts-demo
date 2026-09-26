"""福利厚生検索アプリ MVP。ページの切り替えとログイン。"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from activity import log
from auth import current_user, demo_login, login, logout
from db import is_demo

ASSETS = Path(__file__).resolve().parent / "assets"
st.set_page_config(page_title="福利厚生検索アプリ", page_icon=str(ASSETS / "icon.png"), layout="wide")

# ブランドのアイコン（assets/icon.png）をサイドバーの左上に出す
st.logo(str(ASSETS / "logo.png"), size="large")

user = current_user()
with st.sidebar:
    st.title("福利厚生検索アプリ")
    if user is None and is_demo():
        from demo_db import demo_users
        st.caption("お試し版（データは仮のもの）")
        name = st.selectbox("利用者を選ぶ", [u["name"] for u in demo_users()])
        if st.button("ログイン", type="primary", icon=":material/login:"):
            u = demo_login(name)
            log(u, "login"); st.rerun()
    elif user is None:
        with st.form("login"):
            email = st.text_input("メール")
            password = st.text_input("パスワード", type="password")
            if st.form_submit_button("ログイン", type="primary", icon=":material/login:"):
                u = login(email, password)
                if u is None:
                    st.error("メールアドレスまたはパスワードが違います")
                else:
                    log(u, "login"); st.rerun()
    else:
        st.write(f"{user.name}（{user.department or ''}）")
        pages = {"search": ":material/search: 検索", "mypage": ":material/confirmation_number: クーポン使用履歴"}
        if user.is_admin():
            pages["admin"] = ":material/settings: メニュー管理"
        choice = st.radio("メニュー", list(pages.values()), label_visibility="collapsed")
        chosen = next(k for k, v in pages.items() if v == choice)
        if st.session_state.get("page") not in ("detail",) or chosen != "search":
            st.session_state["page"] = chosen
        if st.button("ログアウト", icon=":material/logout:"):
            logout(); st.rerun()

if user is None:
    st.info("左からログインしてください。")
    st.stop()

page = st.session_state.get("page", "search")
if page == "search":
    from ui.search_page import render
elif page == "detail":
    from ui.detail_page import render
elif page == "admin":
    from ui.admin_page import render
elif page == "mypage":
    from ui.mypage import render
else:
    from ui.search_page import render
render()
