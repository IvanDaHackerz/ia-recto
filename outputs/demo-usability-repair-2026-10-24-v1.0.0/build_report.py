import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
current=read(ROOT/'CURRENT_ARTIFACTS.json');local=read(ROOT/current['local_pipeline_evaluation']/'metrics.json')
scores=local['strata']['all']['baseline'];live=read(BASE/'live-summary.json')
safety=read(BASE/'safety-check/metrics.json');returns=read(BASE/'return-check/metrics.json');browser=read(BASE/'browser-evidence.json')
for key in ['classifier','retrieval','verifier']:
    directory=ROOT/current[key]
    assert all(sha(directory/n)==expected for n,expected in read(directory/'artifact_checksums.json').items())
assert 'Ran 264 tests' in (BASE/'backend-release-tests.log').read_text(encoding='utf-8')
assert '\nOK\n' in (BASE/'backend-release-tests.log').read_text(encoding='utf-8')
assert scores['unsupported_admission']['numerator']==0
errata={'case_id':'DEMO_NEW_016','frozen_expected_domains':['labor'],'question_also_contains':'A separate shop delivered the wrong ordered item','engineering_interpretation':'The frozen domain expectation omitted consumer although the question explicitly contains both labor and retail concerns. The classifier retained both.','frozen_files_changed':False,'raw_scores_preserved':True,'independent_label_review':False}
save(BASE/'annotation-errata.json',errata)
summary={'selected_stack':{k:current[k] for k in ['classifier','retrieval','verifier','local_pipeline_evaluation']},'local_metrics':local,
    'full_live_cohort':live,'final_status_recheck':safety,'final_return_recheck':returns,'browser':browser,
    'annotation_errata':errata,'backend_tests':{'run':264,'passed':True},'classifier_tests':69,'retrieval_tests':60,'verifier_tests':37,'concern_tests':31,
    'all_project_issues_closed':False,'independent_human_gold_questions':0,'legal_answer_accuracy':None,
    'full_live_46_was_followed_by_targeted_backend_repairs':True,'final_targeted_results_do_not_replace_first_observations':True}
save(BASE/'summary.json',summary)
report=f'''# Demo usability repair — 24 October 2026

The ordinary labor, consumer, mixed and excluded demo flows are substantially more usable. This remains a supervised development prototype: some AI paragraphs are withheld, some source topics remain unavailable, and legal interpretation/currentness has not been independently approved. No promise is made that every unseen professor question will work.

## What changed

- Scenario follow-ups retain their context; ordinary overtime, probation, online-order and safety questions no longer become duplicate or false unanswered concerns in the repaired examples.
- Employment introductions no longer discard unpaid-salary or repeated-contract complaints. Overseas, government/civil-service, prediction-only and exact-current-wage boundaries are preserved, including hyphenated wording and negated alternatives.
- English words such as contractor and production survive local spelling repair.
- Retrieval follows the actual issue: offsetting/leave substitution, religious rest preference, deductions, payroll contents, status, procedure, platform redress, prices and cash change. Nearby deceased-worker, arbitration, tax-training and specialized-homework provisions are filtered from unrelated requests.
- The AI support assessor receives the actual component query and checks issue relevance, actor identity and attachment of conditions. Further checks reject observed invented undertime payments, overly broad original-goods return duties and ambiguous one-year/status claims.
- Valid mixed-question paragraphs survive another paragraph failing validation, and each retained paragraph still passes its own citation and semantic checks. Failed concerns remain explicit.
- Prompts avoid unrequested holiday-date lists and unrelated special-case catalogs. Output budgets and reasoning were adjusted after observed provider truncation/time-limit failures.
- Metrics compare domain sets independently of list order. The earlier raw observations remain unchanged.

Atomic model weights, vocabulary, training membership and routing thresholds remain inherited. Calibration was refreshed on the original training folds only. No diagnostic or new demo question was fitted. Canonical source text, eligibility holds and legal approval gates remain unchanged.

## Verification

| Check | Recorded result |
|---|---|
| Backend suite | 264 passed |
| Classifier / retrieval / verifier suites | 69 / 60 / 37 passed; overlapping suites, not a combined unique-test count |
| Focused concern suite | 31 passed |
| Local development inputs | 436 forms, 425 labeled |
| Topic and coverage matches | 425/425 each; macro-F1 1.000 each |
| Routing | 432/436; four preserved conservative policy deferrals |
| Excluded-input admissions | 0/80 |
| Known-relevant retrieval | Hit@5 93/93; Hit@1 70/93; MRR@5 0.8728; known-relevant recall 0.9570 |
| Local evidence integrity | 1,465 candidate checks, no failures; 413/413 exact excerpts passed |
| Earlier inspected 100-question replay | Topic/scope 100/100; route 98/100; two clarifications retained |
| AI-on cohort | 46 questions: 24 initially new and 22 inspected replays; all 46 topic/scope/route expectations matched after repair |
| Full AI-on outcomes | 27 generated, 3 partial, 16 withheld; 9 withheld were correctly outside scope |
| Full AI citation audit | 156 candidate, 83 citation and 9 fallback-excerpt checks; no mechanical failures |
| Final targeted checks | Six status/provider cases: four generated, two withheld; two return-condition cases: both generated; no application/provider errors in either targeted check |
| Browser rehearsal | {len(browser['questions'])} submitted questions, plus references, AI toggle, empty-input validation and current performance-page checks |

The full 46-question run was followed by targeted backend repairs and checks; it is not represented as a full fresh evaluation of the final backend. The same 24-question cohort was inspected and reused during repair. These scores are engineering diagnostics, not independent human, population-level or legal-answer accuracy.

The frozen domain expectation for DEMO_NEW_016 omitted its consumer concern. Raw domain agreement remains 45/46; see annotation-errata.json. No frozen question or expected label was changed to improve a score. A separate order-sensitive domain-comparison bug affected earlier raw mixed-case observations; the metric implementation is now set-based and has a regression test.

## Live-answer limits retained

The full run had three provider-limited answers; their subsequent targeted checks had no provider failures. PH4_053 still failed a source-qualification check and PH4_056 still failed semantic support in the six-case recheck. They remain withheld, with source/local fallback behavior. Held counted-working-time authority still prevents PH4_007 from receiving an AI rule explanation. Some mixed questions retain only their approved paragraphs.

The complete 46-question run still exposed overbroad status/return wording. Those observations remain in QUESTIONS_AND_RESULTS.md. The later safety-check and return-check directories preserve the corrective checks; they do not erase earlier failures. Exact citations and same-model approval are not proof of legal correctness.

Both full AI runs and the targeted checks used {returns['usage']['provider_requests']} cumulative provider requests at an estimated US${returns['usage']['estimated_usd']:.5f}, within the same 200-request / US$0.35 study cap. This excludes browser requests and is not verified billing. Website limits were unchanged. Every exported question was fictional synthetic test text; no personal chat was used.

## Demo handoff

Use the URL printed by start-website.ps1. The repaired preview is verified at http://127.0.0.1:5174/ with AI enabled. Follow DEMO_GUIDE.md for a rehearsal. The Performance page is bound to local-pipeline-evaluation-v1.6.27; historical generated-answer studies remain marked stale where appropriate.

Source-currentness/legal review, held working-time/meal-period material, missing final-pay/COE deadlines and related thirteenth-month authority remain open. Exact current regional wage amounts, excluded legal fields and case-outcome predictions remain outside this MVP. Unknown questions may still require clarification or receive a limited response.

## Preserved evidence

CHANGES.md, DEMO_GUIDE.md, summary.json, annotation-errata.json, QUESTIONS_AND_RESULTS_RELEASE.md, QUESTIONS_AND_RESULTS.md, release-pass/, final-pass/, safety-check/, return-check/, browser-evidence.json and browser-consumer-answer.png. The prepared first-pass/ was never executed. Failed and superseded packaging attempts and evaluation v1.6.25's detected government-boundary regression are retained. Evaluation v1.6.26 verified its repair; v1.6.27 verifies the selected classifier/retrieval stack. No earlier study was overwritten or relabeled.
'''
(BASE/'REPORT.md').write_text(report,encoding='utf-8')
save(BASE/'checksums.json',{p.relative_to(BASE).as_posix():sha(p) for p in sorted(BASE.rglob('*')) if p.is_file() and p.name!='checksums.json' and not p.name.endswith(('.sqlite3-wal','.sqlite3-shm'))})
print('Wrote the demo report, summary, annotation errata and evidence checksums.')
