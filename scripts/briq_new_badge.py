#!/usr/bin/env python3
"""Briq NEW badge helpers — stamp on weekly sync insert, expire after 7 days.

Weekly syncs register new SKUs with a fresh ``registeredAt``. Call
``stamp_new_badge`` for those rows and ``expire_new_badge`` / ``apply_new_badge_ttl``
on every rebuild so ``badge: "New"`` cannot linger past one week.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

NEW_BADGE_DAYS = 7
NEW_BADGE_LABEL = "New"
# Badges that must never be overwritten by Briq NEW.
PROTECTED_BADGES = {"Sale", "Nearly New", "% OFF"}


def _parse_iso(raw: str | None) -> datetime | None:
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(dt: datetime) -> str:
    return (
        dt.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def new_badge_start(prod: dict[str, Any]) -> datetime | None:
    return _parse_iso(prod.get("newBadgeAt")) or _parse_iso(prod.get("registeredAt"))


def is_within_new_window(prod: dict[str, Any], *, now: datetime | None = None) -> bool:
    start = new_badge_start(prod)
    if not start:
        return False
    now = now or utc_now()
    age = now - start
    return timedelta(0) <= age < timedelta(days=NEW_BADGE_DAYS)


def stamp_new_badge(
    prod: dict[str, Any],
    *,
    now: datetime | None = None,
    force: bool = False,
) -> bool:
    """Set Briq NEW on a newly synced / newly registered product.

    Skips Sale / Nearly New. Preserves an existing ``newBadgeAt`` so weekly
    re-runs do not extend the 7-day window. Returns True when modified.
    """
    now = now or utc_now()
    badge = (prod.get("badge") or "").strip()
    if badge in PROTECTED_BADGES and not force:
        return False
    changed = False
    if prod.get("badge") != NEW_BADGE_LABEL:
        prod["badge"] = NEW_BADGE_LABEL
        changed = True
    if force or not prod.get("newBadgeAt"):
        iso = to_iso(now)
        # Prefer existing registeredAt as the window start when present.
        reg = prod.get("registeredAt")
        if not force and reg and not prod.get("newBadgeAt"):
            iso = reg if isinstance(reg, str) else iso
        if prod.get("newBadgeAt") != iso:
            prod["newBadgeAt"] = iso
            changed = True
    if prod.get("editTier") not in {"signature", "bestseller", "new"}:
        prod["editTier"] = "new"
        changed = True
    return changed


def expire_new_badge(prod: dict[str, Any], *, now: datetime | None = None) -> bool:
    """Clear expired Briq NEW. Returns True when the row was modified."""
    now = now or utc_now()
    badge = (prod.get("badge") or "").strip()
    start = new_badge_start(prod)
    changed = False

    if badge == NEW_BADGE_LABEL:
        if start is None or (now - start) >= timedelta(days=NEW_BADGE_DAYS):
            prod.pop("badge", None)
            changed = True
            if prod.get("editTier") == "new":
                prod["editTier"] = "signature"
                changed = True

    # Drop stale newBadgeAt once outside the window (keeps catalogues tidy).
    nba = _parse_iso(prod.get("newBadgeAt"))
    if nba is not None and (now - nba) >= timedelta(days=NEW_BADGE_DAYS):
        if "newBadgeAt" in prod:
            prod.pop("newBadgeAt", None)
            changed = True

    return changed


def apply_new_badge_ttl(
    prod: dict[str, Any],
    *,
    now: datetime | None = None,
    newly_synced: bool = False,
) -> bool:
    """Stamp NEW for newly synced rows, otherwise expire past the 7-day window."""
    now = now or utc_now()
    if newly_synced:
        return stamp_new_badge(prod, now=now)
    # Migrate legacy badge:New → newBadgeAt from registeredAt so TTL can run.
    if (prod.get("badge") or "").strip() == NEW_BADGE_LABEL and not prod.get("newBadgeAt"):
        reg = prod.get("registeredAt")
        if reg:
            prod["newBadgeAt"] = reg
    return expire_new_badge(prod, now=now)
