#!/usr/bin/env python3
"""Block a Briq Instagram publish when that product is already on the live feed."""

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit, urlunsplit, urlencode

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env.local"
LEDGER = Path(__file__).resolve().parent / "posted-products.json"
IG_USER = "17841459842402055"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from slide_layout import assert_cover_matches_caption, caption_search_phrase  # noqa: E402
from slide_product import assert_carousel_is_one_product  # noqa: E402


def token():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if line.startswith("INSTAGRAM_ACCESS_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(3)


def api(path):
    if path.startswith("https://graph.instagram.com/"):
        parts = urlsplit(path)
        query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "access_token"]
        url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))
    else:
        url = f"https://graph.instagram.com/v21.0/{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token()}"})
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            return json.loads(response.read().decode())
    except Exception as exc:
        print(f"instagram unreachable: {exc.__class__.__name__}", file=sys.stderr)
        raise SystemExit(3)


def live_posts():
    posts = []
    url = f"{IG_USER}/media?fields=id,caption,media_type,timestamp&limit=50"
    pages = 0
    while url and pages < 8:
        data = api(url)
        posts.extend(data.get("data") or [])
        next_url = (data.get("paging") or {}).get("next")
        url = next_url
        pages += 1
    return posts


def matches(caption, product_id, keyword):
    text = caption or ""
    if product_id and product_id in text:
        return True
    if keyword and keyword in text:
        return True
    return False


def find_live(product_id, keyword):
    hits = []
    for post in live_posts():
        if matches(post.get("caption") or "", product_id, keyword):
            hits.append(post)
    return hits


def load_ledger():
    if not LEDGER.exists():
        return {"posts": []}
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def save_ledger(data):
    data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_check(args):
    products = args.product or []
    if len(products) > 1:
        print("blocked: one post can contain only one product")
        for product_id in products:
            print(product_id)
        raise SystemExit(2)
    if not args.caption_file:
        print("blocked: pass --caption-file so the cover headline can be checked against the caption")
        raise SystemExit(4)
    caption_path = Path(args.caption_file)
    if not caption_path.is_file():
        print(f"blocked: caption file missing {caption_path}")
        raise SystemExit(4)
    caption = caption_path.read_text(encoding="utf-8")
    quoted = caption_search_phrase(caption)
    if quoted or "briq.kr에서" in caption:
        if not args.cover:
            print("blocked: product post needs --cover pointing at the cover jpeg")
            raise SystemExit(4)
        try:
            assert_cover_matches_caption(args.cover, caption, args.keyword or "")
        except ValueError as exc:
            print(f"blocked: {exc}")
            raise SystemExit(4)
        if not products:
            print(
                "blocked: pass --product for the single product in this carousel. "
                "A matching color is not another product."
            )
            raise SystemExit(4)
        try:
            assert_carousel_is_one_product(products[0], args.keyword or quoted, caption, args.cover)
        except ValueError as exc:
            print(f"blocked: {exc}")
            raise SystemExit(4)
    product_id = products[0] if products else ""
    hits = find_live(product_id, args.keyword or "")
    if hits:
        print("blocked: this product is already on the live feed")
        for post in hits:
            first = (post.get("caption") or "").splitlines()[0][:80]
            print(f"{post.get('timestamp')} {post.get('media_type')} {post.get('id')} {first}")
        raise SystemExit(2)
    print("clear: not on the live feed")


def cmd_record(args):
    if not args.product or not args.media_id:
        print("record needs --product and --media-id", file=sys.stderr)
        raise SystemExit(3)
    data = load_ledger()
    posts = [p for p in data.get("posts", []) if p.get("mediaId") != args.media_id]
    posts.append(
        {
            "mediaId": args.media_id,
            "productId": args.product,
            "keyword": args.keyword or "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    data["posts"] = posts
    save_ledger(data)
    print(f"recorded {args.product} {args.media_id}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    check = sub.add_parser("check")
    check.add_argument("--product", action="append")
    check.add_argument("--keyword")
    check.add_argument("--caption-file")
    check.add_argument("--cover")
    record = sub.add_parser("record")
    record.add_argument("--product", required=True)
    record.add_argument("--keyword")
    record.add_argument("--media-id", required=True)
    args = parser.parse_args()
    if args.cmd == "check":
        cmd_check(args)
    else:
        cmd_record(args)


if __name__ == "__main__":
    main()
