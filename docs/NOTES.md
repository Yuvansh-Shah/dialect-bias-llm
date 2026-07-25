# Note on what looks wrong or surprising in this data

Eight things are worth your attention. The first three are about the run, the rest are about
the results.

## 1. items.csv did not exist

The brief names `items.csv` as the input. It was not in the project folder, not in uploads,
and not anywhere I could reach. I stopped rather than invent an item set, and with your
approval rebuilt it from the two original sources in `Downloads\research paper\`: the 32-item
Indian English sheet and the 20-item AAE JSON. Provenance is in `run_log.md` section 7. If
you have a canonical `items.csv` somewhere I did not look, the whole run should be redone
against it, because item identity is the one thing that cannot be checked after the fact.

## 2. The NVIDIA model listing advertises models that are not served

Five of the models we tried are listed by `/v1/models` but do not answer. `deepseek-v4-pro`
times out at the gateway after about 300 seconds, `deepseek-v4-flash` returns service
unavailable, and `qwen3.5-397b-a17b`, `mistral-large-2-instruct` and `kimi-k2.6` return an
instant 404. This is why you could not have the DeepSeek continuity slate. Worth knowing
before planning a follow-up: the listing is not a availability guarantee, and any model should
be probed before a study is designed around it.

## 3. The endpoint degraded badly mid-run, and glm-5.2 returns transient 404s

An identical call took 34 seconds at 09:45 and 99 seconds at 10:28. There were 469 gateway
timeouts and 160 rate-limit responses across the run. Separately, `z-ai/glm-5.2` intermittently
returns 404 while demonstrably alive minutes either side. My first collector treated 404 as
fatal and lost 12 calls to this; they were all recovered on retry. If you rerun this, treat
404 as transient for that model.

## 4. The headline result of the earlier draft does not reproduce, and the new headline is length

The pilot reported 100 per cent accuracy everywhere and zero discordant pairs. Here accuracy
is 98.08 per cent in the SAE arm and 94.66 per cent in the dialect arm, with 6 discordant
pairs out of 156. The correctness comparison is still null, p = 0.22, and the variance
decomposition shows why it should be treated as null: for all three models the between-arm
difference in correctness is smaller than the model's own variation across three identical
calls.

The real finding is length. Dialect answers are shorter in 105 of 156 matched pairs, with a
pooled Wilcoxon p of 1.45 x 10^-8. Nothing in the earlier design could have seen this, because
length was never measured.

## 5. The length effect is wildly uneven, and one case is extreme

The median pooled difference is 9.5 words but the mean is 52.6, which tells you it is a small
difference on most items and an enormous one on a few. On procedural guidance the median
difference is 277 words. The clearest single case: asked in SAE how to renew a passport,
llama-3.3-70b gives about 490 words covering eligibility, the specific form, documents and
fees. Asked the matched Indian English question, it gives a bare numbered list of about 48
words. Both are scored correct, because both contain the required steps. Accuracy scoring
cannot see this at all.

## 6. The models appear to change country, not just length

This one I was not looking for. The SAE passport answer describes the United States process
and names a US form; the Indian English answer describes the Indian process and mentions
police verification. Counting country-specific terms across the Indian English track, the
direction is the same for all three models: more India-specific terms in the dialect arm, more
US-specific terms in the SAE arm. The counts are small and this was found after the fact, so
the manuscript reports it without a p-value, in section 3.5. I think it is the most promising
thing in the dataset for a follow-up, because it suggests a mechanism: the model may be
inferring a locale from the dialect and then answering a slightly different question.

## 7. The spelling finding does not replicate, and one model leans the other way

The pilot's side finding was that a model shifted towards British spelling on the dialect arm.
Pooled here it is 4 items against 1, p = 0.375. gemma-4-31b actually used Commonwealth forms
more often in the SAE arm than the dialect arm, which is the opposite direction. Caveat that
matters: DeepSeek, the model that produced the original observation, could not be reached, so
this is not a direct refutation. It does mean the effect is not general.

## 8. Two defects I introduced and caught, and one item you should look at

I want these on the record rather than buried.

**Scoring defect.** Item IE07, gold answer `Au`, scored 0 out of 18. Every model had in fact
answered correctly. My span scorer dropped tokens of two characters or fewer when building its
keyword list, so a two-letter gold answer produced an empty list and returned zero before the
exact-match test ran. Fixed, and the fix is arm-blind. It moved SAE accuracy from 96.15 to
98.08 per cent and dialect accuracy from 92.74 to 94.66. It did not move any paired test,
because the item was wrong in both arms and therefore concordant either way.

**Counting defect.** I first reported 113 of 156 pairs as having the shorter answer in the
dialect arm. That was n minus the number of longer pairs, which silently counts the 8 exactly
tied pairs as shorter. The correct split is 105 shorter, 43 longer, 8 tied. The manuscript now
gives all three numbers.

Both were caught by `verify.py`, which recomputes the length result from the raw log without
reusing the analysis code. It now runs 73 checks and all pass.

**AAE08.** The gingerbread and apple pie item, gold answer 540, which the earlier run excluded
as faulty. I did not exclude it, on the principle that an exclusion should be a finding rather
than an assumption. It is the second-worst item in the set at 5 correct out of 18, and it
supplies 2 of the 5 discordant pairs that go against the dialect arm. Two further discordant
pairs come from IE21. So 4 of the 5 pairs behind the correctness result come from just two
items. The correctness null does not depend on this, but if that comparison ever becomes
significant in a larger run, check those items first. The item does look genuinely hard rather
than broken: models disagree with themselves across repeats, not just across arms.
