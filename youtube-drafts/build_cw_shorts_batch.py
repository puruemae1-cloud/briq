#!/usr/bin/env python3
"""Build 10 Christopher Ward Shorts: 5 topics × male/female news-style VO."""
from __future__ import annotations

import asyncio
import json
import re
import subprocess
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/Users/jeonghyunlee/Documents/briq/youtube-drafts/04-cw-shorts-batch")
IMG_ROOT = Path("/Users/jeonghyunlee/Documents/briq/public/products/cw-pdp")
FFMPEG = Path(
    "/Users/jeonghyunlee/Library/Python/3.9/lib/python/site-packages/"
    "imageio_ffmpeg/binaries/ffmpeg-osx64-v4.2.2"
)
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
DISPLAY = "/tmp/briq-font/Fraunces-500.ttf"

INK = (20, 18, 16)
CREAM = (247, 244, 236)
GOLD = (154, 118, 62)
MUTED = (110, 102, 92)
WHITE = (255, 255, 255)

PREVIEW_SPEED = 1.08
VOICES = {
    "male": ("ko-KR-InJoonNeural", "-5%", "-2Hz"),
    "female": ("ko-KR-SunHiNeural", "-4%", "-1Hz"),
}

TOPICS = [
    {
        "slug": "01-sealander-auto",
        "folder": "c63-39ada4-s00b0-rk",
        "brand": "Christopher Ward",
        "name": "C63 시랜더 오토매틱",
        "color": "스카이 블루",
        "price": 2603000,
        "gbp": 1150,
        "title": "요즘 크리스토퍼 워드 왜 이렇게 많이 보여요?",
        "thumb": ["시랜더", "260만"],
        "lines": [
            "최근 소셜미디어에서 크리스토퍼 워드 시계를 심심치 않게 볼 수 있습니다.",
            "그중에서도 가장 많이 언급되는 모델이, C63 시랜더 오토매틱입니다.",
            "영국 공식 가격은 천백오십 파운드. 브릭 기준으로는 이백육십만 원대입니다.",
            "영국 매뉴팩처의 완성도를, 미드레인지 가격대에서 만날 수 있다는 점이 인기 요인입니다.",
            "일상용 첫 기계식 시계를 고민하는 분들 사이에서 특히 선택이 많습니다.",
            "시랜더 재고와 옵션은, 브릭 점 케이알에서 확인하실 수 있습니다.",
        ],
        "cards": [
            ("요즘 왜 이렇게", "많이 보이지?"),
            ("Christopher Ward", "C63 시랜더 오토매틱"),
            (None, "PRICE"),
            ("영국 매뉴팩처 감성", "가격은 미드레인지"),
            ("시랜더 = CW 입문의 정석", "데일리로 많이 고르는 이유"),
            ("briq.kr", "검색: 시랜더"),
        ],
    },
    {
        "slug": "02-sealander-gmt",
        "folder": "c63-36agm4-s00b0-b0",
        "brand": "Christopher Ward",
        "name": "C63 시랜더 GMT",
        "color": "스카이 블루",
        "price": 3116000,
        "gbp": 1395,
        "title": "출장 많은 분들, 시랜더 GMT 보셨나요?",
        "thumb": ["시랜더 GMT", "311만"],
        "lines": [
            "여행과 출장이 잦은 분들 사이에서, 시랜더 GMT 관심이 커지고 있습니다.",
            "시랜더 라인에 두 번째 시침을 더한, C63 시랜더 GMT입니다.",
            "영국 공식 가격은 천삼백구십오 파운드. 브릭 기준 삼백십일만 원대입니다.",
            "일상용 디자인에 시차 확인 기능을 더해, 활용 범위가 넓습니다.",
            "과하지 않은 GMT를 찾는 분들께 자주 추천되는 구성입니다.",
            "시랜더 GMT 재고는 브릭 점 케이알에서 확인하실 수 있습니다.",
        ],
        "cards": [
            ("출장 많은 분들", "시랜더 GMT 보셨나요?"),
            ("Christopher Ward", "C63 시랜더 GMT"),
            (None, "PRICE"),
            ("데일리 디자인에", "시차 확인까지"),
            ("과하지 않은 GMT", "실사용 추천 구성"),
            ("briq.kr", "검색: 시랜더 GMT"),
        ],
    },
    {
        "slug": "03-bel-canto",
        "folder": "c01-41apt3-t00o0-mw",
        "brand": "Christopher Ward",
        "name": "C1 벨 칸토 클래식",
        "color": "Negroni",
        "price": 10650000,
        "gbp": 4995,
        "title": "점핑아워 시계, 벨 칸토가 왜 화제죠?",
        "thumb": ["벨 칸토", "점핑아워"],
        "lines": [
            "크리스토퍼 워드 가운데, 가장 화제가 된 모델 중 하나가 벨 칸토입니다.",
            "시간은 창으로 뛰어 넘기고, 분은 궤도를 따라 움직이는 점핑아워 구조입니다.",
            "영국 공식 가격은 사천구백구십오 파운드. 브릭 기준 천육십오만 원대입니다.",
            "미드레인지에서 보기 드문 컴플리케이션이라, 소장 가치가 높게 평가됩니다.",
            "디자인과 기계적 재미를 동시에 원하는 분들께 특히 반응이 좋습니다.",
            "벨 칸토 옵션은 브릭 점 케이알에서 확인하실 수 있습니다.",
        ],
        "cards": [
            ("점핑아워 시계", "왜 이렇게 화제죠?"),
            ("Christopher Ward", "C1 벨 칸토 클래식"),
            (None, "PRICE"),
            ("미드레인지에서 드문", "컴플리케이션"),
            ("디자인 + 기계적 재미", "소장 수요가 큰 이유"),
            ("briq.kr", "검색: 벨 칸토"),
        ],
    },
    {
        "slug": "04-trident-pro",
        "folder": "c60-44ada31s0bb1-b0",
        "brand": "Christopher Ward",
        "name": "C60 트라이던트 프로 300",
        "color": "블루",
        "price": 2480000,
        "gbp": 1095,
        "title": "다이버 입문, 트라이던트 프로 300",
        "thumb": ["트라이던트", "248만"],
        "lines": [
            "다이버 워치 입문을 고민하신다면, 트라이던트 프로 삼백을 먼저 보시면 좋습니다.",
            "크리스토퍼 워드의 대표 다이버 라인, C60 트라이던트 프로 삼백입니다.",
            "영국 공식 가격은 천구십오 파운드. 브릭 기준 이백사십팔만 원대입니다.",
            "삼백 미터 방수와 선명한 가독성이, 실사용 다이버로서 강점입니다.",
            "과시보다 기능과 완성도를 보는 분들께 잘 맞는 선택입니다.",
            "트라이던트 재고는 브릭 점 케이알에서 확인하실 수 있습니다.",
        ],
        "cards": [
            ("다이버 입문", "어디서 시작할까요?"),
            ("Christopher Ward", "C60 트라이던트 프로 300"),
            (None, "PRICE"),
            ("300m 방수", "실사용 다이버의 기본기"),
            ("과시보다 완성도", "입문 다이버로 자주 추천"),
            ("briq.kr", "검색: 트라이던트"),
        ],
    },
    {
        "slug": "05-twelve",
        "folder": "c12-38h2h1-sk0k0-b0",
        "brand": "Christopher Ward",
        "name": "트웰브 660",
        "color": "BLK · 38mm",
        "price": 4114000,
        "gbp": 1875,
        "title": "각진 케이스 좋아하면, 트웰브 보세요",
        "thumb": ["트웰브", "411만"],
        "lines": [
            "둥근 케이스에 질리셨다면, 크리스토퍼 워드 트웰브를 한번 보세요.",
            "각진 실루엣이 특징인, 트웰브 육백육십 삼십팔 밀리미터입니다.",
            "영국 공식 가격은 천팔백칠십오 파운드. 브릭 기준 사백십일만 원대입니다.",
            "도심 착장에서 존재감이 분명해, 스타일 포인트로 고르는 분들이 많습니다.",
            "스포츠와 드레스 사이, 그 중간 지점을 찾는 분들께 잘 맞습니다.",
            "트웰브 재고는 브릭 점 케이알에서 확인하실 수 있습니다.",
        ],
        "cards": [
            ("각진 케이스", "좋아하시나요?"),
            ("Christopher Ward", "트웰브 660 · 38mm"),
            (None, "PRICE"),
            ("도심 착장에서", "존재감이 분명한 실루엣"),
            ("스포츠와 드레스 사이", "중간 지점의 선택"),
            ("briq.kr", "검색: 트웰브"),
        ],
    },
]


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


def run(cmd: list[str]) -> None:
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def dur(path: Path) -> float:
    p = subprocess.run([str(FFMPEG), "-i", str(path)], capture_output=True, text=True)
    text = (p.stderr or "") + (p.stdout or "")
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", text)
    if not m:
        raise RuntimeError(f"no duration: {path}")
    h, m_, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return h * 3600 + m_ * 60 + s


def pick_shots(folder: str) -> list[Path]:
    d = IMG_ROOT / folder
    prefer = [1, 2, 3, 4, 5, 6]
    shots = []
    for i in prefer:
        p = d / f"{i}.jpg"
        if p.exists():
            shots.append(p)
    if not shots:
        shots = sorted(d.glob("*.jpg"))[:4]
    while len(shots) < 4:
        shots.append(shots[-1])
    return shots[:4]


def render_frames(topic: dict, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    shots = pick_shots(topic["folder"])
    W, H = 1080, 1920
    frames: list[Path] = []
    for idx, (line1, line2) in enumerate(topic["cards"]):
        if idx == 5:
            im = Image.new("RGB", (W, H), INK)
            d = ImageDraw.Draw(im)
            center_text(d, (W / 2, H * 0.40), line1, font(72, display=True), CREAM)
            center_text(d, (W / 2, H * 0.52), line2, font(44), GOLD)
            center_text(d, (W / 2, H * 0.62), "Christopher Ward 공식 취급", font(30), MUTED)
        else:
            photo = shots[min(idx, len(shots) - 1)]
            im = fit_cover(Image.open(photo), W, H).convert("RGBA")
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            shade(d, (0, int(H * 0.50), W, H), 8, 220)
            if line2 == "PRICE":
                center_text(d, (W / 2, H * 0.62), won(topic["price"]), font(84), WHITE, 2)
                center_text(
                    d,
                    (W / 2, H * 0.72),
                    f"£{topic['gbp']:,} · 영국 공식",
                    font(40),
                    GOLD,
                    1,
                )
                center_text(d, (W / 2, H * 0.82), topic["color"], font(34), CREAM, 1)
            else:
                center_text(d, (W / 2, H * 0.68), line1, font(48), WHITE, 1)
                center_text(
                    d,
                    (W / 2, H * 0.78),
                    line2,
                    font(48 if idx == 0 else 42),
                    GOLD if idx else GOLD,
                    1,
                )
            im = Image.alpha_composite(im, ov).convert("RGB")
        path = out_dir / f"{idx+1:02d}.jpg"
        im.save(path, quality=92)
        frames.append(path)
    return frames


async def synth_segment(text: str, voice: str, rate: str, pitch: str, mp3: Path) -> None:
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(str(mp3))


async def build_one(topic: dict, gender: str) -> Path:
    slug = topic["slug"]
    out = ROOT / slug
    frames_dir = out / "frames"
    voice_dir = out / f"voice_{gender}"
    voice_dir.mkdir(parents=True, exist_ok=True)
    frames = render_frames(topic, frames_dir)

    voice_name, rate, pitch = VOICES[gender]
    wavs = []
    for i, text in enumerate(topic["lines"], 1):
        mp3 = voice_dir / f"seg_{i:02d}.mp3"
        wav = voice_dir / f"seg_{i:02d}.wav"
        await synth_segment(text, voice_name, rate, pitch, mp3)
        run([str(FFMPEG), "-y", "-i", str(mp3), "-ac", "1", "-ar", "44100", str(wav)])
        fast = voice_dir / f"seg_{i:02d}_fast.wav"
        run(
            [
                str(FFMPEG),
                "-y",
                "-i",
                str(wav),
                "-filter:a",
                f"atempo={PREVIEW_SPEED}",
                "-ac",
                "1",
                "-ar",
                "44100",
                str(fast),
            ]
        )
        d = dur(fast)
        pad = 0.14 if i < 6 else 0.08
        wavs.append((fast, d, pad))

    alist = voice_dir / "concat.txt"
    lines = []
    for i, (wav, d, pad) in enumerate(wavs):
        lines.append(f"file '{wav}'")
        sil = voice_dir / f"sil_{i+1:02d}.wav"
        run(
            [
                str(FFMPEG),
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=44100:cl=mono",
                "-t",
                f"{pad:.3f}",
                str(sil),
            ]
        )
        lines.append(f"file '{sil}'")
    alist.write_text("\n".join(lines) + "\n")
    narration = voice_dir / "narration.wav"
    run([str(FFMPEG), "-y", "-f", "concat", "-safe", "0", "-i", str(alist), "-c", "copy", str(narration)])
    narration_eq = voice_dir / "narration_eq.wav"
    run(
        [
            str(FFMPEG),
            "-y",
            "-i",
            str(narration),
            "-af",
            "highpass=f=80,lowpass=f=12000,equalizer=f=3000:t=q:w=1:g=2,loudnorm=I=-16:TP=-1.5:LRA=11",
            str(narration_eq),
        ]
    )

    vlist = voice_dir / "video_concat.txt"
    vlines = []
    for img, (wav, d, pad) in zip(frames, wavs):
        vlines.append(f"file '{img}'")
        vlines.append(f"duration {d+pad:.3f}")
    vlines.append(f"file '{frames[-1]}'")
    vlist.write_text("\n".join(vlines) + "\n")
    silent = voice_dir / "silent.mp4"
    run(
        [
            str(FFMPEG),
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(vlist),
            "-vf",
            "fps=30,format=yuv420p",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(silent),
        ]
    )

    final = out / f"{slug}-{gender}.mp4"
    run(
        [
            str(FFMPEG),
            "-y",
            "-i",
            str(silent),
            "-i",
            str(narration_eq),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(final),
        ]
    )

    # SRT rough from lines + durations
    srt_lines = []
    t = 0.0
    for i, ((wav, d, pad), text) in enumerate(zip(wavs, topic["lines"]), 1):
        start, end = t, t + d + pad

        def ts(x: float) -> str:
            h = int(x // 3600)
            m = int((x % 3600) // 60)
            s = x % 60
            return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

        srt_lines.append(f"{i}\n{ts(start)} --> {ts(end)}\n{text}\n")
        t = end
    (out / f"{slug}-{gender}.srt").write_text("\n".join(srt_lines))
    print(f"OK {final.name} {dur(final):.1f}s", flush=True)
    return final


async def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    # validate images
    for t in TOPICS:
        shots = pick_shots(t["folder"])
        if not shots:
            raise SystemExit(f"missing images for {t['folder']}")
        print("topic", t["slug"], "shots", len(shots), flush=True)

    results = []
    for topic in TOPICS:
        meta = {
            "title": topic["title"],
            "thumb": topic["thumb"],
            "price": topic["price"],
            "gbp": topic["gbp"],
            "name": topic["name"],
            "folder": topic["folder"],
        }
        (ROOT / topic["slug"]).mkdir(parents=True, exist_ok=True)
        (ROOT / topic["slug"] / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2)
        )
        for gender in ("male", "female"):
            results.append(await build_one(topic, gender))

    index = []
    for p in results:
        index.append({"file": str(p), "size": p.stat().st_size})
    (ROOT / "INDEX.json").write_text(json.dumps(index, ensure_ascii=False, indent=2))
    readme = [
        "# Christopher Ward Shorts × 10",
        "",
        "남성(InJoon) 5 + 여성(SunHi) 5. 뉴스 톤 뉴럴 TTS, 보도체 대본, 1.08× 미리보기 속도.",
        "",
        "| # | 주제 | 남성 | 여성 | 제목 |",
        "|---|------|------|------|------|",
    ]
    for t in TOPICS:
        readme.append(
            f"| {t['slug'][:2]} | {t['name']} | `{t['slug']}-male.mp4` | `{t['slug']}-female.mp4` | {t['title']} |"
        )
    (ROOT / "README.md").write_text("\n".join(readme) + "\n")
    print("DONE", len(results), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
