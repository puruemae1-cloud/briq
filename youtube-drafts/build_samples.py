#!/usr/bin/env python3
"""Build Briq YouTube sample frames: Shorts 9:16 + long-form 16:9 cards."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
DISPLAY = "/tmp/briq-font/Fraunces-500.ttf"
FFMPEG = Path(
    "/Users/jeonghyunlee/Library/Python/3.9/lib/python/site-packages/"
    "imageio_ffmpeg/binaries/ffmpeg-osx64-v4.2.2"
)

INK = (20, 18, 16)
CREAM = (247, 244, 236)
GOLD = (154, 118, 62)
MUTED = (110, 102, 92)
WHITE = (255, 255, 255)


def font(size: int, *, display: bool = False) -> ImageFont.FreeTypeFont:
    path = DISPLAY if display and Path(DISPLAY).exists() else FONT
    try:
        return ImageFont.truetype(path, size=size, index=0)
    except Exception:
        return ImageFont.truetype(FONT, size=size)


def fit_cover(img: Image.Image, w: int, h: int) -> Image.Image:
    img = img.convert("RGB")
    scale = max(w / img.width, h / img.height)
    nw, nh = int(img.width * scale), int(img.height * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return img.crop((left, top, left + w, top + h))


def shade(draw: ImageDraw.ImageDraw, box, top_a=0, bot_a=180):
    x0, y0, x1, y1 = box
    for i in range(y1 - y0):
        a = int(top_a + (bot_a - top_a) * (i / max(1, y1 - y0 - 1)))
        draw.line([(x0, y0 + i), (x1, y0 + i)], fill=(20, 18, 16, a))


def center_text(draw, xy, text, fnt, fill=WHITE, stroke=0):
    x, y = xy
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        (x - tw / 2, y - th / 2),
        text,
        font=fnt,
        fill=fill,
        stroke_width=stroke,
        stroke_fill=(0, 0, 0),
    )


def won(n: int) -> str:
    return f"{n:,}원"


def build_shorts() -> Path:
    meta = json.loads((ASSETS / "66075906" / "meta.json").read_text())
    img0 = Image.open(ASSETS / "66075906" / "0.jpg")
    img1 = Image.open(ASSETS / "66075906" / "1.jpg")
    out_dir = ROOT / "01-shorts-tomford" / "frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    W, H = 1080, 1920

    frames: list[tuple[Path, float]] = []

    # 1 brand reveal
    im = fit_cover(img0, W, H).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    shade(d, (0, int(H * 0.55), W, H), 0, 200)
    center_text(d, (W / 2, H * 0.72), "TOM FORD", font(72, display=True), GOLD, 1)
    center_text(d, (W / 2, H * 0.80), "가죽 재킷", font(64), WHITE, 1)
    im = Image.alpha_composite(im, overlay).convert("RGB")
    p = out_dir / "01.jpg"
    im.save(p, quality=92)
    frames.append((p, 3.0))

    # 2 sale price slam
    im = fit_cover(img0, W, H).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    shade(d, (0, int(H * 0.45), W, H), 20, 220)
    center_text(d, (W / 2, H * 0.62), won(meta["price"]), font(96), WHITE, 2)
    center_text(d, (W / 2, H * 0.72), won(meta["compareAtPrice"]), font(44), MUTED, 0)
    # strike approximation
    bb = d.textbbox((0, 0), won(meta["compareAtPrice"]), font=font(44))
    tw = bb[2] - bb[0]
    y = H * 0.72
    d.line([(W / 2 - tw / 2 - 8, y), (W / 2 + tw / 2 + 8, y)], fill=GOLD, width=4)
    center_text(d, (W / 2, H * 0.82), "영국 Flannels 클리어런스", font(36), GOLD, 1)
    im = Image.alpha_composite(im, overlay).convert("RGB")
    p = out_dir / "02.jpg"
    im.save(p, quality=92)
    frames.append((p, 5.0))

    # 3 detail
    im = fit_cover(img1, W, H).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    shade(d, (0, int(H * 0.65), W, H), 0, 190)
    center_text(d, (W / 2, H * 0.78), "영국 현지몰 재고 기준", font(48), WHITE, 1)
    im = Image.alpha_composite(im, overlay).convert("RGB")
    p = out_dir / "03.jpg"
    im.save(p, quality=92)
    frames.append((p, 6.0))

    # 4 trust
    im = fit_cover(img0, W, H).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    shade(d, (0, int(H * 0.55), W, H), 10, 210)
    center_text(d, (W / 2, H * 0.70), "병행이 아니라", font(52), WHITE, 1)
    center_text(d, (W / 2, H * 0.78), "영국 Flannels 직송", font(52), GOLD, 1)
    im = Image.alpha_composite(im, overlay).convert("RGB")
    p = out_dir / "04.jpg"
    im.save(p, quality=92)
    frames.append((p, 7.0))

    # 5 CTA
    im = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(im)
    center_text(d, (W / 2, H * 0.42), "briq.kr", font(72, display=True), CREAM)
    center_text(d, (W / 2, H * 0.52), "검색창에 톰포드", font(44), GOLD)
    center_text(d, (W / 2, H * 0.62), "링크는 고정댓글", font(36), MUTED)
    p = out_dir / "05.jpg"
    im.save(p, quality=92)
    frames.append((p, 5.0))

    # write concat list for ffmpeg
    lst = out_dir / "concat.txt"
    lines = []
    for fp, sec in frames:
        lines.append(f"file '{fp}'")
        lines.append(f"duration {sec}")
    lines.append(f"file '{frames[-1][0]}'")
    lst.write_text("\n".join(lines) + "\n")

    mp4 = ROOT / "01-shorts-tomford" / "shorts-tomford.mp4"
    cmd = [
        str(FFMPEG),
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(lst),
        "-vf",
        "fps=30,format=yuv420p",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(mp4),
    ]
    subprocess.check_call(cmd)
    print("shorts", mp4, "sec", sum(s for _, s in frames))
    return mp4


def card_16x9(path: Path, lines: list[tuple[str, int, tuple]], bg=INK):
    W, H = 1920, 1080
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    d.rectangle((80, 80, W - 80, H - 80), outline=GOLD, width=2)
    y = 220
    for text, size, color in lines:
        center_text(d, (W / 2, y), text, font(size, display=("briq" in text.lower())), color)
        y += size + 36
    im.save(path, quality=92)


def photo_card(path: Path, photo: Path, title: str, price: str, was: str):
    W, H = 1920, 1080
    base = fit_cover(Image.open(photo), W, H).convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    shade(d, (0, int(H * 0.45), W, H), 0, 210)
    center_text(d, (W / 2, H * 0.62), title, font(48), WHITE, 1)
    center_text(d, (W / 2, H * 0.74), price, font(64), WHITE, 2)
    center_text(d, (W / 2, H * 0.84), was, font(36), MUTED, 0)
    Image.alpha_composite(base, overlay).convert("RGB").save(path, quality=92)


def build_long_cards() -> None:
    out = ROOT / "02-long-uk-vs-parallel" / "cards"
    out.mkdir(parents=True, exist_ok=True)
    card_16x9(
        out / "01-hook.jpg",
        [
            ("병행수입 vs 영국 직송", 64, CREAM),
            ("뭐가 다를까요?", 52, GOLD),
        ],
    )
    card_16x9(
        out / "02-parallel.jpg",
        [
            ("병행수입", 56, CREAM),
            ("누가 / 어디서 사 왔는지 한 겹 더", 40, MUTED),
        ],
    )
    card_16x9(
        out / "03-official.jpg",
        [
            ("공식수입", 56, CREAM),
            ("국내 A/S · 가격 체계가 명확", 40, MUTED),
        ],
    )
    card_16x9(
        out / "04-uk.jpg",
        [
            ("영국 현지몰 직송 (Briq)", 52, CREAM),
            ("영국에서 실제로 파는 재고 기준", 40, GOLD),
        ],
    )

    tf = json.loads((ASSETS / "66075906" / "meta.json").read_text())
    ow = json.loads((ASSETS / "66074518" / "meta.json").read_text())
    dz = json.loads((ASSETS / "11206003" / "meta.json").read_text())
    photo_card(
        out / "05-tomford.jpg",
        ASSETS / "66075906" / "0.jpg",
        "톰포드 라펠 재킷",
        won(tf["price"]),
        f"비교가 {won(tf['compareAtPrice'])}",
    )
    photo_card(
        out / "06-offwhite.jpg",
        ASSETS / "66074518" / "0.jpg",
        "오프화이트 애로우 후디",
        won(ow["price"]),
        f"비교가 {won(ow['compareAtPrice'])}",
    )
    photo_card(
        out / "07-diesel.jpg",
        ASSETS / "11206003" / "0.jpg",
        "디젤 첼시 부츠",
        won(dz["price"]),
        f"비교가 {won(dz['compareAtPrice'])}",
    )
    card_16x9(
        out / "08-howto.jpg",
        [
            ("결제 전에 볼 것", 56, CREAM),
            ("UK 사이즈 · 재고 · 할인율", 40, GOLD),
        ],
    )
    card_16x9(
        out / "09-cta.jpg",
        [
            ("briq.kr", 72, CREAM),
            ("다음 편: 시계 시세 차이", 40, GOLD),
        ],
    )
    print("long cards", out)


def write_docs() -> None:
    shorts_srt = """1
00:00:00,000 --> 00:00:03,000
톰포드 가죽 재킷

2
00:00:03,000 --> 00:00:08,000
440,000원
(비교가 9,638,000원)

3
00:00:08,000 --> 00:00:14,000
영국 Flannels 클리어런스

4
00:00:14,000 --> 00:00:21,000
병행이 아니라
영국 현지몰 재고 기준

5
00:00:21,000 --> 00:00:26,000
briq.kr
검색창에 톰포드
"""
    (ROOT / "01-shorts-tomford" / "shorts.srt").write_text(shorts_srt)

    long_srt = """1
00:00:00,000 --> 00:00:08,000
병행수입이랑, 영국 현지몰 직송은 뭐가 다르냐

2
00:00:08,000 --> 00:00:20,000
병행은 보통 “누가 어디서 사 왔는지”가 한 겹 더 있습니다

3
00:00:20,000 --> 00:00:32,000
공식수입은 국내 A/S·가격 체계가 명확하고요

4
00:00:32,000 --> 00:00:50,000
Briq가 하는 건 세 번째.
영국에서 실제로 파는 재고를 기준으로 올립니다

5
00:00:50,000 --> 00:01:05,000
그래서 가격이 흔들릴 수 있어요.
영국 세일·클리어런스가 그대로  Reflex니다

6
00:01:05,000 --> 00:01:25,000
예시 1. 톰포드 재킷 — 44만 원대

7
00:01:25,000 --> 00:01:45,000
예시 2. 오프화이트 후디 — 31만 원대

8
00:01:45,000 --> 00:02:05,000
예시 3. 디젤 첼시 부츠 — 35만 원대

9
00:02:05,000 --> 00:02:35,000
싸다고 바로 결제하지 마세요.
UK 사이즈, 재고, 할인율을 먼저 보세요

10
00:02:35,000 --> 00:03:00,000
링크는 설명란에.
다음엔 시계 시세 차이로 이어가겠습니다
"""
    (ROOT / "02-long-uk-vs-parallel" / "long.srt").write_text(long_srt)

    timing = ROOT / "01-shorts-tomford" / "TIMING.md"
    timing.write_text(
        """# Shorts 타이밍표 (45초 목표 / 현재 무성 샘플 ~26초)

| 초 | 화면 | 자막 | 나레이션 |
|----|------|------|----------|
| 0–3 | 01.jpg 전면 | 톰포드 가죽 재킷 | 톰포드 재킷, 국내에서 보면 가격이 확 뛰죠 |
| 3–8 | 02.jpg 가격 | 440,000원 / 비교가 취소선 | Briq는 영국 Flannels 클리어런스 기준으로 44만 원대 |
| 8–14 | 03.jpg 디테일 | 영국 Flannels 클리어런스 | 정가 환산하면 900만 원대 구간입니다 |
| 14–21 | 04.jpg 신뢰 | 병행이 아니라 / 영국 Flannels 직송 | 영국 현지몰 재고를 그대로 올리는 구조입니다 |
| 21–26 | 05.jpg CTA | briq.kr | 사이즈·재고는 briq.kr에서 확인하세요 |

## CapCut 편집
1. `shorts-tomford.mp4` 불러오기
2. `shorts.srt` 자막 임포트 (또는 화면 자막 유지)
3. 보이스오버 녹음 후 볼륨 -6dB로 깔기
4. 썸네일: 02.jpg 크롭 + 텍스트 `톰포드` / `44만`
"""
    )

    long_timing = ROOT / "02-long-uk-vs-parallel" / "TIMING.md"
    long_timing.write_text(
        """# 본영상 타이밍표 (~3분)

| 초 | 카드/화면 | 나레이션 포인트 |
|----|-----------|----------------|
| 0–8 | 01-hook | 오프닝 질문 |
| 8–20 | 02-parallel | 병행 한 겹 |
| 20–32 | 03-official | 공식수입 |
| 32–50 | 04-uk | Briq = 영국 재고 |
| 50–65 | 04-uk 유지 or 사이트 화면녹화 | 가격이 흔들리는 이유 |
| 65–85 | 05-tomford | 예시1 톰포드 |
| 85–105 | 06-offwhite | 예시2 오프화이트 |
| 105–125 | 07-diesel | 예시3 디젤 |
| 125–155 | 08-howto + 사이트 화면녹화 | UK/재고/할인율 |
| 155–180 | 09-cta | CTA + 다음 편 |

## CapCut 편집
1. `cards/` 순서대로 타임라인에 배치 (위 표 길이)
2. 65초·125초 구간에 briq.kr 상품페이지 화면녹화 삽입
3. `long.srt` 임포트
4. 썸네일: 01-hook 위에 `병행 ≠ 영국직송` / `이번주 세일`
"""
    )

    guide = ROOT / "README.md"
    guide.write_text(
        """# Briq YouTube 샘플 패키지

## Shorts
- 영상: `01-shorts-tomford/shorts-tomford.mp4` (9:16, 무성+번인 자막)
- 자막: `01-shorts-tomford/shorts.srt`
- 타이밍: `01-shorts-tomford/TIMING.md`
- 업로드 제목: `톰포드 재킷, 영국에선 이 가격입니다`
- 썸네일 문구: `톰포드` / `44만`

## 본영상
- 섹션 카드: `02-long-uk-vs-parallel/cards/`
- 자막: `02-long-uk-vs-parallel/long.srt`
- 타이밍: `02-long-uk-vs-parallel/TIMING.md`
- 업로드 제목: `영국 현지몰 직송이 병행수입이랑 뭐가 다른가요? (이번 주 Flannels 포함)`
- 썸네일 문구: `병행 ≠ 영국직송` / `이번주 세일`

## 재생성
```bash
python3 youtube-drafts/build_samples.py
```
"""
    )


def main() -> None:
    write_docs()
    build_long_cards()
    build_shorts()


if __name__ == "__main__":
    main()
