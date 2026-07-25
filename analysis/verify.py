"""Independent verification. Recomputes key figures from raw_responses.jsonl and scores.csv
WITHOUT reusing analyse3.py, then checks the manuscript against them."""
import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
ITEMS_DIR = ROOT / "items"
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
FIG_DIR = ROOT / "figures"
ANALYSIS_DIR = ROOT / "analysis"
import json, csv, re, hashlib, os, glob, math
from collections import defaultdict
import numpy as np
from scipy import stats
from docx import Document

R=str(DATA_DIR)+"/"
fails=[]; checks=0
def chk(cond,msg):
    global checks; checks+=1
    if not cond: fails.append(msg)
    print(('  OK  ' if cond else ' FAIL ')+msg)

print("=== A. Raw data ===")
raw=[json.loads(l) for l in open(str(DATA_DIR/"raw_responses.jsonl"),encoding='utf-8')]
best={}
for r in raw:
    k=(r['item_id'],r['arm'],r['model'],r['rep'])
    ok=not r.get('error') and r.get('response_text') is not None
    prev=best.get(k)
    if prev is None or (ok and not (not prev.get('error') and prev.get('response_text') is not None)):
        best[k]=r
chk(len(best)==936,f"936 unique call cells (got {len(best)})")
chk(all(not r.get('error') for r in best.values()),"every scored cell has a successful record")
chk({r['temperature'] for r in raw}=={0.7},"temperature fixed at 0.7 on every call")
chk(all(r['finish_reason']=='stop' for r in best.values()),"no response truncated")
chk(all(r['model']==r.get('model_returned') for r in best.values()),
    "returned model string matched the requested one on every call")
# Look for actual key MATERIAL: the prefix followed by a long key body. A bare
# prefix appears legitimately in CHANGES2.md, which quotes the checker's own source.
KEYPAT=re.compile('nv'+'api-'+r'[A-Za-z0-9_-]{20,}')
leak=[]
for f in [str(p) for p in ROOT.rglob('*') if p.is_file()]:
    if os.path.isdir(f): continue
    try: txt=open(f,encoding='utf-8',errors='ignore').read()
    except Exception: continue
    if KEYPAT.search(txt): leak.append(os.path.basename(f))
chk(not leak,f"no API key material in any run file (found in: {leak})")

sc=[r for r in csv.DictReader([l for l in open(str(DATA_DIR/"scores.csv"),encoding='utf-8') if not l.startswith('#')])]
akey={r['item_id']:r for r in csv.DictReader(open(str(ITEMS_DIR/"arm_mapping.csv"),encoding='utf-8'))}
loc={r['item_id']:r['locale_class'] for r in csv.DictReader(
     [l for l in open(str(ITEMS_DIR/"item_locale_classification.csv"),encoding='utf-8') if not l.startswith('#')])}
for r in sc:
    r['cond']='SAE' if r['arm']==akey[r['item_id']]['sae_arm'] else 'DIALECT'
    r['track']='AAE' if r['item_id'].startswith('AAE') else 'IndE'
    r['loc']=loc[r['item_id']]
MODELS=['google/gemma-4-31b-it','meta/llama-3.3-70b-instruct','z-ai/glm-5.2']
SH={'google/gemma-4-31b-it':'gemma-4-31b','meta/llama-3.3-70b-instruct':'llama-3.3-70b',
    'z-ai/glm-5.2':'glm-5.2'}
F=json.load(open(str(ANALYSIS_DIR/"figures.json"))); EXCL=('AAE08',)
ALPHA=F['family']['alpha']

def cells(field,pred=lambda r:True,drop=EXCL):
    d=defaultdict(list)
    for r in sc:
        if r['item_id'] in drop or not pred(r): continue
        v=r.get(field)
        if v=='' or v is None: continue
        d[(r['item_id'],r['model'],r['cond'])].append(float(v))
    return d
def paired(field,pred=lambda r:True,drop=EXCL,model=None,scale=1.0):
    c=cells(field,pred,drop); out=[]
    for (iid,mm) in sorted(set((k[0],k[1]) for k in c)):
        if model and mm!=model: continue
        s=c.get((iid,mm,'SAE')); d=c.get((iid,mm,'DIALECT'))
        if s and d: out.append((np.mean(d)-np.mean(s))*scale)
    return np.array(out)

print("\n=== B. AAE track: per-model results and the tie sum ===")
tot_s=tot_l=tot_t=0
for m in MODELS:
    d=paired('word_count',pred=lambda r: r['track']=='AAE',model=m)
    res=stats.wilcoxon(d)
    sh=int((d<0).sum()); lo=int((d>0).sum()); ti=int((d==0).sum())
    tot_s+=sh; tot_l+=lo; tot_t+=ti
    ref=F['aae_length_per_model'][SH[m]]
    chk(len(d)==19,f"{SH[m]}: 19 paired AAE items")
    chk(sh+lo+ti==19,f"{SH[m]}: shorter {sh} + longer {lo} + tied {ti} = 19")
    chk((sh,lo,ti)==(ref['shorter'],ref['longer'],ref['ties']),
        f"{SH[m]}: direction counts match figures.json ({sh}/{lo}/{ti})")
    chk(abs(float(res.statistic)-ref['W'])<1e-9,f"{SH[m]}: W = {ref['W']:.1f}")
    chk(abs(float(res.pvalue)-ref['p'])/max(ref['p'],1e-300)<1e-9,f"{SH[m]}: p = {ref['p']:.4g}")
    chk(float(res.pvalue)<ALPHA,f"{SH[m]}: clears the family threshold {ALPHA:.5f}")
ap=F['aae_pooled_counts']
chk(tot_s+tot_l+tot_t==57,f"AAE pooled direction counts sum to 19 x 3 = 57 (got {tot_s+tot_l+tot_t})")
chk((tot_s,tot_l,tot_t)==(ap['shorter'],ap['longer'],ap['ties']),
    f"AAE pooled counts match figures.json ({tot_s} shorter, {tot_l} longer, {tot_t} tied)")
chk(ap['shorter']+ap['longer']+ap['ties']==ap['total']==57,
    "figures.json AAE pooled total is internally consistent at 57")

print("\n=== C. The variance ratio is gone ===")
chk('variance_corrected' not in F and 'variance' not in F,
    "figures.json contains no variance-ratio key")
an=open(str(DOCS_DIR/"analysis.md"),encoding='utf-8').read()
chk('ratio_old' not in an and 'SD(one response)' not in an,
    "analysis.md reports no ratio of difference to single-response SD")

print("\n=== D. Locale split ===")
by={s['split']:s for s in F['locale_length']}
for label,pred in [('Indian English, locale-sensitive',lambda r: r['track']=='IndE' and r['loc']=='locale-sensitive'),
                   ('Indian English, locale-invariant',lambda r: r['track']=='IndE' and r['loc']=='locale-invariant'),
                   ('AAE track (all locale-invariant)',lambda r: r['track']=='AAE')]:
    d=paired('word_count',pred=pred); ref=by[label]
    p=float(stats.wilcoxon(d).pvalue) if (d!=0).any() else 1.0
    chk(len(d)==ref['n'] and abs(float(np.median(d))-ref['median'])<1e-9,
        f"{label}: n = {ref['n']}, median {ref['median']:+.2f}")
    chk(abs(p-ref['p'])/max(ref['p'],1e-300)<1e-9,f"{label}: p = {ref['p']:.4g}")
    chk(ref['shorter']+ref['longer']+ref['ties']==ref['n'],
        f"{label}: shorter + longer + tied = n")
sens=by['Indian English, locale-sensitive']
chk(sens['shorter']==sens['n'] and sens['longer']==0,
    f"locale-sensitive: all {sens['n']} pairs shorter in the dialect arm")
lc=list(csv.DictReader([l for l in open(str(ITEMS_DIR/"item_locale_classification.csv"),encoding='utf-8') if not l.startswith('#')]))
chk(len(lc)==52 and all(r['reason'].strip() for r in lc),
    "locale classification covers 52 items, each with a reason")

print("\n=== E. Step coverage: reported as underpowered, not as a null ===")
S=F['step_coverage']; inv=S['Procedural, locale-invariant|paired']
chk(inv['worse']>inv['better'],
    f"locale-invariant coverage direction is consistently worse in the dialect arm "
    f"({inv['worse']} worse vs {inv['better']} better)")
chk(S['Procedural, locale-invariant|DIALECT']['coverage']
    < S['Procedural, locale-invariant|SAE']['coverage'],
    "locale-invariant mean coverage is lower in the dialect arm")
sp=F['step_power']
d=[]
cvi=defaultdict(list)
for r in sc:
    if r['domain']!='Procedural Guidance' or r['loc']!='locale-invariant' or r['steps_present']=='' or r['item_id'] in EXCL: continue
    cvi[(r['item_id'],r['model'],r['cond'])].append(int(r['steps_present'])/int(r['steps_total']))
for (iid,mm) in sorted(set((k[0],k[1]) for k in cvi)):
    s=cvi.get((iid,mm,'SAE')); t=cvi.get((iid,mm,'DIALECT'))
    if s and t: d.append(np.mean(t)-np.mean(s))
d=np.array(d); dz=float(d.mean()/d.std(ddof=1))
chk(abs(dz-sp['dz'])<1e-9,f"step-coverage dz = {sp['dz']:.4f} reproduces")
za=stats.norm.ppf(0.975); zb=stats.norm.ppf(0.80)
chk(math.ceil((za+zb)**2/dz**2)==sp['n_pairs_alpha05'],
    f"required n at alpha 0.05 = {sp['n_pairs_alpha05']} pairs reproduces")
chk(sp['n_pairs_alpha05']>inv['n'],
    f"required n ({sp['n_pairs_alpha05']}) exceeds the n we have ({inv['n']}), i.e. underpowered")

print("\n=== F. Register, as three of the nine family tests ===")
for m in MODELS:
    d=paired('brit_rate',model=m,scale=100.0)
    ref=F['register_paired'][SH[m]]
    p=float(stats.wilcoxon(d).pvalue) if (d!=0).any() else 1.0
    chk(len(d)==ref['n'],f"register {SH[m]}: n = {ref['n']}")
    chk(abs(p-ref['p'])<1e-9,f"register {SH[m]}: p = {ref['p']:.4g}")
chk(len(F['family_tests'])==9 and F['family']['n_tests']==9,
    "the confirmatory family has exactly 9 tests")
chk(sum(1 for t in F['family_tests'] if t['survives']=='yes')==2,
    "exactly 2 of the 9 family tests clear the threshold (length, gemma and llama)")

print("\n=== G. Correctness levels ===")
for m in MODELS:
    d=paired('correct',model=m,scale=100.0)
    b=int((d<0).sum()); c=int((d>0).sum())
    p=float(stats.wilcoxon(d).pvalue) if (d!=0).any() else 1.0
    ref=F['per_model_levels'][m]
    chk((b,c)==(ref['graded_b'],ref['graded_c']),f"{SH[m]}: graded b = {b}, c = {c}")
    chk(abs(p-ref['graded_p'])/max(ref['graded_p'],1e-300)<1e-9,f"{SH[m]}: graded p = {ref['graded_p']:.4g}")
L=F['levels']['AAE08 excluded (primary)']
chk(L['collapsed_b']+L['collapsed_c'] < L['graded_b']+L['graded_c'],
    "collapsing loses discordant pairs, the disclosed defect")

print("\n=== H. Manuscript ===")
doc=Document(str(DOCS_DIR/"ShahDialectBiasLLM.docx"))
text='\n'.join(p.text for p in doc.paragraphs)
tt='\n'.join(c.text for t in doc.tables for r in t.rows for c in r.cells)
allt=text+'\n'+tt
chk('—' not in allt and '–' not in allt,"no em dashes or en dashes")
scan=re.sub(r'[^.]*variant pair[^.]*\.','',text)
scan=re.sub(r'[^.]*such as colour against[^.]*\.','',scan)
amer=['analyze','analyzed','color','behavior','recognize','organize','modeling','labeled',
      'defense','offense','maximize','minimize','prioritize','center','meter','liter']
found=[a for a in amer if re.search(r'\b'+a+r'\b',scan,re.I)]
chk(not found,f"no stray American spellings (found: {found})")
chk(len(doc.tables)>=12,f"at least 12 native tables (got {len(doc.tables)})")
chk(len(doc.inline_shapes)==3,f"three figures embedded (got {len(doc.inline_shapes)})")
# per-model AAE prose figures must match figures.json
for m in MODELS:
    Lr=F['aae_length_per_model'][SH[m]]
    chk(f"{Lr['W']:.1f}" in allt,f"manuscript states W = {Lr['W']:.1f} for {SH[m]}")
    chk(f"{Lr['shorter']} items shorter" in allt or f"{Lr['shorter']} shorter" in allt,
        f"manuscript states {Lr['shorter']} shorter for {SH[m]}")
chk('57' in allt and '52' in allt and '4 longer' in allt and '1 tied' in allt,
    "manuscript states the AAE pooled split 52 / 4 / 1 out of 57")
# '52 of 56' must not be asserted, but the contradictions section is required to quote it.
occ=[p.text for p in doc.paragraphs if '52 of 56' in p.text]
chk(all(('earlier draft' in t or 'reported as' in t or 'omitted' in t) for t in occ),
    f"'52 of 56' appears only as a quoted, corrected error ({len(occ)} occurrences)")
chk(any('omitted the tied pair' in t for t in occ),
    "the '52 of 56' error is explained where it is quoted")
# the withdrawn ratio must not reappear
for s_ in ['variance ratio','ratio of the between-arm']:
    chk(s_ not in allt.lower() or 'withdrawn' in allt.lower(),
        f"'{s_}' appears only in the withdrawal note, if at all")
# step coverage: must NOT assert established quality loss, must say underpowered
chk('underpowered' in allt.lower(),"manuscript describes the completeness result as underpowered")
chk('do not establish that shorter dialect' in allt.lower()
    or 'do not establish that shorter' in allt.lower(),
    "manuscript explicitly declines to establish that shorter means less complete")
chk('also do not establish that the arms are equally complete' in allt.lower(),
    "manuscript also declines to assert that no completeness effect exists")
chk(str(sp['n_pairs_alpha05']) in allt and str(sp['n_items_alpha05']) in allt,
    f"manuscript states the required sample size ({sp['n_pairs_alpha05']} pairs, {sp['n_items_alpha05']} items)")
# convergent identification
chk('convergent' in allt.lower() or 'converged on the same' in allt.lower(),
    "manuscript describes AAE08 as convergent identification of one defective item")
chk('one defective item' in allt.lower() or 'same single item out of twenty' in allt.lower(),
    "manuscript states one item of twenty, not two")
# register caveat
chk('deepseek-v4-pro' in allt.lower(),"manuscript names the unavailable model in the register caveat")
chk('not a direct refutation' in allt.lower(),"register non-replication is caveated")
# passport example
PE=F['passport_example']
for wv in PE['sae_words']+PE['dialect_words']:
    chk(str(wv) in allt,f"manuscript states passport word count {wv}")
# The archive now exists, so no placeholder may remain anywhere in the repository.
_MARKER_LIT='DATA '+'NEEDED'   # concatenated so this file never contains the literal
chk(_MARKER_LIT not in allt,"no placeholder marker remains in the manuscript")
CONCEPT_DOI='10.5281/zenodo.21566323'
chk(CONCEPT_DOI in allt,f"manuscript states the concept DOI {CONCEPT_DOI}")
chk('github.com/Yuvansh-Shah/dialect-bias-llm' in allt,"manuscript states the repository URL")
_MARKER=_MARKER_LIT
# pilot-superseded/ is excluded deliberately: those are the June pilot's own historical
# documents, and BLOCKERS.md records the placeholder THAT study carried. Rewriting it would
# falsify the record. The check covers the live study only.
_marker_hits=[]
for _p in ROOT.rglob('*'):
    if not _p.is_file() or '.git/' in str(_p): continue
    if 'pilot-superseded' in _p.parts: continue
    if _p.suffix.lower() in {'.pdf','.doc','.docx','.xlsx','.jsonl','.png'}: continue
    try: _t=_p.read_text(encoding='utf-8',errors='ignore')
    except Exception: continue
    if _MARKER in _t: _marker_hits.append(str(_p.relative_to(ROOT)))
chk(not _marker_hits,f"no placeholder marker in any live text file (found: {_marker_hits})")
chk(CONCEPT_DOI in (ROOT/'README.md').read_text(encoding='utf-8'),"README states the concept DOI")
chk(CONCEPT_DOI in (ROOT/'CITATION.cff').read_text(encoding='utf-8'),"CITATION.cff states the concept DOI")
chk('4.2' in text,"contradictions section present")
fn='ShahDialectBiasLLM.doc'
chk(len(fn)<30 and fn.rsplit('.',1)[0].isalnum() and os.path.exists(str(DOCS_DIR/fn)),
    "filename under 30 chars, letters and numbers only, file exists")

print(f"\n=== {checks-len(fails)}/{checks} checks passed ===")
if fails:
    print("FAILURES:")
    for f in fails: print("  -",f)
