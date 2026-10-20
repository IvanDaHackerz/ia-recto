# Conversational guidance repair — 20 October 2026

The website now gives every **completed analysis** a readable response. A valid
key alone does not guarantee a completed provider request or a valid AI draft;
source-based local responses therefore remain available when AI is disabled,
unavailable, or fails validation. A stopped request or an unavailable local server
still produces the existing recovery/error state rather than a fabricated answer.

## What was causing the strict behavior

An employment-category rule could stop retrieval before sources were searched,
even when the learned topic prediction was strong. For example, the baseline
`My employer has not paid my wages. What can I do?` had labor confidence 0.8700
but was routed to clarification because the employment category was missing.
`Late ang salary ko.` was also stopped by this rule; its baseline learned label
was out of scope. These observations identify routing/context sensitivity, not a
statistical diagnosis of overfitting or underfitting.

The application also returned no explanatory prose when a provider draft failed
source checks. A correctly classified Taglish defective-product question could
have no keyword-search hits. Finally, the launcher could reuse a backend started
before a key was saved because its identity covered code, not provider settings.

## Changes

- Labor concerns missing employment category can trigger a second, checked search
  under an explicitly disclosed hypothetical private-employment context. This
  applies only if the existing classifier/verifier resolves that complete query
  coherently. The original question and original routing remain inspectable.
  The app does not assert that the user is a private employee.
- General labor information asks an employment-type follow-up. Quick choices fill
  the complete question with the selected category; they do not submit it or
  silently assume the answer. Explicit excluded categories retain their scope
  limits, and mixed concerns keep their excluded parts.
- A small equivalent-word search repair can recover an already admitted consumer
  query with no hits (`sira`, `binili`, `palitan`, `ayaw`, `garantiya`). It preserves
  the original classification, domain, concern count and original displayed text.
- Checked AI explanations still require exact citations and automated support.
  Generation now receives the explicit conditional scope and recorded source
  quantities. An uncited quantity can receive one checked correction; the numeric
  rule remains enforced and the existing single-revision/request bound remains.
- Failed/unavailable AI gets local explanatory prose and eligible exact source
  text where available. Complete short provisions or complete paragraphs are
  identified honestly; full source text and exceptions remain inspectable. Known
  wording holds and other source restrictions also apply to these excerpts.
- Runtime reuse identity includes saved provider configuration and AI feature
  settings. Only a digest is exposed; keys are not printed or decrypted for this
  check. Starting after configuration changes does not reuse the old API identity.

Implementation: `backend/application/conversation.py`, `service.py`,
`development_explanation.py`, `identity.py`, and the live-result/chat components.

## Verification

| Check | Result | Evidence |
|---|---|---|
| Backend regression suite | 184 passed | `backend-tests-final.log` |
| Frontend interaction/contract/a11y suite | 24 passed | `frontend-tests-final.log` |
| Frontend lint and production build | Passed | `frontend-lint.log`, `frontend-build.log` |
| Synthetic local behavior sample | 15/15 nonempty local responses; 5 conditional searches; 1 vocabulary recovery; 0 provider calls | `local-diagnostics.json` |
| Live working-hours example | Checked AI explanation, 2 calls | `live-smoke.json`, first case |
| Live wage example after quantity guidance | Checked AI explanation, 2 calls | `live-smoke-quantity-guidance.json` |
| Failed attempts preserved | Wage drafts failed numeric checks before the final prompt improvement; local responses remained available | `live-smoke.json`, `live-smoke-final.json` |
| Browser: desktop and mobile | No horizontal overflow at 1200×800 and 390×844 CSS pixels; employment choices, complete source/highlight and mobile Back-to-chat focus verified | `browser-check.json`, `desktop.png`, `mobile.png` |
| Pinned classifier/retrieval/verifier sources and packages | No tracked differences | `preservation.json` |

Live developer testing reused two fictional questions and public recorded source
text, used eight provider requests across the diagnostic sequence, and sent no
personal chat text or history. The quantity-only diagnostic kept no raw rejected
draft and is local/private. The final wage test passed without a correction.
These are developer smoke cases, not an aggregate generated-answer accuracy score.

Screenshots were captured from the local browser, including a local-only test to
verify fallback behavior without additional provider requests. The browser's
pre-existing zoom was retained; measured CSS dimensions are in the receipt. AI
preference was restored to on, saving remained off, and temporary viewport
overrides were reset. No browser console errors were observed.

## What this does and does not establish

Classifier v1.5.16, retrieval v1.3.3 and verifier v1.0.11 remain selected. No model
weights, training membership, calibration, thresholds, canonical source text or
trusted legal reviews were changed. The recorded classifier metrics remain
measurements of their recorded raw inference pipeline, not measurements of this
new conditional website flow. No claim is made that classifier accuracy increased.

This repair improves response availability and context handling. Its small
synthetic examples cannot establish generalization, legal correctness, or diagnose
over/underfitting. Fresh independent human questions and legal/source-currentness
review remain pending. Current-guidance, independent acceptance and deployment
permissions remain closed. A same-model support judge is not independent review.

For existing group clones: stop the website, run `git pull --ff-only`, then
`npm.cmd --prefix UI/UX/app ci`, then `./start-website.ps1`. Keep AI explanations
enabled in the browser. Previously configured local keys are retained.
