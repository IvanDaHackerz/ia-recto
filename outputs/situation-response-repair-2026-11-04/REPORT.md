# Situation-specific website responses — 4 November 2026

The cinema example now receives a source-backed AI explanation connecting required cash-drawer counting to the recorded working-time conditions. When the application cannot supply a legal explanation, AI-on can instead explain the person's specific source gap, scope boundary or needed clarification, without adding legal rules. All generated output remains subject to checks. AI-off, an unavailable provider, a spent budget, insufficient remaining time, or rejected guidance still produces an identified local response rather than a false claim of successful AI generation.

## Causes and changes

The reproduced cinema input was split into two components. Its factual sentence retrieved wage-payment/banking-method material because it contained cash-related language; its follow-up retrieved hours-worked provisions. The baseline live model returned an empty explanation rather than explain the unrelated first component. The original screenshot's source-only fallback was therefore reproducible without disabling any checks.

The application now groups an explicitly referential follow-up with the preceding scenario when both components share a domain and no separate/excluded issue is present. It retains the original fragments for diagnostics, filters only existing retrieved canonical candidates for the full question, and recomputes source gates. The classifier weights, original routing probabilities, immutable classifier/retrieval/verifier packages, canonical text and legal approval flags are unchanged.

Drafts now include a reported-situation field and a source-derived explanation field. Reported numeric details are checked against the question; legal quantities still require the selected source. The combined displayed prose receives the normal semantic support assessment. This repairs rejection of legitimate user details such as two extra hours without allowing a two-percent legal rate to borrow support from that user detail.

A separate bounded AI situation-response path uses the redacted question and a local response plan, never a rejected legal draft. A second call checks factual fidelity, scope, absence of new legal claims or case outcomes, relevance to the actual question, and consistency with the plan. It can clarify an ambiguous payment or explain why the available source collection cannot determine a remedy. It does not claim citation-supported legal analysis. Known transport failures do not trigger an immediate additional provider attempt. Cancellation and the existing spending/deadline controls still apply.

Local fallbacks now offer topic-specific reading help before expandable source quotations. The interface distinguishes source-supported AI explanations, checked AI situation responses and local output. Diagnostics expose both generation stages. An uncertain city-office employment question now asks whether the role is government-employed or with a private contractor rather than repeating an unrelated generic clarification.

## Verification

- `project-checks-confirmed.log`: complete project check passed: 353 backend tests, 35 frontend tests, dependency consistency, metric reconciliation, lint, production build and zero npm audit findings. Earlier restricted-sandbox runs retain their loopback socket permission errors; the complete successful run used permitted loopback networking.
- `targeted-final.log`: final targeted backend checks after the city-office and response-contract refinements. The frontend test/lint/build was also repeated after the response-contract refinement.
- Added regressions cover coherent cinema grouping and recomputed gates; preservation of separate/excluded concerns; AI versus local provenance; rejected or malformed context checks; fabricated quantities; factual versus legal numeric support; privacy masking; immediate safety; cancellation; and the city-office follow-up. Client tests reject AI situation responses without completed context checks.
- Bounded live development probes are retained in the JSON packets. `baseline-live-cinema.json` has the original no-supported-explanation result. `confirmed-cinema.json` and `confirmed-overtime.json` have source-supported AI explanations; `confirmed-consumer.json` has AI guidance for an actual source gap; `confirmed-unclear.json` has an AI clarification. `city-check-excluded.json` has the final city-office AI clarification. Earlier rejected drafts and failed checks are retained, not overwritten.
- The five final representative cases each produced AI output: two legal explanations and three situation/clarification responses. They were not a 100-case unseen test, and the model performing support checks is not an independent legal reviewer. The consumer source gap remains an evidence limitation; this change does not invent a missing source or certify legal accuracy.
- Browser verification replayed the recorded live packets through the built frontend on temporary loopback port 5190, without additional AI calls. Desktop and 390px mobile captures show readable explanation text, citation/source association and the distinct AI situation-response disclosure. This was a UI replay, not a claim that an existing long-running backend had hot-reloaded.

## Use the fix

The existing backend must be restarted to load the new Python code. In its VS Code terminal press Ctrl+C, then run `.\start-website.ps1` from `C:\IA`. Open the launcher's printed URL and keep Use AI explanations on. Previously displayed or saved answers remain recorded results; submit the question again to exercise the repaired path.

## Interface finish review

The response change preserves the existing navy/paper palette, Literata/Public Sans type roles, source pane, pinned composer, focus behavior and reduced-motion reveal. Exact quotations move into an accessible disclosure below the response; generated guidance has explicit provenance. No new palette, layout system or decorative assets were introduced. Desktop/mobile review found no blocking presentation defect in the changed response flow. Broader independent legal, accessibility and human acceptance remain outside this engineering check.

Screenshots: `desktop-cinema.png`, `desktop-explanation.png`, `mobile-cinema.png`.
