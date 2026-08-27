#!/usr/bin/env python3
"""Tell the agent whether Briq weekly catalogue syncs are still in flight.

Exit 0: safe to push/deploy agent updates.
Exit 2: freeze — do not push main or product-images; tell the user to wait.

Friday UTC (UK early morning): banner + all brand weekly syncs, staggered from
01:00 UTC (02:00 UK during BST; 01:00 UK during GMT).
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

# GitHub cron is UTC. UK local ≈ UTC+1 in BST, UTC+0 in GMT.
FRIDAY = [
    ("weekly-banner-refresh.yml", "배너 리프레시", "금 01:00 UTC / 02:00 UK(BST)"),
    ("weekly-cw-sync.yml", "크리스토퍼 워드", "금 02:00 UTC / 03:00 UK(BST)"),
    ("weekly-gg-sync.yml", "갈빈 그린", "금 03:00 UTC / 04:00 UK(BST)"),
    ("weekly-bb-sync.yml", "버버리", "금 04:00 UTC / 05:00 UK(BST)"),
    ("weekly-ax-sync.yml", "아크테릭스", "금 05:00 UTC / 06:00 UK(BST)"),
    ("weekly-pr-sync.yml", "프라다", "금 06:00 UTC / 07:00 UK(BST)"),
    ("weekly-bs-sync.yml", "벨스태프", "금 07:00 UTC / 08:00 UK(BST)"),
    ("weekly-ps-sync.yml", "폴 스미스", "금 08:00 UTC / 09:00 UK(BST)"),
    ("weekly-lu-sync.yml", "런던언더커버", "금 09:00 UTC / 10:00 UK(BST)"),
    ("weekly-gc-sync.yml", "구찌", "금 10:00 UTC / 11:00 UK(BST)"),
    ("weekly-ch-sync.yml", "샤넬", "금 11:00 UTC / 12:00 UK(BST)"),
]
ALL = FRIDAY


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
        if e.code == 404:
            return []
        raise RuntimeError(f"GitHub Actions API {e.code} for {file}") from e
    return list(data.get("workflow_runs") or [])


def _active(runs: list[dict]) -> list[dict]:
    return [r for r in runs if r.get("status") in {"queued", "in_progress", "waiting", "pending", "requested"}]


def _completed_today(runs: list[dict]) -> dict | None:
    done = [
        r
        for r in runs
        if r.get("status") == "completed"
        and r.get("conclusion") in {"success", "failure", "cancelled", "skipped"}
    ]
    return done[0] if done else None


def _succeeded_today(runs: list[dict]) -> dict | None:
    """Only a successful run counts as finished for required weekly brands."""
    for r in runs:
        if r.get("status") == "completed" and r.get("conclusion") == "success":
            return r
    return None


def main() -> int:
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    created_from = f"{today}T00:00:00Z"
    weekday = now.weekday()  # Mon=0 … Fri=4

    if weekday == 4:
        required = FRIDAY
        day_ko = "금요일 주간 동기화(영국 새벽 2시부터)"
    else:
        required = []
        day_ko = None

    required_files = {file for file, _label, _when in required}

    try:
        by_file = {file: _runs(file, created_from) for file, _label, _when in ALL}
    except Exception as e:
        if required:
            print(
                "주간 동기화 상태를 확인하지 못했습니다. "
                "금요일에는 새 업데이트를 배포하지 않습니다.\n"
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
        ok = _succeeded_today(runs)
        finished = _completed_today(runs)
        must = file in required_files
        if live:
            status = live[0].get("status")
            active_rows.append(f"- {label} ({when}) — {status}")
        elif ok:
            done_rows.append(f"- {label} — success")
        elif must and finished and finished.get("conclusion") != "success":
            # Cancelled/failed weekly jobs auto-requeue; keep freeze until success.
            conc = finished.get("conclusion")
            waiting_rows.append(
                f"- {label} ({when}) — 오늘 {conc} (성공할 때까지 재시도 중·배포 보류)"
            )
        elif must:
            waiting_rows.append(f"- {label} ({when}) — 아직 오늘 실행 없음")
        elif finished:
            conc = finished.get("conclusion")
            done_rows.append(f"- {label} — {conc}")

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
