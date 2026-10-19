# Item 12 — offline citation and evidence verifier

Current dependency binding: **v1.0.3**, classifier **v1.5.6**, retrieval **v1.2.5**. This binding supports the classifier preintegration implementation and is checked with software regressions only. Final performance/generated-answer evaluation is deferred at the owner's request. Verification behavior and real review approvals are unchanged. The earlier evaluated results below are historical. [Current binding report](C:/IA/outputs/item12-verifier-v1.0.3/VERIFICATION_REPORT.md).

Built on 17 October 2026 around classifier v1.5.5 and retrieval v1.2.4. This package checks evidence before drafting and checks structured claims afterward. It runs locally without an LLM API, a new model download or changes to the training/source datasets.

Current artifact-binding revision: **v1.0.2**. It pins the bounded Item 13 scope and retrieval repairs; verification policy is unchanged apart from version/artifact bindings. Requests refresh the default date and recheck file/review integrity, so a long-lived evaluator stops after a source/runtime change and does not retain expired approvals. Explicit historical dates remain available for reproducible offline tests. JSON exponent overflow and invalid direct source-gate modes/candidates are rejected. Development scenarios check the identities of surviving concerns, as well as their counts. The original v1.0.0 packet remains preserved.

## What it does

1. Verifies the pinned classifier, runtime, retrieval index and canonical-source hashes; recomputes actual classifier routing and BM25 retrieval from the original question.
2. Rechecks source eligibility and canonical citation/text/locator metadata. Excluded components never become answerable because a draft says so.
3. Applies recorded freshness conditions and minimum related-authority dependencies. Current-guidance candidates require a scoped operator-managed legal review; a recent status date, a retrieval hit or an accessible URL does not supply one.
4. Accepts a structured draft with individually cited claims. Every evidence quote must match exact Python Unicode character offsets in the full stored provision. Fabricated IDs, mismatched documents, altered quotes and incomplete context fail.
5. Requires separate support, relevance, qualification and concern-coverage review for current-guidance claims, including paraphrases. An existing citation alone never proves an interpretation. One failed claim withholds its entire concern; other independently checked concerns may remain as partial candidates.
6. Produces controlled preview blocks, trusted citation metadata, coverage counts and explicit audit reasons. There is no unchecked introduction, conclusion or free-form answer field.

## Two explicit modes

`current_guidance` is the default. `trusted_reviews.json` intentionally has **zero reviews**. Accordingly, real current-guidance preflight currently blocks on unresolved source conditions. The review mechanism is implemented; no legal approval has been invented. Arbitrary paraphrase entailment is a **review gate**, not an implemented automatic semantic classifier.

`recorded_excerpt` permits an offline developer preview of complete stored provisions with citations and disclosures. A passing excerpt proves text provenance only. It does not establish relevance, current applicability, legal correctness or sufficient coverage of the question. The template uses the first retrieval candidate, which can be irrelevant; inspect candidates or select a different retrieved provision when preparing an example.

Every result keeps `answer_generation_allowed=false`, `display_allowed=false` and `deployment_allowed=false`. `offline_drafting_allowed` and `offline_preview_allowed` apply only to development artifacts. This verifier does not call an LLM, expose a service, connect the UI or authorize production use.

## Commands

Run with the existing Python environment. JSON output is UTF-8, including redirected output on Windows.

```powershell
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item12/verification.py --query "The shop charged me more than the price tag."
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item12/verification.py --query "The shop charged me more than the price tag." --mode recorded_excerpt --excerpt-template --output C:/IA/tmp/price-preview.json
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item12/verification.py --query "The shop charged me more than the price tag." --mode recorded_excerpt --draft C:/IA/tmp/my-structured-draft.json
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item12/test_verifier.py
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item12/evaluate_verifier.py --output C:/IA/tmp/item12-new-evaluation
```

Output files and evaluation directories must be new. Use `--draft` for postflight verification, or omit it for preflight. The original question is supplied independently; changing the draft's question fails. `--excerpt-template` produces a diagnostic structured draft and its verification.

The draft contract is:

```json
{
  "schema_version": "1.0",
  "question_text": "Original question, unchanged",
  "claims": [{
    "claim_id": "claim_001",
    "component_id": "concern_001",
    "kind": "source_excerpt",
    "text": "Exact full provision text",
    "evidence": [{
      "chunk_id": "A retrieved chunk ID",
      "provision_id": "Its provision ID",
      "document_id": "Its document ID",
      "start": 0,
      "end": 25,
      "quote": "Exact full provision text"
    }]
  }]
}
```

The illustrative IDs above are placeholders. `end` is exclusive and must equal the actual full provision length. Do not use UTF-16 JavaScript offsets without converting to Unicode code points. Citation labels and URLs are supplied from the verified index, never from the draft. `kind=paraphrase` is available only through current-guidance review.

## Trusted review boundary

`--review-store` is an **operator configuration**, never an end-user or LLM-controlled argument. A future service must not expose that argument or let a client upload an approval store. The package validates approval shape and bindings; it cannot authenticate a person's identity or license. Protect and audit these files outside the draft input channel.

Reviews bind the exact original question, component, index version, policy, source-file hash, recorded conditions and required related-source hashes. Claim reviews additionally bind the exact claim and evidence payload. Reviews must state their reviewer, rationale, date and expiration (at most 30 days). An expiry window is an operational policy, not a guarantee that the law cannot change. General legal relationships beyond the conservative minimum dependency list still require judgment under the recorded conditions. Related documents being indexed does not prove their applicability.

`development_cases.py` creates **AI-authored software fixtures** with simulated review records to exercise successful review paths. Normal runtime and CLI reject these records. Tests opt into an explicitly flagged fixture mode. These are neither human approvals nor independent legal gold.

Schemas are published in the versioned output's `schemas/` directory. `contracts.py` validates every untrusted input field with a strict standard-library subset, rejects unknown fields/duplicate keys/non-finite values, and publishes output envelope schemas. No new dependency is required.

## Review and continuation

See [verification report](C:/IA/outputs/item12-verifier-v1.0.1/VERIFICATION_REPORT.md), [metrics](C:/IA/outputs/item12-verifier-v1.0.1/metrics.json) and [example previews](C:/IA/outputs/item12-verifier-v1.0.1/examples.json). Classifier probabilities remain label probabilities; retrieval scores remain ranking values. No combined legal-confidence percentage is manufactured.

The offline implementation can proceed to Item 13 system evaluation. Independent human questions, licensed legal review, source-currentness/coverage gaps and formal acceptance remain outstanding. Item 13 must measure answer support and false declines, including relevance and missing conditions, before any live generation or UI integration.
