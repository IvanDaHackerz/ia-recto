# Explanation-layer readiness

This is a repository-state handoff, not a new legal-currentness review or approval. The adapter already exists at `backend/application/explanation.py`; connecting an additional provider is not the missing implementation step.

The current verifier has **zero trusted source reviews and zero trusted claim reviews**. Generation and display remain disabled. The 436-input local packet records `scoped_currentness_review_missing` across 471 retrieved components, and eight components also report the missing related authority `MO_28_1986`. Candidate frequency and reason counts are saved with source hashes in `explanation_readiness.json`.

Before substantive explanations can be enabled:

1. Resolve the applicable source/extraction/currentness work and required related authorities for the intended answer scope. The existing source-review intake is `outputs/pre-item12-repair-2026-10-17/source-repairs/source_review_intake.jsonl`; AI comparisons and the outstanding issues are recorded in `outputs/source-contact-followup-v1.0.0/FOLLOWUP_REPORT.md`. Preserve those histories and obtain actual required reviewer decisions.
2. Review the intended release policy explicitly. Current source and claim review bindings include question/component, source hashes, policy/index version and validity dates. A document-level sign-off alone will not authorize arbitrary new questions. Decide and validate how scoped reviews apply to the website's actual usage before any gate change; do not remove these bindings merely to make an example produce text.
3. Freeze a generated-answer evaluation protocol with reviewed eligible sources and independent reference judgments. Evaluate factual grounding, citation/quote integrity, coverage of every supported concern, exclusions, missing facts and appropriate deferrals. Provider failure and invalid drafts must remain withheld. Existing exact-excerpt checks do not measure paraphrase or legal-answer correctness.
4. Only after the required reviews and answer testing should a separately reviewed release change enable generation/display. Re-run the verifier, API and website checks against that exact version. Deployment and independent acceptance remain separate recorded decisions.

The current development packet's most frequently retrieved documents are the Labor Code IRR, Consumer Act and renumbered Labor Code. That helps prioritize review effort; repeated development hits do not establish complete legal coverage. MO 28's absence must be addressed for affected thirteenth-month-pay guidance before that dependency can pass.

No source/claim approval, current-law conclusion, generated legal answer or permission change was created by this handoff.
