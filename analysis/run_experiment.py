
import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
ITEMS_DIR = ROOT / "items"
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
FIG_DIR = ROOT / "figures"
ANALYSIS_DIR = ROOT / "analysis"
import os, json, csv, time, threading, random, urllib.request, urllib.error, datetime, sys

KEY = os.environ.get("NVIDIA_API_KEY", "").strip()
if not KEY:
    raise SystemExit(
        "NVIDIA_API_KEY is not set. Export it before running:\n"
        "    export NVIDIA_API_KEY=your-key-here\n"
        "The key is never written to disk, logged, or committed."
    )
URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODELS = ["google/gemma-4-31b-it", "meta/llama-3.3-70b-instruct", "z-ai/glm-5.2"]
TEMP = 0.7
MAX_TOKENS = 4096
REPS = 3
RPM = 40
MAX_ATTEMPTS = 5
CONC = 40
OUT = str(DATA_DIR / "raw_responses.jsonl")
EVT = str(DATA_DIR / "events.log")

lock = threading.Lock(); evtlock = threading.Lock()
bucket_lock = threading.Lock(); last_dispatch = [0.0]
sem = threading.Semaphore(CONC)
stats = {"done":0,"fail":0,"429":0,"5xx":0}
t0 = time.time()

def evt(msg):
    with evtlock:
        open(EVT,'a',buffering=1).write(f"{datetime.datetime.now(datetime.timezone.utc).isoformat()} {msg}\n")

def rate_gate():
    # global token gate: at most RPM dispatches per minute
    interval = 60.0/RPM
    with bucket_lock:
        now = time.time()
        wait = last_dispatch[0] + interval - now
        if wait > 0: time.sleep(wait)
        last_dispatch[0] = time.time() + random.uniform(0, 0.25)

done_keys = set()
if os.path.exists(OUT):
    for line in open(OUT, encoding='utf-8'):
        line=line.strip()
        if not line: continue
        try:
            r=json.loads(line)
            if not r.get("error"):
                done_keys.add((r["item_id"], r["arm"], r["model"], r["rep"]))
        except Exception: pass

items = list(csv.DictReader(open(ITEMS_DIR / "items.csv", encoding="utf-8")))
jobs = []
for row in items:                       # file order preserved
    for m in MODELS:
        for rep in range(1, REPS+1):
            k = (row['item_id'], row['arm'], m, rep)
            if k in done_keys: continue
            jobs.append((row, m, rep))

TOTAL = len(jobs)
evt(f"START jobs={TOTAL} already_done={len(done_keys)} models={MODELS} temp={TEMP} max_tokens={MAX_TOKENS} rpm={RPM} conc={CONC}")

def write(rec):
    with lock:
        open(OUT,'a',encoding='utf-8').write(json.dumps(rec, ensure_ascii=False)+"\n")
        stats["done"] += 1
        if rec.get("error"): stats["fail"] += 1
        n = stats["done"]
    if n % 25 == 0:
        el = time.time()-t0
        rate = n/el if el>0 else 0
        rem = (TOTAL-n)/rate if rate>0 else 0
        evt(f"PROGRESS {n}/{TOTAL} failed={stats['fail']} elapsed={el/60:.1f}min est_remaining={rem/60:.1f}min r429={stats['429']} r5xx={stats['5xx']}")

def run(row, model, rep):
    prompt = row['prompt']
    body = json.dumps({"model": model,
                       "messages": [{"role":"user","content":prompt}],
                       "temperature": TEMP, "max_tokens": MAX_TOKENS}).encode()
    attempt = 0; err = None; rec = None
    while attempt < MAX_ATTEMPTS:
        attempt += 1
        # The concurrency slot is held ONLY for the in-flight request. Backoff sleeps
        # happen outside it, so a sleeping retry never starves a ready call.
        sem.acquire()
        try:
            rate_gate()
            req = urllib.request.Request(URL, data=body,
                headers={"Authorization": f"Bearer {KEY}", "Content-Type":"application/json"})
            try:
                r = urllib.request.urlopen(req, timeout=600)
                d = json.load(r)
                ch = d["choices"][0]; msg = ch.get("message", {})
                rec = dict(item_id=row['item_id'], arm=row['arm'], model=model, rep=rep,
                           prompt_sent=prompt, response_text=msg.get("content"),
                           reasoning_content=msg.get("reasoning_content"),
                           temperature=TEMP, max_tokens=MAX_TOKENS,
                           timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                           finish_reason=ch.get("finish_reason"), usage=d.get("usage"),
                           model_returned=d.get("model"), attempt_count=attempt, error=None)
                break
            except urllib.error.HTTPError as e:
                code = e.code; err = f"HTTP {code}"
                if code == 429: stats["429"] += 1
                elif code >= 500: stats["5xx"] += 1
                elif code == 404: stats["404"] = stats.get("404", 0) + 1
                # 404 is retried: this endpoint returns it intermittently for models
                # that are demonstrably live, so it behaves as a transient fault here.
                retryable = (code == 429 or code >= 500 or code == 404)
            except Exception as e:
                err = f"{type(e).__name__}: {str(e)[:200]}"
                retryable = True
        finally:
            sem.release()
        if not retryable or attempt >= MAX_ATTEMPTS:
            break
        back = 30 * (2 ** (attempt - 1)) + random.uniform(0, 5)
        evt(f"BACKOFF {model} {row['item_id']}/{row['arm']}/r{rep} attempt={attempt} {err} sleep={back:.0f}s")
        time.sleep(back)
    if rec is None:
        rec = dict(item_id=row['item_id'], arm=row['arm'], model=model, rep=rep,
                   prompt_sent=prompt, response_text=None, reasoning_content=None,
                   temperature=TEMP, max_tokens=MAX_TOKENS,
                   timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   finish_reason=None, usage=None, model_returned=None,
                   attempt_count=attempt, error=err)
    write(rec)

threads = []
for (row, m, rep) in jobs:
    while threading.active_count() > 220: time.sleep(0.2)
    th = threading.Thread(target=run, args=(row, m, rep)); th.start(); threads.append(th)
for th in threads: th.join()
evt(f"FINISHED total={stats['done']} failed={stats['fail']} elapsed={(time.time()-t0)/60:.1f}min r429={stats['429']} r5xx={stats['5xx']}")
