# Fresh-question handoff

The current implementation is classifier v1.5.12, retrieval v1.2.8 and verifier v1.0.7, with conditional wording normalizer v3.0.0. The fresh test below has **not been collected or run**. Existing 436-form results are AI development results.

`human_intake.jsonl` is a working copy of the project's existing 100 blank intake slots. Every question, label and authorship field is still blank. It is not a dataset of 100 completed human questions.

## Collect before looking at model outputs

1. Have people write their own fictional concerns in their ordinary English or Taglish. Include clear and naturally messy typing. Do not give them AI drafts or ask them to reword the existing development questions. Avoid personal names, account identifiers and real private disputes.
2. Use the approved project scope as the annotation guide. Include labor, consumer, fully supported mixed, partially supported mixed and out-of-scope situations; ensure every topic/coverage class is represented. A balanced collection can help class comparisons, but its overall accuracy will not estimate natural website traffic prevalence.
3. A separate annotator should label each completed question before seeing classifier predictions. Record the actual author/annotator IDs and writing/annotation dates, language, scenario family and genuine provenance. Set `origin` to `independent_human_written`, `ai_assisted_writing` and `used_for_tuning` to false only when that is true. A rewritten AI draft remains AI-assisted.
4. Review ambiguous labels, missing employment/seller facts and near-duplicate scenarios before scoring. Do not invent labels for questions that should only request clarification; the current independent classifier intake supports the five valid labeled pairs. Keep a separately declared routing-only collection for missing-context questions rather than forcing such questions into these labels.
5. Freeze the completed input bytes and agreed labels, audit overlap with training and **all** development packets (including outputs), then freeze the final evaluation protocol. Do not tune on the held-out run and call its replay independent.

The existing project validator requires at least 100 completed independent questions, all four primary classes and all three coverage classes. It checks provenance attestations and exact normalized duplicates; it does not prove authorship or detect every semantic overlap. An independent collection cannot be completed by Codex writing and approving the questions.

From `C:\IA`, after the intake has actually been completed:

```powershell
.\.venv-item10\Scripts\python.exe dataset/pipelines/item10/validate_independent_gold.py --input outputs/current-stack-validation-v1.0.0/human_intake.jsonl --report outputs/current-stack-validation-v1.0.0/human_intake_validation-v1.json
```

Use a new report path for later attempts. The validator checks existing processed Item 9/10 questions; the additional all-output and scenario-overlap audit in step 5 is still required. A passing intake check does not itself run final evaluation or approve deployment. Accuracy/F1, per-class precision/recall, routing, judged retrieval, abstentions, confidence calibration and family-aware uncertainty should be reported on the completed held-out run.
