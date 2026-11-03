# Fresh AI usability study — 25 October 2026

One hundred new fictional questions were authored and labeled before inference: 30 labor, 30 consumer, 10 fully mixed, 15 supported-plus-excluded mixed, and 15 outside scope. English, Taglish and noisy typing are included. Exact duplicate checking covered 1,760 earlier saved input rows. Topics necessarily overlap earlier studies; semantic novelty was not independently judged.

This is an AI-authored development diagnostic. The first pass is preserved separately from all inspected repair rechecks. No question or expected label was edited after inference. These are not human-written gold questions or a legal-accuracy study.

## Full 100-question observations

| Check | Initial stack | Repaired full run |
|---|---:|---:|
| Topic label match | 85/100 | 100/100 |
| Scope label match | 88/100 | 100/100 |
| Route match | 81/100 | 100/100 |
| Supported-domain coverage | 83/100 | 100/100 |
| Outside-only questions admitted to retrieval | 3/15 | 0/15 |
| Full AI explanations | 53 | 59 |
| Partial AI explanations | 6 | 9 |
| Withheld AI explanations | 41 | 32 |
| Application errors | 0 | 0 |
| Median / p95 whole-query time | 6.5s / 18.5s | 7.6s / 19.3s |

All 15 excluded-only questions appropriately had no provider-generated legal explanation in the repaired full run. Of the 85 questions with an in-scope concern, 68 received a full or partial AI explanation. Withholding also reflects missing/held authority, failed content checks, and one provider-incomplete response. A source gap is not counted as a legally correct answer.

The first full run used classifier 1.5.58 / retrieval 1.3.49 / verifier 1.0.56; the repaired full run used 1.5.60 / 1.3.50 / 1.0.57. That full repaired run was followed by 17 targeted observations and one final closure-condition check on the selected 1.5.61 / 1.3.51 / 1.0.58 stack. The final 100-question local classifier replay also matched all frozen labels and routes. The targeted observations do not replace the full-run results or constitute a fresh holdout.

## Repairs

- Current concerns introduced with “unrelated” are retained; comma-enumerated labor, retail and excluded concerns remain separate.
- Private-employment, harvest/seasonal, security-of-tenure, hyphenated overseas-worker, tax, privacy, inheritance and prediction wording is handled more consistently. Original numbers, literals and question text are retained.
- Phonetic/boundary features preserve ordinary words such as printer, pot and badly while retaining tested shorthand repairs. The LLM normalizer still runs only when local understanding fails; the repaired full batch was understood locally and correctly bypassed wording calls.
- Same-scenario requests, coordinate subjects and work-schedule context no longer produce several of the observed duplicate/irrelevant components.
- Retrieval better distinguishes wage deductions, closure, security of tenure, paid service quality, replacement-parts obligations, refurbished-as-new sales, platform redress and source gaps. The broad service focus initially lost two known-relevant replacement-parts hits; regression v1.6.28 exposed that error and v1.6.29 checks the correction.
- Explanation checks preserve payroll versus individual-payslip obligations, retailer versus distributor duties, return conditions, manufacturer defenses, and closure notice/separation-pay conditions. Valid “opt for” return wording is accepted without removing the choice condition.
- Numeric correction feedback identifies unsupported quantities; paragraphs are instructed to leave article/section identifiers to citation fields. Complex support checks have a larger bounded output allowance after an observed truncated support response. Request deadlines, cancellation and the single content-correction limit remain active.

Atomic classifier weights, feature vocabulary, training membership and thresholds remain inherited. Calibration was refreshed using original training folds only. No diagnostic question was fitted. Canonical source text, source eligibility holds and legal approval gates were not changed.

## Broader verification

- 273 backend tests passed, 31 frontend tests passed, and the frontend production build passed.
- 36 focused concern regressions passed. Packaging also passed 69 classifier, 60 retrieval and 37 verifier checks; these overlap other suites and are not a combined unique-test count.
- Final local regression: 436 input forms, 425 labeled; topic and scope 425/425 each; route 432/436; zero admissions among 80 excluded inputs.
- Known-relevant Hit@5: 93/93. Exact recorded excerpts and candidate integrity checks are in the local metrics.
- Both full live runs and targeted runs have separate exact-citation/candidate audits. Exact quotes and same-model semantic acceptance do not establish legal correctness; manual AI inspection found issues despite those checks passing.
- Four frozen route expectations still differ from the current conditional-general-information policy. Their raw observations remain in the regression output; labels were not changed to improve a score.

The final study ledger records 398 provider requests at an estimated US$0.35359, within the original cumulative 400-request / US$0.50 study cap. This is a configured token-price estimate, not verified billing. Website smoke checks use the unchanged separate website ledger and are excluded from this study total. No personal chat text or credentials were exported.

## Remaining limits

Night-pay authority, held working-time/meal-period passages, final-pay/COE deadlines, related thirteenth-month material and specific labeling requirements remain source-coverage gaps. Some supported questions still have withheld or partial AI explanations when validation fails. Detailed employment-status and product-remedy interpretations remain difficult. One same-model assessor can miss or over-reject a qualification; these checks are not independent legal review.

The full repaired 100-question run preceded the later targeted backend changes. Metadata-only metric binding may change the runtime signature after a completed study; frozen snapshots, selected package identities and final browser health disclose the exact revisions. No claim of perfect unseen-question performance, current-law approval or production readiness is made.

## Evidence

- `first-pass/QUESTIONS_AND_RESULTS.md`: all original 100 observations.
- `second-pass/QUESTIONS_AND_RESULTS.md`: full inspected rerun.
- `final-check/QUESTIONS_AND_RESULTS.md` and `closure-check/QUESTIONS_AND_RESULTS.md`: targeted follow-ups.
- `latest-observation-view.json`: explicitly labeled mixed-revision inspection view.
- `review-notes.json`, `summary.json`, `browser-evidence.json`, test/build logs and immutable model/index/verifier packages.

Initial restricted test runs could not open loopback sockets, and discovery without a root package caused duplicate-module patch failures; final tests use the correct root and loopback permissions. Stale metric bindings were refreshed after the new evaluation completed. Initial/superseded package and test logs remain preserved.
