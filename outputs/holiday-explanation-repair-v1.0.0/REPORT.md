# Holiday question / explanation-stage repair

Status: software repair and bounded live diagnostics; final browser check is recorded separately. This is not independent legal acceptance or generated-answer accuracy.

## Findings and changes

- The reported scenario and its rule question were split into separate concerns. A question-only follow-up is now attached only when its topic already appears in the preceding scenario. New topics, actors and employment categories remain separate. Original words remain in fragment accounting.
- Unrestricted lexical ranking put unrelated employment text ahead of holiday provisions. Explicit single-topic holiday queries use the existing holiday topic. Explicitly unworked holidays exclude worked-holiday premium/overtime headings, while work comparisons and explicit other labor topics retain broader searches.
- Written ordinals were missing from quantity matching. Compound dates and ordinal lists now match their equivalent digits; invented quantities still fail.
- The provider was given the schema through response_format but not its text in the prompt. One captured support reply emitted whitespace until its 2,048-token limit. Both prompts now contain the exact schema; claim/component/passage IDs and output counts are bounded to the actual request. Finish reason must still be stop, and all local validation remains mandatory. Together's [structured-output guide](https://docs.together.ai/docs/inference/chat/structured-outputs) explicitly recommends both the prompt schema and API schema.
- The automated judge accepted one earlier draft's unsupported 'only worked holidays' inference. That diagnostic is preserved in live-smoke-final-packet.json and must not be treated as a successful legal answer. The recorded IRR Section 3 wording differs from the government-hosted [DOLE/BWC FAQ, PDF page 12](https://cda.gov.ph/wp-content/uploads/2019/07/coopsday-DOLE-BWC-FAQs-on-Labor-Standards.pdf). The affected provision is now on a generation/citation hold, with inspectable original text and a visible source restriction. No canonical wording, training data or trusted review is silently changed. The comparison is AI-inspected and does not certify current law.
- A later browser draft combined two provisions but cited only one. The assessor now receives claim-specific cited full sources, excluding uncited candidates; it cannot borrow support from the rest of the retrieval set. Generation explicitly requires a citation for each provision whose rule it uses.
- If complete assessments find only qualification or citation-support problems, one bounded correction is allowed when sufficient time remains. The new draft must pass every citation, source, numeric and semantic check. Case outcomes, excluded advice, invented case facts, insufficient context and missing/malformed assessments cannot trigger or override that path. A second rejection withholds the whole answer. Standard daily spending, cancellation and request deadlines still apply.
- Live copy now distinguishes topic coverage, skipped support checks, citation failures, provider HTTP errors and attempted correction. Within project topics does not mean legal entitlement or sufficient evidence.

## Versions and evaluation

Classifier v1.5.16, retrieval v1.3.3, verifier v1.0.11. Learned weights, feature vocabulary, calibration, thresholds and training membership are inherited unchanged. Original source records and trusted reviews are preserved. Intermediate packages remain as inspected development history.

Local-only replay: outputs/local-pipeline-evaluation-v1.5.0. All 436 reused AI input forms returned packets: topic/scope 425/425 labeled forms, routes 435/436, known-relevant Hit@5 93/93, Hit@1 73/93. All 2,341 candidate integrity checks and 473 excerpt checks passed; zero cross-domain leaks. These figures exclude both LLM layers, use inspected development data and establish no independent human/legal accuracy.

The earlier application-evaluation-v1.2.0 AI replay remains immutable and displayed as differing inference code. A full AI replay of this revised path has not been performed. No independent human questions or legal/current-source approvals were added. The prior release ZIP is a historical checkpoint and does not contain this repair.

## Live observations

Earlier failures are retained rather than counted as successful answers: numeric validation, source-support rejection, provider unavailability and incomplete output all occurred. The final schema-bound terminal probe returned provider_http_503 before generating a draft. This is a provider server error, not a request to rewrite the question. Browser verification and final software-test receipts are recorded alongside this report.

The generic missing-employment-category clarification rule remains in place. This repair does not silently assume private employment for the earlier question without a category. Conditional general-answer routing for that case remains a separate design decision.

## Final verification and remaining limit

174 backend tests, 20 frontend tests, 8 concern regressions and the 65 classifier / 47 retrieval / 37 verifier package checks pass. Frontend lint/build pass; 261 displayed metric comparisons reconcile. Source-record bytes, trusted reviews and inherited learned state are unchanged (preservation.json).

The final website submission reached the explanation support stage (2 provider calls), then Together returned HTTP 503. No draft was shown. The UI distinguishes this unavailable check from a negative support verdict. Use this question again was verified to refill the exact complete question and focus the composer without submitting another request. Desktop 1200px and mobile 390px views have no horizontal overflow; captures are desktop.png and mobile.png. This is a bounded manual UI check, not independent legal or accessibility certification.

The final successful live happy path for the stricter, claim-specific verifier remains unconfirmed because of that provider failure. Full AI replay, independent human/legal acceptance and resolution of the held source remain pending. Earlier generated diagnostic paragraphs are historical counterexamples, not approved gold or evidence of legal accuracy. No further API retries were made after the final website failure.
