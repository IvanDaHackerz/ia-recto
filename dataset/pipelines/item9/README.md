# Item 9 — Question classification and referrals

Item 9 creates the examples that will eventually teach the classifier how to route a user's question. It does not train a model yet.

Item 10 is the human-review and classifier-training stage. Its prerequisites and training plan are documented in `dataset/pipelines/item10/README.md`.

## Why Taglish is included

Actual Filipino users may ask in English, Filipino, Taglish, shorthand, or imperfect grammar. A classifier trained only on formal English could fail before retrieval even begins. The current seed set therefore includes English and conversational English-Taglish questions, with the style recorded in `language_style` so performance can later be measured separately.

The present Taglish is synthetic and sometimes deliberately simple. Filipino-speaking reviewers should correct awkward phrasing and add natural variations, misspellings, incomplete questions, and other realistic forms before the data becomes a final gold-standard set.

## Recommended LLM and classifier architecture

Do not translate a Taglish question into English and throw the original away. Preserve both versions.

1. The classifier reads the original question.
2. The system records its domain, supported and excluded topics, scope label, routing action, and confidence.
3. The LLM may optionally create a normalized English search query.
4. Retrieval searches with the original question and the normalized query.
5. Only answer-eligible legal provisions pass to the answer-generating LLM.
6. The LLM receives structured classifier results, retrieved evidence, legal-status warnings, and permitted referrals.
7. Citation and safety checks run before the answer is shown.

The English normalization is a search aid, not the source of legal truth and not the classifier's only input. If classification confidence is low, ask the user to clarify or use a separately recorded LLM routing fallback. Do not allow the LLM to silently override the classifier.

This design permits separate evaluation of English classification, Taglish classification, optional normalization, retrieval, citations, and unsupported claims. It also preserves the independent classifier evaluation required by the project proposal.

## The four classifier labels

- `labor` — the question contains only a supported labor topic.
- `consumer` — the question contains only a supported consumer topic.
- `mixed` — either both supported domains appear, or a supported question also contains an excluded issue.
- `out_of_scope` — the question contains no supported topic and needs a limitation plus an appropriate referral.

The separate `scope_label` records whether the question is fully supported, partially supported, or unsupported. This distinction prevents a mixed question from being treated as entirely answerable.

## How the seed questions were built

The pipeline uses all 42 Item 6 taxonomy topics. Each topic has four realistic situations. Supported topics receive English and conversational English-Taglish forms. Excluded topics use direct questions asking whether the system can help or where the user should go. Mixed examples combine either:

1. one supported labor issue and one supported consumer issue; or
2. one supported issue and one excluded issue.

Questions derived from the same underlying situation share a `scenario_group_id`. Every group is kept entirely within train, validation, or test. This avoids evaluation leakage caused by putting near-paraphrases of the same situation into different splits.

## Important review rule

Every question begins with:

`annotation_status=machine_generated_needs_human_review`

The data is a structured seed set, not a finished gold-standard training set. A human reviewer must confirm the wording, topic labels, routing action, and referral before the row can be used for final classifier training or evaluation. Real anonymized user questions should later be added as a separate provenance class.

## Referral directory

The referral directory is stored separately from classifier text because agency portals, phone numbers, and email addresses can change without requiring model retraining. Each row records the official agency, appropriate use, first step, official URLs, available contact details, verification source, verification status, and last-verified date.

Entries whose detailed contact page could not be verified contain only an official government website. The pipeline does not invent or copy an uncontrolled phone number.

## Outputs

- `classifier_questions.csv` — human-review and annotation format
- `classifier_questions.jsonl` — lossless machine-learning format
- `classifier_questions.parquet` — analytical format
- `referral_directory.csv` — versioned official referral destinations
- `dataset_summary.json` — label, split, language, topic, and routing counts
- `validation_report.json` — structural and safety validation

Run the complete build with:

```powershell
& .\dataset\pipelines\item9\run_item9.ps1
```

Passing validation means the labels are internally consistent, all taxonomy topics are represented, paraphrase groups do not leak across splits, and referral records have verification sources and freshness dates. It does not replace human annotation review or classifier evaluation.
