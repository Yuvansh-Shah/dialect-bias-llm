"""Locale classification of every item.

RULE, fixed before the split analysis was run: an item is locale-sensitive if its
correct answer depends on the jurisdiction the user is in -- national agencies,
government forms and fees, emergency telephone numbers, banking identity regimes,
or legal/administrative procedure. Everything else is locale-invariant.

The classification is made from the item text and gold answer only. Disclosure: by
the time this file was written I had already read responses for IE03, IE21, IE25,
IE27, IE30 and AAE08 while diagnosing other defects. The rule above is stated
independently of those results and can be audited against the item text by any reader.
"""
import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
ITEMS_DIR = ROOT / "items"
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
FIG_DIR = ROOT / "figures"
ANALYSIS_DIR = ROOT / "analysis"
import csv

SENSITIVE = {
 'IE26': 'CPR: gold step 1 is "call for help"; the emergency number is jurisdictional (911 / 112 / 108)',
 'IE27': 'Passport renewal: national agency, national form, national fee schedule',
 'IE28': 'Opening a bank account online: identity regime differs by country (for example video KYC in India)',
 'IE32': 'Filing a noise complaint: local ordinance and non-emergency police route are jurisdictional',
}
INVARIANT_REASON = {
 'Factual QA': 'Universal fact with one correct answer everywhere',
 'Arithmetic': 'Pure arithmetic; answer independent of jurisdiction',
 'Reading Comprehension': 'Answer is contained in the supplied passage',
 'Procedural Guidance': 'Physical or first-aid procedure that does not depend on jurisdiction',
}
akey={r['item_id']:r for r in csv.DictReader(open(ITEMS_DIR/"arm_mapping.csv",encoding="utf-8"))}
items={}
for r in csv.DictReader(open(ITEMS_DIR/"items.csv",encoding="utf-8")):
    items[(r['item_id'],r['arm'])]=r
ids=sorted(set(k[0] for k in items),
           key=lambda s:(s[:3], int(''.join(c for c in s if c.isdigit()))))
rows=[]
for iid in ids:
    it=items[(iid,akey[iid]['sae_arm'])]
    if iid in SENSITIVE:
        rows.append(dict(item_id=iid, track=('AAE' if iid.startswith('AAE') else 'IndE'),
                         domain=it['domain'], locale_class='locale-sensitive',
                         reason=SENSITIVE[iid]))
    else:
        r_ = ('ReDial numeric word problem; jurisdiction-free by construction'
              if iid.startswith('AAE') else INVARIANT_REASON[it['domain']])
        rows.append(dict(item_id=iid, track=('AAE' if iid.startswith('AAE') else 'IndE'),
                         domain=it['domain'], locale_class='locale-invariant', reason=r_))
with open(ITEMS_DIR/"item_locale_classification.csv","w",newline="",encoding="utf-8") as f:
    f.write('# Locale classification. RULE: locale-sensitive = the correct answer depends on\n'
            '# jurisdiction (national agency, government form or fee, emergency number, banking\n'
            '# identity regime, legal or administrative procedure). Rule fixed before the split\n'
            '# analysis was run and applied from item text and gold answer only.\n')
    w=csv.DictWriter(f,fieldnames=['item_id','track','domain','locale_class','reason'])
    w.writeheader(); w.writerows(rows)
from collections import Counter
print(Counter(r['locale_class'] for r in rows))
print("sensitive:",[r['item_id'] for r in rows if r['locale_class']=='locale-sensitive'])
print("procedural split:",Counter(r['locale_class'] for r in rows if r['domain']=='Procedural Guidance'))
