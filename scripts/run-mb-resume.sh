#!/usr/bin/env bash
# Resume Mulberry catalogue ingestion after crashes / disconnects.
# Safe to re-run: skips existing PDP URLs, micro-batches leaves, rebuilds catalog.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STATE="$ROOT/tmp/mb-resume-state.json"
LOG="$ROOT/tmp/mb-resume.log"
LIMIT="${MB_LEAF_LIMIT:-8}"
mkdir -p "$ROOT/tmp"

# Ordered small→large leaves (what's-new last for weekly priority elsewhere)
LEAVES=(
  mb-women-clutches
  mb-women-mini
  mb-women-bucket
  mb-women-backpacks
  mb-women-crossbody
  mb-women-top-handle
  mb-women-totes
  mb-women-shoulder
  mb-women-bags-all
  mb-women-icons
  mb-women-travel-accessories
  mb-women-travel-holdalls
  mb-women-travel-luggage
  mb-women-travel-all
  mb-men-messenger
  mb-men-briefcases
  mb-men-backpacks
  mb-men-holdalls
  mb-men-bags-all
  mb-men-travel
  mb-men-wallets
  mb-men-keyrings
  mb-men-organisers
  mb-men-sunglasses
  mb-men-care
  mb-men-accessories-all
  mb-men-lifestyle
  mb-gifts-him
  mb-women-purses
  mb-women-lifestyle
  mb-gifts-her
  mb-gifts
  mb-men-whats-new
  mb-women-whats-new
)

leaf_done() {
  local leaf="$1"
  local raw="$ROOT/src/data/mb/${leaf}-catalog-raw.json"
  [[ -f "$raw" ]] || return 1
  python3 - "$raw" <<'PY'
import json,sys
p=sys.argv[1]
d=json.load(open(p))
n=len(d.get("products") or [])
# treat as done for this resume pass once we have any products
# (full coverage grows via --skip-existing re-runs / weekly sync)
raise SystemExit(0 if n>0 else 1)
PY
}

write_state() {
  local leaf="$1" status="$2"
  python3 - "$STATE" "$leaf" "$status" <<'PY'
import json,sys,datetime
path,leaf,status=sys.argv[1],sys.argv[2],sys.argv[3]
try: st=json.load(open(path))
except Exception: st={}
st["updatedAt"]=datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z"
st["lastLeaf"]=leaf
st["lastStatus"]=status
st.setdefault("completed",[])
if status=="ok" and leaf not in st["completed"]:
  st["completed"].append(leaf)
json.dump(st, open(path,"w"), indent=2)
print(path)
PY
}

echo "== MB resume $(date -Iseconds) limit=$LIMIT ==" | tee -a "$LOG"

NEXT=""
for leaf in "${LEAVES[@]}"; do
  if leaf_done "$leaf"; then
    echo "skip done $leaf" | tee -a "$LOG"
    write_state "$leaf" "ok" >/dev/null
    continue
  fi
  NEXT="$leaf"
  break
done

if [[ -z "$NEXT" ]]; then
  echo "ALL_LEAVES_HAVE_RAW" | tee -a "$LOG"
  write_state "none" "complete" >/dev/null
  BRIQ_FAST_BUILD=1 python3 scripts/build-mb-catalog.py | tee -a "$LOG"
  echo "RESUME_IDLE" | tee -a "$LOG"
  exit 0
fi

echo "NEXT $NEXT" | tee -a "$LOG"
write_state "$NEXT" "running" >/dev/null

set +e
PYTHONUNBUFFERED=1 python3 scripts/scrape-mulberry-leaf.py \
  --leaf "$NEXT" --limit "$LIMIT" --skip-existing 2>&1 | tee -a "$LOG"
rc=${PIPESTATUS[0]}
set -e

if [[ "$rc" -ne 0 ]]; then
  write_state "$NEXT" "failed" >/dev/null
  echo "RESUME_FAIL leaf=$NEXT rc=$rc" | tee -a "$LOG"
  exit "$rc"
fi

write_state "$NEXT" "ok" >/dev/null
BRIQ_FAST_BUILD=1 PYTHONUNBUFFERED=1 python3 scripts/build-mb-catalog.py | tee -a "$LOG"

# CDN: only missing folders referenced by this leaf raw
python3 - "$NEXT" <<'PY' | tee -a "$LOG"
import json, subprocess, urllib.request, urllib.error, base64, time, datetime, sys
from pathlib import Path
leaf=sys.argv[1]
ROOT=Path('.')
raw_path=ROOT / f'src/data/mb/{leaf}-catalog-raw.json'
if not raw_path.is_file():
  print('no raw'); raise SystemExit(0)
raw=json.loads(raw_path.read_text())
skus=[]
for row in raw.get('products') or []:
  for im in row.get('localImages') or []:
    parts=im.strip('/').split('/')
    if len(parts)>=3 and parts[1]=='mb-pdp':
      skus.append(parts[2])
skus=sorted(set(skus))
missing=[]
for sku in skus:
  url=f'https://raw.githubusercontent.com/puruemae1-cloud/briq/product-images/public/products/mb-pdp/{sku}/1.jpg'
  try:
    req=urllib.request.Request(url, method='HEAD', headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=12) as r:
      pass
  except Exception:
    missing.append(sku)
print('cdn missing', len(missing), missing[:12])
if not missing:
  print('CDN_OK'); raise SystemExit(0)

p=subprocess.run(['git','credential','fill'], input='protocol=https\nhost=github.com\n\n', capture_output=True, text=True, timeout=8)
token=[line.split('=',1)[1] for line in p.stdout.splitlines() if line.startswith('password=')][0]
API='https://api.github.com/repos/puruemae1-cloud/briq'
TAG='product-images'

def gh(method, path, data=None, retries=5):
  body=None if data is None else json.dumps(data).encode()
  for attempt in range(retries):
    req=urllib.request.Request(API+path, data=body, method=method, headers={
      'Authorization':f'Bearer {token}','Accept':'application/vnd.github+json',
      'X-GitHub-Api-Version':'2022-11-28','User-Agent':'briq','Content-Type':'application/json'})
    try:
      with urllib.request.urlopen(req, timeout=180) as r:
        raw=r.read(); return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
      if e.code in (403,409,422,500,502,503) and attempt<retries-1:
        time.sleep(3*(attempt+1)); continue
      raise

BATCH=3
tip=None
for i in range(0,len(missing),BATCH):
  batch=missing[i:i+BATCH]
  print('cdn batch', batch, flush=True)
  ref=gh('GET', f'/git/ref/tags/{TAG}'); parent=ref['object']['sha']
  commit=gh('GET', f'/git/commits/{parent}'); base_tree=commit['tree']['sha']
  tree=[]
  for sku in batch:
    d=ROOT/'public/products/mb-pdp'/sku
    if not d.is_dir():
      continue
    for f in sorted(d.glob('*.jpg'))[:8]:
      b64=base64.b64encode(f.read_bytes()).decode('ascii')
      blob=gh('POST','/git/blobs',{'content':b64,'encoding':'base64'})
      tree.append({'path':f'public/products/mb-pdp/{sku}/{f.name}','mode':'100644','type':'blob','sha':blob['sha']})
      time.sleep(0.08)
  if not tree:
    continue
  new_tree=gh('POST','/git/trees',{'base_tree':base_tree,'tree':tree})
  new_commit=gh('POST','/git/commits',{'message':f'chore: sync PDP images (mb-pdp {leaf} +{len(batch)})\n','tree':new_tree['sha'],'parents':[parent]})
  gh('PATCH', f'/git/refs/tags/{TAG}', {'sha':new_commit['sha'],'force':True})
  tip=new_commit['sha']
  print('OK', tip[:12], flush=True)
if tip:
  man={'publishedAt':datetime.datetime.utcnow().replace(microsecond=0).isoformat()+'Z','tagRev':tip[:12]}
  (ROOT/'src/data/product-images-manifest.json').write_text(json.dumps(man, indent=2)+'\n')
  print('manifest', man)
print('CDN_DONE')
PY

echo "RESUME_OK leaf=$NEXT" | tee -a "$LOG"
echo "NEXT_ACTION: commit mb files for $NEXT then continue"
