# Pre-Item-13 project audit — 17 October 2026

**The audited software is ready to begin offline Item 13 evaluation. Full generated-answer evaluation, formal acceptance and deployment are not ready. Item 13 has not started.**

Current artifacts: classifier **v1.5.4**, retrieval **v1.2.3**, verifier **v1.0.1**. The preceding v1.0.0 verifier packet, legal sources, model artifacts and frozen reviewed data are preserved. No LLM API calls, invented human approvals or source promotions occurred.

## Issues found and repaired

1. Strict JSON parsing rejected literal Infinity/NaN but allowed an exponent such as `1e1000` to overflow. It now rejects overflow while retaining finite JSON numbers.
2. The direct source-check helper treated an unknown mode as excerpt mode and raised an unstructured key error for unknown sources. It now explicitly rejects both. Normal CLI modes were already constrained; this repair hardens direct use.
3. Default verifier dates and artifact integrity were checked only at construction. Each new request now refreshes the default date, verifies source/index/model/runtime files and detects review-store mutation. Tests confirm expired approvals stop passing after date rollover and that changed files fail even if their timestamp is preserved. Explicit historical dates still work for reproducible offline evaluation.
4. Development acceptance checks compared concern counts. They now compare the surviving concern IDs too, so accepting the wrong side of a mixed question cannot satisfy the expectation.

These repairs are saved in a new version. [Review the code changes](C:/IA/outputs/pre-item13-audit-2026-10-17/ITEM12_CHANGES.patch). Historical status records remain unchanged; the new current ledger supersedes their old Item 12 hold.

## Checks executed

| Area | Result |
|---|---:|
| Item 7 source/provision/chunk contracts | Passed; reports redirected out of frozen data |
| Item 8 discovery-only gates and tables | Passed |
| Item 9 original seed/referral contracts | Passed |
| Frozen reviewed seed, splits, workbook formulas/native structure/provenance | 59/59 checks passed |
| Current classifier regression suite | 49/49 passed |
| Current retrieval regression suite | 38/38 passed |
| Repaired verifier software suite | 37/37 passed |
| Source/parser/contact/independent-intake supporting suites | 17/17 passed |
| AI verifier development scenarios | 50/50 met expected behavior |
| Existing retrieval cases through actual classifier → retrieval → verifier | 56/56 positive and 11/11 negative cases passed |
| Frontend TypeScript, Vite production build and lint | Passed |
| Independent human intake | Correctly rejected: 100 blank forms, 0 authored questions |
| Default current-guidance permissions on reused 67 cases | 0 permitted, because actual scoped reviews are missing |

The 56 positive retrieval cases reuse 28 English/Taglish scenario families. The same existing questions and inspected AI relevance judgments were reused, not converted into new independent data. For the audit's positive excerpt path, a known-relevant retrieved provision was selected using the existing development label; passing proves text/citation integrity, not automatic semantic selection or legal-answer correctness.

`final_integrity.json` confirms 27 current packet files, 9 current verifier source/configuration files, 101 preserved parent files and 32 legal-source files match their hashes. The frozen seed and all five cleaned human-review workbooks also match their manifest hashes. No mismatches were found. Legacy validators' reports were redirected into this audit folder; original validation reports were not overwritten.

Frontend checks establish compilation/lint success for the existing scripted prototype. No new browser visual/accessibility audit, production backend connection or deployment was performed. The broad discovery corpus was not recrawled, and official legal/contact pages were not newly certified current by this audit.

## Remaining work and readiness

- **Independent human evaluation:** zero fresh independent questions have been supplied. The existing 200 AI-reviewed questions remain development material. Real-world accuracy and calibration still need independent evidence.
- **Legal sources:** final-pay/COE, MO 28, applicable thirteenth-month guidance and DTI/Consumer IRR review gaps remain. AI-repaired copies have not been silently promoted; the original 258-entry human source queue remains.
- **Currentness and support:** zero real scoped source/claim approvals exist. Current-guidance mode deliberately blocks. Exact excerpt checks do not establish relevance, currentness or sufficient legal support; arbitrary paraphrase checking is a review gate.
- **Answer generation:** there is no connected LLM drafter. Software/citation/decline evaluation can start now; substantive generated-answer metrics cannot be completed until a controlled drafting component and relevant source/support approvals are available.
- **Contacts and application:** 36 fields across 15 of 19 agencies have corroboration; four entries remain unresolved, and the current classifier still uses its frozen directory. Live UI/backend/history integration belongs to Item 14.
- **Acceptance:** required team/adviser acceptance and the proposal's licensed Philippine legal review of selected generated answers remain pending.

An all-declining system cannot be called accurate merely because no unsupported answer was emitted. Item 13 must report answer coverage and false declines, and leave substantive answer metrics unavailable when their denominator is zero. Classifier probabilities, retrieval ranking and legal-support judgments stay separate.

## What can happen next

Prepare Item 13's offline evaluation protocol, grouped scenarios/expected authorities, runner and result table. Keep development material separate from the final independent holdout and freeze final-test criteria before opening results. Evaluate classification, retrieval, citation consistency, mixed concerns and clarification/referral behavior first. Add actual generated-answer evaluation only when its stated dependencies are satisfied.

[Item 13 explained](C:/IA/outputs/pre-item13-audit-2026-10-17/ITEM13_EXPLAINED.md). [Readiness status](C:/IA/outputs/pre-item13-audit-2026-10-17/readiness.json). [Current issue ledger](C:/IA/outputs/pre-item13-audit-2026-10-17/current_issue_ledger.json). [Verifier report](C:/IA/outputs/item12-verifier-v1.0.1/VERIFICATION_REPORT.md).
