#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/scripts:${PYTHONPATH:-}"

# Smallest families first (bags → shoes → accessories → RTW).
FAMILIES=(
  ys-men-bags
  ys-men-shoes
  ys-men-accessories
  ys-men-slg
  ys-women-jewelry
  ys-women-accessories
  ys-women-slg
  ys-women-shoes
  ys-women-rtw
  ys-men-rtw
  ys-women-bags
)

for fam in "${FAMILIES[@]}"; do
  echo "== $fam =="
  python3 scripts/scrape-ys-family.py --family "$fam" || echo "WARN $fam scrape failed"
done

# PLP-only retag so sub-leaves (leather/coats/…) keep membership after View All skip_ids,
# and every gender SKU carries *-rtw-all so Briq '전체' matches 남성용/여성용 counts.
python3 scripts/retag-ys-men-rtw-leaves.py || echo "WARN men RTW retag failed"
python3 scripts/retag-ys-women-rtw-leaves.py || echo "WARN women RTW retag failed"

python3 scripts/build-ys-catalog.py

# Size charts must match PDP option chips (denim waist / F34 / shoes); refresh KO copy.
python3 scripts/patch-ys-size-charts-and-copy.py
python3 scripts/check-catalog-korean.py --brand ys --fail || echo "WARN ys korean check"

# Guard: men leather / coats must not collapse to View-All-only leftovers.
python3 - <<'PY' || exit 1
import json, sys
from pathlib import Path
cat = json.loads(Path("src/data/ys/ys-catalog.json").read_text())
prods = cat if isinstance(cat, list) else cat.get("products") or []

def n(leaf: str) -> int:
    return sum(1 for p in prods if leaf in (p.get("ysCollections") or p.get("collections") or []))

leather, coats = n("ys-men-leather"), n("ys-men-coats-trench")
men_all, women_all = n("ys-men-rtw-all"), n("ys-women-rtw-all")
men_hub = sum(1 for p in prods if "ys-men" in (p.get("ysCollections") or p.get("collections") or []))
women_hub = sum(1 for p in prods if "ys-women" in (p.get("ysCollections") or p.get("collections") or []))
print(f"guard leather={leather} coats={coats} men_all={men_all} men_hub={men_hub} women_all={women_all} women_hub={women_hub}")
ok = leather >= 10 and coats >= 10 and men_all >= men_hub - 2 and women_all >= women_hub - 2
if not ok:
    print("ERROR YS RTW leaf/전체 coverage guard failed", file=sys.stderr)
    sys.exit(1)
PY

# Re-download any catalog photos missing from disk/CDN, then publish.
python3 scripts/repair-ys-missing-images.py || true
chmod +x scripts/ci-publish-pdp-cdn.sh
scripts/ci-publish-pdp-cdn.sh ys-pdp --brand ys --chunk 4 --max-waves 200

python3 scripts/refresh-homepage-rail-picks.py --fail || true
echo "OK YS weekly sync"
