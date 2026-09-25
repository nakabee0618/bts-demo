"""投稿ダイアログ（D3）。星と一言を送信する。"""
from __future__ import annotations

from typing import Optional

import streamlit as st

from models import Menu, Plan, User
from posts import COMMENT_MAX, create, upload_photo, validate_photo


@st.dialog("口コミを書く")
def open_post_dialog(user: User, menu: Menu, plan: Optional[Plan]) -> None:
    """投稿ダイアログ。星と一言を検証して保存する。"""
    st.write(f"**{menu.name}**" + (f"（{plan.name}）" if plan else ""))
    # ① 星（0〜4で返る）と一言を入力
    rating = st.feedback("stars")
    comment = st.text_area(f"コメント（任意・{COMMENT_MAX}文字まで）", max_chars=COMMENT_MAX)
    photo = st.file_uploader("写真（任意・JPEG／PNG・5MBまで）", type=["jpg", "jpeg", "png"])
    st.caption("個人が特定される内容や、契約の詳細は書かないでください。人の顔が写った写真は避けてください。")
    # ② 送信で検証と保存。写真があれば先に保存してURLを得る。星は +1 して保存
    if st.button("投稿する", type="primary"):
        if rating is None:
            st.error("星を選んでください"); return
        photo_url = None
        if photo is not None:
            err = validate_photo(photo.type, photo.size)
            if err:
                st.error(err); return
            try:
                photo_url = upload_photo(user, photo.getvalue(), photo.type)
            except Exception as e:
                st.error(f"写真を保存できませんでした: {e}"); return
        err = create(user, menu.id, int(rating) + 1, comment, plan.id if plan else None, photo_url)
        if err:
            st.error(err); return
        st.success("ありがとうございます。口コミを投稿しました。")
        st.rerun()
