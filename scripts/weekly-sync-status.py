#!/usr/bin/env python3
"""Tell the agent whether Briq weekly catalogue syncs are still in flight.

Exit 0: safe to push/deploy agent updates.
Exit 2: freeze — do not push main or product-images; tell the user to wait.

Monday UTC: banner + CW / GG / BB / AX / Belstaff / Paul Smith / London Undercover
Tuesday UTC: Gucci
Other days: freeze only if a weekly job is still queued or in progress.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

REPO = "puruemae1-cloud/briq"
API = f"https://api.github.com/repos/{REPO}/actions/workflows"

MONDAY = [
    ("weekly-banner-refresh.yml", "배너 리프레시", "월 06:00 UTC / 15:00 KST"),
    ("weekly-cw-sync.yml", "크리스토퍼 워드", "월 08:00 UTC / 17:00 KST"),
    ("weekly-gg-sync.yml", "갈빈 그린", "월 09:00 UTC / 18:00 KST"),
    ("weekly-bb-sync.yml", "버버리", "월 10:00 UTC / 19:00 KST"),
    ("weekly-ax-sync.yml", "아크테릭스", "월 11:00 UTC / 20:00 KST"),
    ("weekly-bs-sync.yml", "벨스태프", "월 12:00 UTC / 21:00 KST"),
    ("weekly-ps-sync.yml", "폴 스미스", "월 13:00 UTC / 22:00 KST"),
    ("weekly-lu-sync.yml", "런던언더커버", "월 14:00 UTC / 23:00 KST"),
]
TUESDAY = [
    ("weekly-gc-sync.yml", "구찌", "화 07:00 UTC / 16:00 KST"),
]
ALL = MONDAY + TUESDAY


def _headers() -> dict[str, str]:
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "briq-weekly-sync-status",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _runs(file: str, created_from: str) -> list[dict]:
    url = (
        f"{API}/{file}/runs?per_page=15&created=>{created_from}"
        "&exclude_pull_requests=true"
    )
    try:
        data = _get(url)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub Actions API {e.code} for {file}") from e
    return list(data.get("workflow_runs") or [])


def _active(runs: list[dict]) -> list[dict]:
    return [r for r in runs if r.get("status") in {"queued", "in_progress", "waiting", "pending", "requested"}]


def _completed_today(runs: list[dict]) -> dict | None:
    done = [
        r
        for r in runs
        if r.get("status") == "completed" and r.get("conclusion") in {"success", "failure", "cancelled", "skipped"}
    ]
    return done[0] if done else None


def main() -> int:
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    created_from = f"{today}T00:00:00Z"
    weekday = now.weekday()  # Mon=0

    if weekday == 0:
        required = MONDAY
        day_ko = "월요일 주간 동기화"
    elif weekday == 1:
        required = TUESDAY
        day_ko = "화요일 주간 동기화(구찌)"
    else:
        required = []
        day_ko = None

    try:
        by_file = {file: _runs(file, created_from) for file, _label, _when in ALL}
    except Exception as e:
        if required:
            print(
                "주간 동기화 상태를 확인하지 못했습니다. "
                "월·화에는 새 업데이트를 배포하지 않습니다.\n"
                f"원인: {e}",
                file=sys.stderr,
            )
            print(
                "지금은 주간 카탈로그 동기화 요일입니다. "
                "동기화가 모두 끝난 뒤에 이어서 배포하겠습니다."
            )
            return 2
        print(f"weekly-sync-status: API unavailable ({e}); no required jobs today — allowing deploy.")
        return 0

    active_rows: list[str] = []
    waiting_rows: list[str] = []
    done_rows: list[str] = []

    for file, label, when in ALL:
        runs = by_file.get(file) or []
        live = _active(runs)
        finished = _completed_today(runs)
        if live:
            status = live[0].get("status")
            active_rows.append(f"- {label} ({when}) — {status}")
        elif finished:
            conc = finished.get("conclusion")
            done_rows.append(f"- {label} — {conc}")
        elif any(item[0] == file for item in required):
            waiting_rows.append(f"- {label} ({when}) — 아직 오늘 실행 없음")

    freeze = bool(active_rows or waiting_rows)

    if not freeze:
        print("weekly-sync-status: clear — weekly jobs are idle.")
        if done_rows:
            print("오늘 완료:")
            print("\n".join(done_rows))
        return 0

    print(
        "지금은 주간 카탈로그 동기화 중입니다. "
        "새 상품·카테고리·코드 업데이트는 동기화가 모두 끝난 뒤에 배포하겠습니다."
    )
    if day_ko:
        print(f"오늘은 {day_ko} 요일입니다.")
    if active_rows:
        print("진행 중:")
        print("\n".join(active_rows))
    if waiting_rows:
        print("대기(아직 시작 전):")
        print("\n".join(waiting_rows))
    if done_rows:
        print("오늘 완료:")
        print("\n".join(done_rows))
    print("동기화가 끝나면 같은 작업을 이어서 배포하면 됩니다.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
