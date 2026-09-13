#!/usr/bin/env python3
"""Preserve Arc'teryx ``registeredAt`` across catalogue rebuilds.

Homepage rails / 최신등록순 use ``registeredAt`` (and ``updatedAt``). Re-stamping
every SKU on each weekly rebuild floods the luxury / shoes / accessories
rails with feed-order noise. Match Belstaff: keep existing dates; only stamp
brand-new SKUs (and apparel/footwear ``isNew``) with ``now``.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


def load_prev_registered(*paths: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in paths:
        if not path or not path.exists():
            continue
        try:
            if path.suffix == ".json":
                data = json.loads(path.read_text())
                rows = data if isinstance(data, list) else data.get("products") or []
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    pid = str(row.get("id") or "")
                    reg = row.get("registeredAt")
                    if pid and reg:
                        out[pid] = str(reg)
            else:
                text = path.read_text()
                parts = re.split(r"\n  \{\n    id: ", text)
                for part in parts[1:]:
                    try:
                        pid = part.split('"', 2)[1]
                    except IndexError:
                        continue
                    m = re.search(r'registeredAt:\s*"([^"]+)"', part)
                    if m:
                        out[pid] = m.group(1)
        except Exception:
            continue
    return out


def resolve_registered_at(
    style_id: str,
    *,
    prev: dict[str, str],
    is_new: bool,
    bump_is_new: bool,
    now: datetime,
    new_stamp_i: list[int],
) -> str:
    """Return ISO registeredAt. ``new_stamp_i`` is a one-element counter list."""
    if style_id in prev and not (bump_is_new and is_new):
        return prev[style_id]
    # Brand-new SKU, or apparel/footwear marked New on the official feed.
    stamp = now - timedelta(seconds=new_stamp_i[0])
    new_stamp_i[0] += 1
    return stamp.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)
