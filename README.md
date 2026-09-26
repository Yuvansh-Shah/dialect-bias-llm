# dialect-bias-llm

Three large language models were asked the same 52 questions twice: once in Standard American
English and once in an English dialect with the same meaning and the same correct answer, three
times each, in 936 independent API calls. On items whose answer cannot depend on where the user
lives, all three models returned the same answers in materially fewer words. On the four items
whose answer does depend on jurisdiction, the dialect wording produced a much shorter answer
describing a different country's procedure, with nothing in the response to signal that a
jurisdiction had been assumed.

Manuscript: `docs/ShahDialectBiasLLM.doc`. Full statistics: `docs/analysis.md`.

## Reproduction

Requires Python 3.11+ and an NVIDIA API key from https://build.nvidia.com.

```bash
git clone https://github.com/Yuvansh-Shah/dialect-bias-llm.git
cd dialect-bias-llm
python3 -m pip install numpy scipy matplotlib python-docx openpyxl
```

The key is read from the environment and is never written to disk, logged, or committed:

```bash
export NVIDIA_API_KEY=your-key-here
```

Then, in order:

```bash
python3 analysis/run_experiment.py     # 936 calls; ~3 hours; appends to data/raw_responses.jsonl
python3 analysis/score_responses.py    # writes data/scores.csv, blind to arm
python3 analysis/analyse.py            # writes analysis/figures.json and docs/analysis.md
python3 analysis/make_figures.py       # writes the three PDFs in figures/
python3 analysis/verify.py             # 92 checks; must report 0 failures
```

`run_experiment.py` checkpoints. If it is interrupted, run it again and it skips every
`(item_id, arm, model, rep)` already collected successfully. To reproduce the analysis without
re-collecting, skip the first step: `data/raw_responses.jsonl` is committed.

`verify.py` recomputes the headline results directly from `data/raw_responses.jsonl` without
reusing `analyse.py`, so it is an independent check rather than a restatement.

## Files

| File | Contents |
|---|---|
| `README.md` | This file. |
| `LICENSE` | MIT Licence. Covers everything under `analysis/`. |
| `LICENSE-DATA` | CC BY 4.0 notice. Covers the items, data, figures and docs. |
| `NOTICE` | Third-party attribution for the ReDial AAE items, and their stated scope of use. |
| `CITATION.cff` | Machine-readable citation metadata. |
| `.gitignore` | Excludes credential files, collection scratch, and Python artefacts. |
| `items/items.csv` | 104 rows: 52 base items x 2 arms. Columns: item_id, domain, arm, prompt, gold_answer, dialect_features. Pre-randomised row order; process in file order. |
| `items/item_locale_classification.csv` | Every item classified locale-sensitive or locale-invariant, with a one-line reason each. Classification rule fixed before the split analysis was run. |
| `items/locale_sensitive_hand_coding.csv` | Hand coding of the 72 responses to the four locale-sensitive items (IE26, IE27, IE28, IE32): jurisdiction of the content (US, India, mixed, generic) and disclosure of the assumed jurisdiction (explicit, hedge, none). Definitions in the file header and in the CJSJ manuscript. |
| `items/arm_mapping.csv` | Which of arm A / arm B is the SAE wording, per item. Not consulted during collection or scoring. |
| `items/sources/aae_items.json` | The 20 ReDial-derived AAE items as received. See `NOTICE`. |
| `items/sources/indian_english_dialect_items.xlsx` | The 32 author-written Indian English items, with the feature used in each. |
| `data/raw_responses.jsonl` | Every API call, verbatim. 971 records covering 936 unique cells; the 35 extra are failed attempts retained as an audit trail and superseded by later successes. One JSON object per call. |
| `data/scores.csv` | Per-response scores. Header documents the blinding procedure. |
| `analysis/run_experiment.py` | Collection. One call per prompt, no history, no system prompt, temperature 0.7, three repeats, rate-gated concurrency, exponential backoff, checkpoint and resume. |
| `analysis/score_responses.py` | Scoring, with the arm withheld from every scoring function. Correctness, step coverage, length, register with an opportunity denominator. |
| `analysis/classify_locale.py` | Builds `items/item_locale_classification.csv` from the stated rule. |
| `analysis/analyse.py` | All statistics. Writes `figures.json` and `docs/analysis.md`. |
| `analysis/figstyle.py` | Shared figure style and the label-overlap gate, which refuses to save a figure with a detected text collision. |
| `analysis/make_figures.py` | The three figures. |
| `analysis/verify.py` | 92 independent checks over the raw data, the figures file and the manuscript. |
| `analysis/figures.json` | Every number in the manuscript, keyed by computation. |
| `docs/analysis.md` | The full statistics with n, method, statistic and p for every test. |
| `docs/run_log.md` | Model strings, temperature, dates, call counts, failures, rate-limit events. No credentials. |
| `docs/CHANGES2.md` | Defects found in the first analysis of this data, and what moved. |
| `docs/CHANGES3.md` | Defects found in the second analysis, and what moved. |
| `docs/NOTES.md` | Things in the data that look wrong or surprising. |
| `docs/ShahDialectBiasLLM.doc` | The manuscript. |
| `docs/ShahDialectBiasLLM.docx` | Same, in the format `verify.py` reads. |
| `figures/fig1_accuracy.pdf` | Per-model per-arm accuracy, binary and graded. |
| `figures/fig2_aae_slope.pdf` | Paired slopes for every AAE item. |
| `figures/fig3_locale_split.pdf` | Indian English, locale-sensitive against locale-invariant. |
| `pilot-superseded/` | The June 2026 pilot's audit files. Not this study's data; see the README in that folder. |

## Main result

Response length on the African American English track: 19 jurisdiction-free, speaker-validated
items, one Wilcoxon signed-rank test per model. The family-wise threshold is 0.05/9 = 0.0056,
correcting for three models by three outcomes.

| Model | n items | Median difference (words) | W | p | shorter / longer / tied | Clears threshold |
|---|---|---|---|---|---|---|
| `gemma-4-31b` | 19 | -17.67 | 0.0 | 0.0002 | 18 / 0 / 1 | yes |
| `llama-3.3-70b` | 19 | -27.67 | 4.0 | 2.7e-05 | 18 / 1 / 0 | yes |
| `glm-5.2` | 19 | -18.67 | 14.0 | 0.00042 | 16 / 3 / 0 | yes |

Pooled, 52 shorter, 4 longer and 1 tied of 57 item-by-model pairs. That pooled count is
descriptive only: it counts the same 19 items three times, so no test rests on it.

## Known defects

**This section is the point of the repository, not a disclaimer.** Five defects were found in
this work, four of them in our own analysis, and all four were found by the verification script
rather than by review. Full accounts in [`docs/CHANGES2.md`](docs/CHANGES2.md) and
[`docs/CHANGES3.md`](docs/CHANGES3.md).

1. **The `content_words` scoring bug.** The span scorer dropped tokens of two characters or
   fewer when building its keyword list, and returned zero before the exact-match test ran. Item
   IE07, gold answer `Au`, scored 0 out of 18 when every model had answered correctly. Fixing it
   moved SAE accuracy from 96.15 to 98.08 per cent and dialect accuracy from 92.74 to 94.66.
   ([CHANGES2](docs/CHANGES2.md))

2. **The tie-counting defect, which occurred twice.** The number of pairs where the dialect
   answer was shorter was computed as the total minus the number of longer pairs, silently
   counting tied pairs as shorter. First occurrence: 105 shorter reported as 113, and 67 per
   cent as 72. Second occurrence, after the first was fixed: the AAE track reported as "52 of
   56" when 19 items and 3 models give 57 pairs, 52 shorter, 4 longer, 1 tied. `verify.py` now
   asserts the direction counts sum to n. ([CHANGES2](docs/CHANGES2.md),
   [CHANGES3](docs/CHANGES3.md))

3. **The repeat-collapsing rule was undisclosed and it produced the null.** Three repeats per
   cell were reduced to one verdict by majority vote without that being stated. Majority voting
   moves the pooled correctness p from 0.0072 to 0.22, and `glm-5.2` from 0.024 to 0.25, because
   a cell falling from 3 correct of 3 to 2 of 3 registers as no change. Both reductions are now
   reported side by side. ([CHANGES3](docs/CHANGES3.md))

4. **The abandoned variance ratio.** Two drafts compared the between-arm difference against the
   standard deviation of a single response and treated the ratio as though it decided whether an
   effect existed. It is not a test: the difference is a mean over items. At one point it set a
   difference in percentage points beside a standard deviation in proportion units and concluded
   an effect had vanished. It contradicted the signed-rank result in both directions, and it has
   been withdrawn entirely rather than reported and set aside. ([CHANGES3](docs/CHANGES3.md))

5. **The register non-replication.** The June pilot reported one model shifting towards British
   spelling on the dialect arm, in 4 of 8 pairs and none the other way. It does not replicate
   here: 4 items against 1 pooled, p = 0.375, and no model reaches significance. This is **not a
   direct refutation**, because `deepseek-v4-pro`, the model that produced the original
   observation, was unreachable throughout the collection window. What these data establish is
   the narrower claim that the effect is not general. ([CHANGES3](docs/CHANGES3.md))

One further limit worth stating with the defects. The completeness measure, step coverage on
procedural items, points consistently downwards in the dialect arm, 0.879 against 0.941 with 6
of 12 pairs worse and 1 better, at p = 0.078. That is underpowered, not null. Detecting an
effect of the observed size at 80 per cent power needs about 23 paired observations, which is 8
items; we have 12 pairs and 4 items. The manuscript therefore declines both to claim that
shorter answers are less complete and to claim that the arms are equally complete.

## Model availability

Five models listed by the endpoint's own `/v1/models` were not served. This is recorded because
it determined which models the study could use, and because it means this study shares no model
with the June pilot. All attempts on 25 July 2026 (UTC).

| Model | Attempts | Result | Times |
|---|---|---|---|
| `deepseek-ai/deepseek-v4-pro` | 3 | HTTP 504 Gateway Timeout after ~300 s each | 09:10, 09:38 (x2) |
| `deepseek-ai/deepseek-v4-flash` | 1 | HTTP 503 Service Unavailable, immediate | 09:38 |
| `qwen/qwen3.5-397b-a17b` | 3 | HTTP 404 Not Found, immediate | 09:38, and twice immediately before collection |
| `mistralai/mistral-large-2-instruct` | 1 | HTTP 404 Not Found, immediate | 09:38 |
| `moonshotai/kimi-k2.6` | 1 | HTTP 404 Not Found, immediate | 09:38 |

The three models used were `google/gemma-4-31b-it`, `meta/llama-3.3-70b-instruct` and
`z-ai/glm-5.2`. The model string returned by the API was compared against the string requested on
all 936 calls and matched every time. The service degraded during collection: 469 gateway
timeouts, 160 rate-limit responses and 32 service-unavailable responses, all retried and all
recovered. Details in [`docs/run_log.md`](docs/run_log.md).

## Licences

Two, covering different things.

- **Code**, everything under `analysis/`: MIT Licence, see [`LICENSE`](LICENSE).
- **Data**, the items, responses, scores, figures and documents: Creative Commons Attribution
  4.0 International, see [`LICENSE-DATA`](LICENSE-DATA).

The African American English items are third-party material from the ReDial dataset, released by
its authors under the MIT Licence and redistributed here with attribution. Their citation, the
basis for the licence determination, and their stated scope of use are in [`NOTICE`](NOTICE).
Read it before reusing those items.

## Citation

See [`CITATION.cff`](CITATION.cff). Please also cite the ReDial paper if you use the AAE items.

Archived on Zenodo. The DOI below is the concept DOI, which always resolves to the most recent
archived version:

**https://doi.org/10.5281/zenodo.21566323**

The version-specific DOI for a given release is listed on that record. Release v1.0.0 is
archived at https://doi.org/10.5281/zenodo.21566324.

```
Shah, Y. (2026). Same Answer, Fewer Words: brevity and unsignalled locale inference in
language model responses to English dialects. Zenodo.
https://doi.org/10.5281/zenodo.21566323
```

Please also cite the ReDial paper if you use the African American English items; see
[`NOTICE`](NOTICE).
