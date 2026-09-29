#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/scripts:${PYTHONPATH:-}"

python3 - <<'PY'
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path("scripts").resolve()))
from al_config import AL_FAMILY_ORDER

for fam in AL_FAMILY_ORDER:
    print(f"== {fam} ==", flush=True)
    r = subprocess.run(
        [sys.executable, "scripts/scrape-al-family.py", "--family", fam],
        cwd=str(Path.cwd()),
    )
    if r.returncode != 0:
        print(f"WARN {fam} failed rc={r.returncode}", flush=True)
    r = subprocess.run(
        [sys.executable, "scripts/retag-al-leaves.py", "--family", fam],
        cwd=str(Path.cwd()),
    )
    if r.returncode != 0:
        print(f"WARN {fam} retag failed rc={r.returncode}", flush=True)

r = subprocess.run([sys.executable, "scripts/build-al-catalog.py"])
if r.returncode != 0:
    raise SystemExit(r.returncode)

# Official size guide tabs on every sized clothing PDP (fails if one is left without).
r = subprocess.run([sys.executable, "scripts/patch-al-size-charts.py", "--refresh", "--check"])
if r.returncode != 0:
    raise SystemExit(r.returncode)

# Korean QA — fail weekly sync if EN leftovers remain.
last_rc = 1
for attempt in range(1, 6):
    print(f"== AL KO retranslate attempt {attempt}/5 ==", flush=True)
    r = subprocess.run(
        [sys.executable, "scripts/retranslate-al-ko.py", "--category", "all"],
        cwd=str(Path.cwd()),
    )
    last_rc = r.returncode
    qa = subprocess.run(
        [sys.executable, "scripts/check-al-korean.py", "--fail", "--max-bad", "0"],
        cwd=str(Path.cwd()),
    )
    if qa.returncode == 0:
        break
    print(f"WARN attempt {attempt}: retranslate_rc={last_rc} qa_rc={qa.returncode}", flush=True)
else:
    # Ship stock/size/price on the committed Korean copy rather than dropping
    # the whole sync; untranslated new styles wait for the next run.
    print("WARN AL KO still English after 5 attempts — stock-only fallback", flush=True)
    import importlib.util

    sys.path.insert(0, str(Path.cwd() / "scripts"))
    from stock_only_fallback import apply_fallback

    spec = importlib.util.spec_from_file_location("check_al_korean", "scripts/check-al-korean.py")
    check_al = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check_al)
    apply_fallback(Path("src/data/al/al-catalog.json"), check_al.product_copy_ok)
    qa = subprocess.run(
        [sys.executable, "scripts/check-al-korean.py", "--fail", "--baseline-ref", "HEAD"],
        cwd=str(Path.cwd()),
    )
    if qa.returncode != 0:
        print("ERROR AL KO regressed past the committed catalogue", flush=True)
        raise SystemExit(qa.returncode)

# Bags / shoes PLPs read slices, not the full catalogue.
for script in ("extract-bags-catalogs.py", "extract-shoes-catalogs.py"):
    r = subprocess.run([sys.executable, f"scripts/{script}", "al"], cwd=str(Path.cwd()))
    if r.returncode != 0:
        raise SystemExit(r.returncode)

# Local image guard — never leave catalogue pointing at missing PDP files.
img = subprocess.run(
    [sys.executable, "scripts/verify-product-images.py", "--brand", "al", "--all-images"],
    cwd=str(Path.cwd()),
)
if img.returncode != 0:
    print("ERROR AL local product images missing after build", flush=True)
    raise SystemExit(img.returncode)

# Record CDN gaps for CI (selective push). Local weekly does not force-push the
# product-images tag — that step is owned by .github/workflows/weekly-al-sync.yml
# so we never hang local sync on a large tag upload.
missing = Path("tmp/al-cdn-missing.txt")
missing.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(
    [
        sys.executable,
        "scripts/list-missing-pdp-on-cdn.py",
        "--dirs",
        "al-pdp",
        "--write",
        str(missing),
    ],
    cwd=str(Path.cwd()),
)
n_miss = sum(1 for line in missing.read_text(encoding="utf-8").splitlines() if line.strip()) if missing.exists() else 0
print(f"AL CDN gap report: {n_miss} SKUs missing (CI will push selectively)", flush=True)

print("OK AL weekly sync (local images verified; CDN push/verify is CI)", flush=True)
PY
echo "OK AL weekly sync"
