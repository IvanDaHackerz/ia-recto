# Performance page verification

Verified 2026-10-18. This is a UI demonstration, not a classifier evaluation.

- Production build and lint pass after the final UI corrections.
- Fixture consistency assertions pass for all six domain/scope and language combinations: confusion-matrix sums, class support, correct counts, calibration-bin denominators, routing totals, and all four preset probability distributions.
- Browser checks confirm count/row-percent switching, domain/scope switching, English/Taglish filtering, a zero-cell explanation, low-confidence clarification and expanded probabilities.
- Sample JSON download succeeds and explicitly records `sample_data: true`, `measured: false`, and illustrative provenance.
- Desktop (1440), mobile (390) and current window (1280) captures recorded. Extra-large text and high contrast were checked at mobile width; no page-level horizontal overflow. Original reading preferences restored.
- No browser warning/error entries during the interaction checks.
- The fresh finish reviewer requested three layout fixes. Its verdict pass scored all three resolved: mobile sample disclosure, chart axis separation, and table-scroll instructions. Disposition: ship, at the scope of those fixes.

Source fixtures remain in `src/data/performance.ts`. No classifier artifacts, backend evaluation records or training data were changed by this addition.
