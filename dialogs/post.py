"""投稿ダイアログ（D3）。星と一言を送信する。"""
from __future__ import annotations

from typing import Optional

import streamlit as st

from models import Menu, Plan, User
from posts import COMMENT_MAX, create


@st.dialog("感想を投稿")
def open_post_dialog(user: User, menu: Menu, plan: Optional[Plan]) -> None:
    """投稿ダイアログ。星と一言を検証して保存する。"""
    st.write(f"**{menu.name}**" + (f"（{plan.name}）" if plan else ""))
    # ① 星（0〜4で返る）と一言を入力
    rating = st.feedback("stars")
    comment = st.text_area(f"一言（{COMMENT_MAX}文字以内・任意）", max_chars=COMMENT_MAX)
    st.caption("個人情報や契約の内訳は書かないでください。")
    # ② 送信で検証と保存。星は +1 して保存
    if st.button("送信", type="primary"):
        if rating is None:
            st.error("星を選んでください"); return
        err = create(user, menu.id, int(rating) + 1, comment, plan.id if plan else None)
        if err:
            st.error(err); return
        st.success("ありがとうございます。投稿しました。")
        st.rerun()
