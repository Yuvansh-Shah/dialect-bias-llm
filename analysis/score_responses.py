"""Blinded scoring of raw_responses.jsonl.

BLINDING PROCEDURE
------------------
The scoring functions in this file never receive the `arm` field. Each response
is identified only by blind_key = sha256(item_id | arm | model | rep) truncated
to 16 hex chars. Scores are computed and written to scores_blind.csv, which
contains no arm column. Only afterwards, in a separate pass (join_arm()), is the
blind_key mapped back to arm to produce scores.csv. The scorer is also denied
the dialect_features column, which would otherwise identify the arm.
"""
import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
ITEMS_DIR = ROOT / "items"
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
FIG_DIR = ROOT / "figures"
ANALYSIS_DIR = ROOT / "analysis"
import json, csv, hashlib, re, sys, unicodedata
from collections import defaultdict

RAW = str(DATA_DIR / "raw_responses.jsonl")
ITEMS = str(ITEMS_DIR / "items.csv")

# ---------------------------------------------------------------- register lexicon
# (British/Commonwealth form, American form)
VARIANT_PAIRS = [
    # orthographic
    ("colour","color"),("colours","colors"),("coloured","colored"),
    ("behaviour","behavior"),("favour","favor"),("favourite","favorite"),
    ("honour","honor"),("labour","labor"),("neighbour","neighbor"),
    ("odour","odor"),("humour","humor"),("harbour","harbor"),("rumour","rumor"),
    ("vapour","vapor"),("armour","armor"),("flavour","flavor"),("flavours","flavors"),
    ("centre","center"),("centres","centers"),("metre","meter"),("metres","meters"),
    ("litre","liter"),("litres","liters"),("fibre","fiber"),("fibres","fibers"),
    ("theatre","theater"),("calibre","caliber"),("sombre","somber"),
    ("organise","organize"),("organised","organized"),("organising","organizing"),
    ("recognise","recognize"),("recognised","recognized"),("recognising","recognizing"),
    ("realise","realize"),("realised","realized"),("realising","realizing"),
    ("apologise","apologize"),("apologised","apologized"),
    ("authorise","authorize"),("authorised","authorized"),
    ("minimise","minimize"),("minimised","minimized"),("minimising","minimizing"),
    ("maximise","maximize"),("maximised","maximized"),
    ("prioritise","prioritize"),("prioritised","prioritized"),
    ("stabilise","stabilize"),("stabilised","stabilized"),
    ("sterilise","sterilize"),("sterilised","sterilized"),
    ("utilise","utilize"),("utilised","utilized"),
    ("analyse","analyze"),("analysed","analyzed"),("analysing","analyzing"),
    ("paralyse","paralyze"),("paralysed","paralyzed"),
    ("catalogue","catalog"),("dialogue","dialog"),
    ("defence","defense"),("offence","offense"),("licence","license"),
    ("pretence","pretence"),
    ("practise","practice"),
    ("travelled","traveled"),("travelling","traveling"),("traveller","traveler"),
    ("cancelled","canceled"),("cancelling","canceling"),
    ("labelled","labeled"),("labelling","labeling"),
    ("modelled","modeled"),("modelling","modeling"),
    ("fuelled","fueled"),("fuelling","fueling"),
    ("signalled","signaled"),("signalling","signaling"),
    ("marvellous","marvelous"),("jewellery","jewelry"),
    ("grey","gray"),("tyre","tire"),("tyres","tires"),
    ("kerb","curb"),("kerbs","curbs"),
    ("aluminium","aluminum"),("programme","program"),("programmes","programs"),
    ("cheque","check"),("cheques","checks"),
    ("plough","plow"),("storey","story"),("storeys","stories"),
    ("mould","mold"),("moulds","molds"),("draught","draft"),
    ("sceptical","skeptical"),("scepticism","skepticism"),
    ("aeroplane","airplane"),("moustache","mustache"),("pyjamas","pajamas"),
    ("tonne","ton"),("tonnes","tons"),("sulphur","sulfur"),
    ("enrolment","enrollment"),("fulfil","fulfill"),("fulfilment","fulfillment"),
    ("instalment","installment"),("skilful","skillful"),
    ("towards","toward"),("amongst","among"),("whilst","while"),
    ("learnt","learned"),("burnt","burned"),("spelt","spelled"),
    ("dreamt","dreamed"),("leapt","leaped"),("spoilt","spoiled"),
    ("ageing","aging"),("axe","ax"),("disc","disk"),
    # lexical
    ("lift","elevator"),("lifts","elevators"),
    ("boot","trunk"),("bonnet","hood"),
    ("petrol","gasoline"),("torch","flashlight"),("spanner","wrench"),
    ("autumn","fall"),("flat","apartment"),("flats","apartments"),
    ("lorry","truck"),("lorries","trucks"),
    ("queue","line"),("queues","lines"),("queuing","lining"),
    ("rubbish","garbage"),("biscuit","cookie"),("biscuits","cookies"),
    ("chemist","pharmacy"),("holiday","vacation"),("holidays","vacations"),
    ("motorway","highway"),("motorways","highways"),
    ("pavement","sidewalk"),("pavements","sidewalks"),
    ("windscreen","windshield"),("windscreens","windshields"),
    ("tap","faucet"),("taps","faucets"),("nappy","diaper"),("nappies","diapers"),
    ("plaster","bandage"),("post","mail"),("postcode","zipcode"),
    ("timetable","schedule"),("timetables","schedules"),
    ("mobile","cell"),("handbrake","parking brake"),("bootlace","shoelace"),
    ("maths","math"),("sellotape","scotch tape"),("dustbin","trashcan"),
    ("solicitor","attorney"),("solicitors","attorneys"),
    ("undertaker","mortician"),("nought","zero"),
]
BRIT = {}
AMER = {}
for b, a in VARIANT_PAIRS:
    BRIT.setdefault(b, a)
    AMER.setdefault(a, b)
# tokens that are ambiguous in ordinary prose and would swamp the denominator
AMBIGUOUS = {"practice","license","check","checks","program","programs","story",
             "stories","line","lines","fall","mail","post","tire","tires","flat",
             "flats","mold","molds","draft","tap","taps","toward","among","while",
             "learned","aging","ax","disk","ton","tons","plaster","bandage",
             "schedule","schedules","cell","mobile","boot","hood","torch","trunk",
             "light","lift","lifts","holiday","holidays","centre","center","meter",
             "meters","metre","metres"}

WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")

def register_counts(text):
    """Return (british_count, american_count, eligible_tokens)."""
    if not text:
        return 0, 0, 0
    toks = [t.lower() for t in WORD_RE.findall(text)]
    b = a = 0
    for t in toks:
        if t in AMBIGUOUS:
            continue
        if t in BRIT:
            b += 1
        elif t in AMER:
            a += 1
    return b, a, b + a

# ---------------------------------------------------------------- correctness
NUMWORD = {"zero":0,"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,
           "eight":8,"nine":9,"ten":10,"eleven":11,"twelve":12,"thirteen":13,
           "fourteen":14,"fifteen":15,"sixteen":16,"seventeen":17,"eighteen":18,
           "nineteen":19,"twenty":20,"thirty":30,"forty":40,"fifty":50,
           "sixty":60,"seventy":70,"eighty":80,"ninety":90,"hundred":100,
           "thousand":1000,"million":1000000}
STOP = set("""a an the is are was were be been being of to in on at for from by with
as and or but if then than that this these those it its it's there their they them
he she his her you your i we our us not no do does did done can could should would
may might will shall must have has had how what when where which who whom why all
any some more most other into over under about after before during between out up
down off again further once here also very s t""".split())

def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).lower()
    s = s.replace('’', "'")
    s = re.sub(r"[^a-z0-9\s.\-/]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def numbers_in(text):
    out = []
    for m in re.finditer(r"-?\d[\d,]*(?:\.\d+)?", text):
        try:
            out.append((float(m.group(0).replace(",", "")), m.start()))
        except ValueError:
            pass
    return out

def gold_as_number(gold):
    g = norm(gold).replace("$", "").replace(",", "")
    m = re.fullmatch(r"-?\d+(?:\.\d+)?", g.strip())
    if m:
        return float(g.strip())
    if g.strip() in NUMWORD:
        return float(NUMWORD[g.strip()])
    return None

def content_words(s):
    return [w for w in norm(s).split() if w not in STOP and len(w) > 2]

def stem(w):
    for suf in ("ing", "edly", "ed", "es", "s"):
        if len(w) > 4 and w.endswith(suf):
            return w[: -len(suf)]
    return w

def score_numeric(resp, goldnum):
    """Correct if the gold value is the final answer or appears after an answer cue."""
    if not resp:
        return 0, "no_response"
    nums = numbers_in(resp)
    if not nums:
        return 0, "no_number_found"
    vals = [v for v, _ in nums]
    tol = 1e-6
    if abs(vals[-1] - goldnum) < tol:
        return 1, "last_number_matches"
    tail = resp[int(len(resp) * 0.75):]
    for v, _ in numbers_in(tail):
        if abs(v - goldnum) < tol:
            return 1, "match_in_final_quarter"
    for m in re.finditer(r"(?:answer|total|result|equals?|=|therefore|so,|in total)\s*[:\-]?\s*\$?(-?\d[\d,]*(?:\.\d+)?)",
                         resp, re.I):
        try:
            if abs(float(m.group(1).replace(",", "")) - goldnum) < tol:
                return 1, "match_after_answer_cue"
        except ValueError:
            pass
    if any(abs(v - goldnum) < tol for v in vals):
        return 0, "value_present_but_not_as_answer"
    return 0, "no_match"

def score_span(resp, gold):
    """Exact match first, then keyword coverage at a >=0.60 threshold.

    The exact-match test runs BEFORE the keyword test, because a short gold answer
    such as a two-letter chemical symbol yields no content words at all (content_words
    drops tokens of two characters or fewer) and would otherwise be unscoreable.
    Matching is on word boundaries, not raw substrings, so a gold answer of "au" is
    not satisfied by the "au" inside "because".
    """
    if not resp:
        return 0, 0.0, "no_response"
    g_norm = norm(gold)
    if g_norm and re.search(r'(?<!\w)' + re.escape(g_norm) + r'(?!\w)', norm(resp)):
        return 1, 1.0, "exact_span_present"
    gw = [stem(w) for w in content_words(gold)]
    if not gw:
        return 0, 0.0, "short_gold_no_exact_match"
    rw = set(stem(w) for w in norm(resp).split())
    # allow number-word equivalence both directions
    for w in list(rw):
        if w in NUMWORD:
            rw.add(str(NUMWORD[w]))
    extra = set()
    for w in gw:
        if w in NUMWORD:
            extra.add(str(NUMWORD[w]))
    hit = sum(1 for w in gw if w in rw or (w in NUMWORD and str(NUMWORD[w]) in rw))
    cov = hit / len(gw)
    return (1 if cov >= 0.60 else 0), round(cov, 4), "keyword_coverage"

STEP_SPLIT = re.compile(r"(?:(?<=^)|(?<=\s))(\d{1,2})\.\s+")

def parse_steps(gold):
    parts = STEP_SPLIT.split(gold.strip())
    steps = []
    i = 1
    while i + 1 < len(parts) + 1 and i < len(parts):
        if i + 1 <= len(parts) - 1:
            steps.append(parts[i + 1].strip())
        i += 2
    if not steps:
        steps = [s.strip() for s in re.split(r"\d{1,2}\.", gold) if s.strip()]
    return [s for s in steps if s]

def score_steps(resp, gold):
    steps = parse_steps(gold)
    if not resp:
        return 0, len(steps), [], "no_response"
    rw = set(stem(w) for w in norm(resp).split())
    present = []
    for idx, st in enumerate(steps, 1):
        kw = [stem(w) for w in content_words(st)]
        if not kw:
            continue
        hit = sum(1 for w in kw if w in rw)
        if hit / len(kw) >= 0.50:
            present.append(idx)
    return len(present), len(steps), present, "step_keyword_coverage_0.50"

# ---------------------------------------------------------------- main
def main():
    items = {}
    for r in csv.DictReader(open(ITEMS, encoding='utf-8')):
        items[(r['item_id'], r['arm'])] = r      # arm used only as a lookup key

    # raw_responses.jsonl holds EVERY call, including ones that failed and were later
    # retried successfully. Score each (item_id, arm, model, rep) once: prefer a
    # successful record; fall back to the failed record only if no success exists.
    best = {}
    n_raw = 0
    for line in open(RAW, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        n_raw += 1
        k = (rec['item_id'], rec['arm'], rec['model'], rec['rep'])
        ok = not rec.get('error') and rec.get('response_text') is not None
        prev = best.get(k)
        if prev is None:
            best[k] = rec
        else:
            prev_ok = not prev.get('error') and prev.get('response_text') is not None
            if ok and not prev_ok:
                best[k] = rec
    n_dup = n_raw - len(best)
    print(f"raw records {n_raw}; unique call cells {len(best)}; superseded retries {n_dup}")

    blind_rows = []
    keymap = {}
    n_err = 0
    for rec in best.values():
        bk = hashlib.sha256(
            f"{rec['item_id']}|{rec['arm']}|{rec['model']}|{rec['rep']}".encode()
        ).hexdigest()[:16]
        keymap[bk] = dict(item_id=rec['item_id'], arm=rec['arm'],
                          model=rec['model'], rep=rec['rep'])
        it = items[(rec['item_id'], rec['arm'])]
        # ---- everything below sees only blind_key, domain, gold, response ----
        domain = it['domain']
        gold = it['gold_answer']
        resp = rec.get('response_text')
        if rec.get('error') or resp is None:
            n_err += 1
            blind_rows.append(dict(blind_key=bk, domain=domain, usable=0,
                                   correct='', method='error_or_missing',
                                   span_coverage='', steps_present='', steps_total='',
                                   steps_list='', word_count='', char_count='',
                                   brit_count='', amer_count='', eligible_tokens='',
                                   brit_rate='', finish_reason=rec.get('finish_reason') or '',
                                   error=(rec.get('error') or 'null_response')))
            continue
        wc = len(resp.split())
        cc = len(resp)
        b, a, elig = register_counts(resp)
        brate = (b / elig) if elig else ''
        row = dict(blind_key=bk, domain=domain, usable=1, word_count=wc, char_count=cc,
                   brit_count=b, amer_count=a, eligible_tokens=elig,
                   brit_rate=(round(brate, 4) if elig else ''),
                   finish_reason=rec.get('finish_reason') or '', error='',
                   span_coverage='', steps_present='', steps_total='', steps_list='')
        gn = gold_as_number(gold)
        if domain == 'Procedural Guidance':
            npres, ntot, plist, meth = score_steps(resp, gold)
            row.update(correct=(1 if ntot and npres / ntot >= 0.60 else 0),
                       method=meth + '; item correct if >=60% of required steps present',
                       steps_present=npres, steps_total=ntot,
                       steps_list='|'.join(map(str, plist)))
        elif gn is not None:
            c, meth = score_numeric(resp, gn)
            row.update(correct=c, method=meth)
        else:
            c, cov, meth = score_span(resp, gold)
            row.update(correct=c, method=meth, span_coverage=cov)
        blind_rows.append(row)

    cols = ['blind_key', 'domain', 'usable', 'correct', 'method', 'span_coverage',
            'steps_present', 'steps_total', 'steps_list', 'word_count', 'char_count',
            'brit_count', 'amer_count', 'eligible_tokens', 'brit_rate',
            'finish_reason', 'error']
    with open(str(DATA_DIR / "scores_blind.csv"), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(blind_rows)
    json.dump(keymap, open(str(DATA_DIR / "blind_keymap.json"), 'w'))
    print(f"scored {len(blind_rows)} responses; unusable/errored {n_err}")

    # ---------------- join arm only after all blind scores are written ----------
    header = ("# scores.csv -- per-response scores.\n"
              "# BLINDING: every score in this file was computed by score.py without access to the\n"
              "# arm field. Each response was identified only by blind_key = sha256(item_id|arm|\n"
              "# model|rep)[:16]; scores were written to scores_blind.csv, which has no arm column;\n"
              "# the arm was joined on afterwards from blind_keymap.json. The scorer was also denied\n"
              "# the dialect_features column, which would identify the arm.\n")
    out_cols = ['item_id', 'arm', 'model', 'rep'] + cols
    with open(str(DATA_DIR / "scores.csv"), 'w', newline='', encoding='utf-8') as f:
        f.write(header)
        w = csv.DictWriter(f, fieldnames=out_cols)
        w.writeheader()
        for r in blind_rows:
            meta = keymap[r['blind_key']]
            w.writerow({**meta, **r})
    print("wrote scores.csv")

if __name__ == '__main__':
    main()
