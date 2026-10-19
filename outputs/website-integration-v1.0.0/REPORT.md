# Website integration — local development preview

Completed 19 October 2026. The website connects to the current classifier v1.5.10, retrieval v1.2.7 and verifier v1.0.5. The classifier packages, training, thresholds, calibration and legal-source records were not edited.

## What works

- New Ask questions use the real backend. The UI shows topic and coverage confidence, clarification or exclusion decisions, complete stored candidate provisions, source links, recorded status dates and use restrictions. A rejected wording interpretation produces clarification without fabricated labels or sources.
- The Performance page now reads the checksum-pinned `normalization-evaluation-v2.0.0` record, rather than mock fixtures. Overview stays simple; Detailed results contains F1, precision/recall, confusion matrices including withheld outputs, routing, known-relevant Hit@5, calibration and timing. Both views have searchable per-case expected/predicted labels and confidence. Clear/noisy, language and classifier-only/conditional-path filters use the same recorded predictions.
- Archived design conversations remain explicitly scripted examples. They cannot be mistaken for the new question path. New questions are temporary and independently analyzed; the backend does not save or train on them.
- A separate Together structured explanation adapter is wired behind the source preflight and claim postflight. Credentials remain server-side. There are no client-provided approval, review-store or policy switches. Source URLs/citations come from the trusted index; unverified model text is never returned as an answer.

**The explanation adapter is implemented, but substantive answer generation is not enabled.** The current verifier has no scoped current-source reviews and its generation/display permissions are false. Thus the application makes zero explanation calls, displays an explicit withheld state, and permits inspection of candidate sources. A separate reviewed release change, source/claim reviews and generated-answer evaluation are required before legal explanations can be served. `llm_integration_completed` remains false for this reason; `explanation_adapter_implementation_completed` is true.

## Run it

Run `C:\IA\start-website.ps1` in PowerShell and visit <http://127.0.0.1:5173/>. Existing preview processes may already be serving it. The script starts a hidden local backend on 8766 and runs Vite in the terminal; Ctrl+C stops the session and the backend it owns. Manual two-terminal commands and API boundaries are in `../../backend/application/README.md`.

The Vite `/api` proxy is for development. The `dist/` build requires a separate same-origin API proxy when served elsewhere. No public deployment, persistent conversation history or standalone browser API key was introduced.

## Verification

| Check | Result |
|---|---|
| New application integration suite | **18 tests passed**, no live provider calls |
| Frontend metric reconciliation | **174 numeric comparisons**, exact confusion matrices for both paths across all/clear/noisy subsets |
| Denominator/empty-data checks | Passed: language subsets, empty results, unavailable confidence and both withheld labels |
| Frontend build / lint | Passed |
| Real browser path | Real local labor classification and five candidate provisions; complete stored Article 83 text; confidence visible |
| Responsive behavior | Desktop split pane, mobile Sources/Back, detailed table scrolling; mobile document width equals 390px viewport |
| Browser console | No errors/warnings observed during the tested paths |
| Impeccable finish review | One misleading fixed deferral-count sentence corrected; follow-up **ship** verdict covers that scored fix |
| Documentation handoff | Incumbent system preserved; no new visual-world or design-system artifacts |

HTTP tests cover strict JSON, duplicate keys, unsupported fields, size/type limits, invalid methods/paths, exact origins, Host protection, no-store and sanitized errors. Explanation tests cover skipped calls on closed gates, source filtering, provider failures, redirects, request limits and withholding failed postflight drafts. Mocked future-permission tests are software checks, not real legal approvals or a live explanation evaluation.

The first HTTP attempt encountered the sandbox's localhost socket restriction. The complete suite then passed with approved execution allowing localhost connections. Browser servers likewise had to run outside that sandbox to become accessible to the local browser. No external service calls or personal-question exports were performed in this integration task.

Screenshots: `../../UI/UX/app/.impeccable/review/integration/`. Test logs and structured evidence are beside this report.

## Metrics interpretation

The default full pipeline selection shows **412/414 (99.5%)** correct topic and coverage labels, **418/424 (98.6%)** matching routes, and **78/83 (94.0%)** judged concern groups with a known-relevant hit in the first five. The page exposes the raw denominators and includes withheld labeled outputs as misses. Confidence calibration uses available predictions only and does not fabricate probabilities for withheld outputs.

The record contains **424 input forms across 167 families**, including repeated noisy variants, and **zero independent human questions**. These cases were inspected while repairing the system. High scores support development regression claims, not population accuracy, legal correctness or independent acceptance. The recorded noisy classifier-only topic score (251/252) is slightly higher than the conditional pipeline (250/252); the page discloses that distinction.

## Remaining work and one new finding

1. Source/currentness and scoped claim reviews, a reviewed generation/display policy change, and generated-answer evaluation before enabling substantive explanations.
2. Independent/generalization testing and owner acceptance. Earlier development misses remain documented in the frozen repair report.
3. **A new joined-concern segmentation edge case remains open.** “Private employee ako. Hindi binayaran ang overtime ko at ayaw ibalik ng landlord ang rental deposit.” routes entirely out of scope. Splitting the two concerns into separate sentences correctly yields mixed/partial support and searches only the labor concern. The UI suggests separate sentences. The exact synthetic diagnostic is recorded in `known-routing-edge-case.json`; it was not added retroactively to the 424-form metrics or hidden by rewriting the classifier.
4. Public hosting, API authentication/rate limits appropriate to exposure and persistence choices are later deployment work. This preview binds to loopback and keeps deployment permission false.

Pre-existing PRODUCT.md planning drift was reported by the documentation handoff and left outside this narrow integration. Current runtime facts and commands are in the app/backend README files and this report.
