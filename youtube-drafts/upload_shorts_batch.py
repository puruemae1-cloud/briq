#!/usr/bin/env python3
"""Upload a Briq Shorts batch folder: rich description, tags, channel comment.

Pinning is not exposed by YouTube Data API — comment is posted as the channel
so you can pin it in Studio in one tap. Usage:

  python3 upload_shorts_batch.py 06-multi-brand-shorts-10 --privacy public
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from yt_auth import get_credentials
from yt_copy import build_description, build_pinned_comment
from yt_upload import upload

ROOT = Path(__file__).resolve().parent


def load_meta(folder: Path) -> dict:
    meta = json.loads((folder / "meta.json").read_text())
    idx_lines = []
    # prefer live INDEX lines if present
    index_path = folder.parent / "INDEX.json"
    if index_path.exists():
        for t in json.loads(index_path.read_text()):
            if t.get("slug") == folder.name or t.get("id") == meta.get("id"):
                meta = {**t, **meta}
                idx_lines = t.get("lines") or []
                break
    if idx_lines and not meta.get("lines"):
        meta["lines"] = idx_lines
    if not meta.get("search"):
        title = meta.get("title") or ""
        meta["search"] = title.split("|", 1)[-1].strip() if "|" in title else meta.get("nameKo") or ""
    if not meta.get("brandKo"):
        meta["brandKo"] = (meta.get("title") or "").split("|", 1)[0].strip()
    if not meta.get("brandEn"):
        meta["brandEn"] = meta.get("brand") or meta.get("brandKo") or ""
    if not meta.get("kind"):
        meta["kind"] = "상품"
    if not meta.get("productUrl") and meta.get("id"):
        meta["productUrl"] = f"https://www.briq.kr/product/{meta['id']}"
    return meta


def post_comment(youtube, video_id: str, text: str) -> str | None:
    body = {
        "snippet": {
            "videoId": video_id,
            "topLevelComment": {"snippet": {"textOriginal": text[:9000]}},
        }
    }
    for attempt in range(1, 6):
        try:
            resp = youtube.commentThreads().insert(part="snippet", body=body).execute()
            return resp["id"]
        except HttpError as e:
            # comments can lag right after upload
            if e.resp.status in {400, 403, 409} and attempt < 5:
                time.sleep(2.5 * attempt)
                continue
            print(f"COMMENT_FAIL {video_id}: {e}")
            return None
    return None


def upload_folder(folder: Path, privacy: str, publish_at: str | None = None) -> dict:
    meta = load_meta(folder)
    video = folder / meta.get("file", f"{folder.name}.mp4")
    if not video.exists():
        mp4s = list(folder.glob("*.mp4"))
        if not mp4s:
            raise SystemExit(f"No mp4 in {folder}")
        video = mp4s[0]

    desc = build_description(meta)
    pinned = build_pinned_comment(meta)
    (folder / "description.txt").write_text(desc)
    (folder / "pinned-comment.txt").write_text(pinned)

    tags = [
        "Briq",
        "브릭",
        "명품직구",
        "영국명품",
        "영국직송",
        "Shorts",
        meta.get("brandKo") or "",
        meta.get("brandEn") or "",
        meta.get("search") or "",
        meta.get("kind") or "",
    ]
    tags = [t for t in tags if t][:15]

    title = meta.get("title") or f"{meta.get('brandKo')} | {meta.get('search')}"
    if "#Shorts" not in title and len(title) < 90:
        title = f"{title} #Shorts"

    resp = upload(
        file=video,
        title=title,
        description=desc,
        privacy=privacy,
        tags=tags,
        shorts=True,
        publish_at=publish_at,
    )
    video_id = resp["id"]
    youtube = build("youtube", "v3", credentials=get_credentials())
    # short wait so comments open
    time.sleep(3)
    comment_id = post_comment(youtube, video_id, pinned)

    out = {
        **meta,
        "youtubeId": video_id,
        "youtubeUrl": f"https://youtu.be/{video_id}",
        "studio": f"https://studio.youtube.com/video/{video_id}/edit",
        "commentId": comment_id,
        "description": desc,
        "pinnedComment": pinned,
        "privacy": "private" if publish_at else privacy,
        "publishAt": publish_at,
    }
    (folder / "upload.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(
        f"UPLOADED {folder.name} -> https://youtu.be/{video_id}"
        f" comment={'ok' if comment_id else 'FAIL (pin manually)'}"
    )
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("batch", help="Batch folder under youtube-drafts, e.g. 06-multi-brand-shorts-10")
    p.add_argument("--privacy", choices=("private", "unlisted", "public"), default="public")
    p.add_argument(
        "--publish-at",
        default="",
        help="ISO 8601 UTC schedule (e.g. 2026-11-10T13:00:00Z). Forces private until then.",
    )
    p.add_argument("--only", default="", help="Comma slug prefixes to upload, e.g. 01,02")
    args = p.parse_args()

    batch = Path(args.batch).expanduser()
    if not batch.is_absolute():
        batch = (ROOT / batch).resolve()
    if not batch.is_dir():
        raise SystemExit(f"Missing batch: {batch}")

    folders = sorted(
        [d for d in batch.iterdir() if d.is_dir() and (d / "meta.json").exists()],
        key=lambda d: d.name,
    )
    if args.only:
        want = {x.strip().zfill(2) for x in args.only.split(",") if x.strip()}
        folders = [d for d in folders if d.name[:2] in want]

    publish_at = args.publish_at.strip() or None
    results = []
    for folder in folders:
        results.append(upload_folder(folder, args.privacy, publish_at=publish_at))
        time.sleep(1.2)

    summary = batch / "UPLOADS.json"
    summary.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"DONE {len(results)} -> {summary}")
    print("NOTE: YouTube API cannot pin comments — Studio에서 방금 단 채널 댓글을 고정해 주세요.")


if __name__ == "__main__":
    main()
