"""施設のプレースホルダー画像（SVG）。写真がないときに、カテゴリ色と施設名で代用する。"""
from __future__ import annotations

import base64
import html

COLORS = {"stay": ("#5B2D8E", "#EEE7F6"), "meal": ("#B3541E", "#FBEDE4"), "leisure": ("#0E7A55", "#E3F3EC")}
ICONS = {"stay": "🏨", "meal": "🍽", "leisure": "🎡"}


def svg(name: str, category: str, width: int = 320, height: int = 180) -> str:
    """施設名とカテゴリからSVG文字列を作る。"""
    fg, bg = COLORS.get(category, ("#6B6472", "#F1EFF3"))
    icon = ICONS.get(category, "📍")
    label = html.escape(name if len(name) <= 12 else name[:11] + "…")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" rx="10" fill="{bg}"/>'
        f'<text x="{width/2}" y="{height/2-8}" font-size="44" text-anchor="middle">{icon}</text>'
        f'<text x="{width/2}" y="{height/2+40}" font-size="13" font-family="sans-serif" fill="{fg}" text-anchor="middle">{label}</text>'
        f'</svg>'
    )


def data_url(name: str, category: str, **kw) -> str:
    """st.image に渡せる data URL。"""
    b = base64.b64encode(svg(name, category, **kw).encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b}"


def image_url(photo_url: str | None, name: str, category: str, **kw) -> str:
    """写真URLがあればそれ、なければプレースホルダー。"""
    return photo_url or data_url(name, category, **kw)
