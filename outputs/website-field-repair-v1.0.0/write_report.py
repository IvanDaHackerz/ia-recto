"""Summarize completed checks without presenting development data as human gold."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
current=read(ROOT/'CURRENT_ARTIFACTS.json');summary=read(HERE/'summary.json')
browser=read(HERE/'browser-accepted-results.json')
if len(browser)!=12:raise ValueError('Complete the 12 browser regressions first')
names={'labor':'Labor','consumer':'Consumer','mixed':'Mixed','out_of_scope':'Out of scope'}
for r in browser:
    f=r['facts'];expected=r['expected']
    r['flow_and_label_match']=('work out the concern' in ' '.join(f['headings']).lower() if expected=='clarify' else any(t.startswith(names[expected]+' ·') for t in f['fields']))
    r['diagnostics_visible']=any(t in ['Topic','Tentative topic'] for t in f['fields']) and 'Topic coverage' in f['fields']
    r['duplicate_quotes']=len(f['quotes'])-len(set(f['quotes']))
    r['zero_llm_calls']=all(not re.search(r'[1-9]\d* LLM calls',t) for t in f['fields'])
old=[json.loads(l) for l in (ROOT/'outputs/item11-retrieval-v1.3.7/records.jsonl').read_text(encoding='utf-8').splitlines()]
new=[json.loads(l) for l in (ROOT/current['retrieval']/'records.jsonl').read_text(encoding='utf-8').splitlines()]
identity=lambda rows:{r['chunk_id']:(r['provision_id'],r['parent_text'],r['display_text']) for r in rows}
preserved=identity(old)==identity(new)
if not preserved:raise ValueError('Original indexed membership or legal text changed')
for r in browser:r['quotes_exact']=all(any(q in hit['parent_text'] for hit in new) for q in r['facts']['quotes'])
receipt={'browser_cases':len(browser),'flow_and_label_matches':sum(r['flow_and_label_match'] for r in browser),
    'diagnostics_visible':sum(r['diagnostics_visible'] for r in browser),'duplicate_quotes':sum(r['duplicate_quotes'] for r in browser),
    'all_browser_quotes_exact':all(r['quotes_exact'] for r in browser),'zero_live_llm_calls':all(r['zero_llm_calls'] for r in browser),
    'indexed_membership_and_text_preserved':preserved,'chunks':len(new),'provisions':len({r['provision_id'] for r in new})}
(HERE/'browser-summary.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
metrics=read(ROOT/current['local_pipeline_evaluation']/'metrics.json');m=metrics['strata']['all']['baseline']
checks=read(ROOT/current['verifier']/'software_tests.json');front=read(HERE/'frontend-checks.json')
log=(HERE/'backend-tests-accepted.log').read_text(encoding='utf-8')
if not re.search(r'\nRan \d+ tests? in [^\n]+\n\nOK(?:\n|$)',log):raise ValueError('Backend suite is not passing')
backend=int(re.findall(r'Ran (\d+) tests?',log)[-1])
reg=summary['sets']['regression'];additional=summary['sets']['fresh_synthetic']
text=f'''# Website classifier and source repair

The reproduced spelling, concern-handling and source-selection failures have been repaired and checked in the local application and real website. This is a development improvement, not independent human or legal acceptance.

Active stack: **{Path(current['classifier']).name}, {Path(current['retrieval']).name}, {Path(current['verifier']).name}**. The running website is http://127.0.0.1:5174/.

## Changes

- Local spelling repair no longer restores vowels or invents word boundaries in ordinary words as freely. “kind”, “hiring” and “liking” survive the reported transformations; the original typing-noise, literal, name, negation and idempotence checks pass.
- Employment detection requires an employment relationship or an intrinsic labor issue. “I must pay for repair” no longer creates an employment concern. Employer industry is distinguished from an actual banking, insurance or medical-service complaint.
- Rule questions stay connected to their existing concern. A new scope exclusion takes precedence over shared vocabulary, so an exact minimum-wage question remains separate from unpaid wages.
- Natural descriptions of household and overseas employment are recognized. Actual requests or reported discrepancies are retained instead of being discarded as actor introductions. Recognized financial-service concerns do not ask again what the payment was for.
- Disciplinary charges are distinguished from unexplained monetary charges.
- Retrieval uses explicit query concepts and relevant headings, with procedural subtopics for records, confidentiality, representation and internal redress. Unrelated effectivity provisions, recruitment fees, employee-resignation rules and quantity provisions are filtered from the demonstrated concerns.
- **Enclosing-rule coverage is preserved.** Its exact stored coverage text is carried into source conditions. A generic section heading no longer strips away a hospital-only rule's applicability. Conditions remain source-bound and do not grant legal approval.
- Local passages and LLM context share the topical check. Identical local quotations appear once. Irrelevant same-domain evidence cannot start a provider request in the adapter regression.
- Topic, coverage and label confidence remain available in diagnostics on local, clarification, referral and generated paths. Source excerpts are clearly labeled; they are not presented as AI explanations or findings about the user's rights.

The learned atomic weights, feature vocabulary, original training membership and thresholds are preserved. Calibration was replayed only on the original training folds; diagnostic/evaluation questions were not fitted. The original {len(new)} indexed chunks / {len({r['provision_id'] for r in new})} provisions and all their parent/chunk text are unchanged. Derived rule-coverage restrictions were added; no source was promoted to legal approval or refreshed as current law.

## Completed checks

| Check | Result |
| --- | --- |
| Original website questions, replayed through the application with AI off | {reg['flow_matches']}/{reg['count']} expected paths; {reg['label_matches']}/{reg['labeled']} labeled cases |
| Additional synthetic development questions | {additional['flow_matches']}/{additional['count']} expected paths; {additional['label_matches']}/{additional['labeled']} labeled cases |
| Real website checks, desktop and mobile | {receipt['flow_and_label_matches']}/12 expected paths/labels; {receipt['diagnostics_visible']}/12 diagnostics available |
| Repeated passages in the final browser pass | {receipt['duplicate_quotes']} |
| Browser quotations are exact spans of stored text | {receipt['all_browser_quotes_exact']} |
| Backend tests | {backend} passed |
| Frontend tests | {front['tests_passed']} passed; build and lint passed |
| Packaged classifier / retrieval / verifier checks | {checks['classifier']['tests_run']} / {checks['retrieval']['tests_run']} / {checks['verifier']['tests_run']} passed |

The 24 additional questions and 12 browser questions were new when authored, then inspected during repair. **They are now development/regression cases, not an untouched holdout or a human-written gold set.** A routing match or exact quotation does not establish legal-answer correctness. Some in-scope questions correctly show a source limitation.

The complete {m['inputs']}-input older development replay was rerun on this exact stack, with {metrics['counts']['independent_human_questions']} independent human questions and zero LLM calls. Topic macro-F1: **{m['primary']['macro_f1']:.4f}**; coverage macro-F1: **{m['scope']['macro_f1']:.4f}**. Route matches: **{m['route_match']['numerator']}/{m['route_match']['denominator']}**. Known relevant Hit@5: **{m['known_relevant_hit_at_5']['numerator']}/{m['known_relevant_hit_at_5']['denominator']}**. These are reused synthetic-development results. The four older clarification expectations for already recognizable labor questions are preserved in the raw errors rather than silently relabeled for the broader general-information policy. The Performance page is bound to the new replay; the older full-AI replay remains marked as a different inference version.

## Remaining limits

- This repair did not test live LLM prose, latency, provider reliability or paid end-to-end generation. Adapter/validation tests use mocks; the website submissions used AI off. AI availability is restored afterward for new user submissions.
- Final-pay/COE and main thirteenth-month related-source gaps/reviews remain. A normal-hours passage also does not by itself resolve every compensable-time scenario. The application must state a source limit where the stored material is insufficient.
- Exact source identity and local topic matching are not legal entailment, current-law verification or a guarantee for unfamiliar wording. Fresh independent questions, legal review and owner acceptance remain pending.
- The Impeccable context loader reported a stale design metadata sidecar at `UI/UX/app/.impeccable/design.json`. Its optional `document` refresh was kept separate from this repair.

## Evidence

- `summary.json`, `regression-results.json` and `fresh_synthetic-results.json`: 74 application checks and complete packets.
- `browser-accepted-results.json`, `browser-summary.json`: the final complete 12-question website pass, with displayed fields and passages. `browser-new-results.json` preserves all 27 observations across development passes; the accepted file is its verified final 12-row suffix.
- `warranty-final-desktop.jpg`, `warranty-final-mobile.jpg`: rendered proof.
- `{current['local_pipeline_evaluation']}`: complete current-stack replay, preserved expectations and errors.
- `backend-tests-accepted.log`, `frontend-checks.json`, and the packaged software-test logs: verification records.
- Earlier failed/intermediate builds and observations are preserved. `round1-summary-scorer-mismatch.json` used unmapped internal route names; the final scorer maps those names explicitly without changing raw questions or observations.

No live provider call was made for these repairs. Changes are local; this task did not push a GitHub update.
'''
(HERE/'REPORT.md').write_text(text,encoding='utf-8')
(HERE/'accepted-checksums.json').write_text(json.dumps({p.name:sha(p) for p in HERE.iterdir() if p.is_file() and p.name not in {'accepted-checksums.json'}},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report':str(HERE/'REPORT.md'),'backend_tests':backend,**receipt}))
