# Item 10 reviewed seed dataset v1.0.0

Status as of 17 October 2026: reviewed seed consolidation complete. The version is frozen after successful validation; classifier training is still gated on the independent gold set and recorded team/adviser targets.

| Population | Questions |
|---|---:|
| Human-reviewed source rows | 672 |
| Included questions | 661 |
| Retained human rejections | 11 |
| Training | 459 |
| Validation | 102 |
| Synthetic test | 100 |

Use `classifier_questions.jsonl` or `classifier_questions.csv` for included records. `excluded_questions` retains the 11 rejected records for audit and must never be included in model inputs. JSONL stores topic/referral IDs as arrays; CSV separates those IDs with a pipe. CSV provenance objects use JSON strings.

The four primary classes and three scope classes remain separate. Only question_text is a model text feature. Reviewer names, provenance, labels, topic/referral IDs, split names and cleanup notes must not become model features. Fit preprocessing on training data only. Tune on training/validation data. Keep the synthetic test and independent gold set out of tuning.

The five group members each reviewed their assigned rows. The project owner then authorized Codex to perform discretionary repairs and consolidation. `annotation_status=human_reviewed_owner_authorized_cleanup` makes that distinction explicit. Original reviewer decisions are retained in original_review; consolidation_actor, consolidation_reasons and the change log disclose subsequent edits. This does not claim independent double human annotation.

Original question IDs and scenario_group_id are preserved. Original question text, language and split are separate provenance fields. The new split policy groups underlying single-issue scenarios across rights/steps intents, stratifies by primary/scope label, and ranks whole groups deterministically with seed item10-split-20261017. Targets are approximately 70%/15%/15% by groups; row counts reflect differing group sizes and exclusions. Mixed scenarios remain whole composite groups. The grouping eliminates detected full-scenario split overlap; shared generator style and recurring topic components remain limitations.

The reviewed referral directory corrects employment-specific seafarer routing. Explicit overseas deployment goes to DMW; onboard-pay disputes that do not specify overseas/domestic employment use qualified legal assistance through the existing PAO entry, subject to eligibility. MARINA STCW remains for certificate/training questions. Inherited contact details retain their Item 9 verification dates and were not certified as freshly checked by this cleanup.

Files:

- `dataset_manifest.json`: counts, source hashes, split policy, frozen file hashes and remaining prerequisites.
- `validation_report.json`: source/workbook/data consistency checks.
- `consolidation_changes.json`: every changed review row with before/after cells and reasons.
- `audit_resolutions.csv`: disposition of all 82 pre-cleanup findings.
- `referral_directory.csv`: versioned referral definitions.

The original Item 9 seed and five returned workbooks remain intact. Cleaned workbook copies are under `outputs/item10-review-cleaned/`. Code and explicit adjudication decisions are in `dataset/pipelines/item10/`.

Before training under the current plan, collect and lock the independent human-written/labeled gold set (practical target: at least 100 questions), then record the team/adviser-approved performance targets and abstention policy. The 100-row synthetic test split in this directory is not that independent gold set.
