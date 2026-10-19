# What Item 13 will do

Item 13 evaluates whether the connected system makes the right decisions on questions. It is the evaluation milestone, and it has not started. Item 14 connects the finished pipeline to the application.

The current offline path is:

**Question → classifier → supported concerns → legal retrieval → evidence/citation verifier → development candidate, clarification, referral or evidence gap.**

An LLM drafter is not connected yet. Actual generated-answer quality cannot be measured until that component exists and the relevant source/support conditions are resolved. Exact quotation previews and simulated review approvals are not final legal answers.

## First phase: evaluate the working offline pipeline

Build a repeatable runner and a results table with the question, scenario family, language, expected domain/scope, expected relevant provisions, expected action, actual result, classifier probabilities, ranking values and failure reasons.

Cover labor, consumer, fully supported mixed questions, partially supported mixed questions, exclusions, missing facts, misspellings and English/Taglish wording. Include known evidence gaps such as final pay/COE. Use independent scenario families so related variants do not leak between development and final test.

Existing project questions can support development and regression work. The 200 AI-reviewed general/typing questions and 67 retrieval cases remain development material; copies or light edits do not make a fresh independent holdout. The current independent-intake validator requires at least 100 completed, independently human-written and labeled questions; its existing 100 rows are blank forms.

Measure:

| Part | What the result means |
|---|---|
| Classification | Correct domain/scope, per-class precision/recall/F1 and recall of partially supported concerns |
| Confidence | Whether classifier probabilities agree with observed label correctness; kept separate from legal-answer confidence |
| Retrieval | Whether known relevant provisions appear in the top results, with Hit@5 and ranking measures |
| Citations | Correct document/provision IDs and exact quotation/locator consistency |
| Mixed questions | Correct concerns answered or withheld, with no excluded concern leaking into evidence |
| Clarification/referral | Appropriate requests for facts and limits/referrals for recognized exclusions |
| Coverage/declines | How much eligible material the system can handle, and where it declines despite sufficient verified support |

Freeze the evaluation protocol, acceptance criteria, scenario groups and final-test membership before opening final results. Repairs informed by inspected cases stay development work. Report denominators, language/topic strata, intervals suited to the sampling/groups and an error log; do not present a perfect small development score as real-world accuracy.

## Second phase: evaluate actual generated answers

Connect a controlled offline LLM drafter using retrieved evidence and the structured Item 12 contract. Record provider/model/prompt settings and every drafting/verifier outcome. Keep live answering disabled during testing. No provider was selected and no API calls were authorized or made by this audit.

Resolve the source-currentness/applicability conditions for the chosen answer topics. Current-guidance mode presently has no real scoped reviews, and arbitrary paraphrase support is still a review gate. The system must report these blocks honestly; rejecting everything is not a successful answer-quality result.

For generated answers, measure citation accuracy, claim support, missing qualifications, unsupported-claim rate, concern coverage and false declines. If no substantive answers are produced, answer accuracy and unsupported-claim percentages are unavailable; zero answers must not be reported as perfect accuracy.

A licensed Philippine legal professional should review selected generated answers for relevance, source support and clarity, as recorded in the proposal. Independent human question/label collection and any team/adviser acceptance remain separate requirements. AI checks can assist with development but do not supply those people's authorship, judgment or approval.

## Deliverables and completion

Item 13 should produce a versioned evaluation set with truthful provenance, a repeatable runner, per-question outcomes, metrics with appropriate uncertainty, an error/repair log and the required independent/legal review evidence. Software regression success, formal evaluation acceptance and deployment readiness must be recorded separately.

The current audit permits preparing the first offline phase. Full generated-answer evaluation and deployment remain blocked by the documented prerequisites. No Item 13 benchmark, final-test run, LLM integration or deployment was started by this audit.
