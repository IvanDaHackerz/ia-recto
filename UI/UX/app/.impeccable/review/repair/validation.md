# UI repair verification packet

Request: fix the audited whole-project gaps while preserving the existing Recto website; earlier scope explicitly requested LLM explanations with a word reveal and useful, simpler metrics.

Direction: `UI/UX/app/.impeccable/surfaces/src-pages-chatpage-tsx.md` and the existing performance brief. Ordinary extension, code-led; no approved raster comp or new visual world. PRODUCT.md was updated for owner-authorized factual drift; The incumbent design guide is UI/UX/design_guide.md plus source tokens. DESIGN.md is pre-existing missing context; the final documenter will record the existing implemented system without changing its visual identity.

Required evidence in `UI/UX/app/.impeccable/review/repair/`:
- `desktop.jpg`: 1200x833 CSS desktop, live synthetic Taglish question/explanation and full exact highlighted source. The page is vertically scrolled to response 3.
- `mobile.jpg` and `mobile-explanation.jpg`: same response at 390 CSS pixels; two scroll states (question context and full explanation/citation controls). Earlier turns remain above; these are not a landing-page composition.
- `mobile-sources.jpg`: 390 CSS pixels, exact-source highlight and Back to chat.
- `mobile-settings-large-contrast.jpg`: 468 CSS pixels, 22px text/high contrast controls.
- `mobile-history-large-contrast.jpg`: 390 CSS pixels, saved records with 22px text/high contrast.
- `performance-ai.jpg`: 1200 CSS pixels, detailed report's separate whole-application replay (82 shown / 354 withheld, 459 attempts, estimated cost and latency).

An IAB high-DPI capture issue made the initial viewport-only screenshot blurry/cropped; those files were replaced with correctly bounded captures. The original chat tab has devicePixelRatio 1.2. Final screenshots use explicit physical clip bounds; the normal settings/report tab has DPR 1. No CSS/image edits were used to alter screenshots.

Observed: local-only classification/retrieval produced five sources and no LLM; opt-in saving survived navigation; direct saved URL reopened the stored packet with recorded/not-rechecked copy. A live checked Taglish explanation rendered, source clicks selected the correct concern and highlighted exact passages inside complete text. Mobile source/return controls worked; returned focus was Response 3. No horizontal overflow at 390 or 1200 pixels; history with 22px text/high contrast fit at 390. Preferences were restored to default size/contrast, AI on and saving off after verification. One fictional saved question remains as a browser test record.

15 initial frontend tests passed, then 16 including the discovered canceled-report-load race regression. Tests cover reduced motion initially/at runtime, skip animation/no rewind, component-aware source links, rejecting unchecked drafts, complete quoted-source rendering, structural axe checks, keyboard privacy opt-in, history failure/confirmation/navigation and malformed responses. Color contrast is excluded from jsdom axe because it has no layout engine; browser contrast/reading checks do not establish accessibility conformance. Actual screen-reader/PWD user testing remains pending.

Detector ran once on the changed targets: `detector.json` = [] (no findings). Build/lint and 261 saved-metric comparisons pass. Final build/test logs are in `outputs/project-repair-v1.0.0`.

Legal/data boundaries: 436 reused synthetic development inputs, no independent human test. A source-selection/citation/support pass is an automated same-model check, not professional legal approval or currentness. Missing authorities/reviews keep explanations withheld. The UI must preserve those distinctions.

Recapture completed: the malformed Settings image was replaced with a legible 468x1014 CSS-pixel image showing the masthead, full notice, Settings heading and text-size/high-contrast controls at 22px. Actual width 468, DPR 1, document scrollWidth 453; the parent inspected the corrected image. No interface code changed for this recapture. The prior recapture-only report gave no shipping verdict.
