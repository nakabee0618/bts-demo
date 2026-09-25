"""詳細の口コミタブ（投稿・声モジュール）。件数と平均、一覧（写真つき）、口コミを書く入口。"""
from __future__ import annotations

import streamlit as st

from dialogs.post import open_post_dialog
from models import Menu, User
from posts import list_by_menu, summary


def render_review_tab(user: User, menu: Menu) -> None:
    """口コミタブの中身。詳細画面の枠から呼ばれる。"""
    # ① 一覧と要約を取る
    posts = list_by_menu(menu.id)
    s = summary(posts)
    c1, c2 = st.columns([3, 1])
    c1.write(f"{s.count}件" + (f"　平均 ★{s.average}" if s.average else ""))
    if c2.button("口コミを書く"):
        open_post_dialog(user, menu, None)
    # ② 空状態
    if not posts:
        st.info("まだ口コミがありません。利用したら最初の口コミを書いてみてください。")
    # ③ 新しい順に表示（写真があれば本文の下）
    for p in posts:
        with st.container(border=True):
            st.write("★" * p.rating + "☆" * (5 - p.rating) + f"　{p.user_name or '社員'}　{p.created_at.strftime('%Y/%m/%d')}")
            if p.comment:
                st.write(p.comment)
            if p.photo_url:
                st.image(p.photo_url, width=280)
