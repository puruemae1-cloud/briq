"""Prada RTW size extraction — official PDP picker is source of truth.

Algolia ``SizeGroupStore`` often lists letter conversion-chart labels (S/M/L)
alongside purchasable numeric IT or waist sizes. Those letters must not be
merged into variant lists when numeric store sizes exist.

Prevention:
- ``sizes_from_hit`` / ``rtw_sizes`` never emit mixed letter+numeric lists
- ``assert_no_mixed_rtw_sizes`` fails scrape refresh / catalog build if mixed
  sizes appear in raw or built products
"""
from __future__ import annotations

import re
from typing import Iterable

LETTER_SIZES = frozenset({"XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"})
LETTER_ORDER = {"XXS": 0, "XS": 1, "S": 2, "M": 3, "L": 4, "XL": 5, "XXL": 6, "XXXL": 7}
NUMERIC_SIZE_RE = re.compile(r"^(\d{2})(S)?$", re.I)
PDP_SIZE_RE = re.compile(
    r'<button[^>]*aria-label="Select size ([^"]+)"([^>]*)>',
    re.I,
)


class MixedRtwSizesError(ValueError):
    """Raised when letter (S/M/L) and numeric (48/48S) sizes are both present."""


def is_letter_size(label: str) -> bool:
    return label.strip().upper() in LETTER_SIZES


def is_numeric_size(label: str) -> bool:
    return bool(NUMERIC_SIZE_RE.match(label.strip()))


def size_labels(rows: Iterable[dict | str]) -> list[str]:
    out: list[str] = []
    for row in rows:
        if isinstance(row, str):
            label = row.strip()
        else:
            label = str(row.get("size") or row.get("label") or "").strip()
        if label:
            out.append(label)
    return out


def has_mixed_rtw_sizes(labels: Iterable[str]) -> bool:
    """True when conversion-chart letters and purchasable numerics are both present."""
    labs = [str(x).strip() for x in labels if str(x).strip()]
    has_letter = any(is_letter_size(x) for x in labs)
    has_numeric = any(is_numeric_size(x) for x in labs)
    return has_letter and has_numeric


def find_mixed_rtw_size_products(
    products: Iterable[dict],
    *,
    sizes_key: str = "sizes",
    variants_key: str = "variants",
    id_keys: tuple[str, ...] = ("id", "sku", "productCode"),
) -> list[tuple[str, list[str]]]:
    """Return (product_id, labels) for products with mixed letter+numeric sizes."""
    bad: list[tuple[str, list[str]]] = []
    for prod in products:
        labels = size_labels(prod.get(sizes_key) or [])
        if not labels:
            labels = size_labels(prod.get(variants_key) or [])
        if not has_mixed_rtw_sizes(labels):
            continue
        pid = ""
        for key in id_keys:
            val = prod.get(key)
            if val:
                pid = str(val)
                break
        bad.append((pid or "?", labels))
    return bad


def assert_no_mixed_rtw_sizes(
    products: Iterable[dict],
    *,
    context: str = "Prada RTW sizes",
    sizes_key: str = "sizes",
    variants_key: str = "variants",
) -> None:
    """Hard fail if any product mixes S/M/L with numeric IT/waist sizes."""
    bad = find_mixed_rtw_size_products(
        products, sizes_key=sizes_key, variants_key=variants_key
    )
    if not bad:
        return
    sample = "; ".join(f"{pid}={labs}" for pid, labs in bad[:5])
    raise MixedRtwSizesError(
        f"{context}: {len(bad)} product(s) mix letter (S/M/L) and numeric sizes. "
        f"Use PDP picker / availableSizesStore only — never merge SizeGroupStore "
        f"letters with numeric sizes. Sample: {sample}"
    )


def _code_map_from_hit(hit: dict) -> dict[str, str]:
    code_by_label: dict[str, str] = {}
    for src in (hit.get("availableSizesStore") or [], hit.get("availableSizes") or []):
        for sz in src:
            label = str(sz.get("label") or "").strip()
            if label:
                code_by_label.setdefault(label.upper(), str(sz.get("code") or ""))
    return code_by_label


def _in_stock_from_hit(hit: dict) -> set[str]:
    return {
        str(sz.get("label") or "").strip().upper()
        for sz in (hit.get("availableSizes") or [])
        if str(sz.get("label") or "").strip()
    }


def _guard_size_rows(rows: list[dict], *, context: str) -> list[dict]:
    labels = size_labels(rows)
    if has_mixed_rtw_sizes(labels):
        raise MixedRtwSizesError(
            f"{context}: mixed letter+numeric sizes {labels}. "
            "Never merge SizeGroupStore letters with numeric store sizes."
        )
    return rows


def sizes_from_pdp_html(html: str) -> list[dict]:
    """Parse official size picker buttons from PDP HTML."""
    out: list[dict] = []
    seen: set[str] = set()
    for match in PDP_SIZE_RE.finditer(html):
        label = match.group(1).strip()
        if not label:
            continue
        key = label.upper()
        if key in seen:
            continue
        seen.add(key)
        attrs = match.group(2) or ""
        out.append(
            {
                "size": label,
                "code": "",
                "inStock": "disabled" not in attrs.lower(),
            }
        )
    return _guard_size_rows(sort_rtw_sizes(out), context="PDP HTML sizes")


def sizes_from_hit(hit: dict) -> list[dict]:
    """Algolia-only fallback when PDP HTML is unavailable."""
    in_stock_labels = _in_stock_from_hit(hit)
    code_by_label = _code_map_from_hit(hit)

    store_labels: list[str] = []
    seen: set[str] = set()

    def add_label(raw: str) -> None:
        label = raw.strip()
        if not label:
            return
        key = label.upper()
        if key in seen:
            return
        seen.add(key)
        store_labels.append(label)

    for sz in hit.get("availableSizesStore") or []:
        add_label(str(sz.get("label") or ""))
    for sz in hit.get("availableSizes") or []:
        add_label(str(sz.get("label") or ""))

    if not store_labels:
        for label in (hit.get("SizeGroupStore") or {}).get("en_GB") or []:
            add_label(str(label))

    has_numeric_store = any(is_numeric_size(label) for label in store_labels)
    has_letter_store = any(is_letter_size(label) for label in store_labels)

    all_labels = list(store_labels)
    if has_numeric_store:
        # Drop conversion-chart letters; numeric picker is authoritative.
        all_labels = [label for label in store_labels if not is_letter_size(label)]
    elif has_letter_store:
        all_labels = [label for label in store_labels if is_letter_size(label)]

    out = [
        {
            "size": label,
            "code": code_by_label.get(label.upper(), ""),
            "inStock": label.upper() in in_stock_labels,
        }
        for label in all_labels
    ]
    return _guard_size_rows(sort_rtw_sizes(out), context="Algolia sizes_from_hit")


def rtw_sizes(hit: dict, pdp_html: str | None = None) -> list[dict]:
    """Best-effort RTW sizes: PDP picker first, Algolia fallback."""
    code_by_label = _code_map_from_hit(hit)
    in_stock_labels = _in_stock_from_hit(hit)

    pdp_sizes = sizes_from_pdp_html(pdp_html) if pdp_html else []
    if pdp_sizes:
        for row in pdp_sizes:
            key = row["size"].upper()
            if not row.get("code"):
                row["code"] = code_by_label.get(key, "")
            # Prefer Algolia online-stock flag when label matches exactly.
            if key in in_stock_labels:
                row["inStock"] = True
        return _guard_size_rows(pdp_sizes, context="rtw_sizes PDP")

    return sizes_from_hit(hit)


def sort_rtw_sizes(rows: list[dict]) -> list[dict]:
    def sort_key(row: dict) -> tuple:
        label = str(row.get("size") or "").strip()
        upper = label.upper()
        if is_letter_size(label):
            return (0, LETTER_ORDER.get(upper, 50), 0, label)
        match = NUMERIC_SIZE_RE.match(label)
        if match:
            base = int(match.group(1))
            variant = 0 if match.group(2) else 1
            return (1, base, variant, label)
        return (2, 50, 0, label)

    return sorted(rows, key=sort_key)
