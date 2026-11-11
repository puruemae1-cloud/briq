#!/usr/bin/env python3
"""10 multi-brand Briq Shorts previews — alternate male/female VO, product links for pinned comments."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import subprocess
import unicodedata
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageStat

from yt_copy import build_description, build_pinned_comment

ROOT = Path("/Users/jeonghyunlee/Documents/briq/youtube-drafts/06-multi-brand-shorts-10")
PUBLIC = Path("/Users/jeonghyunlee/Documents/briq/public/products")
SHIP = Path("/Users/jeonghyunlee/Documents/briq/src/data")
if not SHIP.exists():
    SHIP = Path("/Users/jeonghyunlee/briq-ship/src/data")
FFMPEG = Path(
    "/Users/jeonghyunlee/Library/Python/3.9/lib/python/site-packages/"
    "imageio_ffmpeg/binaries/ffmpeg-osx64-v4.2.2"
)
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
DISPLAY = "/Users/jeonghyunlee/Documents/briq/instagram-drafts/fonts/Fraunces-500.ttf"
if not Path(DISPLAY).exists():
    DISPLAY = "/tmp/briq-font/Fraunces-500.ttf"
BGM_DIR = Path(__file__).resolve().parent / "bgm" / "rotate"
# Real Mixkit rhythm beds (not sine drones). Keep audible under VO without burying speech.
BGM_VOLUME = 0.26
BGM_FADE_IN_SEC = 0.8
BGM_FADE_OUT_SEC = 2.0  # start lowering volume this many seconds before the end
# Legacy single-file fallback if rotate folder empty.
BGM_PATH = Path(__file__).resolve().parent / "bgm" / "luxury-cinematic-bed.wav"

INK = (20, 18, 16)
CREAM = (247, 244, 236)
GOLD = (212, 175, 90)
WHITE = (255, 255, 255)

# VO + slide pacing. 1.2 keeps reels tight without rushing past product beats.
PREVIEW_SPEED = 1.20
VOICES = {
    "male": ("ko-KR-InJoonNeural", "-5%", "-2Hz"),
    "female": ("ko-KR-SunHiNeural", "-4%", "-1Hz"),
}

# Mid brand-card tails — product/lifestyle facts only.
# Never rotate “손이 자주/자꾸 가는” filler (it duplicates across a batch).
MID_CARD_TAILS = (
    "데일리로 쓰기 좋은",
    "오래 곁에 두고 싶은",
    "실루엣이 깔끔한",
    "마감이 탄탄한",
    "존재감이 분명한",
    "언제든 가지고 다니고 싶은",
    "코디에 넣기 쉬운",
    "오래 함께하고 싶은",
    "밸런스가 좋은",
    "완성도가 느껴지는",
    "디테일이 살아 있는",
    "비율이 안정적인",
    "착용감이 편안한",
    "포인트가 분명한",
    "실사용에 강한",
)


def mid_card_tail(product_id: str) -> str:
    """Stable per-SKU rotation across distinct mid-card tails."""
    digest = hashlib.md5((product_id or "").encode("utf-8")).hexdigest()
    return MID_CARD_TAILS[int(digest, 16) % len(MID_CARD_TAILS)]


def vo_key(s: str) -> str:
    return re.sub(r"[\s,.\u3000]+", "", (s or "").strip())


def vo_stem(s: str) -> str:
    """Normalize endings so near-duplicate VO (…적어요 / …들어갑니다) collide."""
    t = vo_key(s)
    t = re.sub(
        r"(이에요|예요|에요|습니다|ㅂ니다|니다|져요|가요|와요|돼요|됩니다|적어요|적습니다|줍니다|줘요|좋아요|좋습니다)+$",
        "",
        t,
    )
    return t


def vo_clause(s: str) -> str:
    """Leading reason clause — shared '…해서/아서' openings must collide."""
    t = vo_stem(s)
    for sep in ("해서", "이라서", "라서", "아서", "어서", "니까", "지만"):
        idx = t.find(sep)
        if idx >= 4:
            return t[: idx + len(sep)]
    return t[:12]


def vo_near_dup(a: str, b: str, *, ignore_phrases: list[str] | None = None) -> bool:
    """True when two VO lines share the same spoken beat (not just product name)."""
    ignore = [vo_key(x) for x in (ignore_phrases or []) if x and len(vo_key(x)) >= 4]

    def scrub(s: str) -> str:
        t = vo_stem(s)
        for phrase in sorted(ignore, key=len, reverse=True):
            t = t.replace(phrase, "")
        return t

    sa, sb = scrub(a), scrub(b)
    if len(sa) < 8 or len(sb) < 8:
        # After stripping product/search names little content remains — not a dup beat.
        return False
    if sa == sb:
        return True

    def clause_of(stem: str) -> str:
        for sep in ("해서", "이라서", "라서", "아서", "어서", "니까", "지만"):
            idx = stem.find(sep)
            if idx >= 4:
                return stem[: idx + len(sep)]
        return stem[:12]

    ca, cb = clause_of(sa), clause_of(sb)
    if len(ca) >= 8 and ca == cb:
        return True
    n = min(len(sa), len(sb))
    if n >= 10 and sa[:10] == sb[:10]:
        return True
    # Shared mid-phrase (e.g. both say “메탈 디테일이 얼굴을 밝혀…”) = same beat.
    shorter, longer = (sa, sb) if len(sa) <= len(sb) else (sb, sa)
    chunk = 10
    if len(shorter) >= chunk:
        for i in range(0, len(shorter) - chunk + 1):
            if shorter[i : i + chunk] in longer:
                return True
    return False


def assert_no_near_dup_vo(
    lines: list[str],
    *,
    label: str = "",
    ignore_phrases: list[str] | None = None,
) -> None:
    """Hard fail if any two VO lines share the same opening/mid beat."""
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            if vo_near_dup(lines[i], lines[j], ignore_phrases=ignore_phrases):
                where = f" ({label})" if label else ""
                raise RuntimeError(
                    f"near-duplicate VO{where} [{i}]/[{j}]: "
                    f"{lines[i]!r} / {lines[j]!r}"
                )


def list_bgm_tracks() -> list[Path]:
    """~10 rhythmic Mixkit beds under bgm/rotate (mp3/wav)."""
    if not BGM_DIR.is_dir():
        return []
    tracks = sorted(
        [
            p
            for p in BGM_DIR.iterdir()
            if p.suffix.lower() in {".mp3", ".wav", ".m4a"} and p.is_file()
        ],
        key=lambda p: p.name,
    )
    return tracks


def pick_bgm(product_id: str) -> Path | None:
    """Stable per-SKU rotation across the rhythm bed library."""
    tracks = list_bgm_tracks()
    if tracks:
        digest = hashlib.md5((product_id or "briq").encode("utf-8")).hexdigest()
        return tracks[int(digest, 16) % len(tracks)]
    if BGM_PATH.is_file():
        return BGM_PATH
    return None


# Purchase-desire beat: VO line + on-screen caption (title, subtitle).
# Inserted after the price scene so viewers hear *why* to buy, not just cost.
FEATURE_BEAT: dict[str, dict[str, tuple[str, str, str]]] = {
    "ys": {
        "male": (
            "손잡이 비율이 좋아서, 들어도 걸쳐도 형태가 쉽게 안 무너집니다.",
            "형태가 안 무너짐",
            "들어도 걸쳐도 실루엣 유지",
        ),
        "female": (
            "수납은 알차면서도 겉모습은 슬림해서, 들고 나가도 형태가 잘 유지돼요.",
            "슬림한데 수납이 알참",
            "들고 나가도 형태가 유지되는",
        ),
    },
    "bv": {
        "male": (
            "인트레치아토가 가까이서도 조밀해서, 볼수록 고급스럽습니다.",
            "조밀한 위빙감",
            "가까이서 봐도 완성도가 다름",
        ),
        "female": (
            "가벼우면서 메탈 디테일이 얼굴을 밝혀 줘서, 저녁 약속에도 잘 받쳐 줘요.",
            "가벼운데 존재감",
            "저녁 룩에도 잘 받쳐 주는",
        ),
    },
    "bv_tote": {
        "male": (
            "인트레치아토가 가까이서도 조밀해서, 들고 나가도 형태가 잘 유지됩니다.",
            "조밀한 위빙감",
            "들고 나가도 형태 유지",
        ),
        "female": (
            "인트레치아토가 조밀해서, 토트로 들어도 실루엣이 쉽게 안 무너져요.",
            "조밀한 위빙 토트",
            "들어도 실루엣이 유지되는",
        ),
    },
    # Default = RTW / outerwear. Shoes/bags override in build_vo_and_hooks via kind.
    "al": {
        "male": (
            "데님 특유의 무게감이 있어서, 티 한 장 위에도 옷이 살아납니다.",
            "데님의 무게감",
            "티 한 장 위에도 옷이 살아남",
        ),
        "female": (
            "워싱이 자연스러워서 새 옷 티가 덜 나고, 첫날부터 익숙한 룩이 나와요.",
            "자연스러운 워싱",
            "첫날부터 익숙한 룩",
        ),
    },
    "al_shoes": {
        "male": (
            "로우탑 실루엣이라, 팬츠 밑단이 깔끔하게 떨어집니다.",
            "깔끔한 로우탑 실루엣",
            "팬츠 밑단이 정돈되는",
        ),
        "female": (
            "발이 답답하지 않아서, 하루 종일 신어도 부담이 적어요.",
            "답답하지 않은 착용감",
            "하루 종일 신어도 부담 적음",
        ),
    },
    "al_bags": {
        "male": (
            "수납이 실사용 중심으로 짜여서, 들고 다녀도 형태가 잘 유지됩니다.",
            "실사용 수납",
            "들고 다녀도 형태 유지",
        ),
        "female": (
            "가벼우면서도 입구가 안정적이라, 일상에서 쓰기 편해요.",
            "가볍고 안정적인",
            "일상에서 쓰기 편한",
        ),
    },
    "al_bottoms": {
        "male": (
            "실루엣이 과하지 않아서, 상의만 바꿔도 코디가 정리됩니다.",
            "과하지 않은 실루엣",
            "상의만 바꿔도 정리되는",
        ),
        "female": (
            "기장이 애매하지 않아서, 신발 바꿔도 비율이 안정적이에요.",
            "애매하지 않은 기장",
            "비율이 안정적인",
        ),
    },
    "al_dress": {
        "male": (
            "실루엣이 분명해서, 한 장으로도 코디가 정리됩니다.",
            "분명한 실루엣",
            "한 장으로도 정리되는",
        ),
        "female": (
            "기장이 애매하지 않아서, 신발 바꿔도 비율이 안정적이에요.",
            "애매하지 않은 기장",
            "비율이 안정적인",
        ),
    },
    "cw_twelve": {
        "male": (
            "케이스 비율이 안정적이라, 데일리로 차도 부담이 적습니다.",
            "안정적인 케이스 비율",
            "데일리로 부담이 적은",
        ),
        "female": (
            "다이얼 대비가 선명해서, 평소에도 시간 읽기가 편해요.",
            "선명한 다이얼 대비",
            "평소에도 읽기 편한",
        ),
    },
    "om_seamaster": {
        "male": (
            "다이버 스펙인데도 데일리로 차기 좋아서, 활용도가 분명합니다.",
            "데일리로 쓰기 좋은 다이버",
            "활용도가 분명한",
        ),
        "female": (
            "다이버인데도 과하지 않아서, 평소 룩에도 잘 어울려요.",
            "과하지 않은 다이버",
            "평소 룩에도 잘 어울림",
        ),
    },
    "om_deville": {
        "male": (
            "다이얼이 단정해서, 오피스에도 데일리에도 잘 어울립니다.",
            "단정한 다이얼",
            "오피스·데일리 둘 다 가능",
        ),
        "female": (
            "다이얼이 깔끔해서, 오피스 룩에도 잘 어울려요.",
            "깔끔한 다이얼",
            "오피스 룩에도 잘 어울림",
        ),
    },
    "mc": {
        "male": (
            "길이감이 애매하지 않아서, 시티 룩에도 주말에도 같이 쓰기 좋습니다.",
            "애매하지 않은 기장",
            "시티·주말 둘 다 쓰기 좋은",
        ),
        "female": (
            "후드가 있어도 얼굴이 묻히지 않아서, 한겨울에도 코트 대신 입을 수 있어요.",
            "후드 있어도 얼굴이 안 묻힘",
            "한겨울 코트 대용으로도",
        ),
    },
    "gg": {
        "male": (
            "방풍인데도 답답하지 않아서, 라운드뿐 아니라 여행에도 쓰기 좋습니다.",
            "방풍인데 답답하지 않음",
            "라운드·여행 둘 다 가능",
        ),
        "female": (
            "레이어드가 깔끔해서, 필드 룩이 한층 정돈돼 보여요.",
            "깔끔한 레이어드",
            "필드 룩이 한층 정돈됨",
        ),
    },
    "cw": {
        "male": (
            "다이얼 가독성이 좋아서, 데일리로 차도 시간이 바로 읽힙니다.",
            "데일리 가독성",
            "차면 시간이 바로 읽힘",
        ),
        "female": (
            "GMT 핸즈 대비가 선명해서, 여행 때도 시간 읽기가 편해요.",
            "선명한 GMT 대비",
            "여행 때도 시간 읽기가 편한",
        ),
    },
    "td": {
        "male": (
            "사이즈가 부담스럽지 않아서, 첫 오토매틱으로 고르기 좋습니다.",
            "부담 없는 사이즈",
            "첫 오토매틱으로도 충분",
        ),
        "female": (
            "블랙 다이얼이라 옷 색을 거의 안 가리고, 존재감은 분명해요.",
            "옷 색을 안 가림",
            "존재감은 분명한 블랙 다이얼",
        ),
    },
    "th": {
        "male": (
            "차면 손목에 착 감겨서, 하루 종일 편안한 착용감을 줍니다.",
            "착 감기는 착용감",
            "하루 종일 편안한",
        ),
        "female": (
            "차면 손목에 착 감겨서, 하루 종일 편안한 착용감을 줘요.",
            "착 감기는 착용감",
            "하루 종일 편안한",
        ),
    },
    "iw": {
        "male": (
            "케이스 마감이 단단해서, 소장용으로 골라도 후회가 적습니다.",
            "단단한 케이스 마감",
            "소장용으로 골라도 후회 적음",
        ),
        "female": (
            "다이얼 대비가 선명해서 읽기 편하고, 큰 시계도 잘 소화돼요.",
            "선명한 다이얼 대비",
            "큰 시계도 잘 소화되는",
        ),
    },
    "om": {
        "male": (
            "문워치 DNA가 살아 있어서, 차는 순간 상징감이 분명합니다.",
            "문워치 DNA",
            "차는 순간 상징감이 분명",
        ),
        "female": (
            "크로노 푸셔 감이 분명해서, 차면 디테일이 오래 눈에 남아요.",
            "분명한 푸셔 감",
            "차면 디테일이 오래 남는",
        ),
    },
    "ms": {
        "male": (
            "쓸수록 가죽이 변해서, 멋지게 에이징되는 맛이 분명합니다.",
            "쓸수록 에이징되는 가죽",
            "오래 쓸수록 더 멋져지는",
        ),
        "female": (
            "쓸수록 가죽이 변해서, 에이징될수록 더 멋있어 보여요.",
            "쓸수록 에이징되는 가죽",
            "오래 쓸수록 더 멋있어지는",
        ),
    },
    "pp": {
        "male": (
            "디테일 완성도가 달라서, 가까이 볼수록 소장 가치가 느껴집니다.",
            "디테일의 완성도",
            "가까이 볼수록 소장 가치",
        ),
        "female": (
            "다이얼 밸런스가 좋아서, 차면 존재감이 분명하고 오래 남아요.",
            "균형 잡힌 다이얼",
            "차면 존재감이 오래 남음",
        ),
    },
    "rx": {
        "male": (
            "모델만 바꿔도 분위기가 달라져서, 컬렉션으로 모으는 맛이 있습니다.",
            "모델이 곧 분위기",
            "컬렉션으로 모으는 맛",
        ),
        "female": (
            "클래식하면서도 데일리에 과하지 않아서, 자주 차게 되는 쪽입니다.",
            "클래식한 데일리감",
            "자주 차게 되는 밸런스",
        ),
    },
}

BRAND_META = {
    "ys": ("ys-pdp", "생로랑", "Saint Laurent", "가방"),
    "bv": ("bv-pdp", "보테가 베네타", "Bottega Veneta", "가방"),
    "al": ("al-pdp", "올세인츠", "AllSaints", "의류"),
    "mc": ("mc-pdp", "몽클레르", "Moncler", "패딩"),
    "gg": ("gg-pdp", "갤빈그린", "Galvin Green", "골프웨어"),
    "cw": ("cw-pdp", "크리스토퍼 워드", "Christopher Ward", "시계"),
    "td": ("td-pdp", "튜더", "Tudor", "시계"),
    "th": ("th-pdp", "태그호이어", "TAG Heuer", "시계"),
    "iw": ("iw-pdp", "IWC", "IWC", "시계"),
    "om": ("om-pdp", "오메가", "Omega", "시계"),
    "ms": ("ms-pdp", "미스모", "Mismo", "가방"),
    "pp": ("pp-pdp", "파텍필립", "Patek Philippe", "시계"),
    "rx": ("rx-pdp", "롤렉스", "Rolex", "시계"),
}

DEFAULT_ORDER = ["ys", "bv", "al", "mc", "gg", "cw", "td", "th", "iw", "om"]
BATCH2_ORDER = ["ms", "pp", "rx", "ys", "bv", "al", "mc", "cw", "gg", "om"]


def _catalog_kind_hint(path: Path) -> str | None:
    name = path.name.lower()
    if "shoe" in name:
        return "신발"
    if "bag" in name:
        return "가방"
    return None


def _with_catalog_kind(items: list[dict], hint: str | None) -> list[dict]:
    if not hint:
        return items
    out = []
    for x in items:
        row = dict(x)
        row.setdefault("_catalogKind", hint)
        out.append(row)
    return out


def infer_product_kind(code: str, product: dict, default_kind: str) -> str:
    """Resolve SKU kind from catalog file / category / name — never brand default alone.

    Root cause of IG DferSy1lWD5: AllSaints brand default was 의류, so shoe photos
    got outerwear VO (아우터/데님/티 위에도).
    """
    hint = product.get("_catalogKind")
    if hint in {"신발", "가방"}:
        return str(hint)
    cat = str(product.get("category") or "").strip().lower()
    blob = f"{product.get('name') or ''} {product.get('nameKo') or ''} {cat}".lower()
    shoe_keys = (
        "shoes",
        "shoe",
        "footwear",
        "trainer",
        "sneaker",
        "runners",
        "loafer",
        "boot",
        "sandal",
        "slipper",
        "트레이너",
        "스니커",
        "러너",
        "로퍼",
        "부츠",
        "샌들",
        "슬리퍼",
        "구두",
        "신발",
        "슬립온",
    )
    bag_keys = (
        "bags",
        "bag",
        "tote",
        "clutch",
        "backpack",
        "crossbody",
        "shoulder",
        "가방",
        "토트",
        "클러치",
        "백팩",
        "숄더",
        "크로스백",
        "배니티",
    )
    if cat in {"shoes", "shoe", "footwear"} or any(k in blob for k in shoe_keys):
        return "신발"
    if cat in {"bags", "bag", "handbags"} or (
        code in {"al", "bv", "ys", "ms"} and any(k in blob for k in bag_keys)
    ):
        return "가방"
    return default_kind


def assert_vo_matches_kind(kind: str, lines: list[str], cards: list[str], label: str) -> None:
    """Hard fail when clothing copy ships on shoes (or the reverse)."""
    joined = " ".join([*(lines or []), *(cards or [])])
    banned_by_kind: dict[str, tuple[str, ...]] = {
        "신발": (
            "아우터",
            "재킷",
            "자켓",
            "데님 아우터",
            "데님 특유의 무게감",
            "티 한 장 위에도",
            "티셔츠 위에도",
            "셔츠 위에도",
            "옷이 살아남",
            "새 옷 티",
            "매일 입는 아우터",
            "걸쳐도 완성도",
            "청바지랑도, 스커트",
            "후디",
            "패딩",
        ),
        "가방": (
            "아우터",
            "재킷",
            "자켓",
            "신으면",
            "발볼",
            "아웃솔",
            "티 한 장 위에도",
            "매일 입는 아우터",
        ),
        "의류": (
            "신으면",
            "발볼",
            "아웃솔",
            "로우탑 실루엣",
            "하루 종일 신어도",
        ),
    }
    banned = banned_by_kind.get(kind) or ()
    hits = [b for b in banned if b in joined]
    if hits:
        raise RuntimeError(
            f"kind/VO mismatch for {label} (kind={kind}): banned {hits} in copy"
        )


def assert_vo_matches_sku(
    *,
    code: str,
    sku_blob: str,
    lines: list[str],
    cards: list[str],
    label: str,
) -> None:
    """Hard fail when brand-line filler names the wrong product family."""
    joined = " ".join([*(lines or []), *(cards or [])])
    blob = sku_blob or ""
    banned: list[str] = []
    is_bottoms = _is_al_bottoms(blob)
    if is_bottoms or _is_al_dress(blob):
        banned.extend(
            (
                "아우터",
                "재킷",
                "자켓",
                "데님 아우터",
                "데님 특유의 무게감",
                "티 한 장 위에도",
                "티셔츠 위에도",
                "셔츠 위에도",
                "매일 입는 아우터",
                "걸쳐도 완성도",
                "걸쳐도 질리지 않는 아우터",
            )
        )
    if code == "bv" and _is_bv_tote(blob) and not _is_bv_clutch(blob):
        banned.extend(
            (
                "미니 클러치",
                "클러치 라인",
                "손안에 들어오는",
                "파티·디너에 들고",
            )
        )
    if any(k in blob for k in ("고무", "rubber", "러버")) and "브레이슬릿" not in blob.lower():
        banned.extend(("브레이슬릿",))
    if code == "om":
        is_speed = any(k in blob for k in ("스피드마스터", "Speedmaster", "speedmaster"))
        is_seamaster = any(
            k in blob for k in ("씨마스터", "Seamaster", "seamaster", "플래닛", "Planet Ocean", "planet ocean")
        )
        is_aqua = any(k in blob for k in ("아쿠아 테라", "Aqua Terra", "aqua terra"))
        is_deville = any(k in blob for k in ("드 빌", "드빌", "De Ville", "de ville", "prestige"))
        if is_seamaster and not is_speed:
            banned.extend(("스피드마스터", "문워치", "크로노 푸셔", "애니버서리", "푸셔 감"))
        if is_speed and not is_seamaster:
            banned.extend(("플래닛 오션", "아쿠아 테라", "드 빌", "프레스티지"))
        if is_aqua:
            banned.extend(("스피드마스터", "문워치", "크로노 푸셔", "푸셔 감"))
        # Non-Speedmaster SKUs must never inherit Speedmaster brand-default VO.
        if not is_speed:
            banned.extend(
                (
                    "스피드마스터",
                    "문워치",
                    "크로노 푸셔",
                    "애니버서리",
                    "푸셔 감",
                    "스피드마스터 DNA",
                )
            )
        if is_deville:
            banned.extend(("씨마스터", "플래닛 오션", "아쿠아 테라", "다이버"))
    if code == "cw":
        is_twelve = any(k in blob for k in ("트웰브", "Twelve", "twelve", "C12"))
        is_sealander = any(k in blob for k in ("시랜더", "Sealander", "sealander"))
        is_c60 = "C60" in blob
        if is_twelve and not is_sealander:
            banned.extend(("시랜더", "GMT 핸즈", "GMT 대비"))
        if is_c60:
            banned.extend(("시랜더",))
        if is_sealander and not is_twelve:
            banned.extend(("트웰브",))
    hits = [b for b in banned if b in joined]
    if hits:
        raise RuntimeError(
            f"SKU/VO mismatch for {label}: banned {hits} in copy (sku={blob[:80]!r})"
        )


def _is_al_bottoms(sku_blob: str) -> bool:
    blob = (sku_blob or "").lower()
    # Korean catalog often shortens jeans → "진" (e.g. 릴랙스 진).
    if re.search(r"(?<![가-힣a-z])진(?![가-힣a-z])", blob):
        return True
    return any(
        k in blob
        for k in (
            "바지",
            "팬츠",
            "trousers",
            "pants",
            "jeans",
            "jean",
            "skirt",
            "스커트",
            "쇼츠",
            "shorts",
            "데님 팬츠",
        )
    )


def _sku_text(
    *,
    search_name: str = "",
    name_ko: str = "",
    product_id: str = "",
    product: dict | None = None,
) -> str:
    """English catalog name must be in the blob — Korean titles alone miss 'Jeans'/'Tote'."""
    en = str((product or {}).get("name") or "")
    return f"{search_name} {name_ko} {en} {product_id}"


def _is_bv_clutch(sku_blob: str) -> bool:
    blob = (sku_blob or "").lower()
    return any(k in blob for k in ("클러치", "clutch", "파우치", "pouch"))


def _is_bv_tote(sku_blob: str) -> bool:
    blob = (sku_blob or "").lower()
    if _is_bv_clutch(blob):
        return False
    return any(k in blob for k in ("토트", "tote", "barbara", "바바라", "andiamo", "아르코", "arco"))


def _is_al_dress(sku_blob: str) -> bool:
    blob = (sku_blob or "").lower()
    return any(k in blob for k in ("드레스", "원피스", "dress", "gown", "바디콘"))


def load_products(code: str) -> list[dict]:
    paths: list[Path] = []
    d = SHIP / code
    if code == "ys":
        paths = [d / "ys-bags-catalog.json"]
    elif code == "bv":
        paths = [d / "bv-bags-catalog.json", d / "bv-shoes-catalog.json"]
    elif code == "al":
        paths = [d / "al-catalog.json", d / "al-shoes-catalog.json", d / "al-bags-catalog.json"]
    elif code == "mc":
        paths = [d / "mc-catalog.json"]
    elif code == "gg":
        paths = [d / "gg-catalog.json", d / "gg-catalog.ts"]
    elif code == "cw":
        paths = [d / "cw-catalog.ts"]
    elif code == "td":
        paths = [d / "td-catalog.ts", d / "td-catalog.json"]
    elif code == "th":
        paths = [d / "th-catalog.ts", d / "th-catalog.json"]
    elif code == "iw":
        paths = [d / "iw-catalog.ts", d / "iw-catalog.json"]
    elif code == "om":
        paths = [d / "om-catalog.ts", d / "om-catalog.json"]
    elif code == "ms":
        paths = [d / "ms-catalog.json"]
    elif code == "pp":
        paths = [d / "pp-catalog.ts", d / "pp-catalog.json"]
    elif code == "rx":
        paths = [d / "rx-catalog.ts", d / "rx-catalog.json"]

    out: list[dict] = []
    seen: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        hint = _catalog_kind_hint(path)
        batch: list[dict] = []
        if path.suffix == ".ts":
            batch = parse_ts(path)
        else:
            data = json.loads(path.read_text())
            if isinstance(data, list):
                batch = [x for x in data if isinstance(x, dict) and "id" in x and "price" in x]
            elif isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        batch.extend(
                            [x for x in v if isinstance(x, dict) and "id" in x and "price" in x]
                        )
        for row in _with_catalog_kind(batch, hint):
            pid = str(row.get("id") or "")
            if not pid or pid in seen:
                # Prefer first catalog hit, but let a later shoes/bags file upgrade kind hint.
                if pid in seen and hint and not any(
                    x.get("id") == pid and x.get("_catalogKind") for x in out
                ):
                    for x in out:
                        if x.get("id") == pid and not x.get("_catalogKind"):
                            x["_catalogKind"] = hint
                continue
            seen.add(pid)
            out.append(row)
    return out


def parse_ts(path: Path) -> list[dict]:
    text = path.read_text(errors="ignore")
    prods = []
    for m in re.finditer(r'id:\s*"([^"]+)"([\s\S]*?)(?=\n\s*id:\s*"|$)', text):
        b = m.group(0)

        def g(k: str):
            mm = re.search(rf'{k}:\s*"([^"]*)"', b)
            return mm.group(1) if mm else None

        def gi(k: str):
            mm = re.search(rf"{k}:\s*([0-9][0-9_,.]*)", b)
            return float(mm.group(1).replace(",", "")) if mm else None

        prods.append(
            {
                "id": m.group(1),
                "name": g("name"),
                "nameKo": g("nameKo"),
                "brand": g("brand"),
                "price": int(gi("price") or 0),
                "gbpPrice": gi("gbpPrice") or 0,
                "category": g("category"),
                "image": g("image") or "",
            }
        )
    return prods


def _is_product_shot(path: Path) -> bool:
    """Drop ultra-wide lifestyle/landscape stills that are not the product."""
    try:
        with Image.open(path) as im:
            w, h = im.size
        if w <= 0 or h <= 0:
            return False
        # Catalog lifestyle landscapes are typically much wider than tall.
        if w / h > 1.45:
            return False
        return True
    except Exception:
        return True


def score_cover_photo(path: Path) -> float:
    """Higher = clearer product hero for IG/YT thumbnail. Penalize dark/flat/wide."""
    try:
        with Image.open(path) as im:
            rgb = im.convert("RGB")
            w, h = rgb.size
        if w <= 0 or h <= 0:
            return -1e9
        aspect = w / float(h)
        if aspect > 1.45:
            return -1e9
        # Square catalog heroes read best as reel covers.
        aspect_score = 1.0 - min(abs(aspect - 1.0), 1.0)
        cx0, cy0 = int(w * 0.18), int(h * 0.12)
        cx1, cy1 = int(w * 0.82), int(h * 0.88)
        crop = rgb.crop((cx0, cy0, max(cx0 + 1, cx1), max(cy0 + 1, cy1)))
        st = ImageStat.Stat(crop)
        mean = sum(st.mean) / 3.0
        var = sum(st.var) / 3.0
        # Near-black lume / night macros and blown whites make weak thumbs.
        if mean < 35:
            mean_pen = -60.0
        elif mean > 245:
            mean_pen = -12.0
        else:
            mean_pen = 0.0
        detail = min(var / 4000.0, 2.5)
        brightness = 1.0 - abs(mean - 160.0) / 160.0
        return aspect_score * 2.0 + detail + brightness + mean_pen
    except Exception:
        return -1e9


def pick_cover_photo(shots: list[Path]) -> Path:
    """Pick the clearest product still for Instagram cover_url / poster.jpg."""
    if not shots:
        raise ValueError("no product shots for cover")
    ranked = sorted(
        enumerate(shots),
        key=lambda pair: (score_cover_photo(pair[1]), -pair[0]),
        reverse=True,
    )
    return ranked[0][1]


def write_clean_poster(photo: Path, dest: Path, *, w: int = 1080, h: int = 1920) -> Path:
    """1080×1920 product cover with no VO text / shade — IG thumbnail must show the SKU."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    im = fit_cover(Image.open(photo), w, h).convert("RGB")
    im.save(dest, quality=92)
    return dest


def folder_images(pdp: str, folder: str, *, filter_landscape: bool = False) -> list[Path]:
    d = PUBLIC / pdp / folder
    if not d.is_dir():
        return []
    shots = []
    for i in range(1, 12):
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            p = d / f"{i}{ext}"
            if p.exists():
                shots.append(p)
                break
    if not shots:
        shots = sorted(
            [p for p in d.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}],
            key=lambda p: p.name,
        )
    # Only open images when rendering — pick_topics calls this for every SKU.
    if filter_landscape:
        product = [p for p in shots if _is_product_shot(p)]
        return product or shots
    return shots


def pick_topics(
    order: list[str] | None = None,
    exclude_ids: set[str] | None = None,
    pick_shift: int = 0,
    force_ids: dict[str, str] | None = None,
    platform: str = "shorts",
) -> list[dict]:
    topics = []
    order = order or DEFAULT_ORDER
    exclude_ids = exclude_ids or set()
    force_ids = force_ids or {}
    platform = "instagram" if platform == "instagram" else "shorts"
    seen_name_keys: set[str] = set()
    for i, code in enumerate(order, 1):
        pdp, brand_ko, brand_en, kind = BRAND_META[code]
        prods = load_products(code)
        local = {
            d.name
            for d in (PUBLIC / pdp).iterdir()
            if d.is_dir() and len(folder_images(pdp, d.name)) >= 3
        } if (PUBLIC / pdp).exists() else set()
        usable = []
        for p in prods:
            pid = str(p.get("id") or "")
            if pid in exclude_ids and pid != force_ids.get(code):
                continue
            img = str(p.get("image") or "")
            m = re.search(r"/products/[a-z0-9-]+-pdp/([^/]+)/", img)
            folder = m.group(1) if m else None
            if not folder and pid.startswith(f"{code}-"):
                cand = pid[len(code) + 1 :]
                if cand in local:
                    folder = cand
            # Moncler etc: CDN image but local folder matches slug in id
            if not folder:
                for f in local:
                    if f in pid or pid.endswith(f) or pid.replace(f"{code}-", "") == f:
                        folder = f
                        break
            if not folder or folder not in local:
                continue
            shots = folder_images(pdp, folder)
            if len(shots) < 3:
                continue
            price = int(p.get("price") or 0)
            if price < 200000:
                continue
            # Never feature sold-out SKUs (force-ids also cannot override).
            variants = p.get("variants") or []
            in_stock = p.get("inStock")
            if in_stock is None and variants:
                in_stock = any(bool(v.get("inStock")) for v in variants)
            if in_stock is False:
                continue
            name_ko = (p.get("nameKo") or p.get("name") or "").strip()
            if len(name_ko) < 2:
                continue
            blob = f"{name_ko} {p.get('name') or ''}"
            # skip non-product / accessory-only noise
            if any(k in blob.lower() for k in ("더스트백", "dust bag", "dustbag", "shopping bag", "선물 박스", "gift box", "라이터", "lighter")):
                continue
            # skip CW straps / bracelet-only SKUs
            if code == "cw" and any(k in blob for k in ("스트랩", "Strap", "브레이슬릿")):
                if not any(k in blob for k in ("시랜더", "트라이던트", "벨 칸토", "트웰브", "Sealander", "Trident", "Bel Canto", "Twelve")):
                    continue
            usable.append({**p, "folder": folder, "shots": shots[:6]})

        if not usable:
            raise SystemExit(f"No usable products for {code} (local folders={len(local)}, catalog={len(prods)})")

        usable.sort(key=lambda x: int(x["price"]))
        # Prefer SKUs whose display name was not already used in this batch.
        diversified = [
            x
            for x in usable
            if re.sub(r"\s+", " ", str(x.get("nameKo") or x.get("name") or "").strip().lower())
            not in seen_name_keys
        ]
        pick_pool = diversified or usable
        # diversify pick index per brand / batch
        idx = min(len(pick_pool) // 2 + (i % 3) + pick_shift, len(pick_pool) - 1)
        chosen = pick_pool[idx]
        if force_ids.get(code):
            forced = next((x for x in usable if x["id"] == force_ids[code]), None)
            if forced:
                chosen = forced
            else:
                raw = next((p for p in prods if p.get("id") == force_ids[code]), None)
                why = "sold out / filtered" if raw is not None else "not in catalog"
                raise SystemExit(f"Forced id not usable for {code} ({why}): {force_ids[code]}")
        if code == "bv" and code not in force_ids:
            bags = [
                x
                for x in usable
                if any(
                    k in str(x.get("nameKo") or x.get("name") or "").lower()
                    for k in ("백", "bag", "토트", "tote", "클러치", "숄더", "카세트", "조디", "핸드")
                )
            ]
            if bags:
                chosen = bags[min(len(bags) // 2 + pick_shift, len(bags) - 1)]
        if code == "ms" and code not in force_ids:
            bags = [
                x
                for x in usable
                if any(
                    k in str(x.get("nameKo") or x.get("name") or "").lower()
                    for k in ("백", "bag", "브리프", "메신저", "토트", "aspire", "endeavour", "드롭")
                )
            ]
            if bags:
                chosen = bags[min(len(bags) // 3 + pick_shift, len(bags) - 1)]
        if code == "mc" and code not in force_ids:
            jackets = [
                x
                for x in usable
                if any(
                    k in str(x.get("nameKo") or x.get("name") or "").lower()
                    for k in ("재킷", "자켓", "패딩", "다운", "jacket", "down", "파카", "코트")
                )
            ]
            if jackets:
                chosen = jackets[min(len(jackets) // 2 + pick_shift, len(jackets) - 1)]
        if code in {"cw", "td", "th", "om", "iw", "pp", "rx"} and code not in force_ids:
            watches = [
                x
                for x in usable
                if not any(k in str(x.get("nameKo") or "") for k in ("스트랩", "브레이슬릿"))
            ] or usable
            chosen = watches[min(len(watches) // 3 + i + pick_shift, len(watches) - 1)]

        # Same-batch brand/name repeats must not re-pick the same SKU/title.
        exclude_ids.add(str(chosen.get("id") or ""))
        name_key = re.sub(
            r"\s+",
            " ",
            str(chosen.get("nameKo") or chosen.get("name") or "").strip().lower(),
        )
        if name_key:
            seen_name_keys.add(name_key)
        gender = "male" if i % 2 == 1 else "female"
        name_ko = sanitize_slide_text(chosen.get("nameKo") or chosen.get("name") or "")
        # Prefer clearer live-ish short names for a few noisy catalog labels
        if code == "gg" and "Lea" not in name_ko and "lea" in str(chosen.get("id") or "").lower():
            name_ko = "Lea 골프 베스트"
        if code == "gg" and "dean" in str(chosen.get("id") or "").lower():
            name_ko = "Dean 골프 미드레이어"
        if code == "gg" and "donnie" in str(chosen.get("id") or "").lower():
            name_ko = "Donnie 골프 스웨트"
        # Per-SKU kind (shoes/bags) overrides brand default (e.g. AllSaints 의류).
        kind = infer_product_kind(code, chosen, kind)
        price = int(chosen["price"])
        gbp = float(chosen.get("gbpPrice") or 0)
        search_name = simplify_search_name(name_ko, brand_ko, brand_en, kind)
        display_name = sanitize_slide_text(name_ko)
        if len(display_name) > 28:
            display_name = display_name[:27].rstrip() + "…"

        price_spoken = speak_won(price)
        gbp_spoken = speak_gbp(gbp) if gbp else ""
        lines, card_hooks = build_vo_and_hooks(
            code=code,
            gender=gender,
            brand_ko=brand_ko,
            brand_en=brand_en,
            kind=kind,
            search_name=search_name,
            price_spoken=price_spoken,
            gbp_spoken=gbp_spoken,
            platform=platform,
            name_ko=name_ko,
            product_id=str(chosen.get("id") or ""),
            product=chosen,
        )
        title = f"{brand_ko} | {search_name}"
        feature_title, feature_sub = card_hooks[3], card_hooks[4]
        # Card order must match VO beat order (feature → lifestyle → select → Naver → CTA/end).
        cards = [
            (search_name, card_hooks[0]),
            (brand_en, f"{search_name} · {mid_card_tail(str(chosen['id']))}"),
            (None, "PRICE"),
            (feature_title, feature_sub),
            # Must match the post-feature lifestyle VO (e.g. logo / suit-casual for Mismo).
            (card_hooks[1], card_hooks[2]),
            ("영국 현지 명품 직송", "Briq에서 바로 확인"),
            NAVER_PAY_CARD,
            ("briq.kr", f"검색창에 {search_name}"),
        ]
        topic = {
            "slug": f"{i:02d}-{code}-{chosen['folder'][:28]}",
            "num": i,
            "platform": platform,
            "gender": gender,
            "brandCode": code,
            "brandKo": brand_ko,
            "brandEn": brand_en,
            "kind": kind,
            "pdp": pdp,
            "folder": chosen["folder"],
            "id": chosen["id"],
            "name": sanitize_slide_text(chosen.get("name") or ""),
            "nameKo": name_ko,
            "displayName": display_name,
            "price": price,
            "gbp": gbp,
            "title": title,
            "search": search_name,
            "productUrl": f"https://www.briq.kr/product/{chosen['id']}",
            # VO: tensed 빽 + price 때(떼); on-screen cards keep normal Hangul.
            "lines": [prepare_vo_line(x) for x in lines],
            "cards": [
                tuple(sanitize_slide_text(x) if x else x for x in card) for card in cards
            ],
            "pdpFacts": collect_raw_pdp_facts(chosen)[:6],
        }
        topic["pinnedComment"] = build_pinned_comment(topic)
        topic["description"] = build_description(topic)
        topics.append(topic)
    return topics


def sanitize_slide_text(text: str) -> str:
    """Apple SD Gothic Neo often draws Latin accents / marks as □ or ✕.

    Keep Hangul intact. Only fold Latin accented letters (À→A) and drop trademark marks.
    """
    raw = text or ""
    raw = re.sub(r"[®©™℠ºª†‡§¶]+", "", raw)

    def fold_char(ch: str) -> str:
        # Hangul syllables / jamo — never NFKD (would split into components)
        if (
            "\uac00" <= ch <= "\ud7a3"
            or "\u1100" <= ch <= "\u11ff"
            or "\u3130" <= ch <= "\u318f"
        ):
            return ch
        if ord(ch) < 128:
            return ch
        if ch in "£€¥₩/·•&+-.,'%…":
            return ch
        # Latin accents etc: À → A
        parts = unicodedata.normalize("NFKD", ch)
        base = "".join(c for c in parts if not unicodedata.combining(c))
        if base and all(ord(c) < 128 for c in base):
            return base
        name = unicodedata.name(ch, "")
        if name.startswith("HANGUL") or name.startswith("CJK"):
            return ch
        return ""

    cleaned = "".join(fold_char(ch) for ch in raw)
    cleaned = cleaned.replace("–", "-").replace("—", "-").replace("’", "'").replace("‘", "'")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip(" ·/")


def simplify_search_name(name_ko: str, brand_ko: str, brand_en: str, kind: str) -> str:
    """Shorter on-site search phrase — keep model words, drop filler."""
    text = sanitize_slide_text(name_ko or "")
    # drop leading brand repeats
    for b in (
        brand_ko,
        brand_en,
        "Saint Laurent",
        "YSL",
        "TAG Heuer",
        "태그호이어",
        "튜더",
        "Tudor",
        "오메가",
        "Omega",
        "IWC",
        "Moncler",
        "몽클레르",
        "AllSaints",
        "올세인츠",
        "Bottega Veneta",
        "보테가 베네타",
        "Galvin Green",
        "갤빈그린",
        "Christopher Ward",
        "크리스토퍼 워드",
        "Patek Philippe",
        "파텍필립",
        "Rolex",
        "롤렉스",
        "Mismo",
        "미스모",
        "M/S",
    ):
        if b and text.lower().startswith(b.lower()):
            text = text[len(b) :].strip(" ·|-")
    # drop noisy material / size / color tails
    text = re.sub(r"\s*/\s*.*$", "", text)  # color after slash
    text = re.sub(r"\s*·\s*\d+mm\b", "", text, flags=re.I)
    text = re.sub(r"\s+\d+mm\b", "", text, flags=re.I)
    text = re.sub(r"\s+시계\s*$", "", text)
    text = re.sub(r"\bIN\b", "", text, flags=re.I)
    text = re.sub(r"\s*(그레인\s*)?레더\s*$", "", text)
    text = re.sub(r"\s*미드렝스\s*", " ", text)
    text = re.sub(r"\s*후드\s*", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" ·/-")
    # Named model shortcuts
    if re.search(r"NEW\s*KATE|케이트", text, re.I):
        text = "NEW KATE 스몰백"
    if re.search(r"드롭백|Drop\s*Bag", text, re.I):
        text = "드롭백"
    if re.search(r"Veneto", text, re.I):
        blob = f"{name_ko} {text}"
        if re.search(r"벨트|belt", blob, re.I):
            text = "Veneto 벨트 백"
        elif re.search(r"토트|tote", blob, re.I):
            text = "Veneto 토트"
        else:
            text = "Veneto"
    if re.search(r"Dean", text, re.I) or "미드 레이어" in text or "미드레이어" in text:
        text = "Dean 골프 미드레이어"
    if re.search(r"Donnie|도니", text, re.I):
        text = "Donnie 골프 스웨트"
    if re.search(r"문\s*페이즈|Moon\s*Phase", text, re.I):
        text = "문 페이즈"
    if re.search(r"오이스터\s*퍼페츄얼", text, re.I):
        text = "오이스터 퍼페츄얼"
    if re.search(r"플래닛\s*오션|Planet\s*Ocean", text, re.I):
        text = "플래닛 오션"
    elif re.search(r"아쿠아\s*테라|Aqua\s*Terra", text, re.I):
        text = "씨마스터 아쿠아 테라"
    elif re.search(r"다이버\s*300|Diver\s*300", text, re.I):
        text = "씨마스터 다이버 300M"
    elif re.search(r"씨마스터|Seamaster", text, re.I):
        text = "씨마스터"
    if re.search(r"트웰브|Twelve|C12", text, re.I):
        text = "트웰브"
    if re.search(r"C60\s*프로", text, re.I):
        text = "C60 프로 300"
    if re.search(r"버논", text, re.I):
        text = "버논 스키 재킷"
    # YSL classic model: keep LE 5 A 7 + 서플 스몰
    if re.search(r"LE\s*5\s*A\s*7", text, re.I):
        m = re.search(r"(LE\s*5\s*A\s*7(?:\s*서플)?(?:\s*스몰)?)", text, re.I)
        if m:
            text = m.group(1)
    # Andiamo etc: model + type only
    if text.lower().startswith("andiamo"):
        text = re.sub(r"^(Andiamo\s+\S+).*$", r"\1", text, flags=re.I)
    if "브르타뉴" in text and "다운" in text:
        text = "브르타뉴 다운 재킷"
    if "TOP GUN" in text.upper():
        text = "파일럿 워치 TOP GUN"
    if "스피드마스터" in text and "애니버서리" in text:
        text = "스피드마스터 애니버서리"
    if "아쿠아레이서" in text:
        text = "아쿠아레이서 프로페셔널 300"
    if "블랙 베이" in text:
        text = re.sub(r"^(블랙 베이(?:\s*원)?(?:\s*\d+)?).*$", r"\1", text)
    if len(text) > 22:
        text = text[:21].rstrip() + "…"
    return text or sanitize_slide_text(brand_ko)


def _object_particle(word: str) -> str:
    """Rough 을/를 for TTS — Hangul final consonant → 을, else 를."""
    if not word:
        return "를"
    ch = word[-1]
    if "가" <= ch <= "힣":
        return "을" if (ord(ch) - 0xAC00) % 28 else "를"
    return "를"


# Naver card keeps 3 on-screen lines; VO is only this short payment line (no 적립 TTS).
NAVER_PAY_VO = "네이버페이로 안전하게 결제하세요."
NAVER_PAY_CARD = (
    "네이버페이로 간편하게 결제!",
    "안심하고 편리한 원클릭 네이버페이",
    "네이버포인트도 적립하세요.",
)


def tts_bag_pronunciation(text: str) -> str:
    """VO-only: say bag 백 as tensed 빽. On-screen copy stays 백."""
    out = text or ""
    for src, dst in (
        ("워시백", "워시빽"),
        ("드롭백", "드롭빽"),
        ("벨트백", "벨트빽"),
        ("가죽 백", "가죽 빽"),
        ("데일리 백", "데일리 빽"),
        ("미니멀 백", "미니멀 빽"),
        ("생로랑 백", "생로랑 빽"),
        ("내 백", "내 빽"),
        ("는 백", "는 빽"),
        ("백으로", "빽으로"),
        ("백을", "빽을"),
        ("백이", "빽이"),
        ("백은", "빽은"),
        ("백에", "빽에"),
        ("백만", "빽만"),
        ("백도", "빽도"),
        ("백,", "빽,"),
        ("백.", "빽."),
    ):
        out = out.replace(src, dst)
    # trailing bare 백 (e.g. end of clause)
    out = re.sub(r"백(?=\s|$)", "빽", out)
    return out


def tts_price_pronunciation(text: str) -> str:
    """VO-only: price-range 대 must sound as tensed 때 (never 대).

    Edge TTS often reads 「원때」 as 「원대」. Lock with 「원떼」 / 「가격떼」.
    On-screen cards keep normal Hangul (만 원 / 가격대 if ever shown).
    """
    out = text or ""
    # UK list-price: always tensed 까 (판매까 / 현지까), never 가.
    out = out.replace("판매가", "판매까").replace("현지가", "현지까")
    # Normalize any accidental 대 spellings first, then phonetic lock.
    out = out.replace("가격대", "가격때").replace("원대", "원때")
    out = re.sub(r"가격\s*때", "가격떼", out)
    out = re.sub(r"원\s*때", "원떼", out)
    if re.search(r"원\s*대|가격\s*대", out):
        raise RuntimeError(f"VO still has 대 price-range spelling: {out!r}")
    if re.search(r"판매가|현지가", out):
        raise RuntimeError(f"VO still has 가 UK-price spelling: {out!r}")
    return out


def prepare_vo_line(text: str) -> str:
    """Final VO string for TTS: bag 빽 + price 때/까 locks."""
    out = tts_price_pronunciation(tts_bag_pronunciation(sanitize_slide_text(text or "")))
    # Never ship “붙는/붙습니다” lifestyle filler — use 어울립니다.
    if re.search(r"붙는|붙음|붙습니다", out):
        raise RuntimeError(f"VO bans 붙는/붙음 (use 어울립니다): {out!r}")
    # Ban repeated “손이 자주/자꾸 가는” filler (손목·손잡이·손안은 허용).
    if re.search(r"손이\s*(자주|자꾸)\s*가|자꾸\s*손이\s*가|손이\s*가는|손이\s*닿는|손이\s*감(?!각)", out):
        raise RuntimeError(f"VO bans 손이 자주/가는 filler: {out!r}")
    return out


def closing_cta(search_name: str, platform: str = "shorts") -> str:
    """Last VO line — both platforms use briq.kr search.

    Shorts comment/description URLs are non-clickable on mobile, so pinned-link
    CTA does not convert. Same search CTA as Instagram.
    """
    return f"브릭 점 케이알에서 {search_name}{_object_particle(search_name)} 검색해 보세요."


def _clean_pdp_fact(text: str) -> str:
    t = re.sub(r"^[·\-\*\u2022\s]+", "", (text or "").strip())
    t = re.sub(r"\s+", " ", t)
    # Bad EN→KO: "tanned calf leather" → "가축화된 송아지 LE"
    t = t.replace("가축화된 송아지 LE", "송아지 가죽")
    t = t.replace("가축화된 송아지", "송아지 가죽")
    t = re.sub(r"^T\s*100%\s*", "", t)
    t = re.sub(r"^Dimensions:\s*", "", t, flags=re.I)
    return t.rstrip(" .")


PDP_FACT_NOISE = (
    "제품 코드",
    "제조국",
    "사이즈가 애매",
    "깨끗이 닦",
    "세탁",
    "드라이",
    "전용 더스트",
    "기프트 박스",
    "선물 박스",
    "고층 건물",  # bad EN→KO (high-rise → building)
    "모델 키",
    "UK 사이즈",
    "피트",
    "인치이며",
    "입고 있습니다",
    "표시된 측정",
    "개별 제품마다",
    "측정값",
    "가축화",
)

PDP_FACT_BOOST = (
    "밑창",
    "실루엣",
    "가죽",
    "스웨이드",
    "위빙",
    "인트레치아토",
    "방수",
    "방풍",
    "발수",
    "다이얼",
    "케이스",
    "스트랩",
    "굽",
    "지퍼",
    "수납",
    "탈착",
    "조절",
    "보온",
    "통기",
    "크로노",
    "스키브",
    "스티치",
    "칼라",
    "핸들",
    "스트랩",
    "나일론",
)


def collect_raw_pdp_facts(product: dict | None) -> list[str]:
    """Pull concrete PDP bullets from catalog detail fields."""
    if not product:
        return []
    out: list[str] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        t = _clean_pdp_fact(raw)
        if not t or t in seen:
            return
        seen.add(t)
        out.append(t)

    for f in product.get("featuresKo") or []:
        if isinstance(f, str):
            add(f)
    for sec in product.get("storySections") or []:
        if not isinstance(sec, dict):
            continue
        title = str(sec.get("titleKo") or "")
        body = str(sec.get("bodyKo") or "")
        if any(k in title for k in ("디테일", "특징", "포인트", "스펙", "소개")):
            for line in re.split(r"[\n·•\|]", body):
                add(line)
    for spec in product.get("techSpecs") or []:
        if not isinstance(spec, dict):
            continue
        label = str(spec.get("labelKo") or "")
        val = str(spec.get("valueKo") or "")
        if any(k in label for k in ("소재", "스펙", "디테일")):
            for part in re.split(r"[·\n\|]", val):
                if any(k in part for k in ("갑피", "안감", "밑창", "소재", "가죽", "나일론", "고무")):
                    add(part)
    return out


def score_pdp_fact(fact: str, *, source_rank: int = 99) -> float:
    if any(n in fact for n in PDP_FACT_NOISE):
        return -10.0
    if len(fact) < 2:
        return -10.0
    # Long story blurb — usually too diffuse for a Shorts beat.
    if len(fact) > 70 and ":" not in fact:
        return -2.0
    score = 1.0
    # Prefer earlier featuresKo bullets (catalog order ≈ importance).
    score += max(0.0, 2.4 - 0.35 * source_rank)
    if len(fact) > 55:
        score -= 0.8
    if len(fact) > 80:
        score -= 1.5
    if any(b in fact for b in PDP_FACT_BOOST):
        score += 1.2
    # Distinctive design nouns beat generic material percentages.
    if any(k in fact for k in ("상어", "스키브", "로우탑", "발레", "인트레치아토", "위빙", "헥스", "클리티드")):
        score += 2.2
    if re.match(r"^(갑피|안감|밑창)\s*[:：]", fact) and "%" in fact:
        score -= 0.6  # keep as backup, not first pick
    if fact.startswith("굽"):
        score += 0.8
    return score


def fact_to_vo_card(fact: str, gender_key: str) -> tuple[str, str, str] | None:
    """Turn a PDP bullet into spoken VO + on-screen title/subtitle."""
    fact = _clean_pdp_fact(fact)
    if not fact or score_pdp_fact(fact) < 0:
        return None
    polite_da = gender_key == "male"
    # 적습니다/적어요 · 높습니다/높아요 · 분명합니다/분명해요
    end_jeok = "습니다" if polite_da else "어요"
    end_nop = "습니다" if polite_da else "아요"
    end_bun = "합니다" if polite_da else "해요"
    end_ida = "입니다" if polite_da else "예요"

    m = re.match(r"굽\s*높이\s*[:：]?\s*(.+)", fact)
    if m:
        h = m.group(1).replace("cm", "센티").replace("CM", "센티").strip()
        return (
            f"굽 높이는 {h}라, 데일리로 부담이 적{end_jeok}.",
            "굽 높이",
            h,
        )
    m = re.match(r"갑피\s*[:：]\s*(.+)", fact)
    if m:
        mat = _clean_pdp_fact(m.group(1))
        short = mat if len(mat) <= 22 else mat[:21].rstrip() + "…"
        return (
            f"갑피는 {mat} 구성이라, 소재감이 분명{end_bun}.",
            "갑피 소재",
            short,
        )
    m = re.match(r"안감\s*[:：]\s*(.+)", fact)
    if m:
        mat = _clean_pdp_fact(m.group(1))
        short = mat if len(mat) <= 22 else mat[:21].rstrip() + "…"
        return (
            f"안감은 {mat}라, 착용감이 깔끔{end_bun}.",
            "안감",
            short,
        )
    m = re.match(r"밑창\s*[:：]\s*(.+)", fact)
    if m:
        mat = _clean_pdp_fact(m.group(1))
        return (
            f"밑창은 {mat}라, 접지감이 분명{end_bun}.",
            "밑창",
            mat[:22],
        )

    title = fact if len(fact) <= 18 else fact[:17].rstrip() + "…"
    if "상어" in fact and "밑창" in fact:
        return (f"{fact}이라, 접지감과 인상이 분명{end_bun}.", title, "접지감이 분명한")
    if "밑창" in fact:
        return (f"{fact}이라, 접지감이 분명{end_bun}.", title, "접지감이 분명한")
    if "실루엣" in fact or "로우탑" in fact:
        seen = "보입니다" if polite_da else "보여요"
        return (f"{fact}이라, 코디가 정리돼 {seen}.", title, "코디가 정리되는")
    if "스키브" in fact or "스티치" in fact:
        return (
            f"{fact}이라, 빈티지한 디테일이 살아납니다."
            if polite_da
            else f"{fact}이라, 빈티지한 디테일이 살아나요.",
            title,
            "빈티지 디테일",
        )
    if "칼라" in fact:
        return (f"{fact}이라, 착용감이 안정적{end_bun}.", title, "착용감이 안정적인")
    if any(k in fact for k in ("위빙", "인트레치아토")):
        return (
            f"{fact}이라, 가까이서도 완성도가 다릅니다."
            if polite_da
            else f"{fact}이라, 가까이서도 완성도가 달라요.",
            title,
            "가까이서 봐도 다른",
        )
    if any(k in fact for k in ("방수", "방풍", "발수", "통기", "보온")):
        return (f"{fact} 기능이라, 실사용 포인트가 분명{end_bun}.", title, "실사용 포인트")
    if any(k in fact for k in ("탈착", "조절")):
        return (f"{fact}이라, 활용도가 높{end_nop}.", title, "활용도가 높은")
    if any(k in fact for k in ("가죽", "스웨이드", "나일론")):
        return (f"{fact}이라, 소재감이 분명{end_bun}.", title, "소재감이 분명한")
    if any(k in fact for k in ("하드웨어", "버클", "지퍼", "스냅")):
        return (f"{fact}이라, 마감 디테일이 분명{end_bun}.", title, "마감 디테일")
    if any(k in fact for k in ("포켓", "주머니", "수납")):
        return (f"{fact}이라, 수납이 실사용에 맞{end_bun}.", title, "실사용 수납")
    if any(k in fact for k in ("어깨끈", "스트랩", "손잡이", "핸들")):
        return (f"{fact}이라, 활용도가 높{end_nop}.", title, "활용도가 높은")
    if any(k in fact for k in ("민소매", "긴소매", "반소매", "후드", "카라", "칼라")):
        return (f"{fact}이라, 실루엣이 분명{end_bun}.", title, "실루엣이 분명한")
    if any(k in fact for k in ("브리프", "케이스", "토트", "메신저")):
        return (f"{fact}이라, 형태감이 분명{end_bun}.", title, "형태감이 분명한")
    # On-screen: feature only — never “상세에서 고른 포인트” filler.
    # Subtitle repeats a short clip of the fact when title is truncated; else omit.
    sub = ""
    if len(fact) > 18:
        rest = fact[17:].lstrip(" …·,/")
        if len(rest) >= 4:
            sub = rest if len(rest) <= 22 else rest[:21].rstrip() + "…"
    if fact.endswith(("다", "요", "음", "함", "임")):
        if fact.endswith(("습니다", "이에요", "예요", "어요", "니다")):
            return (fact, title, sub)
        return (f"{fact}{end_ida}.", title, sub)
    particle = "가" if fact and (ord(fact[-1]) - 0xAC00) % 28 == 0 else "이"
    if fact and "가" <= fact[-1] <= "힣":
        return (f"{fact}{particle} 포인트{end_ida}.", title, sub)
    return (f"{fact}이 포인트{end_ida}.", title, sub)


def description_intro_line(
    product: dict,
    *,
    brand_ko: str,
    search_name: str,
    gender_key: str,
) -> str | None:
    """Use PDP descriptionKo as the product-intro VO when it has a real fact."""
    desc = _clean_pdp_fact(str(product.get("descriptionKo") or ""))
    if not desc:
        return None
    first = _clean_pdp_fact(re.split(r"[.。]", desc)[0])
    if len(first) < 8 or len(first) > 52:
        return None
    if any(n in first for n in PDP_FACT_NOISE):
        return None
    # Drop trailing product-type echo if too long with brand+name.
    polite = "입니다" if gender_key == "male" else "예요"
    if first.endswith(("다", "요")):
        return f"{brand_ko} {search_name}, {first}."
    # Avoid “…트레이너, 가벼운 발레 스타일 트레이너가 포인트” echo.
    for tail in (
        "트레이너",
        "스니커즈",
        "스니커",
        "러너",
        "워치",
        "시계",
        "재킷",
        "자켓",
        "백팩",
        "토트",
        "클러치",
    ):
        if first.endswith(tail) and tail in (search_name or ""):
            trimmed = first[: -len(tail)].rstrip(" ,")
            if len(trimmed) >= 6:
                return f"{brand_ko} {search_name}, {trimmed} 실루엣이 포인트{polite}."
    return f"{brand_ko} {search_name}, {first}가 포인트{polite}."


def build_pdp_beats(
    product: dict | None,
    gender_key: str,
    *,
    brand_ko: str,
    search_name: str,
) -> dict | None:
    """Pick 1–2 PDP facts for feature/lifestyle VO+cards, optional intro."""
    raw = collect_raw_pdp_facts(product)
    ranked = sorted(
        ((score_pdp_fact(f, source_rank=i), f) for i, f in enumerate(raw)),
        key=lambda x: (-x[0], len(x[1])),
    )
    ranked = [(s, f) for s, f in ranked if s >= 0.5]
    if not ranked:
        return None
    beats: dict = {"raw": [f for _, f in ranked[:4]]}
    cards: list[tuple[str, str, str]] = []
    for _, fact in ranked:
        beat = fact_to_vo_card(fact, gender_key)
        if not beat:
            continue
        # de-dupe near-same titles
        if any(vo_near_dup(beat[0], prev[0], ignore_phrases=[search_name, brand_ko]) for prev in cards):
            continue
        cards.append(beat)
        if len(cards) >= 2:
            break
    if not cards:
        return None
    beats["feature"] = cards[0]
    if len(cards) >= 2:
        beats["lifestyle"] = cards[1]
    intro = description_intro_line(
        product or {}, brand_ko=brand_ko, search_name=search_name, gender_key=gender_key
    )
    if intro:
        beats["intro"] = intro
    return beats


def build_vo_and_hooks(
    *,
    code: str,
    gender: str,
    brand_ko: str,
    brand_en: str,
    kind: str,
    search_name: str,
    price_spoken: str,
    gbp_spoken: str,
    platform: str = "shorts",
    name_ko: str = "",
    product_id: str = "",
    product: dict | None = None,
) -> tuple[list[str], tuple[str, str, str, str, str]]:
    """Unique VO + card hooks per product. Not a fill-in-the-blank template.

    When catalog PDP fields exist (descriptionKo / featuresKo / techSpecs),
    feature + lifestyle beats prefer those real product facts over brand filler.

    Returns lines (7) and hooks:
      0 = intro card subtitle
      1,2 = mid lifestyle card
      3,4 = purchase-desire feature card (title, subtitle)
    """
    # TTS: 현지까 (not 현지가); price range as 때 — prepare_vo_line locks to 원떼.
    price_line = (
        f"브릭 기준으로는 약 {price_spoken}때입니다."
        if not gbp_spoken
        else f"영국 현지까는 {gbp_spoken}, 브릭으로는 약 {price_spoken}때입니다."
    )
    cta = closing_cta(search_name, platform)
    gender_key = "male" if gender == "male" else "female"
    feat_key = code
    sku_early = _sku_text(
        search_name=search_name, name_ko=name_ko, product_id=product_id, product=product
    )
    if code == "al" and kind == "신발":
        feat_key = "al_shoes"
    elif code == "al" and kind == "가방":
        feat_key = "al_bags"
    elif code == "al" and _is_al_bottoms(sku_early):
        feat_key = "al_bottoms"
    elif code == "al" and _is_al_dress(sku_early):
        feat_key = "al_dress"
    elif code == "bv" and _is_bv_tote(sku_early):
        feat_key = "bv_tote"
    elif code == "cw" and any(k in sku_early for k in ("트웰브", "Twelve", "twelve", "C12")):
        feat_key = "cw_twelve"
    elif code == "om" and any(
        k in sku_early for k in ("씨마스터", "Seamaster", "seamaster", "플래닛", "Planet Ocean", "planet ocean")
    ) and not any(k in sku_early for k in ("스피드마스터", "Speedmaster", "speedmaster")):
        feat_key = "om_seamaster"
    elif code == "om" and any(
        k in sku_early for k in ("드 빌", "드빌", "De Ville", "de ville", "prestige", "프레스티지")
    ) and not any(k in sku_early for k in ("스피드마스터", "Speedmaster", "speedmaster")):
        feat_key = "om_deville"
    feat = FEATURE_BEAT.get(feat_key, {}).get(gender_key) or FEATURE_BEAT.get(code, {}).get(
        gender_key
    ) or (
        f"{search_name}, 실사용에서 만족도가 높은 포인트가 분명합니다.",
        "실사용 포인트",
        "만족도가 높은 이유",
    )
    feature_vo, feature_title, feature_sub = feat

    # Per-brand scripts (male/female wording slightly different)
    scripts: dict[str, dict[str, list[str]]] = {
        "ys": {
            "male": [
                "데일리 백으로 쓰기 좋은 생로랑, 지금 반응이 큽니다.",
                f"그중에서도 {search_name}, 실루엣이 깔끔해서 코디가 쉽습니다.",
                price_line,
                "과하지 않은 로고감이라, 출근이랑 주말 룩에 둘 다 잘 어울립니다.",
                "관부가세 포함으로 안내하니, 최종가만 보면 됩니다.",
                cta,
            ],
            "female": [
                "요즘 미니멀 백 찾는 분들, 생로랑부터 많이 보세요.",
                f"{search_name}는 작아 보여도 수납이 생각보다 알찹니다.",
                price_line,
                "어깨에 걸었을 때 라인이 예뻐서, 사진 찍히는 날에도 부담이 적어요.",
                "영국 현지 가격 기준으로 맞춰 드리니 비교하기 편합니다.",
                cta,
            ],
        },
        "bv": {
            "male": [
                "보테가 하면 위빙만 생각하기 쉬운데, 클러치 라인도 강합니다.",
                f"{search_name}, 손안에 들어오는 존재감이 확실해요.",
                price_line,
                "정장에도, 캐주얼 재킷에도 같이 가기 좋은 포인트 아이템입니다.",
                "실재고 기준으로만 안내하니까, 허수 재고는 빼 두었습니다.",
                cta,
            ],
            "female": [
                "보테가 베네타, 위빙 말고 미니 클러치로 가면 분위기가 달라집니다.",
                f"오늘은 {search_name}를 골랐어요.",
                price_line,
                # Lifestyle only — FEATURE_BEAT already covers light + metal face lift.
                "파티·디너에 들고 나가도 과하지 않아서 활용도가 높아요.",
                "배송·관세 포함 가격이라 결제 전에 헷갈릴 게 적어요.",
                cta,
            ],
        },
        "bv_tote": {
            "male": [
                "보테가 토트, 위빙감이 가까이서도 조밀해서 반응이 좋습니다.",
                f"{search_name}, 들고 나가기 좋은 실루엣입니다.",
                price_line,
                "정장에도, 캐주얼에도 포인트가 과하지 않게 살아납니다.",
                "실재고 기준으로만 안내하니까, 허수 재고는 빼 두었습니다.",
                cta,
            ],
            "female": [
                "보테가 베네타 토트로 가면 코디가 한결 정리돼 보여요.",
                f"오늘은 {search_name}를 골랐어요.",
                price_line,
                "정장에도 캐주얼에도 잘 어울리는 타입이에요.",
                "배송·관세 포함 가격이라 결제 전에 헷갈릴 게 적어요.",
                cta,
            ],
        },
        "al": {
            "male": [
                "매일 입는 아우터, 브랜드만 바꿔도 느낌이 확 달라집니다.",
                f"올세인츠 {search_name}, 데님 특유의 무게감이 좋습니다.",
                price_line,
                "핏이 과하지 않아서, 티셔츠 위에도 셔츠 위에도 잘 올라갑니다.",
                "영국 셀렉트 가격으로 보시고, 국내 직송으로 받으시면 됩니다.",
                cta,
            ],
            "female": [
                "가볍게 걸쳐도 완성도 나는 재킷, 올세인츠가 잘합니다.",
                f"{search_name}는 워싱감이 자연스러워서 새 옷 티가 덜 나요.",
                price_line,
                "청바지랑도, 스커트랑도 무난하게 잘 어울립니다.",
                "관부가세까지 포함한 금액으로 안내해 드려요.",
                cta,
            ],
        },
        "al_shoes": {
            "male": [
                "데일리 스니커, 브랜드만 바꿔도 코디 완성도가 달라집니다.",
                f"올세인츠 {search_name}, 실루엣이 깔끔해서 신기 편합니다.",
                price_line,
                "데님에도 잘 어울리는 제품입니다.",
                "영국 셀렉트 가격으로 보시고, 국내 직송으로 받으시면 됩니다.",
                cta,
            ],
            "female": [
                "올세인츠 스니커, 과하지 않은 디테일이 데일리에 잘 맞아요.",
                f"{search_name}는 신었을 때 비율이 안정적이에요.",
                price_line,
                "데님에도 잘 어울리는 제품이에요.",
                "관부가세까지 포함한 금액으로 안내해 드려요.",
                cta,
            ],
        },
        "al_bags": {
            "male": [
                "올세인츠 백, 캐주얼한데 마감이 탄탄해서 반응이 좋습니다.",
                f"{search_name}, 들고 다니기 좋은 실루엣입니다.",
                price_line,
                "출근 룩에도, 주말 룩에도 잘 어울리는 제품입니다.",
                "영국 셀렉트 가격으로 보시고, 국내 직송으로 받으시면 됩니다.",
                cta,
            ],
            "female": [
                "올세인츠 백으로 가면 코디가 한결 가벼워져요.",
                f"오늘은 {search_name}를 골랐어요.",
                price_line,
                "데일리에 과하지 않아서, 자주 들게 되는 쪽이에요.",
                "관부가세까지 포함한 금액으로 안내해 드려요.",
                cta,
            ],
        },
        "al_bottoms": {
            "male": [
                "하의 하나만 바꿔도 코디 완성도가 달라집니다.",
                f"올세인츠 {search_name}, 실루엣이 과하지 않아서 매일이 편합니다.",
                price_line,
                "상의만 바꿔도 분위기가 정리돼서, 데일리로 자주 입게 됩니다.",
                "영국 셀렉트 가격으로 보시고, 국내 직송으로 받으시면 됩니다.",
                cta,
            ],
            "female": [
                "바지·스커트는 기장이 핵심인데, 올세인츠가 그 지점을 잘 잡아요.",
                f"{search_name}는 비율이 안정적이라 신발 바꿔도 무난해요.",
                price_line,
                "상의만 바꿔도 분위기가 정리돼서, 데일리로 자주 입게 돼요.",
                "관부가세까지 포함한 금액으로 안내해 드려요.",
                cta,
            ],
        },
        "al_dress": {
            "male": [
                "원피스 한 장으로 정리되는 룩, 올세인츠가 잘합니다.",
                f"올세인츠 {search_name}, 실루엣이 분명해서 매일이 편합니다.",
                price_line,
                "신발만 바꿔도 분위기가 달라서, 데일리로 자주 입게 됩니다.",
                "영국 셀렉트 가격으로 보시고, 국내 직송으로 받으시면 됩니다.",
                cta,
            ],
            "female": [
                "원피스 하나로 끝나는 날, 올세인츠 드레스가 잘 맞아요.",
                f"{search_name}는 비율이 안정적이라 신발 바꿔도 무난해요.",
                price_line,
                "신발만 바꿔도 분위기가 달라서, 데일리로 자주 입게 돼요.",
                "관부가세까지 포함한 금액으로 안내해 드려요.",
                cta,
            ],
        },
        "mc": {
            "male": [
                "겨울 패딩, 브랜드만 보고 고르면 실패하기 쉽습니다.",
                f"몽클레르 {search_name}, 길이감이 애매하지 않아서 실착 밸런스가 좋습니다.",
                price_line,
                "시티 룩에도, 주말 아웃도어에도 같이 쓰기 좋은 밸런스입니다.",
                "실제 영국 판매 구성 기준으로 재고를 맞춰 둡니다.",
                cta,
            ],
            "female": [
                "다운 재킷은 부피만 크고 핏이 무너지는 경우가 많아요.",
                f"몽클레르 {search_name}, 실루엣이 정돈돼서 걸쳐도 부해 보이지 않아요.",
                price_line,
                # Lifestyle only — FEATURE_BEAT covers hood/face; avoid repeating that beat.
                "소매·밑단 마감이 탄탄해서, 한겨울 바람에도 덜 맵니다.",
                "관세·항공 포함이라 최종가 계산이 단순합니다.",
                cta,
            ],
        },
        "gg": {
            "male": [
                "골프웨어는 기능만 강조하면 밋밋해지기 쉽습니다.",
                f"갤빈그린 {search_name}, 방풍이면서도 레이어드가 깔끔합니다.",
                price_line,
                # Lifestyle only — FEATURE_BEAT already covers round + travel dual use.
                "통기·방풍 밸런스가 좋아서, 땀 차는 코스가 덜합니다.",
                "영국 골프웨어 현지까를 기준으로 안내합니다.",
                cta,
            ],
            "female": [
                "필드에서 바람 막으면서도 답답하지 않은 베스트, 찾기 어렵죠.",
                f"갤빈그린 {search_name}가 그 중간을 잘 잡습니다.",
                price_line,
                "화이트 계열이라 다른 골프웨어랑 섞어 입기 편해요.",
                "브릭은 관부가세 포함 가격으로 보여 드려요.",
                cta,
            ],
        },
        "cw": {
            "male": [
                "미드레인지 시계에서 영국 매뉴팩처 감성 찾는 분들, 많아졌습니다.",
                f"크리스토퍼 워드 {search_name}, 시랜더 라인의 야외용 해석입니다.",
                price_line,
                # Lifestyle only — FEATURE_BEAT already covers dial readability.
                "브레이슬릿 마감이 탄탄해서, 오래 차도 유격이 잘 안 납니다.",
                "영국 공식가 대비 브릭 안내가를 같이 보시면 됩니다.",
                cta,
            ],
            "female": [
                "큰 다이버만 보기 부담스러울 때, 시랜더 쪽이 선택지가 됩니다.",
                f"오늘은 {search_name}, 이걸로 골랐어요.",
                price_line,
                # Lifestyle only — FEATURE_BEAT (GMT 대비) is inserted after price.
                "브레이슬릿 마감이 깔끔해서, 데일리로 차도 거슬림이 적어요.",
                "관세 포함으로 계산해 드리니 비교가 간단해요.",
                cta,
            ],
        },
        "td": {
            "male": [
                "툴워치 입문에서 튜더를 빼놓고 이야기하기 어렵습니다.",
                f"{search_name}, 블랙 베이 계열의 컴팩트한 해석입니다.",
                price_line,
                "사이즈가 부담스럽지 않아서, 첫 오토매틱으로도 많이 고릅니다.",
                "영국 현지 시세 기준으로 안내합니다.",
                cta,
            ],
            "female": [
                "다이버 룩은 원하는데 너무 큰 건 싫다, 그 지점이면 튜더가 잘 맞아요.",
                f"{search_name}는 손목에서 존재감과 착용감의 균형이 좋습니다.",
                price_line,
                "블랙 다이얼이라 옷 색을 거의 안 가려요.",
                "배송·관세 포함 가격으로 보여 드립니다.",
                cta,
            ],
        },
        "th": {
            "male": [
                "스포츠 워치 하면 태그호이어 아쿠아레이서가 먼저 떠오릅니다.",
                f"{search_name}, 다이빙 스펙을 데일리로 풀어낸 모델입니다.",
                price_line,
                # Lifestyle only — FEATURE_BEAT is inserted after price (do not repeat it here).
                "스포츠 워치인데도 과하지 않아서, 평소 룩에도 잘 어울립니다.",
                "영국 판매까 기준으로 브릭 가격을 맞춰 둡니다.",
                cta,
            ],
            "female": [
                "액티브한 날에 차기 좋은 시계, 태그호이어가 강합니다.",
                f"{search_name}은 물이나 땀에도 부담이 적은 구성이에요.",
                price_line,
                "스포츠 워치인데도 과하지 않아서, 평소 룩에도 잘 어울려요.",
                "관부가세 포함이라 최종가만 확인하시면 됩니다.",
                cta,
            ],
        },
        "iw": {
            "male": [
                "파일럿 워치는 많지만, IWC TOP GUN은 결이 다릅니다.",
                f"{search_name}, 항공 무드가 분명한 모델입니다.",
                price_line,
                "케이스 마감이 단단해서, 소장용으로 고르는 분들이 많아요.",
                "영국 현지 기준 가격으로 안내합니다.",
                cta,
            ],
            "female": [
                "큰 시계도 잘 소화하고 싶다면, IWC 파일럿 쪽을 보세요.",
                f"오늘은 {search_name}를 골랐어요.",
                price_line,
                # Lifestyle only — FEATURE_BEAT already covers dial contrast.
                "블랙 앤 화이트 조합이라 옷에 잘 어울려요.",
                "관세·항공 포함 금액으로 비교하시면 됩니다.",
                cta,
            ],
        },
        "om": {
            "male": [
                "스피드마스터는 오메가의 상징이라, 버전만 해도 이야기가 깁니다.",
                f"{search_name}, 애니버서리 무드가 살아 있는 구성입니다.",
                price_line,
                "문워치 DNA를 유지하면서도, 기념 디테일이 분명합니다.",
                "영국 공식 시세 기준으로 브릭에서 맞춰 드립니다.",
                cta,
            ],
            "female": [
                "오메가 스피드마스터, 남녀 가리지 않고 찾는 분들이 늘었어요.",
                f"오늘은 {search_name}를 골랐습니다.",
                price_line,
                "크로노 푸셔 감이 분명해서, 차면 디테일이 오래 남아요.",
                "관부가세 포함 가격이라 계산이 단순합니다.",
                cta,
            ],
        },
        "ms": {
            "male": [
                "덴마크 가죽 백, 미스모는 쓸수록 멋지게 에이징됩니다.",
                f"{search_name}, 심플한데 마감이 단단해서 출근용으로 많이 고릅니다.",
                price_line,
                "로고가 과하지 않아서, 정장·캐주얼 둘 다 잘 받습니다.",
                "영국 현지 셀렉트 기준으로 안내합니다.",
                cta,
            ],
            "female": [
                "미니멀한 브리프·메신저 찾는다면 미스모를 한번 보세요.",
                f"오늘은 {search_name}를 골랐어요.",
                price_line,
                "가죽이 부드럽고, 수납이 실사용 중심으로 짜여 있습니다.",
                "관세·항공 포함이라 최종가가 깔끔해요.",
                cta,
            ],
        },
        "pp": {
            "male": [
                "하이엔드 시계에서 파텍필립은 따로 언급되는 브랜드입니다.",
                f"{search_name}, 디테일 완성도가 확실히 다릅니다.",
                price_line,
                "소장 가치와 착용감을 같이 보는 분들이 많이 찾습니다.",
                "영국 현지 시세 기준으로 안내합니다.",
                cta,
            ],
            "female": [
                "파텍필립은 유행보다 시간을 두고 고르는 시계예요.",
                f"오늘은 {search_name}를 골랐습니다.",
                price_line,
                "다이얼 밸런스가 좋아서, 차면 존재감이 분명합니다.",
                "관부가세 포함으로 계산해 드리니 비교가 쉽습니다.",
                cta,
            ],
        },
        "rx": {
            "male": [
                "롤렉스는 모델만 바꿔도 분위기가 완전히 달라집니다.",
                f"{search_name}, 지금 문의가 꾸준한 구성입니다.",
                price_line,
                "첫 롤렉스로도, 컬렉션용으로도 자주 거론됩니다.",
                "영국 현지 기준 가격으로 안내합니다.",
                cta,
            ],
            "female": [
                "롤렉스, 이름만으로도 설득되는 브랜드지만 모델 선택이 핵심이에요.",
                f"{search_name}는 착용감과 존재감의 균형이 좋습니다.",
                price_line,
                "클래식하면서도 데일리에 과하지 않은 쪽에 가깝습니다.",
                "관세 포함 안내라 결제 전 계산이 단순해요.",
                cta,
            ],
        },
    }

    # hooks[0]=card1 line2, hooks[1..2]=lifestyle card, hooks[3..4]=feature card
    hooks: dict[str, tuple[str, str, str]] = {
        "ys": ("데일리로 쓰기 좋은 생로랑 백", "과하지 않은 로고감", "출근·주말 둘 다 잘 어울림"),
        "bv": ("보테가의 또 다른 얼굴", "정장에도 캐주얼에도", "포인트가 과하지 않음"),
        "bv_tote": ("들고 나가기 좋은 토트", "조밀한 위빙감", "정장·캐주얼 둘 다"),
        "al": ("매일 걸쳐도 질리지 않는 아우터", "데님 아우터", "핏이 과하지 않은 이유"),
        "al_shoes": ("데일리로 신기 좋은 올세인츠 스니커", "깔끔한 실루엣", "데님에도 잘 어울림"),
        "al_bags": ("캐주얼한데 탄탄한 올세인츠 백", "과하지 않은 존재감", "데일리에 자주 들게 됨"),
        "al_bottoms": ("매일 입기 좋은 하의", "과하지 않은 실루엣", "상의만 바꿔도 정리됨"),
        "al_dress": ("한 장으로 정리되는 드레스", "분명한 실루엣", "신발만 바꿔도 분위기 전환"),
        "mc": ("겨울 패딩의 기준이 되는 한 벌", "시티에도 아웃도어에도", "길이감이 애매하지 않음"),
        "gg": ("필드와 일상의 중간 지점", "방풍 골프 베스트", "레이어드가 깔끔한 이유"),
        "gg_mid": ("필드와 일상의 중간 지점", "보온 미드레이어", "레이어드가 깔끔한 이유"),
        "cw": ("영국 매뉴팩처 입문으로 좋은", "시랜더 라인", "데일리로 차기 좋은 기계식"),
        "cw_twelve": ("영국 매뉴팩처 입문으로 좋은", "트웰브 라인", "데일리로 차기 좋은 기계식"),
        "cw_c60": ("영국 매뉴팩처 다이버로 좋은", "C60 다이버", "데일리로 차기 좋은 기계식"),
        "td": ("툴워치 입문의 정석", "블랙 베이 컴팩트", "첫 오토매틱으로도 충분"),
        "th": ("스포츠 워치의 대표 라인", "평소 룩에도 잘 어울림", "과하지 않은 스포츠 워치"),
        "iw": ("파일럿 워치만의 결", "TOP GUN 무드", "소장 수요가 꾸준한 이유"),
        "iw_ingenieur": ("인제니어만의 결", "스틸 툴워치 무드", "소장 수요가 꾸준한 이유"),
        "iw_portofino": ("포르토피노의 단정한 결", "드레스 워치 무드", "소장 수요가 꾸준한 이유"),
        "iw_portugieser": ("포르투기저의 클래식 결", "클래식 크로노 무드", "소장 수요가 꾸준한 이유"),
        "om": ("스피드마스터 DNA가 살아 있는", "애니버서리 에디션", "상징을 남기고 싶을 때"),
        "om_seamaster": ("씨마스터 DNA가 살아 있는", "데일리로 쓰기 좋은 다이버", "여행·평소 둘 다 가능"),
        "om_deville": ("드 빌의 단정한 드레스 무드", "프레스티지 라인", "오피스에도 잘 어울림"),
        "ms": ("덴마크 가죽의 깊이 있는 결", "과하지 않은 로고", "정장·캐주얼 둘 다 잘 받음"),
        "pp": ("하이엔드 시계의 기준점", "디테일의 완성", "소장용으로 고르는 시계"),
        "rx": ("아이콘 워치의 대표 무드", "모델이 곧 분위기", "꾸준히 찾는 수요"),
    }

    script_key = code
    if code == "al" and kind == "신발":
        script_key = "al_shoes"
    elif code == "al" and kind == "가방":
        script_key = "al_bags"
    sku_for_key = _sku_text(
        search_name=search_name, name_ko=name_ko, product_id=product_id, product=product
    )
    if code == "al" and _is_al_bottoms(sku_for_key):
        script_key = "al_bottoms"
    elif code == "al" and _is_al_dress(sku_for_key):
        script_key = "al_dress"
    elif code == "bv" and _is_bv_tote(sku_for_key):
        script_key = "bv_tote"
    is_gg_mid = code == "gg" and any(
        k in sku_for_key.lower()
        for k in ("mid-layer", "midlayer", "미드레이어", "darryl", "daniel", "dean", "insulating", "donnie")
    )
    if is_gg_mid:
        script_key = "gg_mid"
    if code == "cw" and any(k in sku_for_key for k in ("트웰브", "Twelve", "twelve", "C12")):
        script_key = "cw_twelve"
    elif code == "cw" and "C60" in sku_for_key:
        script_key = "cw_c60"
    if code == "om" and any(
        k in sku_for_key for k in ("씨마스터", "Seamaster", "seamaster", "플래닛", "Planet Ocean", "planet ocean")
    ) and not any(k in sku_for_key for k in ("스피드마스터", "Speedmaster", "speedmaster")):
        script_key = "om_seamaster"
    if code == "om" and any(
        k in sku_for_key for k in ("드 빌", "드빌", "De Ville", "de ville", "prestige", "프레스티지")
    ) and not any(k in sku_for_key for k in ("스피드마스터", "Speedmaster", "speedmaster")):
        script_key = "om_deville"
    if code == "iw" and any(k in sku_for_key for k in ("인제니어", "Ingenieur", "ingenieur")):
        script_key = "iw_ingenieur"
    elif code == "iw" and any(k in sku_for_key for k in ("포르토피노", "Portofino", "portofino")):
        script_key = "iw_portofino"
    elif code == "iw" and any(k in sku_for_key for k in ("포르투기저", "Portugieser", "portugieser")):
        script_key = "iw_portugieser"
    lines = scripts.get(script_key, {}).get(gender_key) or scripts.get(code, {}).get(gender_key)
    if not lines:
        lines = [
            f"{brand_ko}에서 지금 눈에 띄는 구성을 골랐습니다.",
            f"{search_name}입니다.",
            price_line,
            f"{kind}로 실사용하기 좋은 밸런스입니다.",
            "관부가세·항공배송 포함으로 안내합니다.",
            cta,
        ]

    # Product-specific overrides so VO matches the actual SKU, not just brand.
    if code == "cw" and any(k in sku_for_key for k in ("트웰브", "Twelve", "twelve", "C12")):
        lines = [
            "미드레인지에서 깔끔한 드레스·데일리 워치 찾는다면 트웰브가 잘 맞습니다.",
            f"크리스토퍼 워드 {search_name}, 케이스 비율이 안정적입니다.",
            price_line,
            "브레이슬릿 마감이 탄탄해서, 오래 차도 유격이 잘 안 납니다.",
            "영국 공식가 대비 브릭 안내가를 같이 보시면 됩니다.",
            cta,
        ] if gender_key == "male" else [
            "큰 다이버만 보기 부담스러울 때, 트웰브 쪽이 선택지가 됩니다.",
            f"오늘은 {search_name}, 이걸로 골랐어요.",
            price_line,
            "브레이슬릿 마감이 깔끔해서, 데일리로 차도 거슬림이 적어요.",
            "관세 포함으로 계산해 드리니 비교가 간단해요.",
            cta,
        ]
    if code == "cw" and "C60" in search_name:
        if gender_key == "female":
            lines = [
                "브론즈 다이버 찾는다면, 크리스토퍼 워드 C60 쪽이 잘 맞아요.",
                f"오늘은 {search_name}를 골랐습니다.",
                price_line,
                # Lifestyle only — do not repeat FEATURE_BEAT case/sleeve wording.
                "브론즈 톤이 캐주얼 룩에도 잘 어울려서 데일리로 차기 좋아요.",
                "관세 포함으로 계산해 드리니 비교가 간단해요.",
                cta,
            ]
        else:
            lines = [
                "프로 다이버 스펙을 데일리로 가져오고 싶을 때 C60이 자주 거론됩니다.",
                f"크리스토퍼 워드 {search_name}, 브론즈 무드가 분명합니다.",
                price_line,
                # Lifestyle only — FEATURE_BEAT already covers dial readability.
                "브론즈 케이스가 빛에 따라 톤이 바뀌어서, 차는 맛이 분명합니다.",
                "영국 공식가 대비 브릭 안내가를 같이 보시면 됩니다.",
                cta,
            ]
    if code == "gg" and "Dean" in search_name:
        lines = [
            "라운드 전후 체온 관리, 미드레이어에서 갈립니다.",
            f"갤빈그린 {search_name}, 보온이면서도 움직임이 답답하지 않습니다.",
            price_line,
            "필드뿐 아니라 평소 레이어드로도 쓰기 좋아요.",
            "영국 골프웨어 현지까를 기준으로 안내합니다.",
            cta,
        ] if gender_key == "male" else [
            "골프 미드레이어, 색만 예쁘고 기능이 빠지면 아쉽죠.",
            f"갤빈그린 {search_name}가 그 중간을 잘 잡습니다.",
            price_line,
            "레이어드해도 부피가 과하지 않아서 코디가 쉽습니다.",
            "브릭은 관부가세 포함 가격으로 보여 드려요.",
            cta,
        ]
    sku_blob = _sku_text(
        search_name=search_name, name_ko=name_ko, product_id=product_id, product=product
    )
    if code == "iw" and any(k in sku_blob for k in ("인제니어", "Ingenieur", "ingenieur")):
        lines = [
            "IWC 인제니어, 파일럿과 결이 다른 툴워치 라인입니다.",
            f"{search_name}, 스틸 무드가 분명한 구성입니다.",
            price_line,
            "케이스 마감이 단단해서, 소장용으로 고르는 분들이 많아요.",
            "영국 현지 기준 가격으로 안내합니다.",
            cta,
        ] if gender_key == "male" else [
            "파일럿만 보기 부담스러울 때, 인제니어 쪽이 선택지가 됩니다.",
            f"오늘은 {search_name}를 골랐어요.",
            price_line,
            "블랙 앤 화이트 조합이라 옷에 잘 어울려요.",
            "관세·항공 포함 금액으로 비교하시면 됩니다.",
            cta,
        ]
    if code == "iw" and any(k in sku_blob for k in ("포르토피노", "Portofino", "portofino")):
        lines = [
            "IWC 포르토피노, 드레스 워치 쪽으로 많이 고릅니다.",
            f"{search_name}, 깔끔한 다이얼이 강점입니다.",
            price_line,
            "케이스 마감이 단단해서, 소장용으로 고르는 분들이 많아요.",
            "영국 현지 기준 가격으로 안내합니다.",
            cta,
        ] if gender_key == "male" else [
            "포르토피노로 가면 IWC가 한결 단정해 보여요.",
            f"오늘은 {search_name}를 골랐어요.",
            price_line,
            "블랙 앤 화이트 조합이라 옷에 잘 어울려요.",
            "관세·항공 포함 금액으로 비교하시면 됩니다.",
            cta,
        ]
    if code == "iw" and any(k in sku_blob for k in ("포르투기저", "Portugieser", "portugieser")):
        lines = [
            "IWC 포르투기저, 클래식 크로노로 반응이 꾸준합니다.",
            f"{search_name}, 비율이 안정적인 구성입니다.",
            price_line,
            "케이스 마감이 단단해서, 소장용으로 고르는 분들이 많아요.",
            "영국 현지 기준 가격으로 안내합니다.",
            cta,
        ] if gender_key == "male" else [
            "포르투기저로 가면 클래식 IWC 무드가 분명해요.",
            f"오늘은 {search_name}를 골랐어요.",
            price_line,
            "블랙 앤 화이트 조합이라 옷에 잘 어울려요.",
            "관세·항공 포함 금액으로 비교하시면 됩니다.",
            cta,
        ]
    if code == "th" and any(k in sku_blob for k in ("까레라", "Carrera", "carrera")):
        lines = [
            "태그호이어 까레라, 레이싱 DNA를 데일리로 가져온 라인입니다.",
            f"{search_name}, 클래식한 크로노·데이트 무드가 분명합니다.",
            price_line,
            "스포츠 워치인데도 과하지 않아서, 평소 룩에도 잘 어울립니다.",
            "영국 판매까 기준으로 브릭 가격을 맞춰 둡니다.",
            cta,
        ] if gender_key == "male" else [
            "까레라로 가면 태그호이어 분위기가 한결 단정해져요.",
            f"오늘은 {search_name}를 골랐어요.",
            price_line,
            "스포츠 워치인데도 과하지 않아서, 평소 룩에도 잘 어울려요.",
            "관부가세 포함이라 최종가만 확인하시면 됩니다.",
            cta,
        ]
    if code == "th" and any(k in sku_blob for k in ("모나코", "Monaco", "monaco")):
        lines = [
            "태그호이어 모나코, 스퀘어 크로노의 아이콘 라인입니다.",
            f"{search_name}, 존재감이 분명한 구성입니다.",
            price_line,
            "스퀘어 케이스라 차면 분위기가 바로 달라집니다.",
            "영국 판매까 기준으로 브릭 가격을 맞춰 둡니다.",
            cta,
        ] if gender_key == "male" else [
            "모나코로 가면 태그호이어가 한결 아이코닉해 보여요.",
            f"오늘은 {search_name}를 골랐어요.",
            price_line,
            "스퀘어 크로노라 평소 룩에도 포인트가 분명해요.",
            "관부가세 포함이라 최종가만 확인하시면 됩니다.",
            cta,
        ]
    if code == "gg" and any(
        k in sku_blob.lower()
        for k in ("mid-layer", "midlayer", "미드레이어", "darryl", "daniel", "dean", "insulating")
    ):
        # Mid-layers, not wind vests — avoid 베스트 copy.
        lines = [
            "라운드 전후 체온 관리, 미드레이어에서 갈립니다.",
            f"갤빈그린 {search_name}, 보온이면서도 움직임이 답답하지 않습니다.",
            price_line,
            "필드뿐 아니라 평소 레이어드로도 쓰기 좋아요.",
            "영국 골프웨어 현지까를 기준으로 안내합니다.",
            cta,
        ] if gender_key == "male" else [
            "골프 미드레이어, 색만 예쁘고 기능이 빠지면 아쉽죠.",
            f"갤빈그린 {search_name}가 그 중간을 잘 잡습니다.",
            price_line,
            "레이어드해도 부피가 과하지 않아서 코디가 쉽습니다.",
            "브릭은 관부가세 포함 가격으로 보여 드려요.",
            cta,
        ]
    if code == "om" and any(
        k in sku_blob for k in ("씨마스터", "Seamaster", "seamaster", "플래닛", "Planet Ocean", "planet ocean")
    ) and not any(k in sku_blob for k in ("스피드마스터", "Speedmaster", "speedmaster")):
        if "아쿠아 테라" in search_name or "Aqua Terra" in sku_blob:
            lines = [
                "스피드마스터만 있는 게 아니에요. 아쿠아 테라도 많이 찾습니다.",
                f"오늘은 {search_name}를 골랐습니다.",
                price_line,
                "드레스와 캐주얼 사이, 데일리로 차기 좋은 밸런스예요.",
                "관부가세 포함 가격이라 계산이 단순합니다.",
                cta,
            ] if gender_key == "female" else [
                "오메가 씨마스터 아쿠아 테라, 오피스에도 주말에도 같이 갑니다.",
                f"{search_name}, 깔끔한 다이얼이 강점입니다.",
                price_line,
                "과하지 않은 존재감이라 첫 오메가로도 많이 고릅니다.",
                "영국 현지 기준 가격으로 안내합니다.",
                cta,
            ]
        else:
            lines = [
                "오메가 씨마스터, 다이버인데도 데일리로 많이 찹니다.",
                f"{search_name}, 물에도 부담이 적은 구성입니다.",
                price_line,
                "다이버 스펙인데도 과하지 않아서, 평소 룩에도 잘 어울립니다.",
                "영국 현지 기준 가격으로 안내합니다.",
                cta,
            ] if gender_key == "male" else [
                "오메가 씨마스터, 남녀 가리지 않고 찾는 분들이 늘었어요.",
                f"오늘은 {search_name}를 골랐습니다.",
                price_line,
                "여행이랑 데일리 둘 다 쓰기 좋아서, 활용도가 높아요.",
                "관부가세 포함 가격이라 계산이 단순합니다.",
                cta,
            ]
    if code == "om" and any(
        k in sku_blob for k in ("드 빌", "드빌", "De Ville", "de ville", "prestige", "프레스티지")
    ) and not any(k in sku_blob for k in ("스피드마스터", "Speedmaster", "speedmaster")):
        lines = [
            "오메가 드 빌, 단정한 드레스 워치를 찾는 분들이 많이 보세요.",
            f"오늘은 {search_name}를 골랐습니다.",
            price_line,
            "다이얼이 깔끔해서, 오피스 룩에도 잘 어울려요.",
            "관부가세 포함 가격이라 계산이 단순합니다.",
            cta,
        ] if gender_key == "female" else [
            "오메가 드 빌 프레스티지, 과하지 않은 드레스 워치입니다.",
            f"{search_name}, 비율이 안정적인 구성입니다.",
            price_line,
            "마감이 탄탄해서, 데일리 드레스 워치로 고르기 좋습니다.",
            "영국 현지 기준 가격으로 안내합니다.",
            cta,
        ]
    elif code == "om" and "아쿠아 테라" in search_name:
        lines = [
            "스피드마스터만 있는 게 아니에요. 아쿠아 테라도 많이 찾습니다.",
            f"오늘은 {search_name}를 골랐습니다.",
            price_line,
            "드레스와 캐주얼 사이, 데일리로 차기 좋은 밸런스예요.",
            "관부가세 포함 가격이라 계산이 단순합니다.",
            cta,
        ] if gender_key == "female" else [
            "오메가 씨마스터 아쿠아 테라, 오피스에도 주말에도 같이 갑니다.",
            f"{search_name}, 깔끔한 다이얼이 강점입니다.",
            price_line,
            "과하지 않은 존재감이라 첫 오메가로도 많이 고릅니다.",
            "영국 현지 기준 가격으로 안내합니다.",
            cta,
        ]
    if code == "ys" and "KATE" in search_name.upper():
        lines = [
            "생로랑 케이트, 클래식한데 지금 다시 반응이 좋습니다.",
            f"{search_name}, 체인 드롭이 얼굴 라인을 살려 줍니다.",
            price_line,
            "미니멀 룩에도, 포인트 룩에도 잘 어울리는 타입이에요.",
            "영국 현지 가격 기준으로 맞춰 드리니 비교하기 편합니다.",
            cta,
        ]
    if code == "bv" and ("백팩" in search_name or "backpack" in search_name.lower()):
        lines = [
            "보테가 백팩, 위빙감이 가까이서도 조밀해서 반응이 좋습니다.",
            f"{search_name}, 메고 다니기 좋은 실루엣입니다.",
            price_line,
            "정장에도, 캐주얼에도 포인트가 과하지 않게 살아납니다.",
            "실재고 기준으로만 안내하니까, 허수 재고는 빼 두었습니다.",
            cta,
        ] if gender_key == "male" else [
            "보테가 베네타 백팩으로 가면 양손이 자유로워져요.",
            f"오늘은 {search_name}를 골랐어요.",
            price_line,
            "메고 있을 때 라인이 정리돼 보여서, 여행이랑 데일리 둘 다 쓰기 좋아요.",
            "배송·관세 포함 가격이라 결제 전에 헷갈릴 게 적어요.",
            cta,
        ]
    if code == "bv" and "Veneto" in search_name and "벨트" in search_name:
        lines = [
            "보테가 벨트백, 손 안 쓰고 싶을 때 제일 먼저 떠오르는 타입입니다.",
            f"{search_name}, 바디 라인이 깔끔한 실루엣입니다.",
            price_line,
            "정장에도 캐주얼에도 포인트가 과하지 않게 살아납니다.",
            "실재고 기준으로만 안내하니까, 허수 재고는 빼 두었습니다.",
            cta,
        ] if gender_key == "male" else [
            "보테가 베네타 벨트백으로 가면 코디가 한결 가벼워져요.",
            f"오늘은 {search_name}를 골랐습니다.",
            price_line,
            "허리에 찼을 때 라인이 예뻐서, 여행이랑 데일리 둘 다 쓰기 좋아요.",
            "배송·관세 포함 가격이라 결제 전에 헷갈릴 게 적어요.",
            cta,
        ]
    if code == "bv" and _is_bv_tote(sku_blob):
        lines = scripts["bv_tote"][gender_key]
    if code == "cw" and any(k in sku_blob.lower() for k in ("고무", "rubber", "러버")):
        lines = [
            "미드레인지 시계에서 영국 매뉴팩처 감성 찾는 분들, 많아졌습니다.",
            f"크리스토퍼 워드 {search_name}, 통합 러버 스트랩 구성입니다.",
            price_line,
            "러버 스트랩이라 땀·비에도 부담이 적고, 데일리로 차기 좋습니다.",
            "영국 공식가 대비 브릭 안내가를 같이 보시면 됩니다.",
            cta,
        ] if gender_key == "male" else [
            "러버 스트랩 워치 찾는다면, 크리스토퍼 워드 쪽이 잘 맞아요.",
            f"오늘은 {search_name}를 골랐어요.",
            price_line,
            "통합 러버라 착용감이 가볍고, 데일리로 차도 거슬림이 적어요.",
            "관세 포함으로 계산해 드리니 비교가 간단해요.",
            cta,
        ]

    hook_key = script_key if script_key in hooks else code
    base = hooks.get(hook_key, hooks.get(code, ("브릭에서 고른 한 점", f"{kind} · 실재고", "관부가세 포함 안내")))

    # Prefer real PDP detail facts for feature/lifestyle VO + on-screen cards.
    pdp_beats = build_pdp_beats(
        product,
        gender_key,
        brand_ko=brand_ko,
        search_name=search_name,
    )
    if pdp_beats and pdp_beats.get("feature"):
        feature_vo, feature_title, feature_sub = pdp_beats["feature"]
        if pdp_beats.get("intro") and len(lines) >= 2:
            lines = list(lines)
            lines[1] = pdp_beats["intro"]
        # Intro card subtitle: short PDP hook when description exists.
        desc0 = _clean_pdp_fact(str((product or {}).get("descriptionKo") or ""))
        if desc0:
            short_intro = _clean_pdp_fact(re.split(r"[.。]", desc0)[0])
            if 8 <= len(short_intro) <= 28:
                base = (short_intro, base[1], base[2])
        if pdp_beats.get("lifestyle"):
            life_vo, life_title, life_sub = pdp_beats["lifestyle"]
            intro_vo = lines[1] if len(lines) >= 2 else ""
            # Drop lifestyle PDP beat when it collides with intro/feature (same fact echo).
            if not (
                vo_near_dup(life_vo, intro_vo, ignore_phrases=[search_name, brand_ko])
                or vo_near_dup(life_vo, feature_vo, ignore_phrases=[search_name, brand_ko])
            ):
                # Keep brand lifestyle card copy if PDP subtitle is empty (feature-only on-screen).
                if life_title and life_sub:
                    base = (base[0], life_title, life_sub)
                elif life_title:
                    base = (base[0], life_title, base[2])
                if len(lines) >= 4:
                    lines = list(lines)
                    lines[3] = life_vo

    # If the script already used the feature line as lifestyle, swap it before insert
    # so FEATURE_BEAT does not play twice back-to-back.
    lifestyle_vo = (
        f"{base[1]}이라, {base[2]}."
        if base[1] and base[2]
        else f"{kind}로 실사용하기 좋은 밸런스입니다."
    )
    ignore_phrases = [search_name, brand_ko, brand_en]
    if len(lines) >= 4 and vo_near_dup(lines[3], feature_vo, ignore_phrases=ignore_phrases):
        lines = list(lines)
        lines[3] = lifestyle_vo

    # Always insert purchase-desire feature beat after the price line.
    if len(lines) == 6:
        lines = lines[:3] + [feature_vo] + lines[3:]
    elif len(lines) < 7:
        lines = lines[:3] + [feature_vo] + lines[3:]
        while len(lines) < 7:
            lines.append(cta)

    # Hard stop: feature (idx 3) and lifestyle (idx 4) must never be the same / near-same VO.
    if len(lines) >= 5 and vo_near_dup(lines[3], lines[4], ignore_phrases=ignore_phrases):
        lines = list(lines)
        lines[4] = lifestyle_vo
    if len(lines) >= 5 and vo_near_dup(lines[3], lines[4], ignore_phrases=ignore_phrases):
        raise RuntimeError(
            f"duplicate feature/lifestyle VO for {code}: {lines[3]!r} / {lines[4]!r}"
        )
    assert_no_near_dup_vo(lines, label=code, ignore_phrases=ignore_phrases)
    assert_vo_matches_kind(
        kind,
        lines,
        [feature_title, feature_sub, base[0], base[1], base[2]],
        label=f"{code}:{search_name}",
    )
    assert_vo_matches_sku(
        code=code,
        sku_blob=sku_blob,
        lines=lines,
        cards=[feature_title, feature_sub, base[0], base[1], base[2]],
        label=f"{code}:{search_name}",
    )
    # Subtype guards (same class of bug as shoe→outerwear).
    joined_copy = " ".join(
        [*(lines or []), feature_title or "", feature_sub or "", base[0] or "", base[1] or "", base[2] or ""]
    )
    if ("백팩" in search_name or "backpack" in search_name.lower()) and "클러치" in joined_copy:
        raise RuntimeError(
            f"backpack/VO mismatch for {code}:{search_name}: copy still says 클러치"
        )
    if code == "bv" and _is_bv_tote(sku_blob) and any(
        k in joined_copy for k in ("미니 클러치", "클러치 라인", "손안에 들어오는")
    ):
        raise RuntimeError(
            f"tote/VO mismatch for {code}:{search_name}: copy still says clutch"
        )
    if any(k in sku_blob.lower() for k in ("고무", "rubber", "러버")) and "브레이슬릿" in joined_copy:
        raise RuntimeError(
            f"rubber-strap/VO mismatch for {code}:{search_name}: copy still says 브레이슬릿"
        )
    if any(k in sku_blob for k in ("까레라", "Carrera", "carrera")) and "아쿠아레이서" in joined_copy:
        raise RuntimeError(
            f"Carrera/VO mismatch for {code}:{search_name}: copy still says 아쿠아레이서"
        )
    if any(k in sku_blob for k in ("모나코", "Monaco", "monaco")) and "아쿠아레이서" in joined_copy:
        raise RuntimeError(
            f"Monaco/VO mismatch for {code}:{search_name}: copy still says 아쿠아레이서"
        )
    if any(k in product_id.lower() for k in ("darryl", "daniel", "dean", "mid-layer", "midlayer")) and "베스트" in joined_copy:
        raise RuntimeError(
            f"mid-layer/VO mismatch for {code}:{search_name}: copy still says 베스트"
        )
    if any(k in sku_blob for k in ("인제니어", "Ingenieur", "ingenieur")) and "파일럿" in joined_copy and "인제니어" not in "".join(
        L for L in lines if "인제니어" in L or "파일럿" in L
    ):
        # Allow “파일럿과 결이 다른 인제니어…” contrast lines; ban pure pilot pitch.
        if all("인제니어" not in (L or "") for L in lines[:2]):
            raise RuntimeError(
                f"Ingenieur/VO mismatch for {code}:{search_name}: intro still pitches 파일럿 only"
            )
    if any(k in sku_blob for k in ("인제니어", "Ingenieur", "ingenieur")) and lines and "파일럿 쪽을 보세요" in (lines[0] or ""):
        raise RuntimeError(
            f"Ingenieur/VO mismatch for {code}:{search_name}: copy still says 파일럿 쪽을 보세요"
        )

    # TAG Heuer: never ship “도구처럼” tool-watch filler.
    if code == "th":
        banned = ("도구처럼", "도구 같이", "툴처럼")
        for i, line in enumerate(lines):
            if any(b in line for b in banned):
                raise RuntimeError(
                    f"TAG Heuer VO bans tool-watch filler ({banned}): [{i}] {line!r}"
                )
        for chunk in (feature_title, feature_sub, base[1], base[2]):
            if any(b in (chunk or "") for b in banned):
                raise RuntimeError(
                    f"TAG Heuer card bans tool-watch filler: {chunk!r}"
                )

    # Shorts + Instagram both close with Naver Pay, then platform CTA.
    if lines and lines[-1] == cta:
        body = [x for x in lines[:-1] if x != NAVER_PAY_VO]
        lines = body + [NAVER_PAY_VO, cta]
    elif NAVER_PAY_VO not in lines:
        lines = list(lines) + [NAVER_PAY_VO, cta]

    return lines, (base[0], base[1], base[2], feature_title, feature_sub)


def speak_won(n: int) -> str:
    # rough spoken Korean for TTS
    if n >= 100_000_000:
        return f"{n / 100_000_000:.1f}억 원".replace(".0", "")
    man = n // 10000
    if man >= 10000:
        return f"{man // 10000}억 {(man % 10000)}만 원".replace(" 0만", "")
    return f"{man}만 원"


def speak_gbp(gbp: float) -> str:
    v = int(round(gbp))
    if v >= 1000:
        return f"{v // 1000}천{(v % 1000) if v % 1000 else ''} 파운드".replace("천0", "천")
    return f"{v} 파운드"


def font(size: int, *, display: bool = False, bold: bool = False):
    path = DISPLAY if display and Path(DISPLAY).exists() else FONT
    index = 1 if bold and path == FONT else 0
    try:
        return ImageFont.truetype(path, size=size, index=index)
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


def shade(draw, box, top_a=0, bot_a=200):
    x0, y0, x1, y1 = box
    for i in range(y1 - y0):
        a = int(top_a + (bot_a - top_a) * (i / max(1, y1 - y0 - 1)))
        draw.line([(x0, y0 + i), (x1, y0 + i)], fill=(12, 10, 8, a))


def text_out(draw, xy, text, fnt, fill=WHITE, stroke=3, stroke_fill=(0, 0, 0)):
    x, y = xy
    text = sanitize_slide_text(text)
    if not text:
        return
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        (x - tw / 2, y - th / 2),
        text,
        font=fnt,
        fill=fill,
        stroke_width=stroke,
        stroke_fill=stroke_fill,
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
        raise RuntimeError(path)
    h, m_, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return h * 3600 + m_ * 60 + s


def render_frames(topic: dict, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    base_shots = folder_images(topic["pdp"], topic["folder"], filter_landscape=True)
    if not base_shots:
        raise RuntimeError(f"no product shots for {topic.get('id')}")
    W, H = 1080, 1920
    frames: list[Path] = []
    n_cards = len(topic["cards"])
    need_photos = max(1, n_cards - 1)
    shots = [base_shots[i % len(base_shots)] for i in range(need_photos)]
    for idx, card in enumerate(topic["cards"]):
        line1 = card[0] if len(card) > 0 else None
        line2 = card[1] if len(card) > 1 else None
        line3 = card[2] if len(card) > 2 else None
        is_endcard = idx == n_cards - 1
        if is_endcard:
            im = Image.new("RGB", (W, H), INK)
            d = ImageDraw.Draw(im)
            text_out(d, (W / 2, H * 0.40), line1, font(76, display=True), CREAM, 2)
            text_out(d, (W / 2, H * 0.52), line2, font(44, bold=True), CREAM, 3)
            text_out(d, (W / 2, H * 0.62), "영국 현지 명품 직송", font(32, bold=True), GOLD, 3)
        else:
            # Skip endcard index when mapping photos; feature scene gets a mid shot.
            photo = shots[min(idx, len(shots) - 1)]
            im = fit_cover(Image.open(photo), W, H).convert("RGBA")
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            # Strong lift above Shorts bottom UI (likes / title / home indicator).
            shade(d, (0, int(H * 0.32), W, H), 8, 250)
            if line2 == "PRICE":
                text_out(d, (W / 2, H * 0.48), won(topic["price"]), font(88, bold=True), WHITE, 5)
                if topic.get("gbp"):
                    text_out(
                        d,
                        (W / 2, H * 0.58),
                        f"£{int(topic['gbp']):,} · 영국 기준",
                        font(40, bold=True),
                        CREAM,
                        3,
                    )
                text_out(d, (W / 2, H * 0.67), topic["brandEn"], font(34, bold=True), GOLD, 3)
            elif line3:
                # Naver Pay — visual only (no VO). Line3 tucked under line2, slightly larger.
                text_out(d, (W / 2, H * 0.44), line1, font(54, bold=True), WHITE, 5)
                text_out(d, (W / 2, H * 0.535), line2, font(42, bold=True), CREAM, 4)
                text_out(d, (W / 2, H * 0.575), line3, font(42, bold=True), GOLD, 3)
            else:
                # Mid-frame stack: line1 big white, line2 smaller cream, wide gap.
                # Feature beat (idx 3) uses a slightly smaller second line for longer copy.
                # Skip empty / meta filler subtitles (“상세에서 고른 포인트”).
                filler_sub = {
                    "상세에서 고른 포인트",
                    "상세 포인트",
                    "상세에서 고른",
                }
                draw_sub = bool(line2) and str(line2).strip() not in filler_sub
                text_out(
                    d,
                    (W / 2, H * (0.52 if not draw_sub else 0.48)),
                    line1,
                    font(60, bold=True),
                    WHITE,
                    5,
                )
                if draw_sub:
                    text_out(
                        d,
                        (W / 2, H * 0.62),
                        line2,
                        font(40 if idx == 3 else 44, bold=True),
                        CREAM,
                        4,
                    )
            im = Image.alpha_composite(im, ov).convert("RGB")
        path = out_dir / f"{idx+1:02d}.jpg"
        im.save(path, quality=92)
        frames.append(path)
    return frames


async def synth(text: str, voice: str, rate: str, pitch: str, mp3: Path) -> None:
    last_err: Exception | None = None
    for attempt in range(1, 5):
        try:
            if mp3.exists():
                mp3.unlink()
            await asyncio.wait_for(
                edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(mp3)),
                timeout=45.0,
            )
            if mp3.exists() and mp3.stat().st_size > 500:
                return
            raise RuntimeError(f"empty tts output: {mp3}")
        except Exception as e:
            last_err = e
            await asyncio.sleep(1.2 * attempt)
    raise RuntimeError(f"TTS failed after retries: {last_err}")


async def build_one(topic: dict) -> Path:
    out = ROOT / topic["slug"]
    frames_dir = out / "frames"
    voice_dir = out / "voice"
    voice_dir.mkdir(parents=True, exist_ok=True)
    frames = render_frames(topic, frames_dir)

    # Instagram cover_url / feed thumb: clean product still only.
    # Never reuse frames/01.jpg (VO text + shade hide the SKU).
    base_shots = folder_images(topic["pdp"], topic["folder"], filter_landscape=True)
    if not base_shots:
        raise RuntimeError(f"no product shots for poster: {topic.get('id')}")
    cover_photo = pick_cover_photo(base_shots)
    poster_path = write_clean_poster(cover_photo, out / "poster.jpg")
    topic["poster"] = poster_path.name
    topic["posterSource"] = str(cover_photo)

    voice_name, rate, pitch = VOICES[topic["gender"]]
    search_raw = str(topic.get("search") or "")
    assert_no_near_dup_vo(
        list(topic.get("lines") or []),
        label=str(topic.get("id") or topic.get("slug") or ""),
        ignore_phrases=[
            search_raw,
            # VO may already be 빽-locked while search/on-screen still uses 백.
            tts_bag_pronunciation(search_raw),
            prepare_vo_line(search_raw) if search_raw else "",
            str(topic.get("brandKo") or ""),
            str(topic.get("brandEn") or ""),
            str(topic.get("nameKo") or ""),
        ],
    )
    wavs = []
    for i, text in enumerate(topic["lines"], 1):
        fast = voice_dir / f"seg_{i:02d}_fast.wav"
        # Hard guard: never synth a line that would say 원대/가격대/판매가/붙습니다.
        if re.search(r"원\s*대|가격\s*대", text or ""):
            raise RuntimeError(f"refusing TTS with 대 price-range: [{i}] {text!r}")
        if "원때" in (text or "") or "가격때" in (text or ""):
            raise RuntimeError(
                f"VO must use phonetic 원떼/가격떼 before TTS: [{i}] {text!r}"
            )
        if re.search(r"판매가|현지가", text or ""):
            raise RuntimeError(
                f"VO must use 판매까/현지까 before TTS: [{i}] {text!r}"
            )
        if re.search(r"붙는|붙음|붙습니다", text or ""):
            raise RuntimeError(f"VO bans 붙는/붙음 (use 어울립니다): [{i}] {text!r}")
        if re.search(
            r"손이\s*(자주|자꾸)\s*가|자꾸\s*손이\s*가|손이\s*가는|손이\s*닿는|손이\s*감(?!각)",
            text or "",
        ):
            raise RuntimeError(f"VO bans 손이 자주/가는 filler: [{i}] {text!r}")
        # Naver Pay VO is only the short safe-payment line (card still shows 적립 text).
        if text != NAVER_PAY_VO and "네이버포인트" in (text or ""):
            raise RuntimeError(f"Naver 적립 must not be spoken: [{i}] {text!r}")
        mp3 = voice_dir / f"seg_{i:02d}.mp3"
        wav = voice_dir / f"seg_{i:02d}.wav"
        await synth(text, voice_name, rate, pitch, mp3)
        run([str(FFMPEG), "-y", "-i", str(mp3), "-ac", "1", "-ar", "44100", str(wav)])
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
        # Slightly longer gaps so the feature beat + overall runtime breathe more.
        pad = 0.22 if i < len(topic["lines"]) else 0.10
        wavs.append((fast, d, pad))

    def _ffconcat_path(p: Path) -> str:
        # ffmpeg concat resolves relative paths against the list file dir
        return str(Path(p).resolve()).replace("'", r"'\''")

    alist = voice_dir / "concat.txt"
    lines = []
    for i, (wav, d, pad) in enumerate(wavs):
        lines.append(f"file '{_ffconcat_path(wav)}'")
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
        lines.append(f"file '{_ffconcat_path(sil)}'")
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

    # Rhythmic Mixkit bed under VO (rotate ~10 tracks per SKU). Keep drums/pulse —
    # no heavy lowpass that turns music into a featureless hum.
    narration_mix = narration_eq
    bgm_path = pick_bgm(str(topic.get("id") or topic.get("slug") or ""))
    if bgm_path and bgm_path.is_file():
        narration_mix = voice_dir / "narration_bgm.wav"
        topic["bgm"] = bgm_path.name
        vo_dur = max(0.1, dur(narration_eq))
        fade_out_st = max(0.0, vo_dur - BGM_FADE_OUT_SEC)
        run(
            [
                str(FFMPEG),
                "-y",
                "-i",
                str(narration_eq),
                "-stream_loop",
                "-1",
                "-i",
                str(bgm_path),
                "-filter_complex",
                (
                    "[0:a]loudnorm=I=-16:TP=-1.5:LRA=11,volume=0.95[vo];"
                    f"[1:a]volume={BGM_VOLUME},"
                    f"afade=t=in:st=0:d={BGM_FADE_IN_SEC},"
                    f"afade=t=out:st={fade_out_st:.3f}:d={BGM_FADE_OUT_SEC},"
                    "highpass=f=60,lowpass=f=14000[bg];"
                    "[vo][bg]amix=inputs=2:duration=first:dropout_transition=2:"
                    "weights=1 1[a]"
                ),
                "-map",
                "[a]",
                str(narration_mix),
            ]
        )

    vlist = voice_dir / "video_concat.txt"
    vlines = []
    for img, (wav, d, pad) in zip(frames, wavs):
        vlines.append(f"file '{_ffconcat_path(img)}'")
        vlines.append(f"duration {d+pad:.3f}")
    vlines.append(f"file '{_ffconcat_path(frames[-1])}'")
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
    final = out / f"{topic['slug']}.mp4"
    run(
        [
            str(FFMPEG),
            "-y",
            "-i",
            str(silent),
            "-i",
            str(narration_mix),
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

    meta = {
        "title": topic["title"],
        "gender": topic["gender"],
        "brand": topic["brandEn"],
        "brandKo": topic["brandKo"],
        "nameKo": topic["nameKo"],
        "price": topic["price"],
        "gbp": topic["gbp"],
        "productUrl": topic["productUrl"],
        "pinnedComment": topic["pinnedComment"],
        "file": final.name,
        "id": topic["id"],
        "poster": "poster.jpg",
        "posterSource": topic.get("posterSource"),
        "bgm": topic.get("bgm"),
    }
    meta["description"] = topic.get("description") or build_description({**topic, **meta})
    meta["pinnedComment"] = topic.get("pinnedComment") or build_pinned_comment({**topic, **meta})
    if not (out / "poster.jpg").is_file():
        raise RuntimeError(f"missing poster.jpg for {topic.get('id')}")
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    (out / "pinned-comment.txt").write_text(meta["pinnedComment"])
    (out / "description.txt").write_text(meta["description"])
    print("OK", topic["slug"], topic["gender"], final.name, round(dur(final), 1), "s")
    return final


async def main() -> None:
    global ROOT
    p = argparse.ArgumentParser()
    p.add_argument(
        "--out",
        default=str(ROOT),
        help="Output batch folder",
    )
    p.add_argument(
        "--batch2",
        action="store_true",
        help="Second multi-brand set (ms/pp/rx + alternate picks)",
    )
    p.add_argument(
        "--exclude-index",
        default="",
        help="Prior INDEX.json whose product ids to skip",
    )
    p.add_argument("--pick-shift", type=int, default=0)
    p.add_argument(
        "--force-ids-json",
        default="",
        help="JSON object {brandCode: productId} to force picks",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Build only the first N topics (for samples). 0 = all.",
    )
    p.add_argument(
        "--brands",
        default="",
        help="Comma brand codes to use as order, e.g. ms or ys,bv",
    )
    p.add_argument(
        "--platform",
        choices=("shorts", "instagram"),
        default="shorts",
        help="shorts|instagram — both use briq.kr search CTA (Shorts links are non-clickable)",
    )
    args = p.parse_args()

    ROOT = Path(args.out).expanduser().resolve()
    ROOT.mkdir(parents=True, exist_ok=True)

    exclude: set[str] = set()
    if args.exclude_index:
        ep = Path(args.exclude_index).expanduser()
        if not ep.is_absolute():
            ep = (Path(__file__).resolve().parent / ep).resolve()
        for t in json.loads(ep.read_text()):
            if t.get("id"):
                exclude.add(t["id"])

    force_ids: dict[str, str] = {}
    if args.force_ids_json:
        raw = json.loads(Path(args.force_ids_json).expanduser().read_text())
        # accept either {code: id} or {code: {id: ...}}
        for k, v in raw.items():
            force_ids[k] = v["id"] if isinstance(v, dict) else str(v)

    if args.brands.strip():
        order = [c.strip() for c in args.brands.split(",") if c.strip()]
    else:
        order = BATCH2_ORDER if args.batch2 else DEFAULT_ORDER
    pick_shift = args.pick_shift if args.pick_shift else (4 if args.batch2 else 0)
    topics = pick_topics(
        order=order,
        exclude_ids=exclude,
        pick_shift=pick_shift,
        force_ids=force_ids,
        platform=args.platform,
    )
    if args.limit and args.limit > 0:
        topics = topics[: args.limit]

    (ROOT / "INDEX.json").write_text(json.dumps(topics, ensure_ascii=False, indent=2))
    rows = [
        "| # | 성우 | 브랜드 | 상품 | 파일 |",
        "|---|------|--------|------|------|",
    ]
    for t in topics:
        rows.append(
            f"| {t['num']:02d} | {t['gender']} | {t['brandKo']} | {t['nameKo'][:28]} | `{t['slug']}.mp4` |"
        )
        # also drop description/pinned ready for upload
    platform_note = (
        "Instagram VO ends with briq.kr search CTA."
        if args.platform == "instagram"
        else "YouTube Shorts VO ends with pinned-comment CTA."
    )
    (ROOT / "README.md").write_text(
        f"# Briq multi-brand {args.platform} batch (preview)\n\n"
        f"{platform_note} 브랜드·카테고리 혼합, 남/여 성우 교차. "
        "설명·고정댓글은 각 폴더 `description.txt` / `pinned-comment.txt`.\n\n"
        + "\n".join(rows)
        + "\n"
    )
    for t in topics:
        print(
            f"{t['num']:02d} {t['gender'][0]} {t['brandKo']:12} {t['price']:>10,}  {t['nameKo'][:40]}"
        )
        print("   VO:", t["lines"][0])
        print("   CTA:", t["lines"][-1])
    # Always rebuild — caption/copy fixes must not be skipped.
    for t in topics:
        await build_one(t)
        out = ROOT / t["slug"]
        (out / "description.txt").write_text(t["description"])
        (out / "pinned-comment.txt").write_text(t["pinnedComment"])
    print("DONE", ROOT, "platform=", args.platform)


if __name__ == "__main__":
    asyncio.run(main())
