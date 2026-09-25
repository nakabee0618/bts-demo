"""検索画面（C2）。条件を入力して候補一覧へ渡す。"""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from auth import require_login
from models import CATEGORIES
from nl_search import parse
from search import Condition, list_areas, search, validate


def render() -> None:


    """検索画面。条件を入力→検証→検索→候補一覧に渡す。"""
    user = require_login()
    st.subheader("探す")
    # ① エリアの選択肢を取り、フォームを描画する
    areas = list_areas()
    # ① 入口を2つ用意する: 文章から／条件から。文章は変換結果を表示してから条件に入れる
    nl_tab, form_tab = st.tabs(["文章から探す", "条件で探す"])
    defaults = {"area": "指定なし", "category": "指定なし", "checkin": date.today() + timedelta(days=14), "adults": 2, "budget": 30000}
    with nl_tab:
        text = st.text_input("やりたいこと", placeholder="例: 来週末に箱根で2人、3万円以内で温泉に泊まりたい")
        if st.button("条件に変換", key="nl-convert") and text.strip():
            parsed = parse(text, [a.name for a in areas])
            st.session_state["nl_parsed"] = parsed
        parsed = st.session_state.get("nl_parsed")
        if parsed:
            st.caption(f"変換結果（{parsed.as_dict()['変換']}）。下の「条件で探す」に反映しています。直してから検索してください")
            st.json({k: v for k, v in parsed.as_dict().items() if k != "変換"})
            if parsed.area_name: defaults["area"] = parsed.area_name
            if parsed.category: defaults["category"] = CATEGORIES[parsed.category]
            if parsed.adults: defaults["adults"] = parsed.adults
            if parsed.budget: defaults["budget"] = parsed.budget
            if parsed.checkin: defaults["checkin"] = parsed.checkin
    with form_tab, st.form("search"):
        c1, c2 = st.columns(2)
        area_opts = ["指定なし"] + [a.name for a in areas]
        cat_opts = ["指定なし"] + list(CATEGORIES.values())
        area = c1.selectbox("エリア", area_opts, index=area_opts.index(defaults["area"]))
        category = c2.selectbox("カテゴリ", cat_opts, index=cat_opts.index(defaults["category"]))
        c3, c4, c5 = st.columns(3)
        checkin = c3.date_input("日程（チェックイン）", value=defaults["checkin"])
        adults = c4.number_input("人数（大人）", min_value=1, max_value=10, value=int(defaults["adults"]))
        budget = c5.number_input("予算（福利厚生価格・円）", min_value=0, value=int(defaults["budget"]), step=1000)
        submitted = st.form_submit_button("検索", type="primary")
    if not submitted and "results" not in st.session_state:
        return
    # ② 送信されたら条件を組み立てて検証する
    if submitted:
        cond = Condition(
            area_id=next((a.id for a in areas if a.name == area), None),
            category=next((k for k, v in CATEGORIES.items() if v == category), None),
            checkin=checkin, adults=int(adults), budget=int(budget) if budget else None,
        )
        err = validate(cond)
        if err:
            st.error(err); return
        # ③ 検索してセッションに結果を置く
        st.session_state["condition"] = cond
        st.session_state["results"] = search(user.tenant_id, cond)
    # ④ 一覧（C3）に渡す
    from ui.results_page import render_results
    render_results(st.session_state["results"], st.session_state["condition"])
