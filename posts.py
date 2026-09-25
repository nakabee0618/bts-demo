"""投稿と社員の声（D3）。星と一言を保存し、メニューごとの一覧と要約を返す。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from db import table
from models import Post, User

COMMENT_MAX = 200


def validate(rating: int, comment: str) -> Optional[str]:
    """入力の検証。問題があれば理由の文字列、なければ None。"""
    if not 1 <= int(rating) <= 5:
        return "星は1〜5で選んでください"
    if len(comment or "") > COMMENT_MAX:
        return f"一言は{COMMENT_MAX}文字以内にしてください"
    return None


def create(user: User, menu_id: str, rating: int, comment: str, plan_id: Optional[str] = None) -> Optional[str]:
    """投稿を保存する。失敗時はエラー文字列。"""
    # ① 入力を検証する
    err = validate(rating, comment)
    if err:
        return err
    # ② 保存する行を組み立てる（一言の空文字は None）
    row = {
        "tenant_id": user.tenant_id,
        "user_id": user.id,
        "menu_id": menu_id,
        "plan_id": plan_id,
        "rating": int(rating),
        "comment": (comment or "").strip() or None,
    }
    # ③ 保存する。失敗は文字列で返す
    try:
        table("posts").insert(row).execute()
    except Exception as e:
        return f"投稿を保存できませんでした: {e}"
    return None


def list_by_menu(menu_id: str) -> list[Post]:


    """メニューの投稿一覧（非表示・削除済みを除く、新しい順、投稿者名つき）。"""
    # ① 非表示・削除済みを除き、投稿者名を結合して新しい順に取る
    rows = (
        table("posts").select("*, users(name)")
        .eq("menu_id", menu_id).eq("hidden", False).is_("deleted_at", "null")
        .order("created_at", desc=True).execute().data
    )
    return [Post.from_row(r) for r in rows]


@dataclass
class Summary:
    count: int
    average: Optional[float]


def summary(posts: list[Post]) -> Summary:


    """件数と星の平均。"""
    # ① 0件なら平均なし、それ以外は星の平均（小数1桁）
    if not posts:
        return Summary(0, None)
    return Summary(len(posts), round(sum(p.rating for p in posts) / len(posts), 1))
