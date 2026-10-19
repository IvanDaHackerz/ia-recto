# Repairs before Item 12 — 17 October 2026

The software defects found in the scan have been repaired and retested. **Not all project issues are closed. Item 12 has not started.** Independent human evaluation, source verification/currentness, contacts and formal approvals remain outstanding.

## Current artifacts

- Classifier: item10-classifier-v1.5.4
- Retrieval: item11-retrieval-v1.2.3
- Canonical files, the frozen reviewed seed and original evaluated parent artifacts are unchanged.
- Earlier intermediate candidates remain historical experiments; use CURRENT_ARTIFACTS.json.

## Repairs

Investment patterns now recognize investment words without swallowing investigation/investigator. Ordinary defective services remain separated from medical and telecom exclusions. Private shops do not become employment concerns. Household repair does not inherit kasambahay employment context. Recognized cashier/product and SEnA procedure context avoids unnecessary clarification. Missing employment categories and unresolved independent concerns still require clarification.

Lexical retrieval normalizes a disclosed English/Taglish concept glossary symmetrically for documents and queries, handles common inflections, gives headings two occurrences and includes document titles. These changes were informed by inspected development errors. No question rows, IDF on questions or encoder fine-tuning were added. BM25 remains the method selected on the earlier development comparison. Semantic/hybrid search is retained as experimental comparison.

Three additional overseas-remittance chunks are excluded. The index now has **362 chunks / 353 provisions / 12 documents**, with 58 additional quarantined chunks from the original flagged-eligible set. Fewer indexed chunks here reflects tighter scope screening.

Referral candidates come from explicit topic rules and existing directory IDs. Bank and lending-company referrals differ; seafarer-pay referrals do not point to certification services. Unknown financial/provider context yields no invented destination. Candidates disclose old verification dates and require contact refresh; unverified phone/email fields are not exposed by the runtime.

## Classifier development results

| Partition | Classifiable rows | Classification accuracy | Decisive coverage |
|---|---:|---:|---:|
| Seed validation | 102 | 100.0% | 93.1% |
| AI general development | 100 | 100.0% | 92.0% |
| AI typing development | 80 | 100.0% | 96.2% |
| Opened synthetic regression | 100 | 100.0% | 92.0% |

On the opened regression set, partial recall and precision remain **11/11 and 1.000**, all numeric gates pass, and routing coverage improves from 69% to **92.0%**. Thresholds remain 0.80 primary / 0.85 scope, selected on validation. Underlying atomic classifier weights and training membership remain unchanged. Calibration is fitted on purged training-only grouped folds.

The original once-unseen 95/100 result is preserved. The repaired 100/100 result is regression evidence, not a new final accuracy estimate. Confidence remains imperfect: regression primary ECE is 0.132, scope ECE is 0.083. Do not turn label confidence into legal-correctness probabilities or calibrate on the inspected test to improve these figures.

## Retrieval development results

| Method | Hit@5 with supplied domain | MRR@10 |
|---|---:|---:|
| bm25 | 100.0% | 0.896 |
| semantic | 78.6% | 0.568 |
| hybrid | 92.9% | 0.785 |

BM25 finds a known relevant passage for **56/56** existing positive queries (28 English / 28 Taglish); all three methods pass 11/11 negative controls. The actual classifier-to-retrieval path also finds those passages for **56/56**, without a supplied oracle domain, and passes 11/11 negative controls. The classifier pipeline result uses at most five results per supported component.

These 56 queries represent only 28 scenario families. They and their partial relevance judgments were AI-authored, inspected and reused during repair. Perfect development hits do not establish perfect real-world accuracy. Bootstrap intervals in benchmark_metrics.json are descriptive; they do not measure generator bias, missing relevance labels or legal correctness. No generated answers were evaluated.

## Verification

49/49 classifier tests and 38/38 retrieval tests pass. Five independent-intake validator tests and three DTI structure tests pass. Frozen seed validation passes 59/59 checks using the bundled document runtime. Tests cover scope false positives, regulated-service boundaries, household repair, private shops, missing facts, component separation, referral destinations, training/calibration leakage, source/index hashes, numeric BM25 behavior, citations/offsets and token coverage.

The blank 100-row human intake correctly fails validation. It contains **zero questions** and is not an additional dataset.

## Remaining work that cannot be marked complete by Codex

1. **Independent human gold:** a person must write and label fresh questions. Reviewing or lightly rewriting the AI development questions does not make an independent holdout. The blank intake, provenance/overlap validator and handoff are prepared.
2. **Source coverage and review:** 258 original provisions remain pending. Four final-pay records have AI visual-comparison repair proposals. A tested DTI parser produces 29 proper section candidates from 31 original records, without splitting cross-references into fake sections. Proposals remain gated. MO 28 still needs a verified official full-text copy; current-year thirteenth-month guidance remains unconfirmed. Broad discovery candidates are optional acquisitions, not missing verified authorities to bulk-promote.
3. **Currentness and contacts:** all 39 official-source/contact URLs were attempted; 19 were accessible, others returned access, certificate or timeout errors. HTTP success and literal contact matches do not certify currentness. Browser research additionally corroborated the DOLE ARMS portal, the DTI complaints page, the DTI DAO 20-02 listing and a 2026 DOLE final-pay reminder. Original legal-status/contact dates remain unchanged. No unsupported no-amendment conclusion was recorded.
4. **Formal approvals and later milestones:** team/adviser approval and independent evaluation are still required for formal acceptance. Licensed Philippine legal-professional review of selected generated answers belongs to the later answer-evaluation stage. Item 12, answer generation, frontend integration and answer-level evaluation are planned work, not defects that can be honestly declared finished before implementing them.

See HUMAN_REVIEW_HANDOFF.md and issue_ledger.json. Under the owner's instruction to close everything before proceeding, **the project remains held before Item 12**. No human or legal-professional approval, current-law certification, live answer generation or deployment was fabricated.

## Official pages checked

- https://arms.dole.gov.ph/
- https://fairtrade.dti.gov.ph/faq/how-to-file-a-consumer-complaint/
- https://fairtrade.dti.gov.ph/resources/laws-policies/
- https://dole.gov.ph/news/final-pay-coe-must-be-released-on-time-dole/
