# AI-reviewed evaluation data v1.0.0

As of 17 October 2026, Codex completed the project-owner-authorized review of all 200 AI-authored questions. 91 wording revisions and 2 topic-tag corrections were recorded. All 200 are AI-approved for exploratory evaluation. No human approval, professional legal review, independent human authorship or model accuracy is claimed.

- evaluation_questions: 100 questions, 25 per primary class; 50 English and 50 Taglish.
- typing_questions: 100 questions across 20 scenario families; 80 labeled (20 per primary class), plus 20 clarification cases with null primary/scope labels; 50 English and 50 Taglish. The 100 typing rows represent 20 underlying scenarios.

Original text is retained in original_question_text and original workbooks. Revised text, taxonomy tags, AI actor, dates, source hashes and decisions are recorded separately. human_review_status=not_performed; origin=ai_authored; review_status=ai_approved. Review logs cover every ID. Topic corrections: EVAL_042 wrong model is a sales/description issue, not a presumed physical defect; EVAL_050 unexplained charges support complaint routing without presuming deception. Three labor questions now explicitly state private employment. Informal wording and readable typing errors are retained.

These sets are development benchmarks, excluded from training. They remain unlocked because the owner intends revisions during model testing. If results inform changes, feature selection, model selection or thresholds, do not later report these as an untouched final holdout. Keep all variants of a scenario family together. Report classification metrics on 180 labeled records separately from clarification behavior on 20 unresolved records. Missing facts do not create a fifth primary class and must not be forced to out_of_scope. Vocabulary and exact-match screening do not establish semantic independence; legal scenarios and AI style can overlap.

The frozen 661-record human-reviewed seed and its gates remain unchanged. The recorded independent human-written/labeled gold requirement is not satisfied by this AI review. Performance targets and abstention policy remain to be agreed before final model evaluation. No classifier has been trained.

Validation checks count, IDs, exact overlap, topic existence and scope, primary/scope derivation, language metadata, provenance, scenario-family handling, workbook completion formulas and source checksums. Saved-file layout and feature checks are recorded in validation_report.json. These are dataset checks against the project's scope, not current-law certification. Legal-source freshness and pending OCR gates remain as recorded.
