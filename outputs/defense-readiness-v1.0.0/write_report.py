"""Report actual failures and repairs without treating availability as accuracy."""
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
current=read(ROOT/'CURRENT_ARTIFACTS.json')
initial=read(BASE/'discovery-before/metrics.json');reserved=read(BASE/'confirmation/metrics.json')
final=read(BASE/'browser-checked-local/metrics.json');bulk=read(BASE/'live-after/metrics.json');recheck=read(BASE/'live-browser-checked/metrics.json');warranty=read(BASE/'warranty-final/metrics.json')
local=read(ROOT/current['local_pipeline_evaluation']/'metrics.json');scores=local['strata']['all']['baseline']
tests=(BASE/'backend-final-tests.log').read_text(encoding='utf-8',errors='replace')
test_count=int(re.search(r'Ran (\d+) tests',tests).group(1));software_pass='\nOK\n' in tests
summary={'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
 'active_stack':{k:current[k] for k in ['classifier','retrieval','verifier','local_pipeline_evaluation']},
 'new_cases_manifest':read(BASE/'manifest.json'),'initial_discovery':{k:initial[k] for k in ['cases','all_expectations_matched','issue_counts']},
 'initial_reserved_check':{k:reserved[k] for k in ['cases','all_expectations_matched','issue_counts']},
 'final_local_checks':final['groups'],'prior_100':read(BASE/'previous100-check.json'),
 'older_436':{'primary':scores['primary']['accuracy'],'scope':scores['scope']['accuracy'],'primary_macro_f1':scores['primary']['macro_f1'],
              'scope_macro_f1':scores['scope']['macro_f1'],'route':scores['route_match'],'hit_at_5':scores['known_relevant_hit_at_5'],
              'unsupported_admission':scores['unsupported_admission'],'evidence_checks':local['evidence_checks']},
 'AI_first_21':{k:bulk[k] for k in ['input_forms','pending','explanation_status','non_generated_reasons','failure_codes','latency_ms','usage']},
 'AI_warranty_supplement':{k:warranty[k] for k in ['input_forms','explanation_status','latency_ms','usage']},
 'AI_final_targeted_5':{k:recheck[k] for k in ['input_forms','pending','explanation_status','non_generated_reasons','failure_codes','latency_ms','usage']},
 'source_preservation':read(BASE/'source-preservation.json'),
 'software_tests':{'backend':test_count,'backend_passed':software_pass,'frontend':31,'classifier':69,'additional_scope_contrasts':24,'retrieval':52,'verifier':37},
 'runtime_health':read(BASE/'runtime-health-final.json'),
 'browser':read(BASE/'browser-checks.json'),
 'independent_human_gold':False,'legal_accuracy_measured':False,'all_issues_closed':False,
 'limitations':['The 72 cases informed repairs after the initial 48/24 split; do not label the repaired results a fresh holdout.',
                'The six additional classifier-routing checks initially passed without tuning; CHK_001 later informed the browser source-ranking repair. They are inspected development cases, not a fresh end-to-end holdout.',
                'The source corpus is unchanged; held/missing authorities remain gaps, including final pay/COE and thirteenth-month related-source approvals.',
                'Same-model support checks can miss semantic mistakes. Additional source-condition guards are engineering checks, not independent legal review.',
                'Three-way topic-coverage probabilities were not recalibrated on independent data; scope rules can determine retrieval while the original probability remains visible.',
                'Provider failures and variable latency remain possible; failures return local text and eligible excerpts instead of unchecked legal conclusions.']}
save(BASE/'summary.json',summary)
f=final['groups'];a=recheck['explanation_status'];u=recheck['usage'];ev=local['evidence_checks']
report=f'''# Defense usability and accuracy repair

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
| Initial discovery | {initial['all_expectations_matched']}/{initial['cases']} | Failures informed the first repair |
| Initial reserved questions | {reserved['all_expectations_matched']}/{reserved['cases']} | Three further failures were retained and repaired |
| Final discovery replay | {f['discovery']['all_expectations_matched']}/{f['discovery']['cases']} | Reused development checks |
| Final reserved replay | {f['confirmation']['all_expectations_matched']}/{f['confirmation']['cases']} | Also reused development checks after repair |
| Six additional question rechecks | {f['fresh_final']['all_expectations_matched']}/{f['fresh_final']['cases']} | Initial routing pass was 6/6; one case later informed source ranking |

The prior 100-question classifier regression still matched **100/100** expected labels and routes. All these figures concern classification/routing, not the correctness of generated legal advice. The six extra questions initially passed the routing check before browser inspection; CHK_001 then informed the short-change source-ranking repair. They are now inspected development regressions. The original 72 questions and six extra questions retain their original hashes and expectations. No new questions were fitted into the learned model.

## Older 436-question AI-off regression

The final selected stack was replayed against all 436 historical development inputs. Topic labels matched **{scores['primary']['accuracy']['numerator']}/{scores['primary']['accuracy']['denominator']}**, and topic coverage matched **{scores['scope']['accuracy']['numerator']}/{scores['scope']['accuracy']['denominator']}**. Macro F1 was **{scores['primary']['macro_f1']:.4f} / {scores['scope']['macro_f1']:.4f}** on the reused labeled inputs. Routes matched **{scores['route_match']['numerator']}/{scores['route_match']['denominator']}**; known-relevant Hit@5 was **{scores['known_relevant_hit_at_5']['numerator']}/{scores['known_relevant_hit_at_5']['denominator']}**. Unsupported admissions were **{scores['unsupported_admission']['numerator']}/{scores['unsupported_admission']['denominator']}**.

Candidate-integrity failures: **{ev['candidate_integrity_failures']}/{ev['candidate_integrity_checks']}**. Recorded-excerpt provenance passed **{ev['recorded_excerpt_claims_passed']}/{ev['recorded_excerpt_claims']}**. Remaining historical route differences are retained in the current evaluation's `errors.json`. The Performance page is bound only to the completed current-stack report, `{current['local_pipeline_evaluation']}`. No older score is silently relabeled as a new independent result.

## Live AI diagnostics

Twenty-one fictional diagnostic questions went to the configured Together model under a shared **120-attempt / $0.10 estimated** cap. The first run returned all 21 packets: **9 generated, 2 partially generated, 10 withheld**. Four provider failures were retained. Initial median latency was **17.4 s**, p95 **30.0 s**.

Engineering reading found a counted-time/overtime substitution, an invalid seasonal-to-casual inference, and an optional-forwarding paraphrase of the retailer's mandatory duty. Those accepted outputs are explicitly recorded as failures of semantic checking; exact citations did not make them legally correct. The original completions and counts are preserved. Intermediate five-question rechecks and the one-question retailer-recipient correction are preserved separately. The latter rejected an unsourced manufacturer alternative and then regenerated the mandatory distributor-presentment duty.

After the source-condition and browser-found source-ranking repairs, the five affected questions were rechecked: **{a.get('generated',0)} fully generated, {a.get('partially_generated',0)} partially generated, {a.get('withheld',0)} withheld**. Final withholding reasons: `{json.dumps(recheck['non_generated_reasons'])}`. Provider failures: `{json.dumps(recheck['failure_codes'])}`. Median **{recheck['latency_ms']['p50']/1000:.2f} s**, p95 **{recheck['latency_ms']['p95']/1000:.2f} s**. This is a posthoc targeted regression, not a fresh full-21 pass or a controlled speed comparison.

The batch ledger totals **{u['provider_requests']} attempts/reservations**, about **${u['estimated_usd']:.5f} estimated** across all diagnostic/recheck phases. Browser smoke checks use the separate existing website ledger. No personal chat text was included. Costs are estimates at configured rates, not a verified invoice. A source gap should produce an explicit limitation or a partial answer, not a fabricated result merely to increase availability.

## Software and website verification

Final backend: **{test_count} tests**, passed: **{software_pass}**. Frontend: **31 tests**, plus build and lint. Selected package checks: classifier **69**, extra scope contrasts **24**, retrieval **52**, verifier **37**. A candidate classifier build that defeated an explicit threshold-disable test was rejected and preserved; the shipped rule still respects the primary threshold and rejects invalid confidence thresholds.

A final test assertion was corrected to accept the implementing rules of the short-change law as well as the statute; its original failed log is retained. The website is checked against the current API identity, with AI on and device history saving off at handoff. Desktop and emulated narrow-screen checks exercise the supported/excluded and partial-source flows, citation navigation and the question-review action. Screenshot and DOM evidence are included in this directory. Actual measured CSS viewports were 1120×750 and 390×844, with no document-level horizontal overflow. Citation return focus and full-question restoration were checked. Emulated checks do not establish physical-device, screen-reader or accessibility conformance.

Selected packages: `{current['classifier']}`, `{current['retrieval']}`, `{current['verifier']}`. Learned weights, vocabulary, calibration, thresholds and training membership remain unchanged through the repair lineage; canonical records remain byte-identical to the earlier corpus. Source holds and current-law approval gates remain active. Intermediate failed builds, a deliberately superseded local replay, provider failures and the first reserved result are retained rather than removed from the evidence.

## What remains

The unchanged corpus still has held or missing authority for some in-scope questions. Same-model support checks remain imperfect, complex multi-issue paraphrases need further semantic scrutiny, and provider latency/availability varies. New three-way combinations have no independently measured confidence recalibration. Independent human/generalization testing, legal interpretation/currentness approval, and adviser acceptance remain unmeasured. The system should be presented as a repaired, bounded development preview, not as a legally verified adviser.

Design metadata note: the existing Impeccable sidecar is stale. `impeccable document` can refresh it; it was not treated as a blocker or silently regenerated during this functional repair.

Machine-readable results: `summary.json`. Per-question evidence: `browser-checked-local/observations.jsonl`, `live-after/observations.jsonl`, `live-browser-checked/observations.jsonl`. Software logs, source-preservation checks, protocol freezes and final hashes are retained beside this report.
'''
(BASE/'REPORT.md').write_text(report,encoding='utf-8')
files=[BASE/p for p in ['REPORT.md','summary.json','cases.json','manifest.json','fresh-final-cases.json','fresh-final-manifest.json','source-preservation.json',
                       'backend-final-tests.log','runtime-health-final.json','browser-checks.json','browser-desktop.jpg','browser-mobile.jpg','browser-handoff.jpg','fresh-final-use-note.json','semantic-reading-findings.json']]
files += [ROOT/'CURRENT_ARTIFACTS.json',ROOT/'backend/application/grounding.py',ROOT/'backend/application/development_explanation.py',ROOT/'backend/application/conversation.py',ROOT/'UI/UX/app/src/components/LiveResult.tsx',ROOT/'UI/UX/app/src/components/GeneratedExplanation.tsx',ROOT/'UI/UX/app/src/pages/ChatPage.tsx',ROOT/'UI/UX/app/src/data/api.ts',ROOT/'dataset/pipelines/item10/classifier_runtime.py',ROOT/'dataset/pipelines/item10/clause_classifier.py',ROOT/'dataset/pipelines/item10/scope_constraints.py',ROOT/'dataset/pipelines/item11/query_relevance.py']
for name in ['discovery-before','confirmation','browser-checked-local','live-after','live-confirmation','live-final','warranty-final','live-browser-checked']:
    files += [BASE/name/p for p in ['observations.jsonl','metrics.json','protocol.json','freeze.json'] if (BASE/name/p).exists()]
save(BASE/'final-checksums.json',{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()})
print(json.dumps({'software_passed':software_pass,'final_AI':a,'local_checks':final['groups'],'report':str(BASE/'REPORT.md')}))
