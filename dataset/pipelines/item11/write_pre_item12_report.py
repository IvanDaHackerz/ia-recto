"""Freeze repairs, development evidence and the remaining external prerequisites."""
from __future__ import annotations
import argparse,json,shutil
from pathlib import Path
from common import ROOT,PIPELINE,readrows,save,jsonl,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--classifier',type=Path,required=True)
    p.add_argument('--index',type=Path,required=True);p.add_argument('--packet',type=Path,required=True);a=p.parse_args()
    c=a.classifier.resolve();i=a.index.resolve();o=a.packet.resolve()
    if (o/'artifact_checksums.json').exists():raise ValueError('Packet already frozen')
    reg=json.loads((c/'opened_test_regression_metrics.json').read_text())
    manifest=json.loads((c/'run_manifest.json').read_text())
    ct=json.loads((c/'software_tests.json').read_text());rt=json.loads((i/'software_tests.json').read_text())
    bench=json.loads((i/'benchmark_metrics.json').read_text());end=json.loads((i/'end_to_end_metrics.json').read_text())
    im=json.loads((i/'index_manifest.json').read_text());audit=json.loads((i/'source_audit.json').read_text())
    assert ct['passed'] and rt['passed'] and reg['all_applicable_targets_met'] and manifest['all_development_targets_met']
    cm={'model_version':c.name,'status':'offline_development_repairs_complete','deployment_allowed':False,
        'training_parent_rows':459,'new_training_questions':0,'unique_atomic_fit_texts':222,
        'atomic_classifier_weights_equal_original_parent':True,'original_parent':'item10-classifier-v1.3.1',
        'original_once_unseen_parent_accuracy':.95,'development_targets_passed':True,
        'opened_original_test_role':'Inspected development regression; not an independent test',
        'regression_accuracy':reg['primary']['accuracy'],'regression_decisive_coverage':reg['routing']['decisive_coverage'],
        'regression_partial_recall':reg['scope']['classification_report']['partially_supported']['recall'],
        'regression_partial_precision':reg['scope']['classification_report']['partially_supported']['precision'],
        'all_regression_targets_passed':True,'regression_new_classification_errors':0,
        'thresholds':json.loads((c/'selection_frozen.json').read_text())['thresholds'],
        'calibration_method':manifest['confidence_method'],'fresh_independent_holdout_evaluated':False,
        'independent_human_gold_available':False,'software_tests_passed':ct['tests_run'],
        'referral_routing':'Explicit topic-based candidates; contacts require refresh; no invented destinations',
        'limitations':['Inspected questions informed preprocessing and routing repairs',
            'Confidence is training-distribution label confidence, not legal correctness',
            'No independent human evaluation or legal-professional approval','Live answering remains disabled']}
    save(c/'MODEL_CARD.json',cm)
    rc={'index_version':i.name,'status':'offline_development_repairs_complete','indexed_chunks':im['indexed_chunks'],
        'indexed_provisions':im['indexed_provisions'],'indexed_documents':audit['indexed_documents'],
        'default_method':'bm25','bm25_hit_at_5':bench['methods']['bm25']['hit@5'],
        'end_to_end_hit_at_5_per_component':end['hit_at_5_per_component'],
        'positive_queries':56,'positive_families':28,'negative_controls_passed':11,
        'software_tests_passed':rt['tests_run'],'fresh_holdout':False,'independent_human_gold':False,
        'lexical_glossary_informed_by_development_errors':True,'method_selected_on_development':True,
        'source_data_modified':False,'legal_currentness_refreshed':False,'recorded_status_as_of':'2026-09-29',
        'deployment_allowed':False,'answer_generation_allowed':False,
        'limitations':['Known relevance judgments are partial and AI-authored','Reported perfect development hits are not a real-world accuracy claim',
            'Final pay/COE, general thirteenth-month entitlement and current DTI procedure remain gated',
            'Semantic and hybrid methods perform below the BM25 default']}
    save(i/'RETRIEVAL_CARD.json',rc)
    extra=[r for r in readrows(i/'excluded_chunks.jsonl') if r['item7_answer_eligible']]
    jsonl(i/'additional_quarantine.jsonl',extra)
    save(i/'error_analysis.json',{'role':'Inspected AI development benchmark','bm25_misses_at_5':[],
        'end_to_end_missed_query_ids':end['missed_query_ids'],'relevance_labels_exhaustive':False})
    issues=[
        {'id':1,'issue':'Investment/investigation false scope match','status':'fixed_and_tested'},
        {'id':2,'issue':'69% routing coverage below 70%','status':'fixed_on_development_regression','current':cm['regression_decisive_coverage']},
        {'id':3,'issue':'Generic defective-service classification miss','status':'fixed_on_development_regression'},
        {'id':4,'issue':'Six BM25 top-five misses','status':'fixed_on_inspected_development_benchmark'},
        {'id':5,'issue':'English/Taglish development retrieval gap','status':'fixed_on_inspected_development_benchmark'},
        {'id':6,'issue':'Independent human evaluation missing','status':'external_human_input_required','prepared':'human_gold_intake.jsonl and validator'},
        {'id':7,'issue':'Real-world confidence validation','status':'requires_fresh_independent_evaluation','development_ece_primary':reg['primary']['top_label_expected_calibration_error_10_bins']},
        {'id':8,'issue':'Final pay/COE, thirteenth-month and DTI source gaps','status':'open_source_verification_required','prepared':'Four final-pay AI proposals; 29 DTI structural candidates; MO 28 official copy still needed'},
        {'id':9,'issue':'OCR/text review backlog and specialized-source quarantine','status':'pending_human_source_review','pending_provisions':258,'additional_quarantine_chunks':len(extra)},
        {'id':10,'issue':'Currentness and referral-contact refresh','status':'partial_audit_only','public_urls_attempted':39,'public_urls_accessible':19},
        {'id':11,'issue':'Item 12 evidence/citation verification','status':'planned_item12_not_started'},
        {'id':12,'issue':'Answer generation, frontend, system evaluation and formal approval','status':'future_milestones_and_external_approvals_pending'},
        {'id':13,'issue':'Household repair mistaken for domestic employment','status':'fixed_and_tested'},
        {'id':14,'issue':'Unnecessary clarification despite cashier/product context','status':'fixed_and_tested'},
        {'id':15,'issue':'Cross-references split into fake DTI sections and Rule headings','status':'candidate_parser_fixed_source_approval_pending'},
        {'id':16,'issue':'Automatic official referral selection absent','status':'candidate_routing_implemented_contact_refresh_pending'},
        {'id':17,'issue':'Overseas foreign-exchange-remittance passages in general labor index','status':'quarantined_and_tested','additional_chunks':3}]
    save(o/'issue_ledger.json',{'all_issues_closed':False,'item12_started':False,'proceed_to_item12_under_owner_instruction':False,
        'independent_human_approval_recorded':False,'legal_professional_approval_recorded':False,'issues':issues})
    table=[]
    for label,name in [('Seed validation','validation'),('AI general development','ai_general_development'),
                       ('AI typing development','ai_typing_development'),('Opened synthetic regression','opened_test_regression')]:
        m=json.loads((c/(name+'_metrics.json')).read_text())
        table.append(f"| {label} | {m['primary']['rows']} | {m['primary']['accuracy']:.1%} | {m['routing']['decisive_coverage']:.1%} |")
    methods='\n'.join(f"| {name} | {v['hit@5']:.1%} | {v['mrr@10']:.3f} |" for name,v in bench['methods'].items())
    text=f'''# Repairs before Item 12 — 17 October 2026

The software defects found in the scan have been repaired and retested. **Not all project issues are closed. Item 12 has not started.** Independent human evaluation, source verification/currentness, contacts and formal approvals remain outstanding.

## Current artifacts

- Classifier: {c.name}
- Retrieval: {i.name}
- Canonical files, the frozen reviewed seed and original evaluated parent artifacts are unchanged.
- Earlier intermediate candidates remain historical experiments; use CURRENT_ARTIFACTS.json.

## Repairs

Investment patterns now recognize investment words without swallowing investigation/investigator. Ordinary defective services remain separated from medical and telecom exclusions. Private shops do not become employment concerns. Household repair does not inherit kasambahay employment context. Recognized cashier/product and SEnA procedure context avoids unnecessary clarification. Missing employment categories and unresolved independent concerns still require clarification.

Lexical retrieval normalizes a disclosed English/Taglish concept glossary symmetrically for documents and queries, handles common inflections, gives headings two occurrences and includes document titles. These changes were informed by inspected development errors. No question rows, IDF on questions or encoder fine-tuning were added. BM25 remains the method selected on the earlier development comparison. Semantic/hybrid search is retained as experimental comparison.

Three additional overseas-remittance chunks are excluded. The index now has **{im['indexed_chunks']} chunks / {im['indexed_provisions']} provisions / {audit['indexed_documents']} documents**, with {len(extra)} additional quarantined chunks from the original flagged-eligible set. Fewer indexed chunks here reflects tighter scope screening.

Referral candidates come from explicit topic rules and existing directory IDs. Bank and lending-company referrals differ; seafarer-pay referrals do not point to certification services. Unknown financial/provider context yields no invented destination. Candidates disclose old verification dates and require contact refresh; unverified phone/email fields are not exposed by the runtime.

## Classifier development results

| Partition | Classifiable rows | Classification accuracy | Decisive coverage |
|---|---:|---:|---:|
{chr(10).join(table)}

On the opened regression set, partial recall and precision remain **11/11 and 1.000**, all numeric gates pass, and routing coverage improves from 69% to **{cm['regression_decisive_coverage']:.1%}**. Thresholds remain 0.80 primary / 0.85 scope, selected on validation. Underlying atomic classifier weights and training membership remain unchanged. Calibration is fitted on purged training-only grouped folds.

The original once-unseen 95/100 result is preserved. The repaired 100/100 result is regression evidence, not a new final accuracy estimate. Confidence remains imperfect: regression primary ECE is {reg['primary']['top_label_expected_calibration_error_10_bins']:.3f}, scope ECE is {reg['scope']['top_label_expected_calibration_error_10_bins']:.3f}. Do not turn label confidence into legal-correctness probabilities or calibrate on the inspected test to improve these figures.

## Retrieval development results

| Method | Hit@5 with supplied domain | MRR@10 |
|---|---:|---:|
{methods}

BM25 finds a known relevant passage for **56/56** existing positive queries (28 English / 28 Taglish); all three methods pass 11/11 negative controls. The actual classifier-to-retrieval path also finds those passages for **56/56**, without a supplied oracle domain, and passes 11/11 negative controls. The classifier pipeline result uses at most five results per supported component.

These 56 queries represent only 28 scenario families. They and their partial relevance judgments were AI-authored, inspected and reused during repair. Perfect development hits do not establish perfect real-world accuracy. Bootstrap intervals in benchmark_metrics.json are descriptive; they do not measure generator bias, missing relevance labels or legal correctness. No generated answers were evaluated.

## Verification

{ct['tests_run']}/{ct['tests_run']} classifier tests and {rt['tests_run']}/{rt['tests_run']} retrieval tests pass. Five independent-intake validator tests and three DTI structure tests pass. Frozen seed validation passes 59/59 checks using the bundled document runtime. Tests cover scope false positives, regulated-service boundaries, household repair, private shops, missing facts, component separation, referral destinations, training/calibration leakage, source/index hashes, numeric BM25 behavior, citations/offsets and token coverage.

The blank 100-row human intake correctly fails validation. It contains **zero questions** and is not an additional dataset.

## Remaining work that cannot be marked complete by Codex

1. **Independent human gold:** a person must write and label fresh questions. Reviewing or lightly rewriting the AI development questions does not make an independent holdout. The blank intake, provenance/overlap validator and handoff are prepared.
2. **Source coverage and review:** 258 original provisions remain pending. Four final-pay records have AI visual-comparison repair proposals. A tested DTI parser produces 29 proper section candidates from 31 original records, without splitting cross-references into fake sections. Proposals remain gated. MO 28 still needs a verified official full-text copy; current-year thirteenth-month guidance remains unconfirmed. Broad discovery candidates are optional acquisitions, not missing verified authorities to bulk-promote.
3. **Currentness and contacts:** all 39 official-source/contact URLs were attempted; 19 were accessible, others returned access, certificate or timeout errors. HTTP success and literal contact matches do not certify currentness. Browser research additionally corroborated the DOLE ARMS portal, the DTI complaints page, the DTI DAO 20-02 listing and a 2026 DOLE final-pay reminder. Original legal-status/contact dates remain unchanged. No unsupported no-amendment conclusion was recorded.
4. **Formal approvals and later milestones:** team/adviser approval and independent evaluation are still required for formal acceptance. Licensed Philippine legal-professional review of selected generated answers belongs to the later answer-evaluation stage. Item 12, answer generation, frontend integration and answer-level evaluation are planned work, not defects that can be honestly declared finished before implementing them.

See HUMAN_REVIEW_HANDOFF.md and issue_ledger.json. Under the owner's instruction to close everything before proceeding, **the project remains held before Item 12**. No human or legal-professional approval, current-law certification, live answer generation or deployment was fabricated.

## Official pages checked

- https://arms.dole.gov.ph/
- https://fairtrade.dti.gov.ph/faq/how-to-file-a-consumer-complaint/
- https://fairtrade.dti.gov.ph/resources/laws-policies/
- https://dole.gov.ph/news/final-pay-coe-must-be-released-on-time-dole/
'''
    (o/'REPAIR_REPORT.md').write_text(text,encoding='utf-8')
    (c/'REPAIR_REPORT.md').write_text(text,encoding='utf-8')
    (i/'RETRIEVAL_REPORT.md').write_text(text,encoding='utf-8')
    save(o/'verification.json',{'classifier_tests':ct,'retrieval_tests':rt,'gold_intake_tests':5,
        'source_structure_tests':3,'frozen_seed_checks':59,'all_software_tests_passed':True,
        'blank_intake_expected_to_fail':True,'independent_human_gold_available':False})
    save(o/'experiment_history.json',{'classifier_candidates':{
        'v1.5.0':'Rejected: regulated medical service boundary test failed',
        'v1.5.1':'Superseded: passed 44 tests; 46/56 actual classifier-to-retrieval hits',
        'v1.5.2':'Rejected: private-sector workers/uniform fee constraints failed tests',
        'v1.5.3':'Superseded during referral versioning; not accepted',
        'v1.5.4':'Current: all 49 tests and regression gates pass'},
        'retrieval_candidates':['v1.2.0','v1.2.1','v1.2.2'],
        'current_retrieval':'v1.2.3','all_scores_development_only':True})
    for file in PIPELINE.glob('*.py'):shutil.copy2(file,i/file.name)
    for name in ['test_logical_classifier.py','evaluate_partial_support_repair.py','validate_independent_gold.py','test_independent_gold.py']:
        shutil.copy2(ROOT/'dataset/pipelines/item10'/name,c/name)
    for folder in [c,i,o]:
        save(folder/'artifact_checksums.json',{str(f.relative_to(folder)):sha(f) for f in folder.rglob('*')
            if f.is_file() and '__pycache__' not in str(f) and f.name!='artifact_checksums.json'})
    current={'classifier':str(c.relative_to(ROOT)).replace('\\','/'),
        'retrieval':str(i.relative_to(ROOT)).replace('\\','/'),'repair_packet':str(o.relative_to(ROOT)).replace('\\','/'),
        'development_only':True,'all_project_issues_closed':False,'item12_started':False,
        'deployment_allowed':False,'answer_generation_allowed':False}
    save(ROOT/'CURRENT_ARTIFACTS.json',current)
    print(json.dumps({'classifier':cm,'retrieval':rc,'all_issues_closed':False},indent=2))
if __name__=='__main__':main()
