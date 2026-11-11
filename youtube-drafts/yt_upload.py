#!/usr/bin/env python3
"""Upload a video to the authorized Briq YouTube channel.

Example:
  python3 yt_upload.py \\
    --file 01-shorts-tomford/shorts-tomford.mp4 \\
    --title "Tom Ford 선글라스 | Briq" \\
    --description "영국 현지 명품 직송 briq.kr" \\
    --privacy private \\
    --shorts
"""
from __future__ import annotations

import argparse
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from yt_auth import get_credentials

ROOT = Path(__file__).resolve().parent


def upload(
    file: Path,
    title: str,
    description: str,
    privacy: str = "private",
    tags: list[str] | None = None,
    shorts: bool = False,
    category_id: str = "22",
    publish_at: str | None = None,
) -> dict:
    if not file.is_file():
        raise SystemExit(f"Missing video: {file}")

    desc = description.strip()
    if shorts and "#Shorts" not in desc and "#shorts" not in desc:
        desc = f"{desc}\n\n#Shorts".strip()

    youtube = build("youtube", "v3", credentials=get_credentials())
    status: dict = {
        "privacyStatus": privacy,
        "selfDeclaredMadeForKids": False,
    }
    # YouTube schedules only from private + publishAt (ISO 8601 UTC).
    if publish_at:
        status["privacyStatus"] = "private"
        status["publishAt"] = publish_at
        status["selfDeclaredMadeForKids"] = False
    body = {
        "snippet": {
            "title": title[:100],
            "description": desc[:5000],
            "tags": tags or ["Briq", "브릭", "명품직구", "영국명품"],
            "categoryId": category_id,
            "defaultLanguage": "ko",
            "defaultAudioLanguage": "ko",
        },
        "status": status,
    }
    media = MediaFileUpload(str(file), chunksize=8 * 1024 * 1024, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"upload {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"OK: https://youtu.be/{video_id}")
    print(f"studio: https://studio.youtube.com/video/{video_id}/edit")
    return response


def main() -> None:
    p = argparse.ArgumentParser(description="Upload to Briq YouTube")
    p.add_argument("--file", required=True, help="Video path (absolute or under youtube-drafts)")
    p.add_argument("--title", required=True)
    p.add_argument("--description", default="")
    p.add_argument(
        "--privacy",
        choices=("private", "unlisted", "public"),
        default="private",
    )
    p.add_argument("--tags", default="", help="Comma-separated tags")
    p.add_argument("--shorts", action="store_true", help="Append #Shorts to description")
    args = p.parse_args()

    path = Path(args.file).expanduser()
    if not path.is_absolute():
        path = (ROOT / path).resolve()

    tags = [t.strip() for t in args.tags.split(",") if t.strip()] or None
    upload(
        file=path,
        title=args.title,
        description=args.description,
        privacy=args.privacy,
        tags=tags,
        shorts=args.shorts,
    )


if __name__ == "__main__":
    main()
