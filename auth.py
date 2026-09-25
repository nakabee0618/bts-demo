"""ログインと利用者の取得。Supabase Authでメールとパスワードを検証し、bts.users の行に紐づける。"""
from __future__ import annotations

from typing import Optional

import streamlit as st

from db import client, is_demo, table
from models import User

SESSION_KEY = "bts_user"


def login(email: str, password: str) -> Optional[User]:
    """認証に成功したら users の行を返し、セッションに保存する。失敗は None。"""
    # ① Supabase Auth にメールとパスワードで問い合わせる
    try:
        res = client().auth.sign_in_with_password({"email": email, "password": password})
    except Exception:
        return None
    # ② 認証IDを取り出す
    auth_id = res.user.id if res and res.user else None
    if not auth_id:
        return None
    # ③ bts.users から auth_id の一致する行を取る
    rows = table("users").select("*").eq("auth_id", auth_id).is_("deleted_at", "null").limit(1).execute().data
    if not rows:
        return None
    # ④ User にしてセッションに保存する
    user = User.from_row(rows[0])
    st.session_state[SESSION_KEY] = user
    return user


def demo_login(name: str) -> Optional[User]:
    """デモモードのログイン。名前を選ぶだけで users 行を返す。"""
    from demo_db import demo_users
    for r in demo_users():
        if r["name"] == name:
            user = User.from_row(r)
            st.session_state[SESSION_KEY] = user
            return user
    return None


def logout() -> None:
    """Supabase Auth をサインアウトし、セッションの User を消す。"""
    if not is_demo():
        try:
            client().auth.sign_out()
        except Exception:
            pass
    st.session_state.pop(SESSION_KEY, None)


def current_user() -> Optional[User]:
    """セッションに保存された User。未ログインなら None。"""
    return st.session_state.get(SESSION_KEY)


def require_login() -> User:
    """未ログインなら案内を出して処理を止める。"""
    user = current_user()
    if user is None:
        st.info("ログインしてください。")
        st.stop()
    return user


def require_role(*roles: str) -> User:
    """指定ロール以外なら止める（管理画面用）。"""
    user = require_login()
    if user.role not in roles:
        st.warning("この画面を見る権限がありません。")
        st.stop()
    return user
