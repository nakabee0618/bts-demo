"""自然言語→検索条件の変換（検索モジュール）。

- APIキーがあれば LLM（OpenAI互換のチャットAPI）に投げて JSON で条件を返させる
- キーがなければルール変換（エリア名・カテゴリ語・人数・予算・日程の抽出）
- どちらも結果は dict で返し、画面で表示・修正してから検索に渡す（検索そのものはコードで行う）
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

import requests
import streamlit as st

CATEGORY_WORDS = {"stay": ["泊", "宿", "ホテル", "旅館", "温泉"], "meal": ["食事", "ご飯", "ランチ", "ディナー", "レストラン", "食べ"], "leisure": ["遊", "レジャー", "水族館", "テーマパーク", "観光", "日帰り"]}


@dataclass
class Parsed:
    area_name: Optional[str] = None
    category: Optional[str] = None
    adults: Optional[int] = None
    budget: Optional[int] = None
    checkin: Optional[date] = None
    keywords: list[str] = field(default_factory=list)
    source: str = "rule"

    def as_dict(self) -> dict:
        return {"エリア": self.area_name, "カテゴリ": self.category, "人数": self.adults, "予算": self.budget, "日程": self.checkin.isoformat() if self.checkin else None, "キーワード": self.keywords, "変換": "AI" if self.source == "llm" else "ルール"}


def parse(text: str, area_names: list[str]) -> Parsed:
    """入力文を条件に変換する。キーがあれば LLM、なければルール。"""
    # ① LLM の設定があれば使う。失敗したらルールに落ちる
    cfg = _llm_config()
    if cfg:
        try:
            return _parse_llm(text, area_names, cfg)
        except Exception:
            pass
    # ② ルール変換
    return _parse_rule(text, area_names)


def _llm_config() -> Optional[dict]:
    try:
        c = st.secrets.get("llm", {})
    except Exception:
        return None
    if not c or not c.get("api_key"):
        return None
    return {"api_key": c["api_key"], "base_url": c.get("base_url", "https://api.openai.com/v1"), "model": c.get("model", "gpt-4o-mini")}


def _parse_llm(text: str, area_names: list[str], cfg: dict) -> Parsed:
    """LLM に JSON だけを返させる。"""
    # ① 指示: 返す項目と形を固定し、余計な文章を禁止する
    system = ("あなたは福利厚生アプリの検索条件を抽出する係です。利用者の文章から次のJSONだけを返してください。"
              f'{{"area": エリア名（候補: {", ".join(area_names)}。なければnull）, "category": "stay"|"meal"|"leisure"|null, '
              '"adults": 人数の整数|null, "budget": 予算の整数（円）|null, "checkin": "YYYY-MM-DD"|null, "keywords": [語句]}} '
              "JSON以外は出力しないでください。")
    # ② OpenAI互換のチャットAPIを呼ぶ
    r = requests.post(f"{cfg['base_url'].rstrip('/')}/chat/completions", headers={"Authorization": f"Bearer {cfg['api_key']}"},
                      json={"model": cfg["model"], "messages": [{"role": "system", "content": system}, {"role": "user", "content": text}], "temperature": 0}, timeout=20)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"].strip()
    # ③ JSON を取り出す（```json 〜 ``` で囲まれていても拾う）
    content = re.sub(r"^```(?:json)?|```$", "", content, flags=re.M).strip()
    d = json.loads(content)
    return Parsed(area_name=d.get("area") if d.get("area") in area_names else None, category=d.get("category") if d.get("category") in CATEGORY_WORDS else None,
                  adults=int(d["adults"]) if d.get("adults") else None, budget=int(d["budget"]) if d.get("budget") else None,
                  checkin=date.fromisoformat(d["checkin"]) if d.get("checkin") else None, keywords=list(d.get("keywords") or []), source="llm")


def _parse_rule(text: str, area_names: list[str]) -> Parsed:
    """語の一致と正規表現で抜き出す簡易版。"""
    p = Parsed(source="rule")
    # ① エリア名の一致
    for a in area_names:
        if a in text:
            p.area_name = a; break
    # ② カテゴリ語
    for cat, words in CATEGORY_WORDS.items():
        if any(w in text for w in words):
            p.category = cat; break
    # ③ 人数（「2人」「二人」「4名」「家族4人」）
    m = re.search(r"([0-9０-９一二三四五六七八九十]+)\s*[人名]", text)
    if m:
        p.adults = _to_int(m.group(1))
    # ④ 予算（「3万円」「30000円」「3万以内」）
    m = re.search(r"([0-9０-９]+(?:\.[0-9]+)?)\s*万", text) or re.search(r"([0-9０-９,]{4,})\s*円", text)
    if m:
        raw = m.group(1).translate(str.maketrans("０１２３４５６７８９", "0123456789")).replace(",", "")
        p.budget = int(float(raw) * 10000) if "万" in text[m.start():m.end() + 1] else int(float(raw))
    # ⑤ 日程（「来週」「今週末」「11/22」）
    today = date.today()
    if "今週末" in text or "週末" in text:
        p.checkin = today + timedelta(days=(5 - today.weekday()) % 7 or 7)
    elif "来週" in text:
        p.checkin = today + timedelta(days=7)
    m = re.search(r"(\d{1,2})[/月](\d{1,2})", text)
    if m:
        try:
            p.checkin = date(today.year, int(m.group(1)), int(m.group(2)))
        except ValueError:
            pass
    # ⑥ 残りの語をキーワードに（2文字以上の名詞っぽい断片）
    p.keywords = [w for w in re.split(r"[、。,\s]+", text) if len(w) >= 2][:5]
    return p


def _to_int(s: str) -> Optional[int]:
    s = s.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    if s.isdigit():
        return int(s)
    kan = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    return kan.get(s)
