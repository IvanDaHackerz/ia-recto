# Item 12 — offline citation and evidence verification

Built and tested on **2026-10-17** around **outputs/item10-classifier-v1.5.72** and **outputs/item11-retrieval-v1.3.59**. No LLM API was called. Live answering, user display and deployment remain disabled.

## Implemented behavior

Preflight verifies pinned artifacts, reruns the actual classifier/retriever, checks source eligibility, exact citation/text/locator metadata, recorded conditions and minimum related-authority dependencies. It preserves clarification, evidence gaps and excluded concerns.

Postflight accepts only a strict claim/evidence contract. It checks document/provision/chunk identity, retrieval membership for the concern, exact full-provision quotation/offsets and context. Current-guidance claims additionally need scoped support, relevance, qualification and concern-coverage review. A missing citation or an altered/truncated quote fails. A draft cannot supply its own approval, citation label, confidence or unchecked free-form answer.

Each concern is withheld as a unit if any of its claims fail. Independently passing concerns can produce a partial development candidate, accompanied by explicit disclosures. Preview blocks use only checked claim text and trusted citation metadata.

This revision binds the focused classifier/retrieval repairs. Verification policy is unchanged apart from version and artifact bindings. It retains rejection of JSON exponent overflow and invalid source-gate modes/candidates, default-date refresh and file/review integrity checks on every request. Explicit historical dates remain available for reproducible offline evaluation. Development metrics verify which concerns survive, in addition to their count. The previous `outputs/item12-verifier-v1.0.64` packet is preserved.

## Validation results

| Check | Result |
|---|---:|
| Item 12 software tests | 37/37 passed |
| Existing classifier regression tests | 69/69 passed |
| Existing retrieval regression tests | 60/60 passed |
| Total AI development scenarios | 52/52 met expected behavior |
| Valid exact-excerpt controls | 5/5 accepted as intended |
| Adversarial/withholding controls | 40/40 handled as intended |
| Simulated review positive controls | 2/2 exercised successful review paths |
| Real default current-guidance gate | Blocks without source/claim reviews, as required |
| Frozen parent and source files | 111 parent files + 38 source files checked; 0 changed |

Controls cover fabricated citations, wrong documents/provisions, altered quotations, bad/boolean/fractional offsets, removed qualifications, invented remedies, negation, unchecked text, cross-domain citations, excluded concerns, missing mixed components, failing sibling claims, currentness gaps, expired/future reviews and mismatched source/condition/relationship/question/policy/index hashes. Positive controls prevent an always-blocking verifier from passing the suite. CLI execution was tested outside the repository, including UTF-8 output and rejection of simulated approvals. BM25 verification also passed with network/semantic calls disabled by test stubs.

These are **AI-authored, inspected software-development controls**, not independent human/legal gold. The descriptive Wilson 95% interval is 91.2%–100% for the adversarial controls and 56.6%–100% for the four valid-excerpt controls. Related fixtures are dependent; these intervals do not measure legal accuracy, generator bias or real-world confidence. Existing label probabilities and retrieval ranking remain separate. No combined legal-answer confidence is reported.

## Current limits

**Recorded-excerpt mode verifies provenance only.** It does not determine whether a retrieved provision answers the question, applies today, or supplies enough evidence. Full provision text preserves local qualifications; broader applicability still needs judgment.

**Current-guidance mode currently blocks.** The normal trusted review store has zero reviews. A recent source status date is not certification of currentness. Two isolated positive tests use explicitly simulated review records; normal runtime/CLI rejects those records. No human review or professional approval was fabricated.

**Paraphrase checking is a review gate.** Arbitrary legal entailment is not automatically solved by this implementation. Current-guidance approval must bind the exact claim, evidence, concern, source conditions, index and policy. A future service must keep this operator configuration inaccessible to draft/end-user input and authenticate reviewers separately.

The 2026-10-26 source supplement supplies a bounded DOLE final-pay/COE statement, official statutory quotations concerning thirteenth-month pay, and clean working-time topic-map repairs. Original OCR/MO 28 copy holds and the handbook's explanatory-only policy remain intact. Independent currentness/legal evaluation, contact follow-up and formal approvals remain pending. The original corpus files, reviewed seed, model weights and evaluated parent versions remain preserved. This packet replays software review fixtures at their historical date, not a current legal review.

## Next step

Rerun **Item 13 system-level development evaluation** on the frozen cases and unchanged screening targets. Actual generated-answer scoring, independent human questions and licensed Philippine legal review remain separate pending work. An LLM adapter and UI integration are later work. The project owner's offline implementation authorization does not close the remaining legal/data/approval prerequisites.

## Files

- `metrics.json`, `development_cases.json`, `development_results.json`: full expectations, decisions and reasons.
- `software_tests.json` and three test logs: software/regression evidence.
- `examples.json`: real exact-quote previews and blocked current-guidance preflights.
- `schemas/`, `source_snapshot/`, `run_manifest.json`, `VERIFIER_CARD.json`: contracts, provenance and limits.
- `preservation_audit.json`, `artifact_checksums.json`: frozen-parent/source integrity and packet hashes.

Executable commands and review contracts: [pipeline README](C:/IA/dataset/pipelines/item12/README.md).
