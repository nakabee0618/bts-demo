"""クーポンと会員用ページ（D2）。表示は pages/detail.py が行い、ここは記録と文言を担う。"""
from __future__ import annotations

from typing import Optional

from activity import log
from models import Plan, User


def coupon_text(plan: Plan) -> Optional[str]:
    """クーポンがあれば表示用の文言、なければ None。"""
    # ① クーポンがなければ何も出さない
    if not plan.coupon_code:
        return None
    # ② コードと適用後価格の文言を作る
    price = f"適用後 {plan.coupon_price:,}円" if plan.coupon_price is not None else ""
    return f"クーポンコード: {plan.coupon_code}　{price}".strip()


def acquire(user: User, plan: Plan) -> None:
    """「クーポンを取得」を記録する。"""
    # ① 行動ログに「クーポン取得」を記録する
    log(user, "coupon", menu_id=plan.menu_id, plan_id=plan.id)


def member_link(user: User, plan: Plan) -> Optional[str]:
    """会員用ページのURLを返し、クリックを記録する。URLがなければ None。"""
    # ① URLがなければ None
    if not plan.member_url:
        return None
    # ② 行動ログに「リンククリック」を記録してURLを返す
    log(user, "click", menu_id=plan.menu_id, plan_id=plan.id)
    return plan.member_url
