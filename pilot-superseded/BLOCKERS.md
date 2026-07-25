# BLOCKERS.md — what is still missing, and what it blocks

The six source files staged from `Downloads\research paper\` closed almost every gap identified in the
first pass. One true blocker remains, plus four items that are permanently unrecoverable and are now
disclosed in the manuscript rather than filled in.

## 1. TRUE BLOCKER — the repository

`[DATA NEEDED: repository URL and archival DOI]` in §5.

No repository exists. The abstract and the Conclusion promise release of the design, data and code, and
JHSS will expect a resolvable link. Until one exists:

- §5 carries the explicit `[DATA NEEDED]` marker naming the URL, the licence file and the DOI.
- The abstract and Conclusion are worded as intent ("we intend to release"), not as fact.

**To clear it:** create the repository (the six log files, the two prompt-set files, and `audit/verify.py`
are the complete contents), add an MIT LICENSE for the code and a CC BY 4.0 statement for the data,
archive a release to Zenodo, and send me the URL and the DOI. It is a ten-minute change once they exist.

## 2. Unrecoverable — disclosed, not filled

These cannot be reconstructed from anything on disk. Each is now stated in the manuscript as a gap.
None of them blocks submission; inventing any of them would.

**Per-session access dates.** Not recorded. §2.2 gives 1 July 2026, the date the log files were written,
as the closest honest bound and says individual session dates were not kept.

**A DeepSeek version string.** The web interface never displays one. §2.2 identifies Expert mode with
V4-Pro from DeepSeek's April 2026 release notes and labels this an inference, not a reading.

**Raw model response text.** `indian_english_dialect_items.xlsx` has its four model-answer columns
empty, and no response text exists anywhere in the workspace. Consequences: the spelling recount had to
be done from the per-item `DS_RegisterShiftWords` counts rather than by re-reading the responses (which
is sufficient — it tells us which responses contained at least one substitution, and that is exactly the
response-level unit the sign test needs); and the number of spelling-variant *opportunities* per response
is unknowable, so we cannot distinguish "no opportunity" from "opportunity not taken" among the four
concordant pairs. §3.2 says this. The sign test conditions on discordant pairs, so the p-value itself is
unaffected.

**The "how to" scoring rule and any evidence of blinding.** The scoring sheet records one correct-or-not
verdict per item and nothing about how the judgement was reached or how responses were presented to the
rater. Consequences: Supplementary S1 reproduces the eight step lists verbatim but states that per-step
credits and a pass threshold were never written down, and describes the applied rule as post-hoc; and
§2.3, Table 2 and §4.1 now say blinding was intended but cannot be demonstrated, rather than claiming it.

## 3. Resolved since the first pass

For the record, these were blockers and are no longer:

- per-arm accuracy for Table 3a — recovered; it is 100 per cent everywhere
- the response-level spelling recount — recovered from `DS_RegisterShiftWords`
- confirmation of 32 / 19 / 1-excluded / 52 / 51 / 102 / 0 discrepancies — recomputed from the sheets
- the three confidence bounds and every row of Table 4 — recomputed
- the "how to" checklist for Supplementary S1 — recovered from the `Gold_Answer` column
- how the prompts were actually delivered — recovered from the prompt-set files, and it contradicted
  what the draft claimed, so the draft was corrected

## 4. One thing to decide before submission

The manuscript now says, in §2.2 and again in §4.1, that the prompts were delivered as one interleaved
batch per track in a single chat session rather than one at a time. This is what the prompt-set files
show, and it is a weaker design than the earlier draft claimed. If your memory of the runs is that they
were in fact sent individually and the batch files were only a planning document, tell me and I will
correct it — but I have written what the files support, not what would look better.
