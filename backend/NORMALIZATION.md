# Conditional sentence interpretation

Version `conditional-normalization-v3.0.0` retains whole-sentence interpretation and adds scope-anchor preservation. The classifier now has separate conservative local spelling features (`scope-typing-v1.2.0`) before segmentation. The optional first LLM can interpret the **whole question**: unfamiliar phonetic/jeje spelling, missing/repeated vowels, letter/digit substitutions, joined/split words, and messy grammar. Its output is a complete proposed question, not a list of dictionary substitutions.

The website uses the local classifier/retrieval pipeline and conditional wording adapter. The separate explanation adapter remains behind closed verifier generation/display gates. Classifier learned weights, thresholds and approval requirements remain unchanged.

## When the LLM runs

The default terminal mode is `--normalization auto`.

1. The classifier/verifier inspects the original question first, using its local spelling/boundary features. Training wordforms, names, numbers and literals are protected; ambiguous dictionary candidates remain unresolved. This does not claim a faithful full-sentence rewrite, and the original question stays in the output.
2. A decisive supported/retrieval or referral route bypasses the LLM, even if the spelling looks unusual. This preserves the baseline result; it does not prove the baseline is right on every noisy input.
3. For a clarification route, a local gate looks for shorthand/nonstandard character patterns. Familiar ordinary words are excluded from the character-shape trigger. If the classifier cannot identify a reliable concern, several unfamiliar words can also trigger interpretation. A missing employment category or low score alone is not a trigger.
4. Only a validated interpretation is classified/retrieved again. The original routing is recorded under `normalization.baseline_routing` when interpretation is needed.

There is at most **one LLM request per question**, with no retry or automatic provider fallback. Tested clear questions make zero calls, including clear questions that need employment details. This is a heuristic, not a perfect readability detector: clear unusual language can trigger it, and some noisy language can bypass. A classifier that already understands compressed wording may proceed without an LLM call. Messages needing normalization above 400 words ask to be split before a request; all questions still have the existing 8,000-character input limit.

## Interpretation and checks

The provider returns exactly `status` (`normalized`, `unchanged`, or `unclear`) and `normalized_question` (empty for the last two statuses). It receives the full question and readability hints. It can repair grammar and punctuation anywhere, but is instructed to preserve language, all separate concerns, actors, payer/payee roles, negation, uncertainty and event details. It must not answer, classify, cite laws or fill missing facts. `Amo` does not establish private-sector employment, and `bayad` does not establish salary.

Local validation checks:

- Input/output shape, length and control characters.
- Ordered numeric facts, agency tokens, recognized names/acronyms and literal quotations/URLs.
- Observable changes to participant groups and negation.
- Content retention in both directions using spelling/phonetic similarity and joined-word comparisons. This permits unfamiliar repairs while blocking many added or dropped facts/concerns.
- New employment/domain terms need a spelling counterpart in the original.
- Recognized scope anchors and joined anchor phrases must survive the proposed interpretation. This blocks plausible but wrong expansions such as `sngl` to `single` and `bnling` to `billing`.
- Matched split/merged spans can support recovered words and facts; absent categories/acronyms stay unsupported. The conjunction `and` is excluded from phonetic negation counting, and `do I nd to` can mean `do I need to` without treating all `nd` forms as positive.
- Repeated syllables and internal repeated consonants in compressed wording have additional aspect guards; these can also cause conservative deferrals.
- Lexical polarity reversals such as authorized/unauthorized are rejected. Tripled-letter repairs must preserve the collapsed character sequence, blocking extra verb-aspect syllables or substituted consonants. Very short ambiguous content cannot silently become a grammatical filler. These repairs were informed by the first development comparison; they are regression controls, not a semantic-equivalence proof.

These checks **do not prove semantic equivalence**. They can miss subtle changes in meaning or reject a faithful paraphrase. The result explicitly records `meaning_preservation_guaranteed: false` and `performance_evaluation_completed: false`; the latter refers to independent quality validation, not the separate completed development comparisons. Ambiguous output, invalid JSON, failed checks, refusal, timeout or missing configuration stops inference on the proposed rewrite and asks for clarification. The report includes a safe validation-failure code; rejected interpretations are not passed to retrieval.

Original text, accepted interpreted text, computed character edits, gate reason, model, usage and timing remain separate. The pinned verifier receives the accepted interpretation, so its hashes/reviews bind that text. No approval is transferred from the original to the interpretation. Current legal-answer/display/deployment permissions remain false. The inspection-only payment follow-up stays separate from the unchanged verifier result, and clarification labels are tentative.

## Provider configuration

Together is configured locally with **`openai/gpt-oss-120b`**, selected after the smaller Qwen model produced inconsistent interpretations in development. The request uses `reasoning_effort: low`, a 1,536-token total output cap, a 12-second socket timeout, structured JSON, no tools, and no retries/redirects. Reasoning consumes part of that output cap; returned usage is provider-reported. Availability and settings were checked against Together's [model catalog](https://docs.together.ai/docs/serverless/models), live model inventory, and [reasoning documentation](https://docs.together.ai/docs/inference/chat/reasoning). This is still a development selection, not an aggregate quality result.

The existing key remains a Windows-user DPAPI-encrypted blob under ignored `.local/normalizer/`; only provider/model selection is plaintext. No key is embedded in source, browser code or logs. Together receives the full flagged question; its account/data policies apply. The original `Qwen/Qwen3.5-9B` adapter path remains available when explicitly configured, with reasoning disabled and a 768-token cap. An optional OpenAI Responses adapter also remains available; no OpenAI API key is required for the active Together model.

```powershell
cd C:\IA
& .\.venv-item10\Scripts\python.exe -m backend.terminal_test
```

Restart any existing terminal inspector (`/quit`, then run the command again) after changes. Questions are independent; submit the full question again with actual missing facts when clarification is requested.

To replace the key, run `python -m backend.normalizer_credentials` in the pinned Python environment and use its hidden prompt. Environment variables `RECTO_NORMALIZER_PROVIDER`, `RECTO_NORMALIZER_MODEL` and the selected provider's API key override local settings. Unknown providers are rejected. There is no automatic `.env` loading or provider fallback. With no credentials, clear messages still work locally; flagged messages ask for clearer wording without a request.

For the original local baseline:

```powershell
& .\.venv-item10\Scripts\python.exe -m backend.terminal_test --normalization off
```

The Item 13 evaluator also continues to run its original pinned baseline without this layer. Existing aggregate metrics must not be presented as v2 pipeline metrics.

## Development validation

```powershell
& .\.venv-item10\Scripts\python.exe -m unittest backend.test_normalization backend.test_terminal_test -v
```

The software tests use synthetic provider replies and mocked HTTP, plus a real synthetic Windows-encryption round trip. They cover sentence-level grammar repair, unfamiliar phonetic forms, split/merged words, letter/digit substitutions, fact-change rejection, unknown-wording fallback, one-request limits, clear-message bypasses and unchanged inference/approval boundaries.

Historical v2.0.0 live checks on 2026-10-19 with the selected Together model included:

- Reported `inde ako nakoha yung bayad ako sa amu ako... anu pwede gawin.,?` became `Hindi ako nakakuha ng bayad ko sa amo ko... ano pwede gawin?`. It still asks about the payment/work arrangement; missing facts are not supplied.
- `private employee aqoh, hindeh pa nabayarran yung sahod qoh... papanu poh?` became `Private employee ako, hindi pa nababayaran yung sahod ko... paano po?`, then retrieved five candidate provisions.
- `sa storeh aqoh bumilii, ayaw nila irefund yung sirang itemm... anuh gagawenn?` became `Sa store, ako bumili, ayaw nila irefund yung sirang item... ano ang gagawin?`, then retrieved one candidate provision.
- The version using ambiguous `nlah` was interpreted as `na lang` rather than `nila`; validation rejected that proposed rewrite. Gibberish `xkzpt wrkplzzz` also requested clarification.
- A clear consumer question and a clear salary question made zero requests. The salary question still asked for the missing employment category.

These are inspected development examples, not independent human gold or broad accuracy measurements. The last observed total times were about 1.12 seconds for the reported example, 0.99 seconds for the private-work example, and 1.43 seconds for the explicit-pronoun consumer example; these single-run observations do not establish latency guarantees. Earlier Qwen smoke results in the status file are historical.

Before relying on quality improvements, evaluate trigger errors, meaning-changing edits, false rejections, domain/scope accuracy, partial/out-of-scope recall, retrieval relevance, latency and usage on separately labeled examples. Preserve the raw baseline and record the normalizer/prompt/model version. The paired AI development comparison is now complete; independent/generalization validation remains pending and quality approval has not been granted.

For the paired batch comparison, see [NORMALIZATION_EVALUATION.md](NORMALIZATION_EVALUATION.md).


## Paired evaluation and repair

The first frozen v2.0.0 study is preserved at `outputs/normalization-evaluation-v1.0.0/REPORT.md`. It found noisy-input topic accuracy of 84.2% without normalization versus 66.3% with the original conditional layer; 28 additional wording deferrals contributed to the drop. An AI audit of 34 accepted rewrites flagged five meaning changes and one uncertain rewrite. Four clear inputs unnecessarily called the LLM. This is why isolated successful examples did not establish readiness.

The v2.1.0 repair checks the raw question first and tightens the guards described above. The follow-up at `outputs/normalization-evaluation-v1.1.0/` uses 67 recorded families absent from that first selection (134 input forms). They are fresh only relative to the first normalization comparison; they are still reused AI development material. No new independent human gold, classifier training or UI connection is created. The follow-up contains no previously judged retrieval cases, so its retrieval relevance must be reported as unmeasured rather than inferred from returned candidates.


The v2.1.0 comparison and final failed payment smoke are preserved in the [earlier summary](../outputs/normalization-evaluation-summary-v1.0.0/REPORT.md).

The v2.2.1 diagnostic repair and its results are preserved in the [preceding report](../outputs/normalization-repair-summary-v1.0.0/REPORT.md). Provider responses to the original payment example have varied; acceptance in a single smoke test did not establish reliability.

The [v3.0.0 repair report](../outputs/normalization-repair-v2.0.0/REPORT.md) records the identical 424-form replay: 99.2% conditional noisy topic accuracy, 100% noisy partial-support recall, 227 passing software checks, and two accepted LLM reconstructions with no AI-flagged meaning failures. The local classifier alone scores 99.6%; the LLM's extra conservative deferral is counted. These are inspected development results, not independent validation. Website quality approval remains pending owner review and the separate acceptance requirements.

If the provider fails to preserve the original payment wording, inference on that rewrite stays blocked. The inspection follow-up now asks the actual payment/employment facts in Tagalog instead of giving only a generic retyping request. This post-evaluation clarification-copy change does not change labels, routing, retrieval or rewrite acceptance. A captured-response replay and regression test verify it without a new API request.

`ConditionalNormalizer(..., capture_diagnostics=True)` is an explicit development-only opt-in to retain bounded proposed wording in `development_diagnostic`. The batch evaluator enables it; normal terminal use does not. It never licenses rejected text for inference or logs provider credentials, headers or response bodies. Replayed provider responses are new observations and can differ, even with temperature zero.


## Current-stack comparison (19 October 2026)

The [436-form paired comparison](../outputs/current-stack-validation-v1.0.0/REPORT.md) uses classifier v1.5.12, retrieval v1.2.8, verifier v1.0.7 and this v3.0.0 normalizer. It retains 425/425 topic and coverage labels and 93/93 known-relevant Hit@5; expected routes improve from 434/436 local to 436/436 conditional. All 179 clear inputs bypass. Five noisy inputs call Together, three interpretations are accepted and two retain clarification after rejection. All three accepted rewrites received a disclosed AI semantic audit with no flagged meaning changes. Estimated token cost is $0.00110265, not an invoice.

The two prior routing errors resolve in this run without changing the runtime prompt, validation, model, thresholds or weights. Provider variability and the five-call sample still limit any generalization. These are inspected AI development results; independent quality approval remains pending. The Performance page retains its labeled local-only default and older historical comparison; this result lives in its separate versioned report. Fresh human intake and explanation-readiness materials are in `outputs/current-stack-validation-v1.0.0`.
