"""Briq site-wide list pricing.

Every GBP→KRW converter should finish with {@link apply_site_price} so weekly
syncs keep the same public price as the live catalogue.

Current policy: 5% off the brand formula result, round to nearest 1,000원.
No strike-through / sale messaging — this becomes the displayed list price.
"""

from __future__ import annotations

SITE_PRICE_FACTOR = 0.95


def round_to_thousand(krw: float | int) -> int:
    return int(round(float(krw) / 1_000.0) * 1_000)


def apply_site_price(krw: float | int | None) -> int:
    """Final Briq list price from an already-converted KRW amount."""
    if krw is None:
        return 0
    raw = float(krw)
    if raw <= 0:
        return 0
    return round_to_thousand(raw * SITE_PRICE_FACTOR)
