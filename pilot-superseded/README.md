# pilot-superseded

**These files are not this study's data. Do not analyse them as if they were.**

They come from a June 2026 pilot by the same author, which the study in this
repository replaces. They are included because the manuscript's contradictions
section (4.2) reports specific pilot figures, and a reader checking those claims
needs to see where they came from.

## Why the pilot's data is not used

The pilot reached two models through their **public chat websites**, not through
a programming interface. Three consequences, all of which the present study
exists to fix:

1. **The prompts were delivered as one numbered batch per track inside a single
   chat session**, not one at a time. `dialect_prompt_set.txt` and
   `aae_prompt_set.txt` in this folder are those batch files, and they show the
   delivery method directly. Every item in a track shared one context, so a
   model could in principle notice that the questions came in matched pairs. The
   instructions told each model to treat every item independently; there is no
   way to verify that it did.

2. **One generation per prompt.** With a single response per item there is no
   way to separate a dialect effect from ordinary run-to-run variation. The
   present study generates three.

3. **No control or record of sampling temperature.** The chat interfaces do not
   expose it. The present study fixes it at 0.7 and records it with every call.

The pilot also kept no record of its scoring procedure, so its stated blinding
could not be demonstrated. The present study scores by program with the arm
withheld, and the procedure can be re-run.

## What is here

| File | What it is |
|---|---|
| `NUMBERS.md` | The pilot's own audit of every figure it reported, with the computation for each. The source of the pilot numbers quoted in manuscript section 4.2. |
| `BLOCKERS.md` | The pilot's record of what it could not recover, including that no raw model response text was ever kept. |
| `dialect_prompt_set.txt` | The Indian English batch as delivered, showing the interleaved single-session format. |
| `aae_prompt_set.txt` | The African American English batch, same. |

## Which pilot claims survived

Reported in full in `docs/CHANGES3.md` and manuscript section 4.2. In short: the
correctness null survived but for a different reason; the 100 per cent accuracy
figure did not; the zero-event confidence bounds did not apply; and the spelling
register finding did not replicate, with the caveat that the model which
produced it could not be reached.

One thing the pilot got right and this study confirms independently: item AAE08
is defective. The pilot excluded it because both its models answered 990 against
a gold of 540. This study reached the same item from a different direction and
diagnosed the cause. See `NOTICE` and `docs/analysis.md` section 1.

## Raw pilot responses

There are none. The pilot's own `BLOCKERS.md` records that the model-answer
columns of its item sheet were left empty and no response text exists anywhere.
That is a large part of why the study was rebuilt rather than extended.
