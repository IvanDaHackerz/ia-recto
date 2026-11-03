"""Report routing/fragment repairs without relabelling synthetic data as gold."""
import hashlib,json,re
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
old=read(BASE/'baseline.json');first=read(BASE/'reserved-first-check.json');final=read(BASE/'selected-release-check.json')
fresh=read(BASE/'fresh-results.json');fresh_final=read(BASE/'fresh-selected-recheck.json')
new_first=[r for r in first['observations'] if r['case']['phase']=='reserved_wording']
current=read(ROOT/'CURRENT_ARTIFACTS.json');local=read(ROOT/current['local_pipeline_evaluation']/'metrics.json')
baseline=local['strata']['all']['baseline']
pipeline_errors=read(ROOT/current['local_pipeline_evaluation']/'errors.json')
browser=read(BASE/'browser-evidence.json')
backend_log=(BASE/'backend-final-tests.log').read_text(encoding='utf-8-sig')
assert re.search(r'Ran 285 tests',backend_log) and re.search(r'^OK\s*$',backend_log,re.M),backend_log[-2000:]
assert final['passed']==72 and fresh_final['passed']==24
assert baseline['primary']['accuracy']['numerator']==425 and baseline['scope']['accuracy']['numerator']==425
assert baseline['route_match']['numerator']==432
rows=[{'cohort':'40 previously inspected questions','first_checks_passed':old['passed'],'inputs':40,'after_inspection_checks_passed':40},
    {'cohort':'32 first reserved wording questions','first_checks_passed':sum(not r['issues'] for r in new_first),'inputs':32,'after_inspection_checks_passed':32},
    {'cohort':'24 further wording questions','first_checks_passed':fresh['passed'],'inputs':24,'after_inspection_checks_passed':fresh_final['passed']}]
summary={'role':'AI-authored routing and sentence-structure development checks, not independent legal accuracy',
    'cohorts':rows,'final_checked_questions':final['inputs']+fresh_final['inputs'],
    'final_passed':final['passed']+fresh_final['passed'],'independent_human_questions':0,'llm_calls':0,
    'classifier':current['classifier'],'retrieval':current['retrieval'],'verifier':current['verifier'],
    'local_pipeline_evaluation':current['local_pipeline_evaluation'],
    'local_metrics':local,'historical_route_differences':[r['case_id'] for r in pipeline_errors],
    'backend_software_tests':285,'browser_checks':browser,
    'retrieval_preservation':read(BASE/'retrieval-preservation.json'),
    'pre_inference_expectation_correction':read(BASE/'pre-inference-adjudication.json'),
    'limitations':['All questions are synthetic development inputs; inspected rechecks are not unseen validation.',
        'Expected component counts are structural judgments; they do not establish legal correctness.',
        'Classifier weights, vocabulary, probability calibration, thresholds and training membership were preserved.',
        'Source gaps and generated-answer quality were outside this task; no external LLM calls were made.']}
(BASE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Routing and concern-fragment repair — 26 October 2026',
    'The owner authorized steps 1 and 2: repair three valid-question routing failures and stop background/follow-up sentences becoming extra concerns. The study directory retains the date of the interrupted start on 25 October.',
    '## Result',
    f"Final selected stack: {current['classifier']}, {current['retrieval']}, {current['verifier']}. All 96 selected routing/structure checks pass after inspection and repair. The three reported failures now route to a single labor or consumer component. This is development evidence, not an independent accuracy claim.",
    '## Changes',
    '- Keep temporal “saka lang”/“tsaka lang”, probation standards, product-operation descriptions and same-seller responses with their scenarios.',
    '- Recognize retail condition descriptions such as refurbished/used items represented as new, without making a legal finding.',
    '- Keep genuine employment complaints and information requests out of the background-only bucket. Retain excluded-job context, including seafarer versus generic overseas wording.',
    '- Treat pure introductions and vague standards complaints as requiring clarification. Exclude negated category statements from context propagation.',
    '- Attach scope/focus requests to an existing relevant concern. Preserve different actors, independent purchases/employment disputes and actual excluded concerns.',
    'Original questions and a source-fragment accounting record remain available. The repairs change sentence grouping and explicit scope constraints; no new questions were fitted and no confidence threshold was lowered.',
    '## Frozen checks',
    '| Cohort | First check | Recheck after inspection |\n|---|---:|---:|']
for row in rows:lines[-1]+=f"\n| {row['cohort']} | {row['first_checks_passed']}/{row['inputs']} | {row['after_inspection_checks_passed']}/{row['inputs']} |"
lines += ['All initial observations and intermediate failures remain in this directory. The 32- and 24-question cohorts were written/frozen before their respective first inference, then opened and used for repair after failures. Their later passing results are inspected rechecks, not fresh holdout results.',
    'Before the first 32-question reserved check, NEW_032’s expected component count was corrected from one to two: unpaid overtime and a separate equipment-loss deduction should remain distinct. The original case file/hash and the pre-inference adjudication are preserved.',
    '## Packaging and preservation',
    'The selected classifier inherits its trained atomic model, feature vocabulary, probability calibration, thresholds and training membership unchanged. The retrieval rebuild updates integrity bindings: source records, semantic windows, vectors and coverage are byte-identical to the parent, and no law/source was added. Current-law reviews, legal-answer gates and deployment permissions remain unchanged.',
    'Intermediate candidates and failed packaging attempts were preserved. A legacy repacker assumed files absent from this parent, so the existing preintegration packager was used. A later candidate failed an old background-introduction regression; it was not selected. The corrected release passes the required tests.',
    '## Verification',
    'Software checks pass: 45 concern regressions, 69 classifier package tests, 60 retrieval tests, 37 verifier tests and 285 backend tests. These suites overlap and should not be summed as independent questions. The selected application checks also pass 27 tests. See concern-final-source-tests.log, application-selected-tests.log, backend-final-tests.log and the sealed package software_tests.json files. Earlier backend-tests.log preserves the candidate failure and packaging errors; backend-final-tests.log records the corrected stack.',
    f"The final local replay ({current['local_pipeline_evaluation']}) covers 436 forms / 171 families. Topic and coverage each match 425/425 labeled inputs (macro F1 1.0 on this inspected development packet). Routes match 432/436. A known relevant provision appears in the top five for 93/93 judged concern groups, while top-one hits are 70/93. Outside-scope admissions are 0/80. Candidate integrity and recorded-excerpt checks pass; these checks do not establish legal correctness.",
    'Four frozen historical route expectations differ from the existing conditional-general-information policy: '+', '.join(r['case_id'] for r in pipeline_errors)+'. Their original labels are preserved; no new route disagreement remains compared with the pre-repair replay.',
    'Actual website submissions and visible results are saved in browser-evidence.json and browser screenshots. Website tests use AI off to isolate classification and source retrieval; the original AI-on preference is restored afterward. No provider credits were used.',
    '## Limits and remaining work',
    *['- '+s for s in summary['limitations']],
    '- The historical 436-question route expectations include preserved conservative-policy differences; consult the latest errors.json rather than claiming all historical routes match.',
    '- This task does not close independent human evaluation, legal-source currentness review or unrestricted defense acceptance.']
(BASE/'REPORT.md').write_text('\n\n'.join(lines)+'\n',encoding='utf-8')
hashes={p.relative_to(BASE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in BASE.rglob('*') if p.is_file() and p.name!='checksums.json' and '__pycache__' not in p.parts}
(BASE/'checksums.json').write_text(json.dumps(hashes,indent=2)+'\n')
print('Saved report, first-pass/recheck distinctions and',len(hashes),'evidence hashes.')
