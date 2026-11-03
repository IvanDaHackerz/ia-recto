# Classifier usability stress test

Local AI-off testing and repairs, 21 October 2026. This is synthetic development evidence, not independent human gold, legal correctness, or deployment acceptance.

## Result

- Initial new batch: 116/130 labeled questions and 118/138 expected routes matched.
- Final application batch: 208/208 labeled questions and 224/224 routes matched, including 16 intentionally vague prompts.
- Paired uppercase, spacing and light typing variants: 552/552 passed on the packaged classifier. These derive from 184 base questions and are not 552 independent scenarios.
- Previous application regression set: 74/74 routes matched.
- Website: 17/17 questions (12 new scenarios and five retrieval/follow-up/typing regressions) matched displayed topic, coverage and response behavior; every displayed quote matched stored source text; zero provider calls. Five specific source-context regression checks also passed, without claiming legal entailment.
- Historical development replay: 425/425 topic labels, topic macro F1 1.000, scope macro F1 1.000. Its four earlier-policy routing differences remain in errors.json; expectations were preserved.
- Application median analysis time in this local run: 181.5 ms. All 224 excerpt checks passed; 149 responses contained at least one passage. A passage does not prove legal applicability.
- Packaged checks: 69 classifier, 49 retrieval, 37 verifier checks. The 212-test complete backend suite is recorded in backend-tests-noise-final.log; the extra 16 contrastive classifier methods are recorded in contrastive-tests-noise-final.log.

## Repairs

Employment introductions no longer create purchases; employer industries and incidental rest-day wording remain distinct from purchase/service complaints. Taglish work and purchase expressions, project-based status, public school employment and domestic helper categories receive explicit scope handling. Request conjunctions preserve a separate excluded concern. Anaphoric pay follow-ups stay with their scenario, and school-specific passages are filtered from generic office questions. Hyphenated minimum-wage requests and mobile network/data-plan disputes retain their exclusions. Missing-space repair no longer splits network into net work. Repeated letters are repaired against the declared scope and grammar vocabulary, so payroll and anaphoric words keep their context. Unanchored payment and generic help prompts ask for detail. Search facets now recognize cracked screens, native fault/safety wording, ordinary wage-payment forms and required waiting. Offline purchases cannot quote online-only remedies, and shelf prices retrieve price-tag rules rather than comparative-advertising rules.

Atomic model weights, TF-IDF vocabulary, original training membership and routing thresholds were retained. Probability calibration was replayed on the original training folds because preprocessing changed. The final follow-up repair preserved all 459 original training-parent feature rows exactly, so its inherited fitted calibration was retained. No new test questions were fitted into the model. This does not establish absence of overfitting or broad language understanding.

## Exposure and limits

138 initial development questions were opened and used for repairs. A reserved 46-question synthetic probe initially matched 39/42 labels and 40/46 routes; its six failures were inspected and it became development data. A further 40-question probe initially matched 35/36 labels and 39/40 routes; its two failures were inspected and repaired, so it also became development data. Both first-pass outputs remain available. The 12 new website questions were composed after the classifier repairs, then checked through the visible interface. None of these sets is independently human-authored.

Supported scope does not guarantee that the stored corpus can answer the question. 7 final responses still have no quotable passage; see remaining-source-limits.json. In particular, final-pay/COE, thirteenth-month source reviews and specialized facts remain limited. A forced-resignation scenario may also require a better reviewed source. We did not invent text or open legal-answer/deployment gates to conceal these gaps.

Live LLM explanation quality, provider latency and paid requests were not tested here. AI was off throughout the tests and restored afterward for new user submissions. Further independent user testing and legal source review remain necessary. Exact quotes and topic matching are not legal entailment.

## Current stack and evidence

- Classifier: outputs/item10-classifier-v1.5.36
- Retrieval: outputs/item11-retrieval-v1.3.23
- Verifier: outputs/item12-verifier-v1.0.30
- Historical replay: outputs/local-pipeline-evaluation-v1.6.12
- application-search-final.json, its summary, legacy-summary.json, variants-packaged-v36.json and browser-results.json preserve observations. Earlier passes and failed builds are retained.
- browser-classifier-proof.jpg shows the displayed local classifier result.

All changes are local. No GitHub push was performed by this task.
