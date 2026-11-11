"""Locked 1080×1350 frame for every Briq Instagram slide.

Photo window, type sizes, and the gap above briq.kr stay the same on every
slide. Cover kickers read 「briq.kr 검색」 in antique gold. The product name stays ink and the line under it stays muted.

The cover headline is the search keyword, and build_caption must use
that same phrase inside 「」. From the second slide on, the words are
product details only. The selling price is never drawn on a photo. It
belongs only in the caption, via build_caption. The price line sits
at the bottom, just above the air-shipping lines, and starts with 💰.
"""

import re

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
CREAM = (247, 244, 236)
INK = (20, 18, 16)
MUTED = (110, 102, 92)
GOLD = (154, 118, 62)
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
DISPLAY = "/tmp/briq-font/Fraunces-500.ttf"
_FALLBACK = "/Users/jeonghyunlee/Documents/briq/instagram-drafts/fonts/Fraunces-500.ttf"
if not __import__("pathlib").Path(DISPLAY).is_file():
    DISPLAY = _FALLBACK

SIDE = 56
PHOTO_X = 32
PHOTO_TOP = 48
PHOTO_W = W - PHOTO_X * 2
KICKER_COVER = 52
KICKER_BODY = 30
KICKER_SLOT = 54
HEADLINE = 68
SUB = 32
SUB_LEADING = 42
BRIQ = 36
BOTTOM = 28
GAP_SUB_BRIQ = 18
GAP_HEAD_SUB = 12
GAP_KICK_HEAD = 28
GAP_PHOTO_TEXT = 18
SUB_LINES = 2
_PRICE = re.compile(r"^[1-9]\d{0,2}(,\d{3})+원$")

# Lazy filler that must never appear on a slide. Body subtitles are product facts only.
BANNED_SLIDE_PHRASES = (
    "자세히 확인하세요",
    "자세히 확인해 주세요",
    "자세히 보세요",
    "확인해 보세요",
    "확인하세요",
    "더 알아보세요",
    "자세한 내용은",
    "상세 내용은",
    "클릭하세요",
    "검색해 보세요",
    "프로필 링크",
)


def assert_slide_copy(kicker, headline, sub, *, cover=False):
    """Refuse filler or empty body copy before a slide is drawn."""
    fields = {
        "kicker": strip_price(kicker or ""),
        "headline": strip_price(headline or ""),
        "sub": strip_price(sub or ""),
    }
    for name, text in fields.items():
        compact = re.sub(r"\s+", "", text)
        for banned in BANNED_SLIDE_PHRASES:
            if re.sub(r"\s+", "", banned) in compact:
                raise ValueError(
                    f"slide {name} must not use filler {banned!r}. "
                    "Write a short product fact instead."
                )
    if cover:
        return
    headline = fields["headline"].strip()
    sub = fields["sub"].strip()
    if not headline:
        raise ValueError("body headline is empty")
    if not sub:
        raise ValueError(
            "body subtitle is empty. Add a one- or two-line product fact, "
            "never a filler like 「자세히 확인하세요」."
        )
    if sub in {"확인", "자세히", "상세", "더보기", "...", "…"}:
        raise ValueError(f"body subtitle is not a product fact: {sub!r}")


def format_won(amount):
    """Catalog integer won into the only price form the caption accepts."""
    won = int(amount)
    if won < 1000:
        raise ValueError("price must be at least 1,000원")
    return f"{won:,}원"


def require_price(price):
    text = re.sub(r"\s+", "", str(price or ""))
    if not _PRICE.match(text):
        raise ValueError("price must look like 1,314,000원")
    return text


# Marks Apple SD Gothic Neo often draws as tofu (□/🗙) on slides.
# Keep the brand middot 「·」 — it is not in this set.
_SLIDE_MARKS = re.compile(r"[®©™℠ºª†‡§¶]+")


def sanitize_slide_text(text):
    """Drop trademark marks that the slide gothic font cannot draw."""
    cleaned = _SLIDE_MARKS.sub("", text or "")
    return re.sub(r"\s+", " ", cleaned).strip()


def strip_price(text):
    """Drop a selling price if it was passed into on-image copy."""
    cleaned = re.sub(r"[1-9]\d{0,2}(?:,\d{3})+원", "", text or "")
    cleaned = sanitize_slide_text(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip(" ·")


def same_search_phrase(headline, keyword):
    """Cover headline and the caption search phrase are one string."""
    cover = strip_price(headline).strip()
    phrase = (keyword or "").strip()
    if not cover or cover != phrase:
        raise ValueError(
            f"cover headline {cover!r} and caption search phrase {phrase!r} must be identical"
        )
    return phrase


def caption_search_phrase(caption):
    """The first 「검색어」 in a caption. Empty when the post is not a product search post."""
    match = re.search(r"「([^」]+)」", caption or "")
    return match.group(1).strip() if match else ""


def comment_text(raw):
    if isinstance(raw, str):
        return raw
    return (raw or b"").decode("utf-8", errors="replace")


def read_slide_record(path):
    """Headline plus the product, source photo, and category stored on a slide."""
    with Image.open(path) as image:
        raw = image.info.get("comment") or b""
    return parse_slide_comment(comment_text(raw))


def parse_slide_comment(text):
    phrase = ""
    product_id = ""
    source = ""
    category = ""
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("product:"):
            product_id = line.split(":", 1)[1].strip()
        elif line.startswith("source:"):
            source = line.split(":", 1)[1].strip()
        elif line.startswith("category:"):
            category = line.split(":", 1)[1].strip()
        elif not phrase:
            phrase = line
    return {
        "phrase": phrase,
        "product_id": product_id,
        "source": source,
        "category": category,
    }


def slide_comment(phrase, product_id, source, category):
    lines = []
    if (phrase or "").strip():
        lines.append(phrase.strip())
    lines.append(f"product:{(product_id or '').strip()}")
    lines.append(f"source:{(source or '').strip()}")
    lines.append(f"category:{(category or '').strip()}")
    return "\n".join(lines)


def read_search_phrase(path):
    """Phrase stamped into a cover JPEG by save_slide. Empty if the file has none."""
    return read_slide_record(path)["phrase"]


def assert_cover_matches_caption(cover_path, caption, keyword):
    """Refuse a publish when the drawn cover, the caption, and the keyword are not one phrase."""
    quoted = caption_search_phrase(caption)
    stamped = read_search_phrase(cover_path)
    phrase = (keyword or "").strip()
    if not quoted:
        raise ValueError("caption has no 「검색어」")
    if not stamped:
        raise ValueError("cover image has no locked search phrase")
    if len({quoted, stamped, phrase}) != 1:
        raise ValueError(
            "cover headline {cover!r}, caption search phrase {caption!r}, and keyword {keyword!r} must be identical".format(
                cover=stamped,
                caption=quoted,
                keyword=phrase,
            )
        )
    return quoted


PRICE_LINE = "💰 관부가세 및 배송비 모두 포함 : {amount}"
SHIP_LINE = "✈️ 영국 현지에서 항공편으로 안전하게 직배송됩니다."
NAVER_LINE = "네이버페이로 더욱 빠르고 간편하게 만나보세요."
CAPTION_FOOTER = f"{SHIP_LINE}\n{NAVER_LINE}"


def build_caption(keyword, brand_line, body, hashtags, price, *, cover):
    """Caption. Price sits above the air-shipping lines. No URL.

    ``cover`` is the image returned by render_slide(..., cover=True). The
    caption search phrase has to be the headline that image actually drew.
    """
    phrase = (keyword or "").strip()
    drawn = ""
    if cover is not None:
        drawn = (cover.info.get("briq_search") or "").strip()
    if not drawn or drawn != phrase:
        raise ValueError(
            f"caption search phrase {phrase!r} must be the headline drawn on the cover ({drawn!r})"
        )
    amount = require_price(price)
    tags = hashtags.strip() if isinstance(hashtags, str) else " ".join(hashtags)
    if "http://" in body or "https://" in body or "http://" in tags or "https://" in tags:
        raise ValueError("caption must not include a link")
    if not tags.startswith("#"):
        raise ValueError("caption needs hashtags")
    price_line = PRICE_LINE.format(amount=amount)
    if not price_line.startswith("💰 관부가세 및 배송비 모두 포함 : "):
        raise ValueError("price line must name duty, tax, and shipping before the amount")
    footer = f"{price_line}\n{CAPTION_FOOTER}"
    if "모든 상품은" in footer or "\n" in SHIP_LINE:
        raise ValueError("air shipping is one line and does not say 모든 상품은")
    if f"{SHIP_LINE}\n{NAVER_LINE}" not in footer:
        raise ValueError("the airplane line and the Naver Pay line must sit on consecutive lines")
    return (
        f"briq.kr에서 「{phrase}」를 검색하세요.\n"
        f"{brand_line.strip()}\n"
        f"\n"
        f"{body.strip()}\n"
        f"\n"
        f"{footer}\n"
        f"\n"
        f"{tags}\n"
    )


def gothic(size, index):
    return ImageFont.truetype(FONT, size, index=index)


def text_width(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def wrap(draw, text, font, max_width, max_lines):
    rest = (text or "").strip()
    lines = []
    while rest and len(lines) < max_lines:
        if text_width(draw, rest, font) <= max_width:
            lines.append(rest)
            rest = ""
            break
        best, lo, hi = 1, 1, len(rest)
        while lo <= hi:
            mid = (lo + hi) // 2
            if text_width(draw, rest[:mid], font) <= max_width:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        cut = best
        space = rest.rfind(" ", max(0, best - 8), best + 1)
        if 0 < space and space >= best - 6:
            cut = space
        lines.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    if rest and lines:
        last = lines[-1]
        while last and text_width(draw, last + "…", font) > max_width:
            last = last[:-1]
        lines[-1] = (last + "…") if last else "…"
    return lines


def frame():
    """Y positions shared by every slide. Subtitle slot is bottom-aligned."""
    briq_top = H - BOTTOM - BRIQ
    sub_bottom = briq_top - GAP_SUB_BRIQ
    sub_slot = SUB + (SUB_LINES - 1) * SUB_LEADING
    sub_top = sub_bottom - sub_slot
    headline_top = sub_top - GAP_HEAD_SUB - HEADLINE
    kicker_top = headline_top - GAP_KICK_HEAD - KICKER_SLOT
    photo_bottom = kicker_top - GAP_PHOTO_TEXT
    return {
        "briq_top": briq_top,
        "sub_bottom": sub_bottom,
        "sub_top": sub_top,
        "headline_top": headline_top,
        "kicker_top": kicker_top,
        "photo_bottom": photo_bottom,
        "photo_h": photo_bottom - PHOTO_TOP,
    }


def fit(image, width, height):
    scale = min(width / image.width, height / image.height)
    return image.resize(
        (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
        Image.Resampling.LANCZOS,
    )


def save_slide(image, path, product_id, source, category):
    """Write a slide JPEG stamped with the one product that owns the photo.

    `source` is that product's own catalog path, such as
    `/products/bv-pdp/loafer/1.jpg`. A photo is not eligible because its color,
    weave, or material looks like this product.
    """
    product_id = (product_id or "").strip()
    source = (source or "").strip()
    category = (category or "").strip()
    if not product_id or not source or not category:
        raise ValueError(
            "save_slide needs product_id, source, and category from the one product. "
            "Do not pass a photo chosen because the color matches."
        )
    phrase = (image.info.get("briq_search") or "").strip()
    comment = slide_comment(phrase, product_id, source, category)
    image.save(path, format="JPEG", quality=90, comment=comment.encode("utf-8"))
    stored = read_slide_record(path)
    if phrase and stored["phrase"] != phrase:
        raise RuntimeError("cover search phrase was not stored on the image")
    if stored["product_id"] != product_id or stored["source"] != source or stored["category"] != category:
        raise RuntimeError("slide product was not stored on the image")
    return path


def render_slide(photo, kicker, headline, sub, index, total, cover=False):
    kicker = strip_price(kicker)
    headline = strip_price(headline)
    sub = strip_price(sub)
    assert_slide_copy(kicker, headline, sub, cover=cover)
    if cover:
        if kicker != "briq.kr 검색":
            raise ValueError("cover kicker must be briq.kr 검색")
        if not headline:
            raise ValueError("cover headline is empty")
    box = frame()
    canvas = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(canvas)
    image = fit(photo, PHOTO_W, box["photo_h"])
    x = PHOTO_X + (PHOTO_W - image.width) // 2
    y = PHOTO_TOP + (box["photo_h"] - image.height) // 2
    canvas.paste(image, (x, y))

    count = f"{index}  /  {total}"
    count_font = gothic(26, 4)
    draw.text((W - 28 - text_width(draw, count, count_font), 12), count, font=count_font, fill=MUTED)

    kicker_size = KICKER_COVER if cover else KICKER_BODY
    kicker_font = gothic(kicker_size, 6 if cover else 5)
    draw.text((SIDE, box["kicker_top"]), kicker, font=kicker_font, fill=GOLD if cover else MUTED)

    max_width = W - SIDE * 2
    headline_font = gothic(HEADLINE, 6)
    if cover and text_width(draw, headline, headline_font) > max_width:
        raise ValueError(
            f"cover headline does not fit on one line, so it would no longer match the caption: {headline}"
        )
    headline_lines = wrap(draw, headline, headline_font, max_width, 1)
    painted = headline if cover else headline_lines[0]
    if cover and painted != headline:
        raise ValueError("cover headline must be drawn in full")
    draw.text((SIDE, box["headline_top"]), painted, font=headline_font, fill=INK)

    sub_font = gothic(SUB, 4)
    sub_limit = 1 if cover else SUB_LINES
    sub_lines = wrap(draw, sub, sub_font, max_width, sub_limit) if (sub or "").strip() else []
    sub_y = box["sub_bottom"] - (len(sub_lines) * SUB_LEADING - (SUB_LEADING - SUB))
    for line in sub_lines:
        draw.text((SIDE, sub_y), line, font=sub_font, fill=MUTED)
        sub_y += SUB_LEADING

    mark = ImageFont.truetype(DISPLAY, BRIQ)
    label = "briq.kr"
    draw.text((W - 36 - text_width(draw, label, mark), box["briq_top"]), label, font=mark, fill=INK)
    if cover:
        canvas.info["briq_search"] = headline
    return canvas
