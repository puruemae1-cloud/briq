#!/usr/bin/env python3
"""Load Briq Instagram Graph credentials.

Local: INSTAGRAM_ACCESS_TOKEN in briq/.env.local
Cloud Automations: set Runtime Secret INSTAGRAM_ACCESS_TOKEN
Optional: INSTAGRAM_IG_USER_ID (defaults to @briq.kr business id)
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_LOCAL = ROOT / ".env.local"
DEFAULT_IG_USER = "17841459842402055"  # @briq.kr
GRAPH = "https://graph.instagram.com/v21.0"


def _from_dotenv(name: str) -> str:
    if not ENV_LOCAL.exists():
        return ""
    prefix = f"{name}="
    for line in ENV_LOCAL.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def access_token() -> str:
    tok = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip() or _from_dotenv(
        "INSTAGRAM_ACCESS_TOKEN"
    )
    if not tok:
        raise SystemExit(
            "Missing INSTAGRAM_ACCESS_TOKEN (env / Cloud Runtime Secret / .env.local)"
        )
    return tok


def ig_user_id() -> str:
    override = (
        os.environ.get("INSTAGRAM_IG_USER_ID", "").strip()
        or _from_dotenv("INSTAGRAM_IG_USER_ID")
    )
    if override:
        return override
    # Instagram Login tokens expose the publishable id on /me
    try:
        mid = str(verify().get("id") or "")
        if mid:
            return mid
    except Exception:
        pass
    return DEFAULT_IG_USER


def graph_get(path: str, token: str | None = None) -> dict:
    tok = token or access_token()
    url = path if path.startswith("http") else f"{GRAPH}/{path.lstrip('/')}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def verify() -> dict:
    me = graph_get("me?fields=id,username")
    return me


def main() -> None:
    me = verify()
    print(f"OK: @{me.get('username')} id={me.get('id')}")
    print(f"publish_user={ig_user_id()}")


if __name__ == "__main__":
    main()
