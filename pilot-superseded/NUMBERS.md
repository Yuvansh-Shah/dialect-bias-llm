# NUMBERS.md — every figure in the manuscript, with its source and its computation

Source logs (staged from the author's machine, `Downloads\research paper\`):

| Short name | File | Sheet used |
|---|---|---|
| IE sheet | `dialect_results_indian_english.xlsx` | `Indian English Comparison` (32 data rows) |
| AAE sheet | `dialect_combined_results.xlsx` | `AAE Results` (20 data rows) |
| AAE items | `aae_items.json` | 20 records (`row_idx`, `sae`, `aave`, `gold`) |
| IE items | `indian_english_dialect_items.xlsx` | `Item Set`, `README` |
| Prompt sets | `dialect_prompt_set.txt`, `aae_prompt_set.txt` | delivery format |

Recomputation script: `audit/verify.py`. Every figure below is printed by that script; nothing here is
taken from the earlier PDFs of the manuscript.

## 1. Item counts

| Quantity | Value | Computation |
|---|---|---|
| Indian English base items | 32 | row count of the IE sheet |
| — per task type | 8 / 8 / 8 / 8 | `Domain` counts: Factual QA, Arithmetic, Reading Comprehension, Procedural Guidance |
| AAE base items collected | 20 | row count of the AAE sheet |
| AAE items excluded | 1 (`RowIdx` 8) | `Excluded` flag on that row |
| AAE base items scored | 19 | 20 − 1 |
| Base prompts total | 52 | 32 + 20 |
| Base prompts scored | 51 | 32 + 19 |
| Scored item-pairs | 102 | 51 × 2 models |

The excluded item is the gingerbread/apple-pie question: both models answered 990 in both arms against
a gold answer of 540. Both models agreed with themselves across arms on it, so it is not a dialect
discrepancy; it is a faulty item, and it is excluded as such.

## 2. The headline null

| Quantity | Value | Computation |
|---|---|---|
| Pairs with a correctness discrepancy | 0 | see below |

IE sheet: `DS_Correct(Y/N)` = Y on all 32 rows; `Gem_Correct(Y/N)` = Y on all 32 rows. That sheet
records one correctness verdict per question per model, entered as identical for the two arms.

AAE sheet, 19 scored rows: `DS_Correct` = Y ×19, `Gem_Correct` = Y ×19, `DS_A_eq_B` = Y ×19,
`Gem_A_eq_B` = Y ×19. Correct in both arms and the two arms agree, on every scored row, for both models.

Hence 0 discrepancies out of 102 pairs, and per-arm accuracy is 100 per cent in every cell of Table 3a.

## 3. Table 3a (per-arm absolute accuracy)

All ten cells are 100 per cent, derived directly from §2 above: 8/8 for each of the four IE task types
for each model in each arm, and 19/19 for the AAE track for each model in each arm.

This is a ceiling result and the manuscript says so without softening it (§3.1a, Discussion, §4.1).

## 4. Confidence bounds

Clopper–Pearson exact one-sided 95 per cent upper bound with zero events: `p_upper = 1 − 0.05^(1/n)`.

| Track | n | Bound | Value |
|---|---|---|---|
| Indian English | 32 | 1 − 0.05^(1/32) | 8.9368% → reported as 8.9% |
| African American English | 19 | 1 − 0.05^(1/19) | 14.5869% → reported as 14.6% |
| Pooled | 51 | 1 − 0.05^(1/51) | 5.7048% → reported as 5.7% |

These are three separate one-sided quantities, not a range. The pooled figure assumes a single common
error rate across both dialects, which the data cannot test; §3.1 says so.

n = 51, not 102, because the bound is on the per-item quality-gap rate and the two models are not
independent replicates of the same item.

## 5. The spelling finding (recounted at response level)

From the IE sheet, `DS_RegisterShiftWords` is non-zero on four rows only: BaseID 25 → 8, 26 → 1,
29 → 2, 32 → 1. Total 12 words. All four rows are Procedural Guidance items. `Gem_RegisterShiftWords`
is 0 on all 32 rows.

| Quantity | Value | Computation |
|---|---|---|
| Paired "how to" items | 8 | `Domain` = Procedural Guidance |
| Responses with ≥1 substitution towards British (b) | 4 | rows 25, 26, 29, 32 |
| Responses with a substitution in the other direction (c) | 0 | the log records none in either arm |
| Concordant pairs | 4 | 8 − 4 |
| Exact sign test / McNemar, b=4, c=0 | two-sided p = 0.125 | 2 × 0.5^4 |
| | one-sided p = 0.0625 | 0.5^4 |

**Withdrawn:** the previous figure p = 4.9 × 10⁻⁴ was `binom(12, 12, 0.5)` two-sided = 0.00048828125,
i.e. 12 words treated as 12 independent fair-coin tosses. Both halves are wrong: 8 of the 12 words fall
inside a single response, and the comparator is DeepSeek's own SAE answer, not a coin. The finding is
reported as weakened, not significant at the response level, and suggestive only.

Ceiling on this design: even b=8, c=0 would give only two-sided p = 0.0078.

**Not in the log:** the number of spelling-variant *opportunities* per response. The sign test conditions
on discordant pairs only, so the p-value is unaffected, but we cannot say whether the four concordant
pairs had no opportunity or had one and did not take it. The manuscript states this (§3.2).

## 6. Table 4 (simulation / power)

`n = ceil( ln(1 − 0.80) / ln(1 − π) )`, the sample size at which P(≥1 error) = 1 − (1 − π)^n reaches 0.80.

| π | n | recomputed |
|---|---|---|
| 1% | 161 | ✓ |
| 2% | 80 | ✓ |
| 3% | 53 | ✓ |
| 5% | 32 | ✓ |
| 10% | 16 | ✓ |
| 20% | 8 | ✓ |

Every row of Table 4 as printed in the manuscript matches.

## 7. Figures not derivable from the logs

- **Repository URL, licence file, archival DOI** — no repository exists. Flagged in §5 and in BLOCKERS.md.
- **Per-session dates** — not recorded. §2.2 gives the file-write date (1 July 2026) as the closest
  honest bound and says explicitly that individual session dates were not kept.
- **DeepSeek version string** — never shown in the web interface. §2.2 states that the V4-Pro
  identification comes from DeepSeek's April 2026 release notes, not from anything on screen.
- **Per-step scoring credits and the pre-specified pass threshold for "how to" items** — not recorded.
  Supplementary S1 says so.
- **Evidence that the "how to" scoring was blind** — no record kept. §2.3, Table 2 and §4.1 no longer
  claim blinding was achieved, only that it was intended.
