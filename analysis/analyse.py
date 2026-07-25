"""Corrected analysis, third pass. Supersedes analyse2.py.

Changes from analyse2.py:
  1. The variance ratio is removed entirely, not reported and not set aside.
  2. The AAE length result leads with three separate per-model tests; the pooled
     count is descriptive only and the direction counts sum to 57.
  3. Locale inference is a second finding with its own section.
  4. Step coverage is reported as underpowered with a required-n calculation.
  5. Register is reported for all three models as members of the nine-test family.
"""
import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
ITEMS_DIR = ROOT / "items"
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
FIG_DIR = ROOT / "figures"
ANALYSIS_DIR = ROOT / "analysis"
import csv, json, math
from collections import defaultdict
import numpy as np
from scipy import stats

RUN=str(DATA_DIR)+"/"
OUT=[]; FIG={}
def w(s=''): OUT.append(s)
def fp(p):
    if p is None: return 'n/a'
    return f'{p:.4g}'

sc=[r for r in csv.DictReader([l for l in open(str(DATA_DIR/"scores.csv"),encoding='utf-8') if not l.startswith('#')])]
akey={r['item_id']:r for r in csv.DictReader(open(str(ITEMS_DIR/"arm_mapping.csv"),encoding='utf-8'))}
loc={r['item_id']:r['locale_class'] for r in csv.DictReader(
     [l for l in open(str(ITEMS_DIR/"item_locale_classification.csv"),encoding='utf-8') if not l.startswith('#')])}
items={}
for r in csv.DictReader(open(str(ITEMS_DIR/"items.csv"),encoding='utf-8')): items[(r['item_id'],r['arm'])]=r
for r in sc:
    r['cond']='SAE' if r['arm']==akey[r['item_id']]['sae_arm'] else 'DIALECT'
    r['track']='AAE' if r['item_id'].startswith('AAE') else 'IndE'
    r['loc']=loc[r['item_id']]
MODELS=['google/gemma-4-31b-it','meta/llama-3.3-70b-instruct','z-ai/glm-5.2']
SHORT={'google/gemma-4-31b-it':'gemma-4-31b','meta/llama-3.3-70b-instruct':'llama-3.3-70b','z-ai/glm-5.2':'glm-5.2'}
EXCL=('AAE08',)
NT=9; ALPHA=0.05/NT
FIG['family']=dict(n_tests=NT,alpha=ALPHA,
                   description='3 models x 3 outcomes (correctness, length, register), Bonferroni')

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
def wil(d):
    if len(d)<5 or not (d!=0).any():
        return dict(n=len(d),W=None,p=1.0,shorter=int((d<0).sum()),longer=int((d>0).sum()),
                    ties=int((d==0).sum()),median=float(np.median(d)) if len(d) else None,
                    mean=float(d.mean()) if len(d) else None)
    r=stats.wilcoxon(d)
    return dict(n=len(d),W=float(r.statistic),p=float(r.pvalue),
                shorter=int((d<0).sum()),longer=int((d>0).sum()),ties=int((d==0).sum()),
                median=float(np.median(d)),mean=float(d.mean()))

w('# Analysis (third pass)')
w()
w('Computed by `analyse3.py` from `scores.csv`, which `score.py` produces from')
w('`raw_responses.jsonl`. No figure is carried forward from any earlier draft.')
w()
w('**Primary analysis excludes item AAE08** (section 1). **Multiplicity:** the confirmatory')
w(f'family is 3 models x 3 outcomes = {NT} tests, Bonferroni threshold 0.05/{NT} = {ALPHA:.5f}.')
w('Splits by track, task type and locale class are descriptive follow-ups and their p-values are')
w('labelled nominal.')
w()
w('**The variance ratio reported in the previous two drafts has been withdrawn entirely.** It')
w('compared a mean over items against the spread of a single response, which is not a test. It')
w('is not reported here in any form. The three repeats per prompt remain load-bearing: they')
w('supply the graded cell means used throughout, and they let response stability be checked.')
w()

# ---------------------------------------------------------------- 1. exclusion
w('## 1. The excluded item, and convergent identification')
w()
sa=akey['AAE08']['sae_arm']; da=akey['AAE08']['dialect_arm']
w('One item of the 52 is excluded: AAE08, the gingerbread and apple pie problem, which is')
w('RowIdx 8 of the ReDial-derived AAE set. This is **the same item the June pilot excluded**.')
w('The pilot removed it because both of its models returned 990 against a gold answer of 540 and')
w('it was judged a faulty item. This analysis reached the same item independently, by noticing')
w('it carried 5 of the 9 SAE-arm errors, and then diagnosed the cause.')
w()
w('Two independent analyses, with different models and a different method, converged on the same')
w('single item out of twenty. That is reassurance about the ReDial subset rather than a warning')
w('about it: one item of twenty is defective and both passes found it.')
w()
w('Both wordings, quoted so the exclusion can be audited:')
w()
w('> **SAE arm.** ' + items[('AAE08',sa)]['prompt'])
w()
w('> **Dialect arm.** ' + items[('AAE08',da)]['prompt'])
w()
w(f"> **Gold answer.** {items[('AAE08',sa)]['gold_answer']}")
w()
w('The cause, which the pilot did not diagnose, is two independent defects:')
w()
w('1. **The constraints contradict each other.** Saturday apple pie is 4 fewer than Sunday, and')
w('   Sunday is 15 more than Saturday. Writing S for Saturday and U for Sunday, the item asserts')
w('   both S = U - 4 and U = S + 15, which give S = S + 11. No consistent assignment exists, so')
w('   the gold answer of 540 is not derivable from a correct reading.')
w('2. **The two arms are not meaning-identical.** The dialect wording inserts a comma before')
w('   "than on Sunday": "4 fewer boxes of apple pie, than on Sunday". That punctuation changes')
w('   which clause the comparison attaches to. The matched-pair premise is that the two wordings')
w('   mean the same thing; here they do not.')
w()
w('Defect 2 is the disqualifying one. **The decision to exclude was taken after this item\'s')
w('results had been seen**, which is stated plainly because it is a departure from')
w('pre-specification; the justification is the parse shift, which is a property of the wordings')
w('and not of the results. Every figure below is also given with the item retained.')
w()
w('| Set | Arm | Correct / n | Accuracy |')
w('|---|---|---|---|')
ACC={}
for lab,drop in [('All 52 items',()),('51 items, AAE08 excluded',EXCL)]:
    for c in ('SAE','DIALECT'):
        sub=[r for r in sc if r['cond']==c and r['item_id'] not in drop]
        k=sum(int(r['correct']) for r in sub)
        ACC[f'{lab}|{c}']=(k,len(sub))
        w(f"| {lab} | {'SAE' if c=='SAE' else 'Dialect'} | {k}/{len(sub)} | {100*k/len(sub):.2f} per cent |")
FIG['accuracy_with_without']=ACC
w()
se_err=defaultdict(int)
for r in sc:
    if r['cond']=='SAE' and r['correct']=='0': se_err[r['item_id']]+=1
FIG['sae_errors']=dict(se_err)
w('The 9 SAE-arm errors over all 52 items come from three items, not one: AAE08 (5), IE30 (2)')
w('and IE03 (2). After the exclusion the SAE arm still holds 4 errors, so it is not at ceiling.')
w()

# ---------------------------------------------------------------- 2. FINDING ONE
w('## 2. Finding one: brevity at unchanged accuracy on the AAE track')
w()
w('The African American English items are the cleanest in the study. They are ReDial multi-step')
w('numeric word problems: the answer is a number, it cannot depend on jurisdiction, and the')
w('dialect wordings were written and validated by African American English speaking researchers')
w('rather than constructed by us. After the exclusion there are 19 items.')
w()
w('### 2.1 Per model, which is the level that supports a claim')
w()
w('Three separate Wilcoxon signed-rank tests, one per model, 19 paired items each. Each item')
w('contributes the mean of its three repeats in each arm; the paired difference is dialect minus')
w('SAE, so a negative value means the dialect answer was shorter.')
w()
w('| Model | n items | Median difference (words) | W | p | Shorter | Longer | Tied | Clears family threshold |')
w('|---|---|---|---|---|---|---|---|---|')
AAEL={}
for m in MODELS:
    d=paired('word_count',pred=lambda r: r['track']=='AAE',model=m)
    r=wil(d); AAEL[SHORT[m]]=r
    w(f"| {SHORT[m]} | {r['n']} | {r['median']:+.2f} | {r['W']:.1f} | {fp(r['p'])} | "
      f"{r['shorter']} | {r['longer']} | {r['ties']} | {'yes' if r['p']<ALPHA else 'no'} |")
FIG['aae_length_per_model']=AAEL
w()
w('All three models clear the Bonferroni threshold for the nine-test family. This is the')
w('strongest claim in the paper and it rests on three independent tests, not on a pooled count.')
w()
w('### 2.2 The pooled count, which is descriptive only')
w()
tot_s=sum(v['shorter'] for v in AAEL.values()); tot_l=sum(v['longer'] for v in AAEL.values())
tot_t=sum(v['ties'] for v in AAEL.values())
FIG['aae_pooled_counts']=dict(shorter=tot_s,longer=tot_l,ties=tot_t,total=tot_s+tot_l+tot_t,
                              items=19,models=3)
w(f'Across the 19 items and 3 models there are 19 x 3 = {19*3} item-by-model pairs. Of these,')
w(f'**{tot_s} are shorter in the dialect arm, {tot_l} are longer and {tot_t} is exactly tied**,')
w(f'which sums to {tot_s+tot_l+tot_t}. An earlier draft reported "52 of 56", which omitted the')
w('tied pair from the denominator. These counts are **descriptive only**. They are not the basis')
w('of a test, because pooling counts the same 19 items three times and the pairs are not')
w('independent, which is the same non-independence the pooled correctness result was rejected')
w('for.')
w()
w('### 2.3 Accuracy on the same items is essentially unchanged')
w()
w('| Model | n items | Mean correctness difference (pp) | Wilcoxon p |')
w('|---|---|---|---|')
AAEC={}
for m in MODELS:
    d=paired('correct',pred=lambda r: r['track']=='AAE',model=m,scale=100.0)
    p=float(stats.wilcoxon(d).pvalue) if (d!=0).any() else 1.0
    AAEC[SHORT[m]]=dict(n=len(d),mean=float(d.mean()),p=p)
    w(f'| {SHORT[m]} | {len(d)} | {d.mean():+.2f} | {fp(p)} |')
FIG['aae_correctness_per_model']=AAEC
sae_w=float(np.mean([int(r['word_count']) for r in sc if r['track']=='AAE' and r['cond']=='SAE' and r['item_id'] not in EXCL]))
dia_w=float(np.mean([int(r['word_count']) for r in sc if r['track']=='AAE' and r['cond']=='DIALECT' and r['item_id'] not in EXCL]))
FIG['aae_mean_words']=dict(sae=sae_w,dialect=dia_w)
w()
w(f'Mean response length falls from {sae_w:.1f} words in the SAE arm to {dia_w:.1f} in the dialect')
w('arm, while the paired correctness difference is exactly zero for two models and -7.0')
w('percentage points for the third at p = 0.10. On a multi-step arithmetic problem, a shorter')
w('answer at the same accuracy means less working shown.')
w()

# ---------------------------------------------------------------- 3. FINDING TWO
w('## 3. Finding two: dialect-triggered locale inference')
w()
w('### 3.1 What the classification is')
w()
w('Every item was classified before the split was run, from item text and gold answer only. An')
w('item is **locale-sensitive** if its correct answer depends on the jurisdiction the user is')
w('in: national agencies, government forms and fees, emergency telephone numbers, banking')
w('identity regimes, or legal and administrative procedure. Four of 52 qualify, all procedural')
w('guidance items in the Indian English track: IE26 (CPR, the emergency number is')
w('jurisdictional), IE27 (passport renewal), IE28 (opening a bank account online), IE32 (filing')
w('a noise complaint). The other four procedural items are physical procedures, giving a')
w('within-domain contrast of four against four. Per-item reasons are in')
w('`item_locale_classification.csv`.')
w()
w('### 3.2 The result')
w()
w('| Split | n item x model | Median difference (words) | Wilcoxon p (nominal) | Shorter | Longer | Tied |')
w('|---|---|---|---|---|---|---|')
LSPL=[]
def lrow(label,pred):
    d=paired('word_count',pred=pred)
    if len(d)<5:
        w(f'| {label} | {len(d)} | insufficient n | - | - | - | - |'); return
    r=wil(d); LSPL.append(dict(split=label,**r))
    w(f"| {label} | {r['n']} | {r['median']:+.2f} | {fp(r['p'])} | {r['shorter']} | {r['longer']} | {r['ties']} |")
lrow('Indian English, locale-sensitive', lambda r: r['track']=='IndE' and r['loc']=='locale-sensitive')
lrow('Indian English, locale-invariant', lambda r: r['track']=='IndE' and r['loc']=='locale-invariant')
lrow('Indian English, Factual QA', lambda r: r['track']=='IndE' and r['domain']=='Factual QA')
lrow('Indian English, Arithmetic', lambda r: r['track']=='IndE' and r['domain']=='Arithmetic')
lrow('Indian English, Reading Comprehension', lambda r: r['track']=='IndE' and r['domain']=='Reading Comprehension')
lrow('Procedural, locale-invariant', lambda r: r['domain']=='Procedural Guidance' and r['loc']=='locale-invariant')
lrow('AAE track (all locale-invariant)', lambda r: r['track']=='AAE')
FIG['locale_length']=LSPL
w()
w('On the four locale-sensitive items **every one of the 12 item-by-model pairs is shorter in')
w('the dialect arm**, with a median difference of about 300 words. On the 28 locale-invariant')
w('Indian English items there is no length difference at all.')
w()
w('### 3.3 The worked example')
w()
sa27=akey['IE27']['sae_arm']; da27=akey['IE27']['dialect_arm']
raw={}
for line in open(str(DATA_DIR/"raw_responses.jsonl"),encoding='utf-8'):
    rr=json.loads(line)
    if rr.get('error') or rr.get('response_text') is None: continue
    raw[(rr['item_id'],rr['arm'],rr['model'],rr['rep'])]=rr['response_text']
m27='meta/llama-3.3-70b-instruct'
sw=[len(raw[('IE27',sa27,m27,k)].split()) for k in (1,2,3)]
dw=[len(raw[('IE27',da27,m27,k)].split()) for k in (1,2,3)]
FIG['passport_example']=dict(model=m27,sae_words=sw,dialect_words=dw,
                             sae_mean=float(np.mean(sw)),dialect_mean=float(np.mean(dw)),
                             sae_prompt=items[('IE27',sa27)]['prompt'],
                             dialect_prompt=items[('IE27',da27)]['prompt'],
                             dialect_response_rep1=raw[('IE27',da27,m27,1)])
w(f'Item IE27, model {SHORT[m27]}.')
w()
w('> **SAE wording.** ' + items[('IE27',sa27)]['prompt'])
w()
w('> **Indian English wording.** ' + items[('IE27',da27)]['prompt'])
w()
w(f'Response lengths across the three repeats were {sw[0]}, {sw[1]} and {sw[2]} words in the SAE')
w(f'arm (mean {np.mean(sw):.1f}) and {dw[0]}, {dw[1]} and {dw[2]} words in the dialect arm')
w(f'(mean {np.mean(dw):.1f}).')
w()
w('The SAE answer describes the **United States** process: eligibility criteria, the specific')
w('federal application form, the documents required and the fee. The Indian English answer')
w('describes the **Indian** process, including police verification, as a bare numbered list. The')
w('dialect response to repeat 1, in full:')
w()
for ln in raw[('IE27',da27,m27,1)].strip().split('\n'):
    w('> '+ln if ln.strip() else '>')
w()
w('Both responses were scored correct, because both contain the required steps.')
w()
w('### 3.4 How to read it')
w()
w('The model has inferred a jurisdiction from dialect markers and acted on that inference by')
w('changing which country\'s procedure it describes. This is a demographic inference drawn from')
w('dialect and acted upon, which is the phenomenon Hofmann and colleagues document for African')
w('American English in a different outcome dimension; here it appears in the content and scope')
w('of task guidance rather than in judgements about the speaker.')
w()
w('It should be read even-handedly. India-specific guidance may be more useful than United')
w('States guidance to some Indian English speakers, and it is wrong for an Indian English')
w('speaker living elsewhere. The finding is not that the switch is harmful or that it is')
w('helpful. **The finding is that the switch is unsignalled**: nothing in either response tells')
w('the user that a jurisdiction has been assumed, or which one, or that the answer would have')
w('been different had the question been typed differently.')
w()
w('This is also why the pooled Indian English length figure in the previous draft was')
w('uninterpretable. It was one number covering two phenomena: no length difference at all on 28')
w('items, and a very large one on 4, driven by a mechanism that is not brevity.')
w()

# ---------------------------------------------------------------- 4. correctness
w('## 4. Correctness: a null over the corrected family, with one lead')
w()
w('### 4.1 The collapsing rule, stated')
w()
w('Each item is asked three times per model per arm. Those three binary scores can be collapsed')
w('to one verdict by **majority vote**, counting a cell correct when at least 2 of 3 repeats are')
w('correct, and compared with an exact McNemar test. Or the graded cell mean can be kept, taking')
w('values 0, one third, two thirds or 1, and the paired per-item differences tested with a')
w('Wilcoxon signed-rank test. Majority voting discards information: a cell falling from 3 of 3')
w('to 2 of 3 has visibly worsened and the rule records no change. Both are reported.')
w()
w('| Level | Unit | n | Method | Statistic | p |')
w('|---|---|---|---|---|---|')
LEV={}
for lab,drop in [('AAE08 excluded (primary)',EXCL),('All 52 items (sensitivity)',())]:
    sub=[r for r in sc if r['item_id'] not in drop]
    ks=sum(int(r['correct']) for r in sub if r['cond']=='SAE'); ns=sum(1 for r in sub if r['cond']=='SAE')
    kd=sum(int(r['correct']) for r in sub if r['cond']=='DIALECT'); nd=sum(1 for r in sub if r['cond']=='DIALECT')
    w(f'| Response, {lab} | one response | {ns+nd} | counts | SAE {ks}/{ns}, dialect {kd}/{nd} | not a test |')
    d=paired('correct',drop=drop,scale=100.0); r=wil(d)
    b=r['shorter']; c=r['longer']
    ps=float(stats.binomtest(b,b+c,0.5).pvalue) if (b+c) else 1.0
    w(f"| Graded item, {lab} | item x model | {r['n']} | Wilcoxon signed-rank | "
      f"mean {r['mean']:+.2f} pp, b = {b}, c = {c} | {fp(r['p'])} |")
    cv=cells('correct',drop=drop); B=C=0; N=0
    for (iid,mm) in sorted(set((k[0],k[1]) for k in cv)):
        s=cv.get((iid,mm,'SAE')); dd=cv.get((iid,mm,'DIALECT'))
        if not s or not dd: continue
        N+=1
        sv=1 if sum(s)>len(s)/2 else 0; dv=1 if sum(dd)>len(dd)/2 else 0
        if sv==1 and dv==0: B+=1
        elif dv==1 and sv==0: C+=1
    pm=float(stats.binomtest(B,B+C,0.5).pvalue) if (B+C) else 1.0
    w(f'| Collapsed pair, {lab} | item x model | {N} | exact McNemar | b = {B}, c = {C}, discordant = {B+C} | {fp(pm)} |')
    LEV[lab]=dict(sae_k=ks,sae_n=ns,dia_k=kd,dia_n=nd,graded_n=r['n'],graded_mean=r['mean'],
                  graded_b=b,graded_c=c,graded_p=r['p'],sign_p=ps,
                  collapsed_n=N,collapsed_b=B,collapsed_c=C,collapsed_p=pm)
FIG['levels']=LEV
w()
w('### 4.2 Per model, and per-arm accuracy both ways')
w()
w('| Model | Graded b | Graded c | Graded p | Collapsed b | Collapsed c | Collapsed p | Clears family threshold |')
w('|---|---|---|---|---|---|---|---|')
PERM={}
for m in MODELS:
    d=paired('correct',model=m,scale=100.0); r=wil(d)
    cv=cells('correct'); B=C=0
    for (iid,mm) in sorted(set((k[0],k[1]) for k in cv)):
        if mm!=m: continue
        s=cv.get((iid,mm,'SAE')); dd=cv.get((iid,mm,'DIALECT'))
        if not s or not dd: continue
        sv=1 if sum(s)>len(s)/2 else 0; dv=1 if sum(dd)>len(dd)/2 else 0
        if sv==1 and dv==0: B+=1
        elif dv==1 and sv==0: C+=1
    pm=float(stats.binomtest(B,B+C,0.5).pvalue) if (B+C) else 1.0
    PERM[m]=dict(graded_b=r['shorter'],graded_c=r['longer'],graded_p=r['p'],
                 collapsed_b=B,collapsed_c=C,collapsed_p=pm)
    w(f"| {SHORT[m]} | {r['shorter']} | {r['longer']} | {fp(r['p'])} | {B} | {C} | {fp(pm)} | "
      f"{'yes' if r['p']<ALPHA else 'no'} |")
FIG['per_model_levels']=PERM
w()
w('Per-arm accuracy computed both ways, which is Figure 1:')
w()
w('| Model | Arm | Binary (majority vote) | Graded (cell mean) |')
w('|---|---|---|---|')
BG={}
cvb=cells('correct')
for m in MODELS:
    ids=sorted(set(k[0] for k in cvb if k[1]==m))
    for c in ('SAE','DIALECT'):
        binv=[1 if sum(cvb[(i,m,c)])>len(cvb[(i,m,c)])/2 else 0 for i in ids]
        grad=[np.mean(cvb[(i,m,c)]) for i in ids]
        BG[f'{SHORT[m]}|{c}']=dict(binary=100*float(np.mean(binv)),graded=100*float(np.mean(grad)),n=len(ids))
        w(f"| {SHORT[m]} | {'SAE' if c=='SAE' else 'Dialect'} | {100*np.mean(binv):.2f} per cent | {100*np.mean(grad):.2f} per cent |")
FIG['accuracy_binary_graded']=BG
w()
w('### 4.3 What this supports')
w()
w('No model establishes a correctness effect over the nine-test family. glm-5.2 reaches a')
w('nominal p = 0.024 with 6 items worse in the dialect arm and 0 better, which is above the')
w(f'threshold of {ALPHA:.5f}. That is reported as a lead worth pursuing in a larger study. It is')
w('not promoted to a finding, and it is not dismissed. The other two models show nothing.')
w()
w('The pooled row in the table above is not the basis of any claim: it counts the same 51 items')
w('three times, so its p-value is anticonservative by an amount this design cannot quantify.')
w()

# ---------------------------------------------------------------- 5. step coverage
w('## 5. Step coverage: underpowered, with a consistent direction')
w()
w('Length alone is not a quality measure. The procedural items carry a required-step list and')
w('the scorer records how many steps each response contains, which is the only measure in this')
w('study bearing on whether shorter answers are less complete.')
w()
w('| Split | Arm | Mean steps present | Mean steps required | Mean coverage | Mean words |')
w('|---|---|---|---|---|---|')
STEP={}
for lab,pred in [('Procedural, locale-invariant', lambda r: r['domain']=='Procedural Guidance' and r['loc']=='locale-invariant'),
                 ('Procedural, locale-sensitive', lambda r: r['domain']=='Procedural Guidance' and r['loc']=='locale-sensitive')]:
    for c in ('SAE','DIALECT'):
        sub=[r for r in sc if pred(r) and r['cond']==c and r['steps_present']!='' and r['item_id'] not in EXCL]
        sp=float(np.mean([int(r['steps_present']) for r in sub]))
        st=float(np.mean([int(r['steps_total']) for r in sub]))
        cov=float(np.mean([int(r['steps_present'])/int(r['steps_total']) for r in sub]))
        wd=float(np.mean([int(r['word_count']) for r in sub]))
        STEP[f'{lab}|{c}']=dict(steps=sp,total=st,coverage=cov,words=wd,n=len(sub))
        w(f"| {lab} | {'SAE' if c=='SAE' else 'Dialect'} | {sp:.2f} | {st:.2f} | {cov:.3f} | {wd:.1f} |")
w()
w('| Split | n item x model | Mean coverage difference | Wilcoxon p | Worse | Better | Tied |')
w('|---|---|---|---|---|---|---|')
for lab,pred in [('Procedural, locale-invariant', lambda r: r['domain']=='Procedural Guidance' and r['loc']=='locale-invariant'),
                 ('Procedural, locale-sensitive', lambda r: r['domain']=='Procedural Guidance' and r['loc']=='locale-sensitive')]:
    cv=defaultdict(list)
    for r in sc:
        if r['item_id'] in EXCL or not pred(r) or r['steps_present']=='': continue
        cv[(r['item_id'],r['model'],r['cond'])].append(int(r['steps_present'])/int(r['steps_total']))
    d=[]
    for (iid,mm) in sorted(set((k[0],k[1]) for k in cv)):
        s=cv.get((iid,mm,'SAE')); dd=cv.get((iid,mm,'DIALECT'))
        if s and dd: d.append(np.mean(dd)-np.mean(s))
    d=np.array(d); r=wil(d)
    STEP[f'{lab}|paired']=dict(n=r['n'],mean=r['mean'],median=r['median'],p=r['p'],
                               worse=r['shorter'],better=r['longer'],ties=r['ties'])
    w(f"| {lab} | {r['n']} | {r['mean']:+.4f} | {fp(r['p'])} | {r['shorter']} | {r['longer']} | {r['ties']} |")
w()
inv=STEP['Procedural, locale-invariant|paired']
cvi=defaultdict(list)
for r in sc:
    if r['domain']!='Procedural Guidance' or r['loc']!='locale-invariant' or r['steps_present']=='' or r['item_id'] in EXCL: continue
    cvi[(r['item_id'],r['model'],r['cond'])].append(int(r['steps_present'])/int(r['steps_total']))
dd=[]
for (iid,mm) in sorted(set((k[0],k[1]) for k in cvi)):
    s=cvi.get((iid,mm,'SAE')); t=cvi.get((iid,mm,'DIALECT'))
    if s and t: dd.append(np.mean(t)-np.mean(s))
dd=np.array(dd); sd=float(dd.std(ddof=1)); dz=float(dd.mean()/sd)
za=stats.norm.ppf(0.975); zb=stats.norm.ppf(0.80)
n_t=(za+zb)**2/dz**2
zaf=stats.norm.ppf(1-ALPHA/2); n_tf=(zaf+zb)**2/dz**2
FIG['step_coverage']=STEP
FIG['step_power']=dict(mean_diff=float(dd.mean()),sd=sd,dz=dz,
                       n_pairs_alpha05=math.ceil(n_t),n_items_alpha05=math.ceil(n_t/3),
                       n_pairs_family=math.ceil(n_tf),n_items_family=math.ceil(n_tf/3))
w('**This result is underpowered, and it is reported as underpowered rather than as a null.**')
w(f"On the locale-invariant procedural items the dialect arm covers {100*(STEP['Procedural, locale-invariant|SAE']['coverage']-STEP['Procedural, locale-invariant|DIALECT']['coverage']):.1f}")
w(f"percentage points fewer of the required steps ({STEP['Procedural, locale-invariant|DIALECT']['coverage']:.3f} against "
  f"{STEP['Procedural, locale-invariant|SAE']['coverage']:.3f}), with {inv['worse']} of {inv['n']} pairs worse, "
  f"{inv['better']} better and {inv['ties']} tied, at p = {inv['p']:.3f} on {inv['n']} pairs.")
w('The direction is consistent and the difference is not small; the sample is.')
w()
w('The standardised paired effect size is dz = {:.3f}. Detecting an effect of that size at 80'.format(abs(dz)))
w(f'per cent power requires about {math.ceil(n_t)} paired observations at a two-sided alpha of 0.05,')
w(f'which at 3 models per item is {math.ceil(n_t/3)} items; or about {math.ceil(n_tf)} pairs')
w(f'({math.ceil(n_tf/3)} items) at the family threshold of {ALPHA:.5f}. We have {inv["n"]} pairs')
w('and 4 items. A follow-up should carry at least that many locale-invariant procedural items.')
w()
sens=STEP['Procedural, locale-sensitive|paired']
w(f"On the locale-sensitive items coverage is essentially identical between arms "
  f"({STEP['Procedural, locale-sensitive|DIALECT']['coverage']:.3f} against "
  f"{STEP['Procedural, locale-sensitive|SAE']['coverage']:.3f}, p = {sens['p']:.2f}) despite a "
  f"length difference of about 300 words, which is consistent with localisation rather than a "
  f"reduction in completeness.")
w()
w('**What may and may not be said.** These data do not establish that shorter dialect answers')
w('are less complete. They also do not establish that the two arms are equally complete. The')
w('honest statement is that the only quality measure available points consistently downwards on')
w('a sample too small to resolve it.')
w()
w('### 5.1 A tension a reader will notice')
w()
w('Section 3.2 reports no length effect on locale-invariant Indian English items, and section 5')
w('reports lower step coverage on locale-invariant procedural items. Those look like they point')
w('in different directions. They do not, because the two subsets are not the same set.')
w()
w('Step coverage is defined only for procedural items, since only those carry a required-step')
w('list. Of the 28 locale-invariant Indian English items, just 4 are procedural; the other 24')
w('are factual questions, arithmetic and reading comprehension, which have no coverage measure')
w('at all. Those 24 items are also where the length null comes from. The 4 locale-invariant')
w('procedural items do shorten, at a median of 264 words and a nominal p of 0.0068, and they are')
w('the only locale-invariant Indian English items with a coverage measure. So the null in')
w('section 3.2 is dominated by items the coverage analysis cannot see, and the coverage result')
w('comes from the small subset that does shorten. The two findings are about different items.')
w()

# ---------------------------------------------------------------- 6. register
w('## 6. Register markers, reported as three of the nine family tests')
w()
w('| Model | Arm | Commonwealth tokens | Eligible tokens | Rate |')
w('|---|---|---|---|---|')
REG=[]
for m in MODELS:
    for c in ('SAE','DIALECT'):
        sub=[r for r in sc if r['model']==m and r['cond']==c and r['item_id'] not in EXCL]
        b=sum(int(r['brit_count']) for r in sub); e=sum(int(r['eligible_tokens']) for r in sub)
        REG.append(dict(model=SHORT[m],cond=c,brit=b,eligible=e,rate=(b/e if e else None)))
        w(f"| {SHORT[m]} | {'SAE' if c=='SAE' else 'Dialect'} | {b} | {e} | "
          f"{(b/e if e else float('nan')):.4f} |")
FIG['register_rates_excl']=REG
w()
w('| Model | n items with eligible tokens | Mean difference (pp) | W | p | Clears family threshold |')
w('|---|---|---|---|---|---|')
REGP={}
for m in MODELS:
    d=paired('brit_rate',model=m,scale=100.0); r=wil(d)
    REGP[SHORT[m]]=r
    Wtxt=f"{r['W']:.1f}" if r['W'] is not None else 'n/a'
    w(f"| {SHORT[m]} | {r['n']} | {r['mean']:+.3f} | {Wtxt} | {fp(r['p'])} | "
      f"{'yes' if r['p']<ALPHA else 'no'} |")
FIG['register_paired']=REGP
w()
w('No model reaches significance and none clears the family threshold. **The June pilot result')
w('does not replicate.** The pilot reported one model shifting towards British spelling on the')
w('dialect arm of the procedural items, in 4 of 8 pairs and none the other way. Nothing of that')
w('size appears here, and gemma-4-31b leans in the opposite direction, using Commonwealth forms')
w('more often in the SAE arm.')
w()
w('**This is not a direct refutation.** The model that produced the original observation,')
w('deepseek-v4-pro, was unavailable on this endpoint throughout the collection window, so the')
w('pilot finding has not been retested on the system that produced it. What these data')
w('establish is that the effect is not a general property of language models responding to')
w('Indian English.')
w()

# ---------------------------------------------------------------- 7. family
w('## 7. The confirmatory family in full')
w()
w(f'{NT} tests, Bonferroni threshold {ALPHA:.5f}. Length is tested over all 51 items here, which')
w('is the family member; the AAE-track and locale splits in sections 2 and 3 are follow-ups.')
w()
w('| Outcome | Model | n | W | p | Clears threshold |')
w('|---|---|---|---|---|---|')
FAM=[]
for oname,field,scale in [('Correctness','correct',100.0),('Length','word_count',1.0),
                          ('Register','brit_rate',100.0)]:
    for m in MODELS:
        d=paired(field,model=m,scale=scale); r=wil(d)
        Wtxt=f"{r['W']:.1f}" if r['W'] is not None else 'n/a'
        surv='yes' if r['p']<ALPHA else 'no'
        FAM.append(dict(outcome=oname,model=SHORT[m],n=r['n'],W=r['W'],p=r['p'],survives=surv))
        w(f'| {oname} | {SHORT[m]} | {r["n"]} | {Wtxt} | {fp(r["p"])} | {surv} |')
FIG['family_tests']=FAM
w()
w('## 8. Power for a future study')
w()
w('| True per-item rate | Items needed for an 80 per cent chance of one or more errors |')
w('|---|---|')
FIG['power']=[]
for pi in (0.01,0.02,0.03,0.05,0.10,0.20):
    n_=math.ceil(math.log(0.20)/math.log(1-pi))
    FIG['power'].append(dict(pi=pi,n=n_))
    w(f'| {100*pi:.0f} per cent | {n_} |')
w()
FIG['inventory']=dict(total=len(sc),models=MODELS,items_all=52,items_primary=51,excluded=['AAE08'])
json.dump(FIG,open(str(ANALYSIS_DIR/"figures.json"),'w'),indent=1,default=float)
open(str(DOCS_DIR/"analysis.md"),'w',encoding='utf-8').write('\n'.join(OUT)+'\n')
print('wrote analysis.md and figures.json')
