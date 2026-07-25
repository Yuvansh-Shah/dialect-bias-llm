# CHANGES3.md — five corrections, and what moved

All figures re-derived by `analyse3.py` from `scores.csv` and checked independently by
`verify.py`, which recomputes the AAE per-model tests, the tie sums, the locale split and the
step-coverage power from `raw_responses.jsonl` without reusing the analysis code.
**92 checks, 0 failures.**

Title changed, at the author's choice, to **"Same Answer, Fewer Words: Brevity and Unsignalled
Locale Inference in Language Model Responses to English Dialects"**. The previous title asked
whether answers get worse; the answer is that they are not less accurate, but they are shorter
and sometimes about a different country.

---

## Ground-truth correction: AAE08 and the ReDial subset

The author corrected an earlier statement of mine. AAE08 is **the same item the June pilot
excluded**: RowIdx 8 of `dialect_combined_results.xlsx`, the gingerbread and apple pie question,
gold 540, with both pilot models answering 990. There are not two defective ReDial items. There
is one, and two independent analyses converged on it.

Every place implying two has been corrected. The manuscript now states this as **convergent
identification of a single defective item out of twenty**, and frames it as reassurance about
the ReDial subset rather than a warning about it: two analyses, different models, different
methods, same item, with the second diagnosing the cause (contradictory constraints, plus a
comma in the dialect wording that shifts the parse).

---

## Correction 1. The variance ratio is removed entirely

**What changed.** Removed, not reported, not set aside as performed-and-rejected. It no longer
appears in `analysis.md`, in `figures.json` (the `variance_corrected` key is gone), in any
table, or in the manuscript. `verify.py` asserts its absence from both files.

Replaced by one sentence in Methods 2.1: the three repeats were collected so response stability
could be checked and so each cell could contribute a graded score, not as a variance test. The
graded cell means are kept and remain load-bearing for the correctness analysis.

**Figures removed.** The whole three-scale table (SD of one response, SD of one item difference,
SE of the mean, old ratio, difference over SE) for 9 outcome-by-model combinations, and the
"where the old criterion gave the wrong answer" table. Nothing replaces them; the family table
(Table 11) carries the per-model tests that actually support claims.

---

## Correction 2. The AAE length finding restated at a defensible level

**What was wrong.** "Shorter in 52 of 56 pairs" pooled 19 items counted three times, which is
the same non-independence already rejected for the pooled correctness result. The denominator
was also wrong.

**What it is now.** The finding leads with three separate per-model Wilcoxon signed-rank tests,
19 paired items each:

| Model | n items | Median difference (words) | W | p | Shorter | Longer | Tied | Clears alpha = 0.00556 |
|---|---|---|---|---|---|---|---|---|
| gemma-4-31b | 19 | -17.67 | 0.0 | 0.00020 | 18 | 0 | 1 | yes |
| llama-3.3-70b | 19 | -27.67 | 4.0 | 0.000027 | 18 | 1 | 0 | yes |
| glm-5.2 | 19 | -18.67 | 14.0 | 0.00042 | 16 | 3 | 0 | yes |

**The arithmetic resolved.** 19 items x 3 models = 57 pairs. The split is **52 shorter, 4
longer, 1 tied**, which sums to 57. The previously reported "52 of 56" omitted the tied pair
from the denominator. This is the second time a tie-counting defect has occurred in this
project, so `verify.py` now asserts explicitly that shorter + longer + tied equals 19 for each
model and 57 pooled, and that those counts match `figures.json`.

**The pooled count is now labelled descriptive only**, in the analysis, in the manuscript body,
and in the Table 4 row itself, which reads "Pooled (descriptive only)" with "not tested" in the
statistic columns.

| Figure | Was | Now |
|---|---|---|
| AAE headline | "shorter in 52 of 56 pairs", pooled, treated as the result | three per-model tests, each clearing the family threshold |
| AAE direction counts | 52 / 4, denominator 56 | 52 shorter / 4 longer / 1 tied, total 57 |
| Basis of the claim | pooled count | three independent Wilcoxon tests, n = 19 each |

---

## Correction 3. Locale inference promoted to a second finding

**What changed.** It was a confound explaining away a pooled number. It is now a finding with
its own Results subsection (3.2), its own place in the abstract, and its own figure (Figure 3).

**What it says.** On the four locale-sensitive Indian English items, all 12 item-by-model pairs
are shorter in the dialect arm, median difference 299.7 words, nominal p = 0.00049. On the 28
locale-invariant Indian English items there is no length difference at all: median 0.0 words, 38
shorter against 39 longer, p = 0.77.

**The worked example** is quoted in full: item IE27, passport renewal, llama-3.3-70b. Both
wordings are given. SAE responses ran 452, 547 and 486 words (mean 495.0) describing the
**United States** process with a named federal form, eligibility and fee; dialect responses ran
49, 45 and 49 words (mean 47.7) describing the **Indian** process including police verification.
Both scored correct. `verify.py` asserts every one of those six word counts appears in the
manuscript.

**Framing.** Reported even-handedly and explicitly so: India-specific guidance may be more
useful to many Indian English speakers and is simply wrong for one living elsewhere; we do not
claim which case is more common. The finding is stated as **the unsignalled switch** — nothing
in either response tells the user a jurisdiction was assumed, which one, or that a differently
typed question would have produced a different country's answer. It is connected to Hofmann et
al. (reference 11) as the same underlying phenomenon, a demographic inference drawn from dialect
and acted on, appearing in a different outcome dimension.

**And it explains the earlier number.** The manuscript states in both Results and Discussion
that the pooled Indian English length figure was uninterpretable because it was one number
covering two phenomena: nothing on 28 items, and roughly 300 words on 4.

---

## Correction 4. Step coverage reported as underpowered, not null

**What was wrong.** Reported as "not significant", which reads as evidence of no effect. It is
the only measure bearing on whether shorter means less complete, and its direction is
consistent.

**What it is now.** Direction, difference, n and p reported and described as underpowered:
coverage 0.879 in the dialect arm against 0.941 in the SAE arm, a difference of 6.3 percentage
points, with 6 of 12 pairs worse, 1 better and 5 tied, nominal p = 0.078.

**Required sample size**, computed from the observed standardised paired effect size
dz = 0.593: about **23 paired observations (8 items)** for 80 per cent power at a two-sided
alpha of 0.05, or **38 pairs (13 items)** at the family threshold of 0.0056. We have 12 pairs
and 4 items.

**The verify.py assertion changed.** It previously asserted `p >= 0.05`, which asserts that no
effect exists. That conflates two different claims. It now asserts:

- the direction is consistently worse in the dialect arm (6 worse against 1 better),
- mean coverage is lower in the dialect arm,
- the required n exceeds the n we have, that is, the comparison is underpowered,
- the manuscript contains the word "underpowered",
- the manuscript explicitly declines to establish that shorter means less complete,
- **and** the manuscript explicitly declines to assert that the arms are equally complete.

The last two together are what prevent "shorter is worse" being asserted as established without
asserting the opposite.

---

## Correction 5. Two reporting completions

**Register across the family.** All three models are now reported as members of the nine-test
family (Table 11): gemma-4-31b p = 1.00 on 11 eligible items, llama-3.3-70b p = 0.75 on 8,
glm-5.2 p = 0.32 on 16. None clears the threshold. The manuscript states plainly that the June
result does not replicate, and caveats that **deepseek-v4-pro**, the model that produced it, was
unavailable throughout the collection window (three attempts, all HTTP 504 after about 300
seconds), so this is not a direct refutation but the narrower claim that the effect is not a
general property of models responding to Indian English.

**The tension resolved.** Section 3.4 now explains why locale-invariant Indian English items show
no length effect while locale-invariant procedural items show lower coverage. Coverage is defined
only for procedural items, since only those carry a required-step list. Of the 28 locale-invariant
Indian English items only 4 are procedural; the other 24 are factual, arithmetic and reading
comprehension items with no coverage measure at all, and those 24 are what the length null is
made of. The 4 procedural ones do shorten, median 264 words, nominal p = 0.0068. The two results
are about different items.

---

## Manuscript rebuild

Restructured around two positive findings and one null: 3.1 brevity on the AAE track, 3.2
locale inference, 3.3 correctness null with glm-5.2 as a lead (nominal p = 0.024, 6 items worse
and 0 better, reported as neither promoted nor dismissed), 3.4 completeness, 3.5 register.

Methods now state: the endpoint URL; the three model strings and that the returned string was
checked against the requested one on all 936 calls; temperature 0.7 fixed; three generations per
prompt; independent contexts with no history; bare item text **and why** (an SAE-worded
instruction sits in both arms and dilutes the manipulation, and would fix the length and register
outcomes by fiat); rate-gated concurrent dispatch with the reason and the backend-replica note;
deepseek-v4-pro and qwen3.5 unavailability with attempt counts and timestamps; collection dates;
the blinded scoring procedure; and the AAE08 exclusion with both wordings quoted, the parse shift
shown, and the disclosure that the decision was taken after the item's results were seen.

Twelve numbered tables, all native Word tables built from `figures.json`, no images of tables.
Three figures embedded. British English, no em dashes, the display equation set as an equation.

---

## Figures

All three drawn at the 6.5 inch printed text width through the shared `figstyle.py`, using the
project's existing house palette from `paper/figures-src/figcommon.tex` (figblue #36597A against
figrust #B26839, colourblind-safe and separable in greyscale). `figstyle.py` did not exist; it
was created as the shared style module the instruction implies, matching the existing house style
rather than inventing one.

Every figure passes the label-overlap gate in `figstyle.save()`, which tests every text bounding
box against every other text bounding box and against every plotted line, densifying each line to
24 samples per segment so a long segment cannot skip through a label box. `save()` raises rather
than writing a figure with a detected collision.

| Figure | Content | Gate result |
|---|---|---|
| 1 `fig1_accuracy.pdf` | Per-model per-arm accuracy, binary and graded, grouped dot plot | 22 text boxes, 18 lines, **0 collisions** |
| 2 `fig2_aae_slope.pdf` | AAE track paired slope chart, one line per item | 17 text boxes, 57 lines, **0 collisions** |
| 3 `fig3_locale_split.pdf` | Indian English locale-sensitive against locale-invariant | 10 text boxes, 3 lines, **0 collisions** |

One change was made after visual inspection that the gate could not catch: in Figure 1 the
dialect marker is drawn as an open square rather than a filled one, because where the two arms
coincide exactly (gemma-4-31b, graded) a filled square hid the SAE circle entirely.

---

## Every figure that moved

| Figure | Was | Now |
|---|---|---|
| Title | "Dialect Bias in Large Language Models" | "Same Answer, Fewer Words: Brevity and Unsignalled Locale Inference..." |
| AAE direction split | 52 of 56 | 52 shorter, 4 longer, 1 tied, of 57 |
| AAE basis of claim | pooled count | three per-model Wilcoxon tests, W = 0.0 / 4.0 / 14.0 |
| Variance ratio (9 values) | reported as deciding effects | removed entirely |
| Step coverage | "not significant, p = 0.078" | underpowered; dz = 0.593; needs 23 pairs / 8 items |
| Locale finding | confound in a subsection of the length result | second finding, own subsection, own figure |
| Register | reported for the pooled comparison | all three models as family members, p = 1.00 / 0.75 / 0.32 |
| AAE08 framing | "second defective item" implied | convergent identification of one item in twenty |
| Passport example | "about 490" and "about 48" words | 452, 547, 486 (mean 495.0) and 49, 45, 49 (mean 47.7) |
| verify.py | 123 checks, step-coverage asserted p >= 0.05 | 92 checks, tie sums asserted, underpower asserted |

Unchanged: the correctness results (graded b = 9, c = 1, p = 0.0072 pooled; glm-5.2 p = 0.024,
b = 6, c = 0; collapsed b = 3, c = 1, p = 0.63), accuracy 455/459 against 442/459, the locale
classification, and the power table.

The check count fell from 123 to 92 because the 42 assertions covering the variance decomposition
were removed with it, and were replaced by 11 covering the tie sums, the underpower statement and
the per-model AAE prose figures.
