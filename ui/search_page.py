"""検索画面（C2）。条件を入力して候補一覧へ渡す。"""
from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from auth import require_login
from models import CATEGORIES
from db import is_demo
from nl_search import parse
from search import Condition, list_areas, search, validate


def render() -> None:
    """検索画面。上に検索の入口、下に「検索前はトップ（ランキング・新着・口コミ）／検索後は結果」を出す。app.py から呼ばれる。"""
    user = require_login()
    areas = list_areas()
    # ① 検索の入口を枠で囲む（文章で探す／条件で探す）
    with st.container(border=True):
        st.subheader("検索")
        nl_tab, form_tab = st.tabs(["文章で探す", "条件で探す"])
        defaults = {"area": "すべて", "category": "すべて", "checkin": date.today() + timedelta(days=14), "adults": 2, "budget": 0}
        with nl_tab:
            if is_demo():
                st.info("お試し版のため、文章の読み取りは簡易です")
            text = st.text_input("どんな休日にしたいですか", placeholder="例: 来週末に箱根で2人、3万円以内で温泉に泊まりたい")
            if st.button("検索", key="nl-search", type="primary") and text.strip():
                # ② 文章を条件に読み替え、そのまま検索まで行う
                parsed = parse(text, [a.name for a in areas])
                st.session_state["nl_parsed"] = parsed
                cond = Condition(
                    area_id=next((a.id for a in areas if a.name == parsed.area_name), None),
                    category=parsed.category, checkin=parsed.checkin, adults=parsed.adults or 2, budget=parsed.budget,
                )
                err = validate(cond)
                if err:
                    st.error(err)
                else:
                    st.session_state["condition"] = cond
                    st.session_state["results"] = search(user.tenant_id, cond)
            parsed = st.session_state.get("nl_parsed")
            if parsed:
                d = parsed.as_dict()
                st.caption("こう読み取りました。違うときは「条件で探す」から直せます")
                parts = [d["エリア"], d["カテゴリ"], f"{d['人数']}人" if d["人数"] else None, f"{d['予算']:,}円以内" if d["予算"] else None, d["日程"].replace("-", "/")[5:] if d["日程"] else None]
                st.write("・".join(x for x in parts if x))
                if parsed.area_name: defaults["area"] = parsed.area_name
                if parsed.category: defaults["category"] = CATEGORIES[parsed.category]
                if parsed.adults: defaults["adults"] = parsed.adults
                if parsed.budget: defaults["budget"] = parsed.budget
                if parsed.checkin: defaults["checkin"] = parsed.checkin
        with form_tab, st.form("search"):
            c1, c2 = st.columns(2)
            area_opts = ["すべて"] + [a.name for a in areas]
            cat_opts = ["すべて"] + list(CATEGORIES.values())
            area = c1.selectbox("エリア", area_opts, index=area_opts.index(defaults["area"]))
            category = c2.selectbox("カテゴリ", cat_opts, index=cat_opts.index(defaults["category"]))
            c3, c4, c5 = st.columns(3)
            checkin = c3.date_input("宿泊日", value=defaults["checkin"])
            adults = c4.number_input("人数", min_value=1, max_value=10, value=int(defaults["adults"]))
            budget = c5.number_input("予算（円・0なら上限なし）", min_value=0, value=int(defaults["budget"]), step=1000)
            if st.form_submit_button("検索", type="primary"):
                # ③ 条件を組み立てて検証し、検索する
                cond = Condition(
                    area_id=next((a.id for a in areas if a.name == area), None),
                    category=next((k for k, v in CATEGORIES.items() if v == category), None),
                    checkin=checkin, adults=int(adults), budget=int(budget) if budget else None,
                )
                err = validate(cond)
                if err:
                    st.error(err)
                else:
                    st.session_state["condition"] = cond
                    st.session_state["results"] = search(user.tenant_id, cond)
    # ④ 検索前はトップ、検索後は結果。結果の上に「トップに戻る」
    if "results" not in st.session_state:
        from ui.home import render_home
        render_home(user)
        return
    h1, h2 = st.columns([4, 1], vertical_alignment="center")
    h1.subheader("検索結果")
    if h2.button("← トップに戻る", use_container_width=True):
        for k in ("results", "condition", "nl_parsed"):
            st.session_state.pop(k, None)
        st.rerun()
    from ui.results_page import render_results
    render_results(st.session_state["results"], st.session_state["condition"])
