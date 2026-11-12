#!/usr/bin/env python3
"""Guard: PDP option clicks must honour ?color= / ?size= over path props.

CW parent product ids are `cw-{primaryVariantId}`. If SSR path props always
force that primary strap, every swatch click that only updates the query
string looks broken (selection + price stuck).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DETAIL = (ROOT / "src/components/ProductDetail.tsx").read_text()
PAGE = (ROOT / "src/app/product/[id]/page.tsx").read_text()

errors: list[str] = []

# --- ProductDetail: ?color= before colorIdProp ---
m = re.search(
    r"useSearchParams\(\);\s*"
    r"const colorId\s*=\s*([^;]+);",
    DETAIL,
    re.S,
)
if not m:
    errors.append("ProductDetail: could not find colorId resolution after useSearchParams")
else:
    expr = re.sub(r"\s+", " ", m.group(1)).strip()
    if "searchParams.get(\"color\")" not in expr:
        errors.append("ProductDetail colorId must read searchParams.get(\"color\")")
    elif "colorIdProp" in expr:
        # Query must appear before the prop fallback.
        if expr.find("searchParams.get(\"color\")") > expr.find("colorIdProp"):
            errors.append(
                "ProductDetail still prefers colorIdProp over ?color= "
                "(CW strap swatches will appear stuck)"
            )

# --- page.tsx: pathVariant only for variant deep-links ---
if "id !== product.id" not in PAGE:
    errors.append(
        "product/[id]/page.tsx must only apply pathVariant when "
        "id !== product.id (parent CW ids match the primary strap)"
    )

if errors:
    print("PDP option-selection guard FAILED:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)

print("PDP option-selection guard OK")
