# Defense usability and accuracy repair

This round repaired underlying parsing, scope routing, source selection and partial-response behavior. It improves the development preview, but it does not establish legal-answer accuracy or complete defense readiness for arbitrary unseen questions.

## What changed

- Employment complaints about missing cash, deductions or weekly rest are preserved as concerns. They are no longer discarded as employer background.
- Same-issue follow-ups, generic closing requests, retail purchase introductions, and inline “separately” are grouped without inventing extra concerns. Actual separate actors, disputes and excluded topics remain separate.
- A bank transfer explicitly described as only the wage-payment method is background; an actual bank-fee dispute remains excluded.
- Explicit labor + consumer + excluded combinations can retrieve the two supported domains while retaining the excluded concern. This narrow rule requires a passing primary confidence, explicit scope evidence for every component, complete segmentation and no missing context. Original probability values and learned thresholds are preserved. Uncertain learned fragments still require clarification.
- Short-change queries now rank the short-change rules separately from price-tag questions; changing an online order does not become a short-change dispute. The source pane shows a pending state while analysis runs and initially opens a citation from an approved displayed paragraph.
- One missing authority or failed individual support assessment no longer erases another component's approved explanation. The UI says **AI explanation for supported parts**, names every unanswered concern, and shows the explained/total count. Missing, duplicated or malformed assessments cannot authorize partial prose.
- Required meetings and off-the-clock questions now use the counted-time relevance concept consistently in ranking and filtering. Wage-payment intervals, normal-hours ceilings and overtime rates are not substitutes for a missing counted-time authority.
- Source-condition checks reject the observed seasonal/project-to-casual inference and an optional “may forward” paraphrase of a mandatory retailer duty. Generation instructions preserve those distinctions and allow enough words for relevant conditions.
- Draft reasoning effort follows question complexity instead of the length of unrelated source text. Every displayed development paragraph still needs exact citations, local checks and automated support; current legal approval remains separate.

## New local questions and honest denominators

Seventy-two fictional AI-authored questions were frozen before inference. They cover 24 labor, 24 consumer, eight fully mixed, eight partially supported and eight excluded cases.

| Stage | All expected labels, route and domains matched | Interpretation |
| --- | ---: | --- |
| Initial discovery | 41/48 | Failures informed the first repair |
| Initial reserved questions | 21/24 | Three further failures were retained and repaired |
| Final discovery replay | 48/48 | Reused development checks |
| Final reserved replay | 24/24 | Also reused development checks after repair |
| Six additional question rechecks | 6/6 | Initial routing pass was 6/6; one case later informed source ranking |

The prior 100-question classifier regression still matched **100/100** expected labels and routes. All these figures concern classification/routing, not the correctness of generated legal advice. The six extra questions initially passed the routing check before browser inspection; CHK_001 then informed the short-change source-ranking repair. They are now inspected development regressions. The original 72 questions and six extra questions retain their original hashes and expectations. No new questions were fitted into the learned model.

## Older 436-question AI-off regression

The final selected stack was replayed against all 436 historical development inputs. Topic labels matched **425/425**, and topic coverage matched **425/425**. Macro F1 was **1.0000 / 1.0000** on the reused labeled inputs. Routes matched **432/436**; known-relevant Hit@5 was **93/93**. Unsupported admissions were **0/80**.

Candidate-integrity failures: **0/1603**. Recorded-excerpt provenance passed **430/430**. Remaining historical route differences are retained in the current evaluation's `errors.json`. The Performance page is bound only to the completed current-stack report, `outputs/local-pipeline-evaluation-v1.6.21`. No older score is silently relabeled as a new independent result.

## Live AI diagnostics

Twenty-one fictional diagnostic questions went to the configured Together model under a shared **120-attempt / $0.10 estimated** cap. The first run returned all 21 packets: **9 generated, 2 partially generated, 10 withheld**. Four provider failures were retained. Initial median latency was **17.4 s**, p95 **30.0 s**.

Engineering reading found a counted-time/overtime substitution, an invalid seasonal-to-casual inference, and an optional-forwarding paraphrase of the retailer's mandatory duty. Those accepted outputs are explicitly recorded as failures of semantic checking; exact citations did not make them legally correct. The original completions and counts are preserved. Intermediate five-question rechecks and the one-question retailer-recipient correction are preserved separately. The latter rejected an unsourced manufacturer alternative and then regenerated the mandatory distributor-presentment duty.

After the source-condition and browser-found source-ranking repairs, the five affected questions were rechecked: **3 fully generated, 1 partially generated, 1 withheld**. Final withholding reasons: `{"source_context_unavailable": 1}`. Provider failures: `{}`. Median **9.69 s**, p95 **21.38 s**. This is a posthoc targeted regression, not a fresh full-21 pass or a controlled speed comparison.

The batch ledger totals **74 attempts/reservations**, about **$0.07682 estimated** across all diagnostic/recheck phases. Browser smoke checks use the separate existing website ledger. No personal chat text was included. Costs are estimates at configured rates, not a verified invoice. A source gap should produce an explicit limitation or a partial answer, not a fabricated result merely to increase availability.

## Software and website verification

Final backend: **246 tests**, passed: **True**. Frontend: **31 tests**, plus build and lint. Selected package checks: classifier **69**, extra scope contrasts **24**, retrieval **52**, verifier **37**. A candidate classifier build that defeated an explicit threshold-disable test was rejected and preserved; the shipped rule still respects the primary threshold and rejects invalid confidence thresholds.

A final test assertion was corrected to accept the implementing rules of the short-change law as well as the statute; its original failed log is retained. The website is checked against the current API identity, with AI on and device history saving off at handoff. Desktop and emulated narrow-screen checks exercise the supported/excluded and partial-source flows, citation navigation and the question-review action. Screenshot and DOM evidence are included in this directory. Actual measured CSS viewports were 1120×750 and 390×844, with no document-level horizontal overflow. Citation return focus and full-question restoration were checked. Emulated checks do not establish physical-device, screen-reader or accessibility conformance.

Selected packages: `outputs/item10-classifier-v1.5.49`, `outputs/item11-retrieval-v1.3.40`, `outputs/item12-verifier-v1.0.47`. Learned weights, vocabulary, calibration, thresholds and training membership remain unchanged through the repair lineage; canonical records remain byte-identical to the earlier corpus. Source holds and current-law approval gates remain active. Intermediate failed builds, a deliberately superseded local replay, provider failures and the first reserved result are retained rather than removed from the evidence.

## What remains

The unchanged corpus still has held or missing authority for some in-scope questions. Same-model support checks remain imperfect, complex multi-issue paraphrases need further semantic scrutiny, and provider latency/availability varies. New three-way combinations have no independently measured confidence recalibration. Independent human/generalization testing, legal interpretation/currentness approval, and adviser acceptance remain unmeasured. The system should be presented as a repaired, bounded development preview, not as a legally verified adviser.

Design metadata note: the existing Impeccable sidecar is stale. `impeccable document` can refresh it; it was not treated as a blocker or silently regenerated during this functional repair.

Machine-readable results: `summary.json`. Per-question evidence: `browser-checked-local/observations.jsonl`, `live-after/observations.jsonl`, `live-browser-checked/observations.jsonl`. Software logs, source-preservation checks, protocol freezes and final hashes are retained beside this report.
