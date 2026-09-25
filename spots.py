"""周辺情報の取得（周辺情報モジュール）。クローリングで集めた食事・レジャーを詳細画面に出す。"""
from __future__ import annotations

from typing import Optional

from db import table


def spots_by_area(area_id: Optional[str]) -> list[dict]:
    """エリアの周辺情報（食事・レジャー）。共通＋自テナントのもの。"""
    if not area_id:
        return []
    return table("spots").select("*").eq("area_id", area_id).order("kind").execute().data
