"""デモモード用の簡易DB。Supabaseの代わりに seed/ のCSVをメモリに読み、同じ呼び方（table().select().eq()...execute()）で動く。

対応している操作: select / eq / is_ / in_ / order / limit / insert / update / execute。
結合 "users(name)" は posts の user_id から users を引いて埋める。
"""
from __future__ import annotations

import csv
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from prices.rakuten import dummy_price

ROOT = Path(__file__).resolve().parent
_STORE: dict[str, list[dict]] = {}


def _load() -> None:
    if _STORE:
        return
    tenant = {"id": str(uuid.uuid4()), "name": "サンプル株式会社", "code": "sample"}
    _STORE["tenants"] = [tenant]
    areas = []
    for i, (code, name, region) in enumerate([("hakone", "箱根", "関東"), ("atami", "熱海", "関東"), ("karuizawa", "軽井沢", "中部"), ("kyoto", "京都", "関西"), ("okinawa", "沖縄", "九州・沖縄")], 1):
        areas.append({"id": str(uuid.uuid4()), "tenant_id": None, "code": code, "name": name, "region": region, "sort": i})
    _STORE["areas"] = areas
    area_by = {a["code"]: a["id"] for a in areas}
    menus, key_to_id = [], {}
    with open(ROOT / "seed" / "menus.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            mid = str(uuid.uuid4()); key_to_id[r["key"]] = mid
            menus.append({"id": mid, "tenant_id": tenant["id"], "name": r["name"], "category": r["category"], "area_id": area_by.get(r["area_code"]),
                          "address": r["address"], "description": r["description"], "procedure": None, "usage_limit": r["usage_limit"], "family_scope": r["family_scope"],
                          "cancel_policy": r["cancel_policy"], "max_people": None, "visibility": "internal", "hotel_ref": r["hotel_ref"] or None, "matched": bool(r["hotel_ref"]),
                          "content_updated_at": r["content_updated_at"], "deleted_at": None, "created_at": _now(), "updated_at": _now()})
    _STORE["menus"] = menus
    plans = []
    with open(ROOT / "seed" / "plans.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            plans.append({"id": str(uuid.uuid4()), "menu_id": key_to_id[r["menu_key"]], "name": r["name"], "room_type": r["room_type"] or None, "meal": r["meal"] or None,
                          "grade": r["grade"] or None, "adults": int(r["adults"]), "children": int(r["children"]), "nights": int(r["nights"]), "list_price": int(r["list_price"]),
                          "benefit_price": int(r["benefit_price"]), "coupon_code": r["coupon_code"] or None, "coupon_price": int(r["coupon_price"]) if r["coupon_price"] else None,
                          "member_url": r["member_url"] or None, "deleted_at": None})
    _STORE["plans"] = plans
    users = []
    with open(ROOT / "seed" / "users.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            users.append({"id": str(uuid.uuid4()), "tenant_id": tenant["id"], "auth_id": None, "name": r["name"], "role": r["role"], "department": r["department"], "family": r["family"], "deleted_at": None})
    _STORE["users"] = users
    # 実勢価格（ダミー。次の土曜、2名1泊）
    d = date.today()
    sat = d + __import__("datetime").timedelta(days=(5 - d.weekday()) % 7 or 7)
    mp = []
    for m in menus:
        if m["category"] == "stay" and m["hotel_ref"]:
            p = dummy_price(m["hotel_ref"], sat, 1, 2)
            mp.append({"id": str(uuid.uuid4()), "menu_id": m["id"], "hotel_ref": m["hotel_ref"], "checkin": sat.isoformat(), "nights": 1, "adults": 2, "children": 0, "meal": None,
                       "price": p.price, "source": p.source, "source_url": None, "fetched_at": _now(), "is_representative": True})
    _STORE["market_prices"] = mp
    # 初期の声を少し
    _STORE["posts"] = []
    for m, (u, rating, c) in zip(menus[:3], [(0, 5, "露天風呂が広くて家族で満足。差額は思ったより大きかった"), (1, 4, "駅から近い。食事は普通"), (2, 5, "芦ノ湖が見える。子どもも喜んだ")]):
        _STORE["posts"].append({"id": str(uuid.uuid4()), "tenant_id": tenant["id"], "user_id": users[u]["id"], "menu_id": m["id"], "plan_id": None, "used_at": None, "rating": rating,
                                "comment": c, "photo_url": None, "sentiment": None, "anonymous": False, "external_ok": False, "public_selected": False, "hidden": False, "view_count": 0,
                                "deleted_at": None, "created_at": _now()})
    _STORE["activity_logs"] = []
    _STORE["fetch_logs"] = []
    _STORE["spend"] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _Query:
    def __init__(self, name: str):
        _load(); self.name = name; self.filters = []; self._order = None; self._limit = None; self._op = "select"; self._payload = None; self._join = False

    def select(self, cols: str = "*"):
        self._join = "users(" in cols; return self
    def eq(self, col, val): self.filters.append(("eq", col, val)); return self
    def is_(self, col, val): self.filters.append(("is", col, val)); return self
    def in_(self, col, vals): self.filters.append(("in", col, list(vals))); return self
    def order(self, col, desc: bool = False): self._order = (col, desc); return self
    def limit(self, n): self._limit = n; return self
    def insert(self, row: dict): self._op = "insert"; self._payload = row; return self
    def update(self, row: dict): self._op = "update"; self._payload = row; return self
    def upsert(self, row: dict, on_conflict: str = ""): self._op = "insert"; self._payload = row; return self

    def _match(self, r: dict) -> bool:
        for op, col, val in self.filters:
            v = r.get(col)
            if op == "eq" and v != val: return False
            if op == "is" and not ((val == "null" and v is None) or (val != "null" and v is not None)): return False
            if op == "in" and v not in val: return False
        return True

    def execute(self):
        rows = _STORE.setdefault(self.name, [])
        if self._op == "insert":
            row = dict(self._payload); row.setdefault("id", str(uuid.uuid4())); row.setdefault("created_at", _now()); rows.append(row)
            return _Result([row])
        if self._op == "update":
            out = [r for r in rows if self._match(r)]
            for r in out: r.update(self._payload)
            return _Result(out)
        out = [dict(r) for r in rows if self._match(r)]
        if self._join and self.name == "posts":
            users = {u["id"]: u for u in _STORE["users"]}
            for r in out: r["users"] = {"name": users.get(r["user_id"], {}).get("name", "")}
        if self._order:
            col, desc = self._order; out.sort(key=lambda r: (r.get(col) is None, r.get(col)), reverse=desc)
        if self._limit: out = out[: self._limit]
        return _Result(out)


class _Result:
    def __init__(self, data): self.data = data


def table(name: str) -> _Query:
    return _Query(name)


def demo_users() -> list[dict]:
    _load(); return _STORE["users"]
