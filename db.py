"""Supabaseへの接続。接続情報は .streamlit/secrets.toml から読む。"""
from __future__ import annotations

import os

import streamlit as st
from supabase import Client, create_client

SCHEMA = "bts"


@st.cache_resource
def client() -> Client:
    """アプリ全体で1つのクライアントを共有する（cache_resourceで再生成を防ぐ）。"""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]
    return create_client(url, key)


def is_demo() -> bool:
    """デモモードかどうか。環境変数 BTS_DEMO=1、または secrets の demo = true で有効（Supabaseを使わず、CSVをメモリで扱う）。"""
    if os.environ.get("BTS_DEMO", "").strip() in ("1", "true", "True"):
        return True
    try:
        return bool(st.secrets.get("demo", False))
    except Exception:
        return False


def table(name: str):
    """btsスキーマのテーブルを指すクエリビルダーを返す。デモモードでは demo_db の同名関数。"""
    if is_demo():
        from demo_db import table as demo_table
        return demo_table(name)
    return client().schema(SCHEMA).table(name)
