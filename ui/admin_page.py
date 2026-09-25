"""メニュー管理（B1）。人事ロールのみ。一覧と編集。CSV投入はスクリプト（seed/load.py）で行う。"""
from __future__ import annotations

import streamlit as st

from auth import require_role
from db import table
from models import CATEGORIES, Menu


def render() -> None:


    """メニュー管理画面。一覧と、選んだ1件の編集フォーム。"""
    user = require_role("hr", "executive")
    tab_menu, tab_usage, tab_notify = st.tabs(["メニュー管理", "利用の記録（開発予定）", "社内ツール連携（開発予定）"])
    with tab_usage:
        # 見た目のみ（第6回決定）。集計はMVP後に実装する
        st.caption("クーポン取得数・会員用ページへのリンクのクリック数・ログイン数を期間で集計します。MVPでは見た目のみです")
        c1, c2, c3 = st.columns(3)
        c1.metric("クーポン取得", "—")
        c2.metric("リンククリック", "—")
        c3.metric("ログイン", "—")
        st.date_input("期間", value=(), disabled=True)
    with tab_notify:
        # 見た目のみ（第6回決定）。会社ごとにツールが違うため、横展開を考えて後回し
        st.caption("新着メニューや差額の実例を社内の連絡手段に通知します。MVPでは見た目のみです")
        st.selectbox("通知先", ["Slack", "Teams", "メール"], disabled=True)
        st.button("通知を送る（開発予定）", disabled=True)
    with tab_menu:
        _render_menus(user)


def _render_menus(user) -> None:
    """メニュー管理タブの中身。一覧と、選んだ1件の編集フォーム。"""
    # ① 自テナントのメニューを取る
    rows = table("menus").select("*").eq("tenant_id", user.tenant_id).is_("deleted_at", "null").order("name").execute().data
    menus = [Menu.from_row(r) for r in rows]
    st.caption(f"{len(menus)}件。CSVからの投入は `python -m seed.load` で行います。")
    names = {m.name: m for m in menus}
    # ② 未選択なら一覧、選択されたら編集フォーム
    picked = st.selectbox("編集するメニュー", ["（選択）"] + list(names))
    if picked == "（選択）":
        st.table([{"施設名": m.name, "カテゴリ": CATEGORIES.get(m.category, m.category), "取得元の宿ID": m.hotel_ref or "", "名寄せ済み": "○" if m.matched else ""} for m in menus])
        return
    m = names[picked]
    with st.form("edit"):
        name = st.text_input("施設名", m.name)
        hotel_ref = st.text_input("実勢価格取得元の宿ID（楽天のホテル番号）", m.hotel_ref or "")
        usage_limit = st.text_input("利用回数の上限", m.usage_limit or "")
        family_scope = st.text_input("家族の範囲", m.family_scope or "")
        cancel_policy = st.text_input("キャンセル条件", m.cancel_policy or "")
        procedure = st.text_area("利用手順", m.procedure or "")
        # ③ 検証して保存
        if st.form_submit_button("保存", type="primary"):
            if not name.strip():
                st.error("施設名は必須です"); return
            table("menus").update({
                "name": name.strip(), "hotel_ref": hotel_ref.strip() or None, "matched": bool(hotel_ref.strip()),
                "usage_limit": usage_limit or None, "family_scope": family_scope or None,
                "cancel_policy": cancel_policy or None, "procedure": procedure or None,
            }).eq("id", m.id).execute()
            st.success("保存しました"); st.rerun()
