# Website concern repair and development explanations

Date: 19 October 2026. Owner-authorized local development implementation. This report records software and development observations; it is not independent human evaluation or legal approval.

## Result

The reported question, “I was about to get my pay, but i got stabbed in the street,” now routes outside the selected labor/consumer scope. Going to collect pay is background, rather than evidence of an unpaid-wages complaint. An explicit personal-harm notice provides conditional emergency assistance information, without calling either wording or explanation providers. The official Philippine emergency directory is <https://ehotlines.e.gov.ph/>. This was treated as a test question, not an assumption about a present emergency.

Recognized violence, theft, family and general-information concerns now have explicit exclusion handling. Genuine joined supported/excluded concerns remain separate. Missing facts and unrecognized wording can still require clarification; these rules do not establish comprehensive out-of-distribution recognition. The broad general-information patterns also remain candidates for future contextual error analysis.

The website now produces actual GPT-OSS explanations through the configured server-side Together credential for eligible supported concerns. Each generated paragraph links to its recorded provision. The completed, validated response reveals word by word for at most five seconds; **Show full answer** completes it immediately. This is a presentation reveal after validation, not token streaming from an unchecked provider response.

## Runtime and data boundaries

Current packages are classifier **v1.5.13**, retrieval **v1.2.9**, and verifier **v1.0.8**. `CURRENT_ARTIFACTS.json`, backend classifier configuration, verifier policy and Performance bindings reference them. The conditional normalizer remains v3.0.0.

Classifier concern rules changed; learned weights, vocabulary, calibration, thresholds and training membership did not. Retrieval source records, exclusion records, semantic vectors and semantic windows are byte-identical to their parent package; all 719 vectors were reused. Verifier changes bind the new packages. No trusted source/claim reviews were added and no current-guidance approval was granted.

`concern_cases.jsonl` freezes 29 focused cases: the owner-reported example and AI-authored development regressions. `concern_observations.jsonl` preserves actual outputs. This is not an independent human gold set. Previous bindings and policy are retained in this packet.

## Explanation checks and limits

The separate `development_recorded_sources` mode accepts supported routes, non-fixture candidate sources that pass integrity checks, and available required related authorities. Missing eligible context or authority withholds generation. At most three source provisions per supported concern are sent with the interpreted question, in one structured request without automatic retries. The interface discloses this export; credentials stay server-side and normal chat requests are not persisted.

Before display, the backend checks the output shape, known supported-component and source IDs, exact stored quotations with Unicode offsets, source-contained numeric details, and inclusion of every supported component. Quote matching may restore whitespace only; it cannot change words or punctuation. Invalid output remains withheld, without exposing the rejected draft.

Successful results explicitly state `citations_checked: true`, `legal_support_verified: false`, and `currentness_reviewed: false`. Matching quotations and IDs do **not** prove that every paraphrase follows legally from those sources, preserves every qualification, or applies to the user's facts. The live normal-hours sample extrapolates toward overtime from the supplied normal-hours provision; the warranty sample may omit qualifications. These illustrate why semantic/legal review remains pending despite successful integrity checks.

The existing current-guidance verifier path still has closed generation/display/deployment permissions. Health reports that approval boundary separately from `development_explanations_enabled`. This owner-enabled preview does not create legal-professional reviews, certify current law, or complete deployment acceptance.

## Verification

| Check | Observed result |
|---|---:|
| Frozen focused concern routes/labels | 29/29 match |
| Classifier software suite | 65 passed |
| Retrieval software suite | 43 passed |
| Verifier software suite | 37 passed |
| Full backend software suite | 126 passed |
| Distinct software tests across those suites | 271 passed |
| Saved Performance numeric reconciliation | 261 comparisons passed |
| Frontend production build / lint | Passed |
| Packaged checksums | 49 classifier, 25 retrieval, 19 verifier files passed |

Backend tests use mocked providers and real packaged source context. They cover harmful-input provider bypass, supported and excluded routes, exact quote offsets, whitespace restoration, unknown citations/components, invented numeric details, missing supported components, unavailable authority and fixture restrictions. Logs are in `backend-tests.log`; artifact audit is in `artifact_audit.json`.

The current local-only evaluation, `outputs/local-pipeline-evaluation-v1.2.0`, reuses the same frozen 436 input forms / 171 families. Topic and coverage labels each match 425/425 expectations; macro F1 is 1.0 for each. Routes match 434/436 (99.54%); the same two conservative raw-input clarification deferrals remain. Known-relevant Hit@5 is 93/93 judged concern groups. Candidate integrity passes 2,341/2,341 checks, with zero cross-domain candidate leaks; diagnostic exact excerpts pass 473/473. Both LLM stages were disabled, so this evaluation contains **zero generated answers and zero LLM calls**. These figures do not measure explanation accuracy or independent generalization.

The previous conditional comparison, `normalization-evaluation-v3.0.1`, belongs to classifier v1.5.12 / retrieval v1.2.8 / verifier v1.0.7. It remains historical relative to this release; no full new conditional batch was run after packaging this repair.

Five live Together explanation calls were made using fictional supported questions. The first two tests produced one withheld citation failure and one generated price-tag response. After tightening the prompt and allowing whitespace-only quote restoration, two saved API smokes (normal hours and warranty) and one actual browser smoke generated citation-checked explanations. Earlier failure evidence remains preserved. These are small implementation smokes, not an answer-quality benchmark. The reported personal-harm example stayed local and triggered zero provider calls.

Browser checks covered desktop and 390px layouts, actual word reveal and skip without rewind, citation-to-source navigation, phone **Back to chat** with restored focus, and no horizontal document overflow. Complete screen-reader text and reduced-motion handling are implemented; a runtime reduced-motion preference change was not emulated. Final captures are under `UI/UX/app/.impeccable/review/explanations/`.

## UI finish and remaining work

The fresh Impeccable reviewer returned **ship**, scoped to this extension, with no material fixes. It confirmed explanation prominence, source access, disclosure, safety presentation and accessible reveal design. This disposition does not certify legal correctness. The separate documenter compares the finished extension to the incumbent visual system; its report is stored alongside the captures.

Before broader release: evaluate generated explanations for semantic support and omitted qualifications; obtain scoped source/currentness and legal claim reviews where required; run fresh independent user questions; and complete owner acceptance and deployment review. No generated-answer F1/accuracy or legal confidence score is claimed here.
