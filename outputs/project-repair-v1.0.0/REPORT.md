# Project repair — 19 October 2026

The repair implements the reproducible software fixes from the [32-gap audit](../project-gap-audit-v1.0.0/REPORT.md). It also adds missing local history, privacy/operating controls, measured whole-application diagnostics, recovery tooling and current documentation. It does **not** claim that every validation or legal-data gap is closed.

Current packages: **classifier v1.5.15 / retrieval v1.3.1 / verifier v1.0.9**. Fitted weights, calibration, thresholds and training membership are unchanged. No legal source was auto-approved, and no AI-authored question was relabeled as independently human-written. Previous immutable packages, failed/unpromoted builds and all three application replays remain preserved.

## What changed

- Complaint/intent routing now distinguishes incidental general vocabulary, explicit negated categories, clearly historical background and metalinguistic quotations. Genuine supported-plus-excluded concerns stay partial. Safety checks cover more present/Tagalog forms and skip clearly quoted/historical examples; they remain best effort.
- Employer-dismissal searches exclude employee-resignation headings unless resignation is actually requested. Citation labels include distinguishing locators; citation navigation is concern-aware and highlights exact passages inside complete source text. Field-confirmed referrals and missing-source notices are now rendered.
- Generated drafts select numbered source passages. The backend restores exact bytes, rejects unknown/cross-concern selections, invented numeric facts, prohibited guarantees/excluded advice, and incomplete/invalid claim contracts. A separate same-model structured support assessment must pass every claim. This is automated development checking, **not independent legal entailment or currentness approval**.
- Provider failure isolation preserves classification/sources. Short inference locks, four active question slots, cheap health, signed-session cancellation, request deduplication/rate controls, an outage circuit and shared daily request/cost reservations replace the long provider-held lock. Healthy replies reset the outage streak. There are no automatic retries.
- Local-only AI choice and best-effort identifier masking precede provider export. History is explicit opt-in, Windows-user DPAPI encrypted, browser-scoped, capped at 500 turns and retained for 30 days with access-time cleanup. Open/export/delete are implemented. Exported JSON is readable; temporary request-cache cleanup is lazy. Neither masking nor disk deletion is a complete privacy/forensic-erasure guarantee.
- The launcher compares runtime identity, skips occupied ports and stops only its own child API. Frontend history, settings, privacy, source checks, failure states and measured Performance reporting are wired to the actual backend. A canceled-report-load race found during browser QA is fixed. Word reveal uses already checked text and supports immediate/reduced-motion reading.
- The vulnerable source-map-js development dependency and pip installer were patched. Reproducible setup/check scripts, a CI workflow template and a checksummed source/runtime checkpoint workflow were added. Public hosting remains unconfigured.

## Verification

| Check | Result |
|---|---|
| Backend unittest discovery | 162 passed |
| Classifier package suite | 65 passed |
| Retrieval package suite | 43 passed |
| Verifier package suite | 37 passed |
| Additional concern/independent-intake/referral suites | 16 passed |
| Frontend interaction/structural accessibility tests | 16 passed |
| Saved metric reconciliation | 261 numeric comparisons passed |
| Frontend build / lint | Passed |
| npm / installed Python advisory scans | No known findings after patches |
| Fresh Python recovery environment | Exact dependencies installed; pip check and pinned runtime inference passed using existing source/model files |
| Recovery archive | v1.0.1: 834 hashes verified; extracted to a new root and passed actual source/model integrity and local inference |
| Launcher lifecycle | Version-aware reuse passed; temporary Windows venv wrapper and actual listener child both stopped |

Test reruns are not additional independent experiments. Structural axe checks exclude color contrast because jsdom has no layout; browser checks and these tests do not establish WCAG conformance or screen-reader/PWD usability.

Browser verification covered local-only retrieval, opt-in save/reopen, real synthetic Taglish explanation, exact source highlights, mobile source/return navigation, 390px overflow, 22px/high contrast, and live report loading. Capture/review evidence is under `UI/UX/app/.impeccable/review/repair/`. Detector findings: none. Final UI disposition and documentation are recorded in the finish-review/documentation reports there.

The fresh full UI review returned **ship for the reviewed interface**. A malformed Settings capture was corrected before that review. DESIGN.md and its sidecar now document the built existing system; their panel rendering was not independently opened. This verdict does not grant legal or accessibility approval. The final API identity matches the launcher, both website ports use the current API, and the user's existing port-5173 Vite terminal process was preserved. The recoverable checkpoint is [recto-local-repair-v1.0.1.zip](../releases/recto-local-repair-v1.0.1.zip); its initial missing-log draft was removed after the corrected extracted runtime passed. Temporary recovery environments/extractions were cleaned up; validation receipts remain.

## Measured development behavior

The local-only frozen run uses the same 436 AI inputs from 171 wording families: 425 labeled and 11 routing-only forms. Topic/coverage match **425/425**, route match **435/436**, known-relevant Hit@5 **93/93**, Hit@1 **73/93**. One noisy administrative-appeal input conservatively clarifies. Candidate integrity and exact-excerpt checks pass; this does not establish every candidate's relevance or legal support.

The final complete application replay, [v1.2.0](../application-evaluation-v1.2.0/REPORT.md), returned **436/436 packets**, with topic/coverage **424/425**, routes **435/436**, **82 explanations / 125 paragraphs displayed** and **354 withheld**. Four wording requests ran: one accepted, two clarified and one unavailable. The unavailable wording result caused the remaining labeled abstention. Per-question confidence remains a label score, never legal-answer accuracy.

Whole-request median was **2,594 ms**, P95 **9,039 ms**, maximum **23,171 ms**. There were **459 provider attempts** and **$0.452239 estimated** usage/reservations at configured rates. Failed attempts without token usage keep a conservative reservation; this is not confirmed billing. Zero generated responses lacked the automated support pass.

Withheld reasons: 91 unsupported/clarification routes, 28 missing source contexts, eight missing related authorities, 76 claim/selection/numeric-contract failures, 72 negative automated support assessments and 79 provider failures. Contract failures include empty model abstentions; they are not all quotation errors. Verbatim quotation-copy failures fell from 76 in v1.1.0 to zero with source selection. Explanation availability is still limited and must not be hidden behind the classifier's high development scores.

Runs v1.0.0 and v1.1.0 are preserved, including circuit/outage behavior and lower availability. Their estimated usage was $0.084449 and $0.428536 respectively. Across all three runs the estimate is about $0.9652, excluding the small website smoke check. These were full replays after general software changes, with no selective case retries or gold-label changes. The final inference-file hashes are pinned separately from later reporting/documentation edits.

All cases are reused, inspected **synthetic development data**. No independent human population confidence, answer accuracy, legal F1, source currentness or professional approval is inferred from these results. All 125 displayed paragraphs are in `generated_answer_review_queue.jsonl` with blank independent verdicts.

## Disposition of the original gaps

“Fixed” below covers the reproduced defect and its tests, not every possible future input. “Mitigated” retains a stated limitation. “Pending” needs independent people, unavailable official evidence or an owner release decision.

| Gap | Disposition |
|---|---|
| G01 incidental vocabulary exclusions | Fixed with contrastive complaint tests. |
| G02 negated excluded category | Fixed through segmentation/classification. |
| G03 background versus requested concern | Mitigated by explicit history/quotation/negation policy; broader intent annotation remains needed. |
| G04 safety misses/overblocking | Reproduced forms fixed; multilingual emergency detection remains best effort. |
| G05 false decisive bypass | Known false exclusions repaired; decisive bypass retained and still needs independent trigger testing. |
| G06 unsupported claims with real quotes | Hard invalid examples rejected; mandatory automated support added. Independent legal support remains pending. |
| G07 resignation top hit for dismissal | Specific actor-direction ranking repaired; comprehensive relevance/sufficiency judgments remain pending. |
| G08 final pay / MO28 | Mitigated with explicit missing-source notices and withheld explanations. Verified full-text/review remains pending. |
| G09 empty trusted legal review store | Pending; zero source/claim approvals preserved. |
| G10 OCR/text review queue | Pending; 258 original records, including the 255 OCR subset, remain human review work. AI proposals are not approvals. |
| G11 currentness/applicability | Pending legal/source assessment; expiry/review gates retained. |
| G12 ambiguous citations / no highlight | Fixed: distinct locators, concern-aware navigation and exact highlights. |
| G13 missing live referrals | Live display fixed. Unconfirmed fields stay hidden; unresolved agency confirmation remains pending. |
| G14 fresh independent questions | Pending: zero authored independent questions; no fabricated gold set. |
| G15 current full pipeline unmeasured | Current synthetic application replay completed; HTTP/UI delivery checked separately. Independent validation remains pending. |
| G16 calibration/generalization | Mitigated with measured ECE and explicit label-confidence limits. No new calibration fit or legal-confidence claim. |
| G17 reused development data | Provenance/denominators retained. Fresh independent protocol/collection remains pending. |
| G18 complete-pipeline reporting | Added measured availability, withholding, latency, usage/cost and code-binding status in Detailed results. No legal-answer score invented. |
| G19 missing history/database | Implemented opt-in encrypted, browser-scoped history with open/export/delete and tests. |
| G20 independent question workflow | Retained deliberately; composer/new-question/clarification copy makes it explicit. No hidden conversational memory. |
| G21 malformed provider isolation | Fixed; incomplete/malformed/redirect/provider failures withhold drafts and retain sources. |
| G22 provider lock blocks health/chat | Fixed for bounded local concurrency. No public multiuser load claim. |
| G23 no backend cancellation | Implemented, including racing cancel, socket closure and owner isolation. Already processed work may still cost. |
| G24 port/version reuse | Fixed with free-port selection, exact runtime identity and owned-process lifecycle. |
| G25 unbounded/provider coupling | Daily attempt/estimated-cost limits, per-browser rate controls, dedupe, circuit and independent switches implemented. Provider-side caps remain an operator task. |
| G26 privacy/key rotation | Local-only choice, masking, encrypted opt-in retention and disclosure implemented. Provider policy review/key rotation remain owner work. |
| G27 public deployment/operations | Local controls and deployment/recovery handoff prepared; TLS/authentication/hosting/public operations remain pending. |
| G28 vulnerable dependencies | Patched and rescanned; no known current npm/Python findings. |
| G29 frontend/accessibility coverage | Automated regression suite and bounded browser checks added. Actual assistive-technology/user evaluation remains pending. |
| G30 stale current docs/contracts | Current guides, product context, inventory/status and both explanation-display contracts updated. Historical reports stay historical. |
| G31 no whole-project checkpoint/CI/recovery | Reproducible scripts, CI template, fresh dependency check and checksummed local archive supplied. Remote CI and public deployment are not claimed. |
| G32 final legal/user/owner/adviser acceptance | Pending; required people must supply actual decisions. |

See [HUMAN_HANDOFF.md](HUMAN_HANDOFF.md), [SOURCE_FOLLOWUP.md](SOURCE_FOLLOWUP.md) and [deployment/recovery](../../DEPLOYMENT_AND_RECOVERY.md) for the remaining actionable work. The official-source fetch limitations are recorded; their missing approvals were not bypassed.
