# Explanation usability repair — 25 October 2026

This work improves the explanation path and its website presentation. It does not establish legal accuracy or readiness for unrestricted professor queries.

## Changes

- Corrected false numeric rejections for referential “one”, structural numbered lists, and source-side singular time units. Real quantities and deadlines remain checked.

- Allowed explicit cross-references in the selected source, including Taglish phrasing, while preventing an unselected cross-reference from being presented as the selected authority.

- Allowed the explainer to consider five already-eligible retrieved sources rather than only the first three. All source/hold checks remain in place.

- Added a local English/Taglish style hint and question-focused drafting guidance. A shorter prompt regressed and was rejected; the prior condition-preserving drafting constraints were restored.

- Added checks for omitted rest-premium conditions, invented exceptions to a displayed-price ceiling, and agreements incorrectly attached to return costs.

- Correction requests now include the actual rejected prose and a specific instruction for the rejected price-ceiling exception, rather than only a code. The last targeted price-label answer removed the invented exception.

- Labelled multi-concern paragraphs by domain, exposed local excerpts for unanswered parts, and clarified that missing sources cannot be fixed by rewording a clear question.

Classifier weights, classifier/retrieval/verifier artifacts, current-law approvals and deployment permissions were not changed.

## Frozen checks

40 distinct AI-authored fictional inputs: 32 new questions and 8 disclosed earlier-failure replays. Expectations were frozen before inference. The same set was then inspected and reused for repair; these rechecks are not unseen validation.

| Run | Inputs | Full AI | Partial AI | Withheld | Median seconds | p95 seconds |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 40 | 23 | 3 | 14 | 7.98 | 18.10 |
| after-repair | 40 | 18 | 3 | 19 | 8.27 | 22.73 |
| final-recheck | 40 | 24 | 3 | 13 | 7.80 | 26.81 |
| closure-check | 5 | 4 | 1 | 0 | 11.25 | 34.69 |
| condition-closure | 2 | 1 | 0 | 1 | 7.24 | 9.20 |
| revision-context-check | 1 | 1 | 0 | 0 | 8.28 | 8.28 |

The full final-recheck run returned full/partial AI for 27 of 36 inputs with an in-scope concern (26 initially). All four excluded controls remained outside retrieval. Three valid inputs still route incorrectly. Source-gap controls deliberately remain unanswered by AI.

The final condition guards and correction-context repair postdate that full run. condition-closure preserved the rest-premium conditions but withheld a price-label draft that still invented an exception. revision-context-check then generated the price-ceiling explanation without that exception. These are disclosed targeted rechecks; do not report a final-runtime 40/40 pass or conflate AI availability with correctness.

All raw observations, rejected drafts, runtime/source snapshots, protocol hashes, cost ledgers and exact quotation audits are preserved in the run directories. Each audit confirms its frozen files stayed intact. Automated support acceptance is not independent legal review; manual reading found errors that it missed.

Diagnostic provider usage across these runs: 240 requests; $0.234022 estimated, within the shared 250-call/$0.35 stop. Website smoke checks use their separate existing application ledger. These are estimates, not verified billing.

## Software and website checks

Current backend suite: 281 tests passed (backend-final-context-tests.log). Frontend: 33 tests passed and production build passed. The earlier Windows socket-abort failure is preserved; subsequent complete runs passed. Citation/source audits have no integrity failures. The design detector found no findings in the changed component targets.

Browser evidence and the Impeccable review/documentation verdict accompany this report. Checks include desktop/390px rendering, source navigation, local excerpts, reduced-motion/unit accessibility behavior. No independent accessibility conformance is claimed.

UI finish verdict: ship at the changed UI scope (UI_REVIEW.md), including the actual 522×712 user viewport. UI_DOCUMENTATION_CHECK.md confirms the extension follows the incumbent design system. The pre-existing design sidecar drift remains unchanged; an Impeccable document refresh can address it separately.

A final additional website smoke question used fresh grocery/old-price-tag wording on the current API and returned an AI explanation with source citations. See browser-fresh-price.json and website-price-final.png. This single manual smoke check is separate from the frozen metrics.

## Open work before an unrestricted demo

- Three valid synthetic inputs route to clarification incorrectly: EX_NEW_008, EX_NEW_011, EX_NEW_019. Classifier weights and artifacts were not changed in this explanation repair.

- Displayed-price drafts previously repeated an unsupported exception. The correction-context repair passed one targeted check; broader unseen-wording reliability remains unmeasured.

- Some context-only or meta-question fragments are treated as separate concerns, causing duplicate explanations or a misleading missing-part notice.

- Night differential, briefing time, final-pay/COE deadlines and complete thirteenth-month coverage lack usable approved source context.

- Same-model support can miss condition errors. Exact quotations and passed software checks do not establish legal correctness.

- Complex multi-concern requests reached about 40 seconds in the targeted checks.

- No full 40-question run was performed after the last two condition guards; final-runtime checks are targeted and disclosed.

## Running it

From C:\IA run `./start-website.ps1` and use the printed URL. Enable AI explanations. Use complete fictional questions, inspect the interpreted wording and citations, and expect an explicit source response when an AI draft cannot pass the checks.

Do not claim that the study proves a real-world accuracy, F1, legal correctness, overfitting diagnosis or independent human validation.
