"""差額計算と判定（C1）。DBに触らない純粋な処理。

判定の意味:
  good      … 実勢価格より福利厚生価格のほうが安い
  not_good  … 実勢価格のほうが安いか同額（得ではない）
  no_data   … 実勢価格が取れていない（比較不可）
条件（人数・泊数）が揃わない場合は reference=True（参考値）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from models import MarketPrice, Plan

GOOD, NOT_GOOD, NO_DATA = "good", "not_good", "no_data"
LABELS = {GOOD: "得", NOT_GOOD: "得ではない", NO_DATA: "比較不可"}


@dataclass
class PriceResult:
    list_price: int
    benefit_price: int
    market_price: Optional[int]
    diff: Optional[int]
    judgement: str
    reference: bool = False
    source: Optional[str] = None
    fetched_at: Optional[str] = None
    formula: str = ""

    @property
    def label(self) -> str:
        return LABELS[self.judgement] + ("（参考値）" if self.reference else "")


def normalize(market: MarketPrice, plan: Plan) -> tuple[int, bool]:
    """実勢価格をプランの条件（人数・泊数）に揃える。揃えられれば (価格, False)、揃わなければ (価格, True)。

    人数が違う場合は1人あたり単価×プランの人数で換算し、参考値扱いにする。泊数はプランに合わせて比例換算。
    """
    # ① 実勢価格をそのまま起点にする
    price = market.price
    reference = False
    plan_adults = plan.adults or market.adults
    # ② 人数が違えば1人あたり単価×プランの人数に換算し、参考値にする
    if market.adults and plan_adults and market.adults != plan_adults:
        price = round(price / market.adults * plan_adults)
        reference = True
    # ③ 泊数が違えば1泊あたりに換算し、参考値にする
    if market.nights and plan.nights and market.nights != plan.nights:
        price = round(price / market.nights * plan.nights)
        reference = True
    return price, reference


def diff(benefit_price: int, market_price: int) -> int:
    """差額 = 実勢価格 − 福利厚生価格。正なら得。"""
    return market_price - benefit_price


def judge(benefit_price: int, market_price: Optional[int]) -> str:


    """判定。実勢がなければ比較不可、実勢＞福利厚生なら得、それ以外は得ではない。"""
    # ① 実勢価格がなければ比較不可
    if market_price is None:
        return NO_DATA
    # ② 実勢価格が福利厚生価格より高ければ得、それ以外は得ではない
    return GOOD if market_price > benefit_price else NOT_GOOD


def evaluate(plan: Plan, market: Optional[MarketPrice]) -> PriceResult:
    """プランと実勢価格から4価格・差額・判定・根拠をまとめて返す。"""
    # ① 実勢価格がなければ「比較不可」の結果を返す
    if market is None:
        return PriceResult(plan.list_price, plan.benefit_price, None, None, NO_DATA, formula="実勢価格が取得できていないため比較できません")
    # ② 実勢価格をプランの条件（人数・泊数）に揃える
    market_price, reference = normalize(market, plan)
    # ③ 差額と判定
    d = diff(plan.benefit_price, market_price)
    j = judge(plan.benefit_price, market_price)
    # ④ 根拠の文を作る。参考値なら注記を足す
    formula = f"差額 = 実勢価格 {market_price:,}円 − 福利厚生価格 {plan.benefit_price:,}円 = {d:,}円"
    if reference:
        formula += "（人数・泊数をプランに合わせて換算した参考値）"
    # ⑤ まとめて返す
    return PriceResult(plan.list_price, plan.benefit_price, market_price, d, j, reference, market.source, market.fetched_at.strftime("%Y-%m-%d %H:%M"), formula)


def best_result(menu_plans: list[Plan], market: Optional[MarketPrice]) -> Optional[PriceResult]:
    """メニューの代表値: 差額が最大のプランの結果。比較不可なら最初のプラン。"""
    if not menu_plans:
        return None
    # ① 全プランを評価する
    results = [evaluate(p, market) for p in menu_plans]
    # ② 比較できたものがあれば差額最大、なければ最初のプラン
    comparable = [r for r in results if r.diff is not None]
    return max(comparable, key=lambda r: r.diff) if comparable else results[0]
