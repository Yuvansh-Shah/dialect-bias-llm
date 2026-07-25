# run_log.md — collection run record

No credential appears in this file, in any script in this directory, or in any deliverable.
The API key was held in a file outside the project tree, read at runtime into memory only,
and never written to a log, a record, a printed line or a source file.

## 1. Endpoint and models

Endpoint: `https://integrate.api.nvidia.com/v1/chat/completions` (NVIDIA build.nvidia.com).

The available model list was queried from `/v1/models` before collection began and returned
118 model identifiers. Three models from three different labs were selected and confirmed
with the author before any collection call was made.

| Role | Exact model string | Lab | Responses collected |
|---|---|---|---|
| Model 1 | `google/gemma-4-31b-it` | Google | 312 |
| Model 2 | `meta/llama-3.3-70b-instruct` | Meta | 312 |
| Model 3 | `z-ai/glm-5.2` | Zhipu AI (Z.ai) | 312 |

The `model` field returned by the API matched the requested string on all 936 successful
calls. No call was silently served by a different model.

### Models that were selected first and could not be used

The author's first choice was a continuity slate of `deepseek-ai/deepseek-v4-pro`,
`google/gemma-4-31b-it` and `meta/llama-3.3-70b-instruct`, to match the DeepSeek and Google
models used in the previous run. DeepSeek could not be used:

- `deepseek-ai/deepseek-v4-pro` returned HTTP 504 Gateway Timeout on all three probe attempts,
  each after roughly 300 seconds.
- `deepseek-ai/deepseek-v4-flash` returned HTTP 503 Service Unavailable.

The author then nominated `qwen/qwen3.5-397b-a17b`, with `z-ai/glm-5.2` as a fallback.
`qwen/qwen3.5-397b-a17b` returned HTTP 404 Not Found instantly on every attempt, as did
`mistralai/mistral-large-2-instruct` and `moonshotai/kimi-k2.6`: these identifiers appear in
the `/v1/models` listing but were not served. The fallback, `z-ai/glm-5.2`, was verified
working and was used.

## 2. Collection parameters

| Parameter | Value |
|---|---|
| Temperature | 0.7, fixed, identical on every call |
| max_tokens | 4096 |
| Repeats per prompt per model | 3 |
| Messages per call | exactly one user message |
| System prompt | none |
| Conversation history | none; every call an independent context |
| Prompt content | the bare item text from `items.csv`, nothing added, identical treatment in both arms |

Temperature 0.7 was chosen deliberately and not left at 0. The three repeats exist to
measure within-arm sampling variance. At temperature 0 the repeats would be near-identical,
within-arm variance would collapse towards zero, and any between-arm difference would clear
that noise floor by construction. The author confirmed this choice before collection.

## 3. Dates

All collection took place on 25 July 2026 (UTC).

- First call recorded: 2026-07-25T09:45:07Z
- Last call recorded: 2026-07-25T12:44:35Z
- Wall-clock span: 2 hours 59 minutes

## 4. Call counts

| Quantity | Value |
|---|---|
| Item-arm rows in `items.csv` | 104 (52 base items x 2 arms) |
| Cells required (row x model x repeat) | 936 |
| Cells with a successful response | 936 |
| Cells with no response | 0 |
| Total records written to `raw_responses.jsonl` | 971 |
| Records that are failed attempts, superseded by a later success | 35 |
| Responses truncated at the token cap | 0 (every finish_reason was `stop`) |
| Total tokens billed across successful calls | 232,703 |

`raw_responses.jsonl` holds every call, including the 35 that failed and were later retried
successfully. Scoring deduplicates on (item_id, arm, model, rep) and prefers the successful
record, so each of the 936 cells is scored exactly once. The failed records are retained
deliberately as the audit trail; they are not scored twice and they are not discarded.

Attempts needed per successful call: 1 attempt 576, 2 attempts 217, 3 attempts 65,
4 attempts 46, 5 attempts 32.

## 5. Rate limiting, retries and failures

Rate limit applied: the author advised a 40 requests per minute ceiling. A global token gate
spaced every request, including retries, so that no more than 40 requests were issued in any
minute. On any 429 or 5xx the call was retried with exponential backoff starting at 30
seconds, to a maximum of 5 attempts, after which the call was recorded as failed and
collection continued.

HTTP faults observed during the run:

| Fault | Occurrences |
|---|---|
| HTTP 504 Gateway Timeout | 469 |
| HTTP 429 Too Many Requests | 160 |
| HTTP 503 Service Unavailable | 32 |
| Backoff events in total | 835 |

The endpoint degraded substantially during the run. An isolated single call that completed
in 34 seconds at 09:45 took 99 seconds at 10:28 for the same model and a shorter prompt.
This is recorded because it affected throughput and retry counts. It does not affect the
responses themselves: every scored response is a complete generation with finish_reason
`stop`.

### Deviations from the brief, and why

1. **Requests were issued concurrently rather than strictly one at a time.** The brief
   specified sleeping at least 6.5 seconds between calls, which assumes serial issuance. At
   the observed per-call latency of 60 to 200 seconds, serial issuance would have taken over
   20 hours. Requests were instead issued on a rate-gated schedule with a bounded number in
   flight, never exceeding the stated 40 per minute. Concurrency does not affect the
   independence of any call: each remains a separate HTTP request with a single user message,
   no system prompt and no history.

2. **HTTP 404 was treated as retryable.** `z-ai/glm-5.2` returned intermittent 404s during
   the run while demonstrably live minutes earlier and later. Treating 404 as fatal, as the
   first version of the collector did, lost 12 calls. Those calls were retried and all
   succeeded. Every 404 in the final dataset was recovered.

3. **The run was restarted five times** to retune concurrency and to fix the two faults
   above. Restarts resume from the checkpoint and skip any cell already collected
   successfully, so no cell was collected twice and no cell was lost.

## 6. Exclusions

No model, item, response or call has been excluded from the analysis.

The one item flagged as faulty in the previous run, the AAE gingerbread and apple pie
problem (`AAE08`, gold answer 540), was collected and scored on the same footing as every
other item. It was not excluded. Whether it behaves anomalously is now a question the data
can answer rather than an assumption applied beforehand.

## 7. Provenance of the item set

`items.csv` was not supplied with the brief and did not exist in the project workspace. It
was rebuilt, with the author's approval, from the two original item sources on the author's
machine:

- `indian_english_dialect_items.xlsx`, sheet `Item Set` — 32 Indian English base items with
  domain, SAE wording, Indian English wording, features used and gold answer.
- `aae_items.json` — 20 African American English base items with SAE wording, AAE wording
  and gold answer.

Total 52 base items, 104 item-arm rows. Arm labels A and B were assigned per item by a
seeded random draw (seed 20260725), so that the SAE version is arm A for 30 of the 52 items
and arm B for the other 22. Row order was then shuffled with the same seed, so the file is
pre-randomised and was processed in file order. The mapping from arm to condition is held in
`arm_key.csv` and was not consulted during collection or during scoring.

## 8. Scoring correction made during verification

One scoring defect was found by the verification pass and fixed before the final numbers were
produced. It is recorded here because it changed published figures.

Item IE07 asks for the chemical symbol for gold, gold answer `Au`. It scored 0 out of 18
across all three models and both arms. Inspection of the raw responses showed every model
answered `Au` correctly. The cause was in `score.py`: the span scorer built a keyword list by
dropping tokens of two characters or fewer, so a two-letter gold answer produced an empty
keyword list, and the empty-list guard returned zero before the exact-match test was ever
reached.

The fix moves the exact-match test in front of the keyword test and matches on word
boundaries rather than raw substrings, so a gold answer of `au` is not satisfied by the `au`
inside `because`. IE07 is the only item in the set with a gold answer short enough to hit
this path.

The correction is arm-blind: it is a property of the gold answer, not of the wording, and it
applied identically to both arms of the pair. Effect on the reported figures:

| Figure | Before fix | After fix |
|---|---|---|
| SAE pooled accuracy | 450/468, 96.15 per cent | 459/468, 98.08 per cent |
| Dialect pooled accuracy | 434/468, 92.74 per cent | 443/468, 94.66 per cent |
| Cells at 100 per cent | 7 of 24 | 10 of 24 |
| McNemar b, c, p | 5, 1, 0.219 | unchanged |
| Length results | unchanged | unchanged |
| Register results | unchanged | unchanged |

The paired tests are unchanged because IE07 was scored wrong in both arms, so it was
concordant before the fix and concordant after it.

A second defect was found in the same pass. The count of pairs where the dialect answer was
shorter had been computed as n minus the number of longer pairs, which silently counts the 8
exactly tied pairs as shorter. The correct figures are 105 shorter, 43 longer and 8 tied, and
the manuscript now reports all three rather than a single share.

## 9. Verification

`verify.py` runs 73 checks and all pass. It recomputes the length result directly from
`raw_responses.jsonl` without reusing `analyse.py`, checks that every scored cell has a
successful record, that the blind key reproduces the documented hash, that `scores_blind.csv`
has no arm column, that the manuscript contains no em dashes and no stray American spellings,
that each per-model figure quoted in the prose matches `figures.json`, and that no API key
prefix appears in any file in the run directory.
