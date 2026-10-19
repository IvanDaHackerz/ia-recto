# Joined-concern handling repair

Implemented 19 October 2026. Current bindings: classifier **v1.5.11**, unchanged retrieval **v1.2.7**, verifier **v1.0.6**. The local website API has been restarted with these bindings.

## Fixed behavior

Input: “Private employee ako. Hindi binayaran ang overtime ko at ayaw ibalik ng landlord ang rental deposit.”

Before: the combined clause matched the landlord exclusion and the whole question was routed out of scope.

After: **mixed / partially supported**, routed to `retrieve_supported_components`. The labor query is `private employment: hindi binayaran ang overtime ko`; the landlord/rental-deposit concern is recorded separately under `consumer.real_estate`, with retrieval disabled. The original question is retained. The local pipeline makes **zero wording-LLM calls**, and legal explanations remain withheld under the existing source/review gates.

## Implementation

The existing splitter recognized Tagalog `at` only before a small set of introductory words, omitting negative complaint predicates such as `ayaw` and `hindi`. Exclusion matching consequently saw two concerns as one.

A guarded second segmentation pass now recognizes predicate-led complaints joined by `at`, `and`, `pero` and `but` before scope decisions. Both sides must carry their own issue anchor or explicit issue/dispute intent. Unknown explicit concerns remain unresolved and request clarification. Noun lists, negated category qualifications, unanchored follow-ups and explicitly quoted conjunctions do not gain a new split from this pass. These are bounded development rules, not a claim to fully parse every English/Filipino coordination.

No new fitting occurred. The package preservation checks confirm unchanged model weights, fitted feature vocabulary, calibration, confidence thresholds and training membership. Legal records, semantic vectors, source eligibility and legal-review permissions were not modified. The verifier version changes only to pin the new classifier; its source/claim checking behavior is unchanged.

## Verification

| Suite | Passed |
|---|---:|
| Classifier, including 5 new joined-concern checks | 65 |
| Retrieval | 42 |
| Verifier | 37 |
| Classifier API, website integration, typing, normalizer, terminal and evaluator | 106 |
| **Distinct software tests** | **250** |

The five new checks cover both concern orders and all four connectors, an English predicate-led example, fully supported labor-plus-consumer concerns, lists/negated categories/quotes/follow-ups, and an explicit unknown dispute that must trigger clarification. They verify that excluded concerns never enter supported retrieval queries and that source fragments remain accounted for. The original joined form also passes the website application regression and a real loopback HTTP smoke check.

The new classifier replayed the exact **424 existing AI development inputs** without an LLM. Compared with the saved classifier-only baseline, there were **zero changed label/routing decisions and zero new regressions**: topic and scope labels each 413/414 correct, routing 417/424. This is a reused development regression comparison, not an independent human evaluation or a rerun of the conditional LLM pipeline. The joined example was not present in that frozen set; the new checks cover it separately.

The immutable Performance report still describes classifier v1.5.10 / verifier v1.0.5. Its scores were not rewritten. The API now marks that report as a previous stack, so the page discloses the mismatch pending the planned full current-stack evaluation.

The HTTP software checks required approved execution permitting localhost sockets. No external API calls were made and no new project text was sent to Together.ai.

## Evidence and remaining scope

- `development_replay.json`: complete frozen-set comparison and changed-decision list.
- `fixed_pipeline_result.json`: real local pipeline output for the joined question.
- `http-smoke.json`: the restarted HTTP API's route, searched domain, excluded topic and zero LLM calls.
- `backend-tests.log`: the 106 backend software checks.
- `../item10-classifier-v1.5.11/`: preserved learned-state audit and classifier checks.
- `../item12-verifier-v1.0.6/`: source/parent preservation and verifier/retrieval checks.

The specific joined-concern issue recorded during website integration is resolved. Other previously documented retrieval/routing cases, independent evaluation, source/currentness approvals and generated-answer evaluation remain separate pending work. Answer generation and deployment permissions remain false.
