"""Summarize retained observations; never promote synthetic probes to human gold."""
import collections,hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; H=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 current=read(ROOT/'CURRENT_ARTIFACTS.json');rows=read(H/'application-search-final.json');summary=read(H/'application-search-final.summary.json')
 browser=read(H/'browser-results.json');records=[json.loads(s) for s in (ROOT/current['retrieval']/'records.jsonl').read_text(encoding='utf-8').splitlines() if s]
 texts=[r['parent_text'] for r in records]
 browser_checks=[]
 for r in browser:
  c=r['case'];fields=r['fields'];expected_topic={'Mixed topics':'Mixed'}.get(c.get('topic'),c.get('topic'))
  check=bool(r['headings'])
  if c.get('flow')=='clarify':check=check and 'Let’s work out the concern' in r['headings'] and not r['quotes']
  else:
   check=check and any(v.startswith(expected_topic+' ·') for v in fields) and any(v.startswith(c['coverage']+' ·') for v in fields)
   if expected_topic=='Out of scope':check=check and 'Where this concern fits' in r['headings'] and not r['quotes']
   else:check=check and bool(r['quotes'])
  exact=all(any(q in t for t in texts) for q in r['quotes'])
  browser_checks.append({'id':c['id'],'labels_and_flow_match':check,'exact_quotes':exact,'zero_provider_calls':sum('0 LLM calls' in v for v in fields)==2})
 (H/'browser-summary.json').write_text(json.dumps({'checks':browser_checks,'count':len(browser),'matches':sum(x['labels_and_flow_match'] for x in browser_checks),'exact_quote_cases':sum(x['exact_quotes'] for x in browser_checks),'zero_provider_cases':sum(x['zero_provider_calls'] for x in browser_checks)},indent=2)+'\n',encoding='utf-8')
 if len(browser_checks)!=17 or not all(all(c[k] for k in ['labels_and_flow_match','exact_quotes','zero_provider_calls']) for c in browser_checks):raise RuntimeError('Review browser mismatches')
 byid={r['case']['id']:r for r in browser}
 passage_checks={'offline_purchase_has_no_online_remedy':all('online' not in q.lower() for q in byid['WEB03']['quotes']),
  'shelf_price_uses_price_tag_rule':all('price tag' in q.lower() for q in byid['WEB12']['quotes']),
  'holiday_followup_is_one_holiday_passage':len(byid['WEB15']['quotes'])==1 and 'holiday' in byid['WEB15']['quotes'][0].lower(),
  'hidden_fee_has_sales_practice_passage':all('deceptive' in q.lower() or 'unfair' in q.lower() for q in byid['WEB16']['quotes']),
  'noisy_holiday_preserves_same_passage':byid['WEB17']['quotes']==byid['WEB15']['quotes']}
 if not all(passage_checks.values()):raise RuntimeError('Review source-context regression')
 (H/'browser-passage-checks.json').write_text(json.dumps(passage_checks,indent=2)+'\n',encoding='utf-8')
 baseline=read(H/'baseline.summary.json');variants=read(H/'variants-packaged-v36.json');legacy=read(H/'legacy-summary.json')
 metrics=read(ROOT/current['local_pipeline_evaluation']/'metrics.json');hist=metrics['strata']['all']['baseline']
 gaps=[r['case'] for r in rows if r['flow']=='local_sources' and not r['headings']]
 (H/'remaining-source-limits.json').write_text(json.dumps(gaps,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 frozen={n:sha(H/n) for n in ['development_cases.json','reserved_cases.json','final_probe_cases.json','all_cases.json','variant_cases.json']}
 checks=read(ROOT/current['verifier']/'software_tests.json')
 report=f'''# Classifier usability stress test

Local AI-off testing and repairs, 21 October 2026. This is synthetic development evidence, not independent human gold, legal correctness, or deployment acceptance.

## Result

- Initial new batch: {baseline['labels_correct']}/{baseline['labeled']} labeled questions and {baseline['flow_correct']}/{baseline['count']} expected routes matched.
- Final application batch: {summary['labels_correct']}/{summary['labeled']} labeled questions and {summary['flow_correct']}/{summary['count']} routes matched, including 16 intentionally vague prompts.
- Paired uppercase, spacing and light typing variants: {variants['count']-len(variants['failures'])}/{variants['count']} passed on the packaged classifier. These derive from 184 base questions and are not 552 independent scenarios.
- Previous application regression set: {sum(s['flow_matches'] for s in legacy['sets'].values())}/74 routes matched.
- Website: 17/17 questions (12 new scenarios and five retrieval/follow-up/typing regressions) matched displayed topic, coverage and response behavior; every displayed quote matched stored source text; zero provider calls. Five specific source-context regression checks also passed, without claiming legal entailment.
- Historical development replay: {hist['primary']['accuracy']['numerator']}/{hist['primary']['accuracy']['denominator']} topic labels, topic macro F1 {hist['primary']['macro_f1']:.3f}, scope macro F1 {hist['scope']['macro_f1']:.3f}. Its four earlier-policy routing differences remain in errors.json; expectations were preserved.
- Application median analysis time in this local run: {summary['median_ms']:.1f} ms. All {summary['count']} excerpt checks passed; {summary['quoted_responses']} responses contained at least one passage. A passage does not prove legal applicability.
- Packaged checks: {checks['classifier']['tests_run']} classifier, {checks['retrieval']['tests_run']} retrieval, {checks['verifier']['tests_run']} verifier checks. The 212-test complete backend suite is recorded in backend-tests-noise-final.log; the extra 16 contrastive classifier methods are recorded in contrastive-tests-noise-final.log.

## Repairs

Employment introductions no longer create purchases; employer industries and incidental rest-day wording remain distinct from purchase/service complaints. Taglish work and purchase expressions, project-based status, public school employment and domestic helper categories receive explicit scope handling. Request conjunctions preserve a separate excluded concern. Anaphoric pay follow-ups stay with their scenario, and school-specific passages are filtered from generic office questions. Hyphenated minimum-wage requests and mobile network/data-plan disputes retain their exclusions. Missing-space repair no longer splits network into net work. Repeated letters are repaired against the declared scope and grammar vocabulary, so payroll and anaphoric words keep their context. Unanchored payment and generic help prompts ask for detail. Search facets now recognize cracked screens, native fault/safety wording, ordinary wage-payment forms and required waiting. Offline purchases cannot quote online-only remedies, and shelf prices retrieve price-tag rules rather than comparative-advertising rules.

Atomic model weights, TF-IDF vocabulary, original training membership and routing thresholds were retained. Probability calibration was replayed on the original training folds because preprocessing changed. The final follow-up repair preserved all 459 original training-parent feature rows exactly, so its inherited fitted calibration was retained. No new test questions were fitted into the model. This does not establish absence of overfitting or broad language understanding.

## Exposure and limits

138 initial development questions were opened and used for repairs. A reserved 46-question synthetic probe initially matched 39/42 labels and 40/46 routes; its six failures were inspected and it became development data. A further 40-question probe initially matched 35/36 labels and 39/40 routes; its two failures were inspected and repaired, so it also became development data. Both first-pass outputs remain available. The 12 new website questions were composed after the classifier repairs, then checked through the visible interface. None of these sets is independently human-authored.

Supported scope does not guarantee that the stored corpus can answer the question. {len(gaps)} final responses still have no quotable passage; see remaining-source-limits.json. In particular, final-pay/COE, thirteenth-month source reviews and specialized facts remain limited. A forced-resignation scenario may also require a better reviewed source. We did not invent text or open legal-answer/deployment gates to conceal these gaps.

Live LLM explanation quality, provider latency and paid requests were not tested here. AI was off throughout the tests and restored afterward for new user submissions. Further independent user testing and legal source review remain necessary. Exact quotes and topic matching are not legal entailment.

## Current stack and evidence

- Classifier: {current['classifier']}
- Retrieval: {current['retrieval']}
- Verifier: {current['verifier']}
- Historical replay: {current['local_pipeline_evaluation']}
- application-search-final.json, its summary, legacy-summary.json, variants-packaged-v36.json and browser-results.json preserve observations. Earlier passes and failed builds are retained.
- browser-classifier-proof.jpg shows the displayed local classifier result.

All changes are local. No GitHub push was performed by this task.
'''
 (H/'REPORT.md').write_text(report,encoding='utf-8')
 (H/'case-manifest.json').write_text(json.dumps({'provenance':'AI-authored synthetic development and regression cases; not independent human gold','case_files':frozen,'stack':{k:current[k] for k in ['classifier','retrieval','verifier']},'provider_calls':0,'independent_acceptance':False},indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'application':summary,'browser_matches':17,'remaining_source_limits':len(gaps)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
