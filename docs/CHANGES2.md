# CHANGES2.md — four defects, what was wrong, what it is now

Every figure below is re-derived by `analyse2.py` from `scores.csv` and checked independently
by `verify.py`, which recomputes the variance decomposition, the collapsing rule and the locale
split from `raw_responses.jsonl` without reusing the analysis code. **123 checks, 0 failures.**

The primary analysis now excludes one item, AAE08. Every headline figure is also reported with
it retained.

---

## Defect 1. The variance decomposition was reported backwards

**What was wrong.** Two separate faults, one cosmetic and one substantive.

The cosmetic one: the draft set a between-arm difference of "6.4 percentage points" beside a
within-arm figure of "0.15" and said the difference vanished. Those numbers were in different
units. The within-arm figure is a standard deviation of a 0/1 correctness score in **proportion
units**, so it is 15.0 percentage points, not 0.15. The ratio 6.41/14.98 = 0.43 was
arithmetically correct; the sentence describing it was not.

The substantive one: the ratio was being used as though it decided whether an effect existed.
It compares a *mean over 52 items* against the spread of a *single response*. Those are
different scales, and the comparison is not a test.

**What it is now.** Three scales are reported in matched units, and every claim rests on a
Wilcoxon signed-rank test with a stated family-wise correction.

Precisely what the within-arm figure measures: correctness is scored 0 or 1 per response; each
(item, model, arm) cell of three repeats gives one sample SD, which for three binary values can
only be 0 or 0.5774; those are pooled across cells as a root mean square. For glm-5.2 over all
52 items, 97 of 104 cells were unanimous and 7 split, giving 0.1498 in proportion units.

**The old criterion contradicted the test in both directions**, so it was not merely
conservative:

| Outcome | Model | Old ratio | Old reading | Wilcoxon p | Corrected reading |
|---|---|---|---|---|---|
| Length | llama-3.3-70b | 0.70 | "no effect demonstrated" | 0.00013 | clears the family threshold |
| Register | llama-3.3-70b | 1.06 | "larger than within-arm spread" | 0.75 | not significant |

**Figures that moved.** Multiplicity is now stated: the confirmatory family is 3 models x 3
outcomes = 9 tests, Bonferroni threshold 0.05/9 = 0.00556. All values below exclude AAE08.

| Outcome / model | Was | Now |
|---|---|---|
| Correctness, gemma-4-31b | ratio 0.11, "no effect demonstrated" | diff 0.00 pp, p = 0.65 |
| Correctness, llama-3.3-70b | ratio 0.45, "no effect demonstrated" | diff -2.61 pp, p = 0.18 |
| Correctness, glm-5.2 | ratio 0.43, "no effect demonstrated" | diff -5.88 pp, **p = 0.024**, does not clear 0.00556 |
| Length, gemma-4-31b | ratio 1.26, "suggestive" | diff -31.52 words, p = 0.00075, **clears** |
| Length, llama-3.3-70b | ratio 0.70, "no effect demonstrated" | diff -48.94 words, p = 0.00013, **clears** |
| Length, glm-5.2 | ratio 1.46, "suggestive" | diff -46.08 words, p = 0.022, does not clear |
| Register, all three | ratios 0.23 / 1.06 / 0.18 | p = 1.00 / 0.75 / 0.32, all null |
| Within-arm SD, glm correctness | "0.15", units unstated | 0.1498 proportion = 15.0 pp (52 items); 12.78 pp (51 items) |

**Direction of the correction.** The draft's claim that "no correctness effect is demonstrated
for any of the three models" is withdrawn. One model shows a nominal effect. It does not clear
the family threshold, so a correctness effect is still not established, but the draft's stated
*reason* was wrong and the nominal result is now reported rather than dismissed.

---

## Defect 2. The 9 SAE-arm errors

**What was wrong.** Nothing was wrong in the arithmetic, but the draft never accounted for the
errors, and the hypothesis that 9 = 3 models x 3 repeats indicates a single failing item turns
out to be false.

**What it is now.** The 9 SAE errors come from three different items:

| Item | Domain | SAE errors |
|---|---|---|
| AAE08 | Arithmetic | 5 of 9 |
| IE30 | Procedural Guidance | 2 of 9 |
| IE03 | Factual QA | 2 of 9 |

So the SAE arm is **not** at ceiling on all valid items. Even after removing AAE08 it retains 4
errors, on IE30 and IE03. Both were checked by hand: IE03 is a genuine disagreement about how
many continents there are, IE30 is a step-coverage failure. Neither is defective.

**AAE08 is defective and is now excluded**, which is the only exclusion in the study. Two
independent reasons, both recorded in the manuscript with both wordings quoted in full:

1. Its constraints contradict each other. It states Saturday apple pie is 4 fewer than Sunday
   *and* Sunday is 15 more than Saturday, giving S = S + 11. The gold answer of 540 is not
   derivable from any consistent reading.
2. The two arms are not meaning-identical. The dialect wording inserts a comma before "than on
   Sunday", which changes what the comparison attaches to. This is the disqualifying defect: an
   item whose arms differ in meaning cannot measure a dialect effect.

The pilot excluded this item; the first API-run draft reversed that and called it merely hard.
That reversal is now itself reversed, deliberately and with the reason recorded.

**Figures that moved.**

| Figure | Was (52 items) | Now (51 items, primary) |
|---|---|---|
| SAE accuracy | 459/468 = 98.08 per cent | 455/459 = 99.13 per cent |
| Dialect accuracy | 443/468 = 94.66 per cent | 442/459 = 96.30 per cent |
| Arm gap | 3.42 pp | 2.83 pp |
| SAE errors | 9 | 4 |
| Dialect errors | 25 | 17 |

The gap narrows but does not disappear, so the effect is not an artefact of AAE08.

---

## Defect 3. The repeat-collapsing rule was undisclosed and it drove the null

**What was wrong.** The draft reduced three repeats per cell to one verdict by **majority
vote** (correct when at least 2 of 3 repeats are correct) and never said so. That rule is why 25
dialect errors against 9 SAE errors at response level became a handful of discordant pairs: a
cell falling from 3/3 to 2/3 has visibly got worse and majority voting records no change.

The draft also said "6 discordant pairs" in one place and "5 against the dialect arm" in
another. Both were true and neither was complete: 6 was b + c, 5 was b alone.

**What it is now.** The rule is stated explicitly in Methods 2.4. Correctness is reported at
both levels with b and c given separately everywhere, so a reader can reconstruct any test.

| Level | Unit | n | Method | Statistic | p |
|---|---|---|---|---|---|
| Response | one response | 918 | descriptive counts | SAE 455/459, dialect 442/459 | not a test |
| Graded item | item x model | 153 | Wilcoxon signed-rank on per-item mean differences | mean -2.83 pp, b = 9, c = 1 | **0.0072** |
| Graded item | item x model | 10 | exact sign test on non-zero differences | b = 9, c = 1 | 0.021 |
| Collapsed pair | item x model | 153 | exact McNemar after majority-vote collapsing | b = 3, c = 1, discordant = 4 | 0.63 |

Per model, binary against graded, side by side (AAE08 excluded):

| Model | Graded b | Graded c | Graded p | Collapsed b | Collapsed c | Collapsed p |
|---|---|---|---|---|---|---|
| gemma-4-31b | 1 | 1 | 0.65 | 0 | 1 | 1.00 |
| llama-3.3-70b | 2 | 0 | 0.18 | 1 | 0 | 1.00 |
| glm-5.2 | 6 | 0 | **0.024** | 2 | 0 | 0.50 |
| Pooled | 9 | 1 | 0.0072 | 3 | 1 | 0.63 |

**Which level the paper rests on.** The per-model graded test with the Bonferroni threshold of
0.00556 for the nine-test family. On that basis no model establishes a correctness effect. The
pooled row is reported but carries no claim: it counts the same 51 items three times, so the
153 differences are not independent and the pooled p is anticonservative by an unquantified
amount.

**Figures that moved.**

| Figure | Was | Now |
|---|---|---|
| Headline correctness test | collapsed McNemar, b = 5, c = 1, p = 0.22 | graded Wilcoxon, b = 9, c = 1, p = 0.0072 |
| glm-5.2 correctness | p = 0.25 | p = 0.024 |
| Discordant pairs | "6" and "5" used interchangeably | b = 5, c = 1 on 52 items; b = 3, c = 1 on 51 |

---

## Defect 4. The locale-inference explanation was never tested

**What was wrong.** The draft reported the passport observation as an unquantified curiosity
and let a single pooled length effect stand as one phenomenon. It was two.

**What it is now.** Every item is classified as locale-sensitive or locale-invariant by a rule
fixed before the split was run: an item is locale-sensitive if its correct answer depends on
jurisdiction. Four of 52 qualify, all procedural guidance items in the Indian English track:
IE26 (CPR, the emergency number is jurisdictional), IE27 (passport renewal), IE28 (opening a
bank account online), IE32 (filing a noise complaint). The other four procedural items are
physical procedures, giving a clean within-domain contrast. Full classification with per-item
reasons is in `item_locale_classification.csv`.

**Length by subset** (AAE08 excluded; these p-values are nominal follow-ups, not family members):

| Split | n | Median (words) | p | Shorter / longer |
|---|---|---|---|---|
| AAE track (jurisdiction-free, speaker-validated) | 57 | -20.67 | 9.98 x 10^-10 | 52 / 4 |
| Indian English, locale-invariant | 84 | +0.00 | 0.77 | 38 / 39 |
| Indian English, locale-sensitive | 12 | -299.67 | 0.00049 | 12 / 0 |
| Procedural, locale-invariant | 12 | -264.33 | 0.0068 | 9 / 3 |
| Indian English, Factual QA | 24 | +4.17 | 0.077 | 8 / 14 |
| Indian English, Arithmetic | 24 | +1.17 | 0.50 | 10 / 13 |
| Indian English, Reading Comprehension | 24 | +0.00 | 0.67 | 11 / 9 |

**The AAE track in full**, which is the paper's strongest claim, since those items are
jurisdiction-free, numeric, and validated by AAE-speaking researchers:

| Model | n | Median length diff | p | Shorter / longer | Clears family threshold | Correctness diff | Correctness p |
|---|---|---|---|---|---|---|---|
| gemma-4-31b | 19 | -17.67 | 0.00020 | 18 / 0 | yes | +0.00 pp | 1.00 |
| llama-3.3-70b | 19 | -27.67 | 0.000027 | 18 / 1 | yes | +0.00 pp | 1.00 |
| glm-5.2 | 19 | -18.67 | 0.00042 | 16 / 3 | yes | -7.02 pp | 0.10 |

Mean length falls from 106.6 words to 82.9. **The length effect survives on locale-invariant
items, so it is not reducible to localisation.** But the Indian English part of the pooled
effect *is* localisation: on locale-invariant Indian English items there is no length
difference at all.

**Is shorter also worse?** Step coverage on procedural items, set beside word count:

| Split | Arm | Mean coverage | Mean words | Paired coverage diff | p | Worse / better |
|---|---|---|---|---|---|---|
| Locale-invariant | SAE | 0.941 | 564.5 | | | |
| Locale-invariant | Dialect | 0.879 | 368.4 | -0.063 | 0.078 | 6 / 1 |
| Locale-sensitive | SAE | 0.936 | 589.7 | | | |
| Locale-sensitive | Dialect | 0.931 | 279.6 | -0.006 | 0.66 | 4 / 4 |

On locale-sensitive items the dialect answers are ~300 words shorter and cover the same steps:
localisation, not quality loss. On locale-invariant procedural items they are shorter and cover
somewhat fewer steps, but at p = 0.078 on 12 pairs. **The manuscript therefore makes no claim
anywhere that shorter answers are worse answers**, and `verify.py` asserts that neither
step-coverage comparison reaches significance.

**Figures that moved.**

| Figure | Was | Now |
|---|---|---|
| Pooled length | 105/156 shorter, median -9.50, p = 1.45 x 10^-8 | 102/153 shorter, median -8.33, p = 6.2 x 10^-8 |
| Length, gemma-4-31b | median -8.00, p = 0.00044 | mean -31.52, p = 0.00075 |
| Length, llama-3.3-70b | median -15.33, p = 0.000078 | mean -48.94, p = 0.00013 |
| Length, glm-5.2 | median -4.50, p = 0.014 | mean -46.08, p = 0.022 |
| AAE track | -21.17 median, p = 2.8 x 10^-10, 55/60 | -20.67 median, p = 9.98 x 10^-10, 52/56, per model reported |
| Indian English track | -1.17 median, p = 0.028, 50/96 | split: invariant 0.00, p = 0.77; sensitive -299.67, p = 0.00049 |
| Procedural | -277.00 median, p = 3.9 x 10^-6 | split: invariant -264.33, p = 0.0068; sensitive -299.67, p = 0.00049 |
| Locale observation | exploratory counts, no p-value | classified, tested, and separated from the length effect |
| Step coverage | not reported | reported per arm with paired tests |

Unchanged: the power table (161 / 80 / 53 / 32 / 16 / 8) and the register conclusion.

---

## Defect 5a. The assertion removed from verify.py as stale

Quoted from the version of `verify.py` in force at the time. It lived in a list of strings the
manuscript was required to contain:

```python
must=[str(F['accuracy_pooled']['sae_k']), str(F['accuracy_pooled']['dia_k']),
      str(F['mcnemar']['ALL MODELS POOLED']['n']), '96.15','92.74','0.22','1.45','72 per cent',
      'google/gemma-4-31b-it','meta/llama-3.3-70b-instruct','z-ai/glm-5.2','0.7','936',
      '25 July 2026','0.375','277']
for s_ in must:
    chk(s_ in allt, f"manuscript states '{s_}'")
```

The removed element is `'72 per cent'`, so the removed assertion is:

```python
chk('72 per cent' in allt, "manuscript states '72 per cent'")
```

**Why it was wrong.** "72 per cent" was itself the erroneous figure. It came from computing the
number of pairs where the dialect answer was shorter as `n - dia_longer` = 156 - 43 = 113,
which silently counts the 8 exactly tied pairs as shorter; 113/156 is 72 per cent. The strictly
shorter count is 105, which is 67 per cent. The assertion therefore required the manuscript to
contain a number that the same verification run had just proved wrong: it encoded the bug, not
the truth.

**Why removing it is not the same as hiding an error.** The failing check was not deleted in
place of a fix. The underlying defect was fixed first, in `analyse.py`, by computing
`dia_shorter`, `dia_longer` and `ties` separately; the manuscript was corrected from 113 to 105
and from 72 per cent to 67 per cent; and the verification was **strengthened** at the same
time, by adding an independent recomputation of the direction split from `raw_responses.jsonl`
and an assertion that `shorter + longer + tied == n` for every model. The stale string check was
removed only after the thing it was pointing at had been corrected and re-asserted more
strictly. A reader can confirm this because the replacement checks fail loudly if the tie
handling regresses.

For completeness, three other assertions were altered in the same round, none of them to
suppress a real failure:

- The credential check `if 'nvapi-' in txt` was matching `verify.py`'s own source. Rewritten as
  `needle = 'nv' + 'api-'` so the checker does not match itself. The check is otherwise identical.
- The American-spelling check flagged `color` twice, both inside the Methods sentence that names
  American variants as examples of the variant list ("colour against color"). The scan now
  strips those example sentences before searching. The check is otherwise identical.
- `'96.15','92.74'` were updated to `'98.08','94.66'` after the IE07 scoring fix. Those were
  edits to track corrected figures, not deletions.

In the present round `verify.py` was rewritten wholesale, because the figures.json keys it
asserted against (`accuracy_rows`, `mcnemar`, `length`, `length_splits`, `bounds`,
`register_paired`) no longer exist. The per-model prose checks from the previous round
(`'8.0 words'`, `'15.3 words'`, `'35 shorter to 11 longer'` and similar) were dropped because
those figures were computed over all 52 items and the primary analysis now excludes AAE08, so
the manuscript no longer contains those strings. They are replaced by 123 checks that recompute
the variance decomposition, the collapsing rule and the locale split directly from the raw log.

## Defect 5b. Concurrent dispatch and backend replicas

Added to Methods 2.2:

> Requests were issued concurrently rather than one at a time, so different calls may have been
> routed to different backend replicas of the same model. This does not affect the independence
> of any call, since each remains a separate request with a single user message, no system
> prompt and no history, and the model string returned was checked against the model string
> requested on all 936 calls.

`verify.py` asserts the last clause directly.
