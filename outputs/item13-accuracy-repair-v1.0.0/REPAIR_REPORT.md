# Item 13 focused accuracy repair

The seven wage/overtime retrieval misses and one Taglish privacy-scope miss are fixed on the **same frozen 291 AI development cases**. All **11 unchanged development screens pass**. No new per-case findings were introduced.

| Check | Before | After |
|---|---:|---:|
| primary accuracy | 267/268 | 268/268 |
| scope accuracy | 267/268 | 268/268 |
| partial support recall | 31/32 | 32/32 |
| explicit concern match | 31/39 | 39/39 |
| known relevant hit at 5 | 56/56 | 56/56 |
| quote integrity | 289/289 | 288/288 |
| negative candidate leakage | 0/11 | 0/11 |
| decisive coverage | 257/268 | 257/268 |
| route match | 279/291 | 280/291 |
| current guidance candidate coverage | 0/291 | 0/291 |

Cases with any finding decreased from **19 to 11**. The remaining cases are the same conservative routing deferrals; confidence thresholds were not lowered. Relevant-provision ranking on the 56 existing judged system retrieval cases remains MRR@5 0.934. Quotation counts can change when an excluded concern stops reaching retrieval; the check measures provenance, not relevance or legal correctness.

## Changes and controls

The classifier now recognizes bounded Taglish disclosure verbs plus private-data objects and public/unauthorized context. Separate warranty concerns remain supported; private-data disclosure remains excluded. Tests cover negated disclosure, ordinary delivery addresses and reversed concern order.

Labor-only lexical expansion associates late wages with payment timing/frequency and unpaid overtime with additional compensation. Original query words and special overtime qualifiers remain. Expansion terms are ranking aids, never supplied facts, legal support or approval. No expected IDs or evaluation labels enter runtime.

Software tests pass: **53 classifier, 42 retrieval, 37 verifier and 34 evaluator tests**. The verifier also passes its unchanged **50/50 AI development scenarios**. The opened original classifier regression remains **100/100**, with **92%** decisive coverage and **11/11** partial-support recall. These are inspected regression results.

All 291 case bytes and expected labels, source memberships, numerical screening targets, fitted weights, feature vocabulary, calibration and confidence thresholds are unchanged. The new index contains the same 362 chunks / 353 provisions / 12 documents and identical semantic vectors. No training data or legal authority was added. No LLM calls occurred.

## Preservation and versions

137 old-parent file bindings and 186 data/prior-artifact bindings match the pre-repair snapshot. Prior evaluated versions remain available. Current development packages are classifier v1.5.5, retrieval v1.2.4, verifier v1.0.2 and evaluation v1.0.1. `comparison.json` contains complete before/after rates, uncertainty intervals, fixed/remaining IDs and regression checks; `runtime_changes.patch` records the two behavior changes.

## Remaining work

Eleven conservative routing deferrals remain; passing aggregate development screens does not mean every expected route matches. The final-pay/COE evidence gap and prior source/currentness/contact prerequisites remain. The real review store still has zero current-guidance approvals, so current guidance remains blocked.

These reused AI cases provide development evidence, not independent human gold or real-world legal accuracy. Fresh independent human questions, source/support review, licensed Philippine legal review of selected actual generated answers and formal acceptance remain pending. Actual generated-answer accuracy and legal false-decline rates are unmeasured. The next development work is a controlled LLM draft adapter and its offline answer evaluation after required source/support conditions are resolved; Item 14 UI integration has not started. Live answering and deployment remain disabled.
