#!/usr/bin/env python3
"""Keep www.briq.kr up: roll production back when it is down, re-promote once fixed.

  python3 scripts/vercel-auto-rollback.py rollback   # after the homepage guard fails
  python3 scripts/vercel-auto-rollback.py restore    # after every Production deploy

rollback: confirms the outage independently (the guard also fails on cosmetic
checks), then instantly rolls back to the newest earlier Production deployment
that passes the same smoke test. A rollback pauses auto-promotion of new
deployments; `restore` lifts it by promoting the next deployment that passes
the smoke test, so a fixed commit goes live without anyone touching Vercel.

Needs VERCEL_TOKEN; without it both commands are no-ops (exit 0).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

SITE = os.environ.get("SITE", "https://www.briq.kr")
DOMAIN = SITE.split("://", 1)[1]
TEAM = os.environ.get("VERCEL_ORG_ID", "team_gIdHoMTkKstRK0tTfiRglVyi")
PROJECT = os.environ.get("VERCEL_PROJECT_ID", "prj_Wg8ManP2LusTOmD4KilHPBq7rA29")
TOKEN = os.environ.get("VERCEL_TOKEN", "")
PATHS = ["/", "/shop", "/api/products/shop?category=all"]
TIMEOUT = 30


def vapi(path: str, method: str = "GET") -> dict:
    sep = "&" if "?" in path else "?"
    req = urllib.request.Request(
        f"https://api.vercel.com{path}{sep}teamId={TEAM}",
        method=method,
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def fetch_site(path: str) -> tuple[int, str]:
    req = urllib.request.Request(SITE + path, headers={"User-Agent": "briq-auto-rollback"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""


def vercel(*args: str, timeout: int = 300) -> subprocess.CompletedProcess:
    env = dict(os.environ, VERCEL_ORG_ID=TEAM, VERCEL_PROJECT_ID=PROJECT)
    return subprocess.run(
        ["npx", "--yes", "vercel@latest", *args],
        env=env, capture_output=True, text=True, timeout=timeout,
    )


def fetch_deployment(url: str):
    def get(path: str) -> tuple[int, str]:
        try:
            p = vercel("curl", path, "--deployment", url, "-s", "--max-time", str(TIMEOUT),
                       "-w", "\n%{http_code}", timeout=TIMEOUT + 90)
        except subprocess.TimeoutExpired:
            return 0, ""
        body, _, code = p.stdout.rpartition("\n")
        return int(code) if code.strip().isdigit() else 0, body
    return get


def healthy(get) -> list[str]:
    """Paths that fail (empty list = healthy). Checks one product page too."""
    bad = []
    shop = ""
    for path in PATHS:
        code, body = get(path)
        if code != 200:
            bad.append(f"{path}={code}")
        if path == "/shop":
            shop = body
    product = re.search(r'href="(/product/[^"?#]+)"', shop)
    if product:
        code, _ = get(product.group(1))
        if code != 200:
            bad.append(f"{product.group(1)}={code}")
    elif not bad:
        bad.append("/shop has no product links")
    return bad


def current_deployment_id() -> str:
    return vapi(f"/v13/deployments/{DOMAIN}")["id"]


def production_deployments() -> list[dict]:
    deps = vapi(f"/v6/deployments?projectId={PROJECT}&target=production&state=READY&limit=20")["deployments"]
    return sorted(deps, key=lambda d: d["created"], reverse=True)


def rollback() -> int:
    for attempt in range(3):
        bad = healthy(fetch_site)
        if not bad:
            print(f"{SITE} is healthy (check {attempt + 1}) — no rollback.")
            return 0
        print(f"check {attempt + 1}: {SITE} failing: {', '.join(bad)}", flush=True)
        if attempt < 2:
            time.sleep(40)

    current = current_deployment_id()
    tried = 0
    for dep in production_deployments():
        if dep["uid"] == current:
            continue
        tried += 1
        if tried > 4:
            break
        url = "https://" + dep["url"]
        bad = healthy(fetch_deployment(url))
        if bad:
            print(f"candidate {dep['uid']} also failing: {', '.join(bad)}", flush=True)
            continue
        print(f"rolling back {current} → {dep['uid']} ({url})", flush=True)
        p = vercel("rollback", url, "--yes", "--timeout", "5m", timeout=420)
        print(p.stdout[-1500:], p.stderr[-1500:])
        time.sleep(30)
        print(f"after rollback: {healthy(fetch_site) or 'healthy'}")
        return 0 if p.returncode == 0 else 1
    print("ERROR: no healthy earlier deployment to roll back to (platform outage?)")
    return 1


def restore() -> int:
    project = vapi(f"/v9/projects/{PROJECT}")
    if not project.get("lastRollbackTarget"):
        print("production is not rolled back — nothing to restore.")
        return 0
    current = current_deployment_id()
    newest = production_deployments()[0]
    if newest["uid"] == current:
        print("newest deployment is already live.")
        return 0
    url = "https://" + newest["url"]
    bad = healthy(fetch_deployment(url))
    if bad:
        print(f"newest deployment {newest['uid']} still failing ({', '.join(bad)}) — staying rolled back.")
        return 1
    print(f"promoting healthy {newest['uid']} ({url}) and resuming auto-promotion", flush=True)
    p = vercel("promote", url, "--yes", "--timeout", "5m", timeout=420)
    print(p.stdout[-1500:], p.stderr[-1500:])
    return 0 if p.returncode == 0 else 1


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"rollback", "restore"}:
        print(__doc__)
        return 2
    if not TOKEN:
        print("::warning::VERCEL_TOKEN secret is not set — automatic rollback is disabled.")
        return 0
    return rollback() if sys.argv[1] == "rollback" else restore()


if __name__ == "__main__":
    sys.exit(main())
