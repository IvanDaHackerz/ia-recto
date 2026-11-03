"""Publish transparent engineering evidence, including failures and limits."""
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

current=read(ROOT/'CURRENT_ARTIFACTS.json')
local=read(ROOT/current['local_pipeline_evaluation']/'metrics.json')
runs={name:{'protocol':read(BASE/name/'protocol.json'),'metrics':read(BASE/name/'metrics.json'),'audit':read(BASE/name/'audit.json')}
      for name in ['first-pass','second-pass','final-check','closure-check']}
for run in runs.values():assert run['audit']['frozen_files_intact']
for key in ['classifier','retrieval','verifier']:
    directory=ROOT/current[key]
    assert all(sha(directory/name)==expected for name,expected in read(directory/'artifact_checksums.json').items())
final_local=local['strata']['all']['baseline']
assert final_local['unsupported_admission']['numerator']==0
tests=(BASE/'backend-final-tests.log').read_text(encoding='utf-8')
assert 'Ran 273 tests' in tests and '\nOK\n' in tests
first=runs['first-pass']['metrics'];second=runs['second-pass']['metrics'];last=runs['closure-check']['metrics']
browser=read(BASE/'browser-evidence.json') if (BASE/'browser-evidence.json').exists() else {'status':'not recorded'}
latest={}
for name in runs:
    for row in read(BASE/name/'readable-results.json'):
        latest[row['case_id']]={'observation_run':name,**row}
save(BASE/'latest-observation-view.json',{'warning':'Mixed-revision posthoc view, not a full 100-question evaluation of the final backend. Original runs remain separate.', 'questions':list(latest.values())})
summary={'selected_stack':{key:current[key] for key in ['classifier','retrieval','verifier','local_pipeline_evaluation']},
    'fresh_manifest':read(BASE/'live-case-manifest.json'),'live_runs':runs,'local_regression':local,
    'backend_tests':{'passed':True,'count':273},'frontend_tests':{'passed':True,'count':31},
    'frontend_build_passed':True,'focused_concern_tests':36,'browser':browser,
    'study_provider_usage':last['usage'],'independent_human_gold_questions':0,'legal_answer_accuracy':None,
    'full_second_run_precedes_later_targeted_repairs':True,'review':read(BASE/'review-notes.json'),
    'all_project_issues_closed':False}
save(BASE/'summary.json',summary)
def rate(metrics,key):
    value=metrics['routing_and_retrieval'][key]
    return f"{value['numerator']}/{value['denominator']}"
topic=lambda m:f"{m['routing_and_retrieval']['primary']['accuracy']['numerator']}/100"
scope=lambda m:f"{m['routing_and_retrieval']['scope']['accuracy']['numerator']}/100"
report=f'''# Fresh AI usability study — 25 October 2026

One hundred new fictional questions were authored and labeled before inference: 30 labor, 30 consumer, 10 fully mixed, 15 supported-plus-excluded mixed, and 15 outside scope. English, Taglish and noisy typing are included. Exact duplicate checking covered 1,760 earlier saved input rows. Topics necessarily overlap earlier studies; semantic novelty was not independently judged.

This is an AI-authored development diagnostic. The first pass is preserved separately from all inspected repair rechecks. No question or expected label was edited after inference. These are not human-written gold questions or a legal-accuracy study.

## Full 100-question observations

| Check | Initial stack | Repaired full run |
|---|---:|---:|
| Topic label match | {topic(first)} | {topic(second)} |
| Scope label match | {scope(first)} | {scope(second)} |
| Route match | {rate(first,'route_match')} | {rate(second,'route_match')} |
| Supported-domain coverage | {rate(first,'domain_match')} | {rate(second,'domain_match')} |
| Outside-only questions admitted to retrieval | {rate(first,'unsupported_admission')} | {rate(second,'unsupported_admission')} |
| Full AI explanations | {first['explanation_status'].get('generated',0)} | {second['explanation_status'].get('generated',0)} |
| Partial AI explanations | {first['explanation_status'].get('partially_generated',0)} | {second['explanation_status'].get('partially_generated',0)} |
| Withheld AI explanations | {first['explanation_status'].get('withheld',0)} | {second['explanation_status'].get('withheld',0)} |
| Application errors | {len(first['errors'])} | {len(second['errors'])} |
| Median / p95 whole-query time | {first['latency_ms']['p50']/1000:.1f}s / {first['latency_ms']['p95']/1000:.1f}s | {second['latency_ms']['p50']/1000:.1f}s / {second['latency_ms']['p95']/1000:.1f}s |

All 15 excluded-only questions appropriately had no provider-generated legal explanation in the repaired full run. Of the 85 questions with an in-scope concern, 68 received a full or partial AI explanation. Withholding also reflects missing/held authority, failed content checks, and one provider-incomplete response. A source gap is not counted as a legally correct answer.

The first full run used classifier 1.5.58 / retrieval 1.3.49 / verifier 1.0.56; the repaired full run used 1.5.60 / 1.3.50 / 1.0.57. That full repaired run was followed by 17 targeted observations and one final closure-condition check on the selected 1.5.61 / 1.3.51 / 1.0.58 stack. The final 100-question local classifier replay also matched all frozen labels and routes. The targeted observations do not replace the full-run results or constitute a fresh holdout.

## Repairs

- Current concerns introduced with “unrelated” are retained; comma-enumerated labor, retail and excluded concerns remain separate.
- Private-employment, harvest/seasonal, security-of-tenure, hyphenated overseas-worker, tax, privacy, inheritance and prediction wording is handled more consistently. Original numbers, literals and question text are retained.
- Phonetic/boundary features preserve ordinary words such as printer, pot and badly while retaining tested shorthand repairs. The LLM normalizer still runs only when local understanding fails; the repaired full batch was understood locally and correctly bypassed wording calls.
- Same-scenario requests, coordinate subjects and work-schedule context no longer produce several of the observed duplicate/irrelevant components.
- Retrieval better distinguishes wage deductions, closure, security of tenure, paid service quality, replacement-parts obligations, refurbished-as-new sales, platform redress and source gaps. The broad service focus initially lost two known-relevant replacement-parts hits; regression v1.6.28 exposed that error and v1.6.29 checks the correction.
- Explanation checks preserve payroll versus individual-payslip obligations, retailer versus distributor duties, return conditions, manufacturer defenses, and closure notice/separation-pay conditions. Valid “opt for” return wording is accepted without removing the choice condition.
- Numeric correction feedback identifies unsupported quantities; paragraphs are instructed to leave article/section identifiers to citation fields. Complex support checks have a larger bounded output allowance after an observed truncated support response. Request deadlines, cancellation and the single content-correction limit remain active.

Atomic classifier weights, feature vocabulary, training membership and thresholds remain inherited. Calibration was refreshed using original training folds only. No diagnostic question was fitted. Canonical source text, source eligibility holds and legal approval gates were not changed.

## Broader verification

- 273 backend tests passed, 31 frontend tests passed, and the frontend production build passed.
- 36 focused concern regressions passed. Packaging also passed 69 classifier, 60 retrieval and 37 verifier checks; these overlap other suites and are not a combined unique-test count.
- Final local regression: 436 input forms, 425 labeled; topic and scope {final_local['primary']['accuracy']['numerator']}/425 each; route {final_local['route_match']['numerator']}/436; zero admissions among 80 excluded inputs.
- Known-relevant Hit@5: {final_local['known_relevant_hit_at_5']['numerator']}/{final_local['known_relevant_hit_at_5']['denominator']}. Exact recorded excerpts and candidate integrity checks are in the local metrics.
- Both full live runs and targeted runs have separate exact-citation/candidate audits. Exact quotes and same-model semantic acceptance do not establish legal correctness; manual AI inspection found issues despite those checks passing.
- Four frozen route expectations still differ from the current conditional-general-information policy. Their raw observations remain in the regression output; labels were not changed to improve a score.

The final study ledger records {last['usage']['provider_requests']} provider requests at an estimated US${last['usage']['estimated_usd']:.5f}, within the original cumulative 400-request / US$0.50 study cap. This is a configured token-price estimate, not verified billing. Website smoke checks use the unchanged separate website ledger and are excluded from this study total. No personal chat text or credentials were exported.

## Remaining limits

Night-pay authority, held working-time/meal-period passages, final-pay/COE deadlines, related thirteenth-month material and specific labeling requirements remain source-coverage gaps. Some supported questions still have withheld or partial AI explanations when validation fails. Detailed employment-status and product-remedy interpretations remain difficult. One same-model assessor can miss or over-reject a qualification; these checks are not independent legal review.

The full repaired 100-question run preceded the later targeted backend changes. Metadata-only metric binding may change the runtime signature after a completed study; frozen snapshots, selected package identities and final browser health disclose the exact revisions. No claim of perfect unseen-question performance, current-law approval or production readiness is made.

## Evidence

- `first-pass/QUESTIONS_AND_RESULTS.md`: all original 100 observations.
- `second-pass/QUESTIONS_AND_RESULTS.md`: full inspected rerun.
- `final-check/QUESTIONS_AND_RESULTS.md` and `closure-check/QUESTIONS_AND_RESULTS.md`: targeted follow-ups.
- `latest-observation-view.json`: explicitly labeled mixed-revision inspection view.
- `review-notes.json`, `summary.json`, `browser-evidence.json`, test/build logs and immutable model/index/verifier packages.

Initial restricted test runs could not open loopback sockets, and discovery without a root package caused duplicate-module patch failures; final tests use the correct root and loopback permissions. Stale metric bindings were refreshed after the new evaluation completed. Initial/superseded package and test logs remain preserved.
'''
(BASE/'REPORT.md').write_text(report,encoding='utf-8')
save(BASE/'checksums.json',{p.relative_to(BASE).as_posix():sha(p) for p in sorted(BASE.rglob('*'))
    if p.is_file() and p.name!='checksums.json' and '__pycache__' not in p.parts and not p.name.endswith(('.sqlite3-wal','.sqlite3-shm'))})
print('Wrote final report and evidence hashes.')
