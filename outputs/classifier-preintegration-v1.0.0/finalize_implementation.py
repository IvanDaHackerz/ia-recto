"""Finalize the classifier-only preintegration handoff after software checks."""
from __future__ import annotations
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
PACKET=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'dataset/pipelines/item13'))
from evaluation_common import read,save,sha,verify_packet


def audit_preservation():
    freeze=read(PACKET/'implementation_freeze.json')
    groups=['parent_artifact_sha256','immutable_data_and_prior_artifacts_sha256','ui_sha256']
    changed=[name for group in groups for name,expected in freeze[group].items() if sha(ROOT/name)!=expected]
    ui=[]
    for folder,dirs,files in os.walk(ROOT/'UI/UX/app'):
        dirs[:]=[d for d in dirs if d not in {'node_modules','.git','dist'}]
        ui.extend((Path(folder)/name).relative_to(ROOT).as_posix() for name in files)
    added_or_removed=sorted(set(ui)^set(freeze['ui_sha256']))
    result={'passed':not changed and not added_or_removed,'changed_files':changed,'ui_added_or_removed_files':added_or_removed,
        **{group+'_count':len(freeze[group]) for group in groups}}
    save(PACKET/'preservation_audit.json',result)
    if not result['passed']:raise ValueError('Preservation check failed')
    return result


def finalize():
    if (PACKET/'artifact_checksums.json').exists():raise ValueError('Packet already finalized')
    versions={'classifier':'outputs/item10-classifier-v1.5.6','retrieval':'outputs/item11-retrieval-v1.2.5',
        'verifier':'outputs/item12-verifier-v1.0.3'}
    for key,path in versions.items():verify_packet(ROOT/path,runtime=key=='verifier')
    audit=audit_preservation()
    classifier_tests=read(ROOT/versions['classifier']/'software_tests.json')
    api_tests=read(PACKET/'api_software_tests.json')
    dependencies=read(ROOT/versions['verifier']/'software_tests.json')
    assert classifier_tests['passed'] and api_tests['passed'] and all(v['passed'] for v in dependencies.values())
    log=(PACKET/'evaluation_harness_software_tests.log').read_text(encoding='utf-8-sig')
    assert 'Ran 34 tests' in log and log.rstrip().endswith('OK')
    sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
    import joblib
    before=joblib.load(ROOT/'outputs/item10-classifier-v1.5.5/classifier.joblib')
    after=joblib.load(ROOT/versions['classifier']/'classifier.joblib')
    a,b=before['primary_model'].engine,after['primary_model'].engine
    unchanged={'atomic_weights':joblib.hash(a.atomic.model)==joblib.hash(b.atomic.model),
        'feature_vocabulary':joblib.hash(a.atomic.lexical)==joblib.hash(b.atomic.lexical),
        'calibration':joblib.hash(a.joint_model)==joblib.hash(b.joint_model),
        'thresholds':before['thresholds']==after['thresholds']}
    assert all(unchanged.values())
    from backend.classifier.service import ClassifierService
    service=ClassifierService();assert service.health()['status']=='ready'
    assert service.bundle['model_version']==after['model_version']
    protocol=read(ROOT/'dataset/pipelines/item13/protocol.json')
    assert protocol['classifier']==versions['classifier'] and protocol['verifier']==versions['verifier']
    assert protocol['retrieval']==versions['retrieval']
    assert not (ROOT/'outputs/item13-evaluation-v1.0.2').exists()
    repair=read(ROOT/versions['classifier']/'routing_implementation_audit.json')
    assert len(repair)==11 and all(r['implementation_expectation_met'] for r in repair)
    save(PACKET/'routing_implementation_audit.json',repair)
    counts={'classifier':classifier_tests['tests_run'],'api':api_tests['tests_run'],
        'retrieval':dependencies['retrieval']['tests_run'],'verifier':dependencies['verifier']['tests_run'],
        'evaluation_harness':34}
    status={'as_of':'2026-10-18','classifier_preintegration_implementation_complete':True,
        'classifier_routing_repairs_implemented':True,'local_backend_interface_implemented':True,
        'versioned_request_response_contract_implemented':True,'strict_input_and_error_handling_implemented':True,
        'artifact_dependency_and_runtime_checks_implemented':True,'compatible_dependency_bindings_complete':True,
        'software_checks_passed':True,'software_test_counts':counts,'unchanged_learned_state':unchanged,
        'formal_performance_evaluation_completed':False,'display_metrics_implemented':False,
        'interactive_owner_terminal_testing_completed':False,'independent_human_evaluation_completed':False,
        'formal_classifier_acceptance_completed':False,'website_integration_completed':False,'llm_integration_completed':False,
        'new_training_questions':0,'new_independent_human_questions':0,'new_legal_sources':0,'live_llm_calls':0,
        'answer_generation_allowed':False,'deployment_allowed':False}
    save(PACKET/'implementation_status.json',status)
    save(PACKET/'current_issue_ledger.json',{'as_of':'2026-10-18','scope':'Classifier preintegration implementation only',
        'implemented':['Routing/background/follow-up repairs','Bounded spelling and scope/workplace recognition',
            'Preserved confidence/clarification policy','Pinned local Python/HTTP adapter and schemas',
            'Input/error/origin/size/concurrency handling','Versioned classifier and compatible dependency bindings',
            'Current/historical documentation separation','Future evaluation protocol bindings'],
        'deferred_by_owner':['Formal performance evaluation and independent holdout execution','Display metrics',
            'Interactive terminal testing with owner','Website integration','LLM integration'],
        'external_inputs_for_later':['Independent human-written/human-labeled questions','Required formal acceptance'],
        'separate_project_workstreams':['Legal source coverage/currentness/support approvals','Referral-contact completion',
            'Generated-answer and licensed legal review','Application history/database and release decisions'],
        'all_classifier_implementation_tasks_completed':True,'all_project_issues_closed':False})
    save(PACKET/'dataset_inventory_addendum.json',{'new_question_datasets':0,'new_training_questions':0,
        'new_independent_human_questions':0,'new_legal_authorities':0,
        'existing_routing_cases_used_as_software_controls':11,'new_classifier_test_methods':7,
        'backend_software_checks':30,'performance_metric_report_created':False})
    patch=[]
    for name in ['scope_constraints.py','clause_classifier.py','classifier_runtime.py']:
        patch.extend(difflib.unified_diff((PACKET/('before_'+name)).read_text(encoding='utf-8').splitlines(True),
            (ROOT/'dataset/pipelines/item10'/name).read_text(encoding='utf-8').splitlines(True),
            fromfile='parent/'+name,tofile='dataset/pipelines/item10/'+name))
    (PACKET/'CLASSIFIER_CHANGES.patch').write_text(''.join(patch),encoding='utf-8')
    snapshot=PACKET/'backend_snapshot';snapshot.mkdir()
    for file in (ROOT/'backend/classifier').iterdir():
        if file.is_file():shutil.copyfile(file,snapshot/file.name)
    report=f'''# Classifier preintegration implementation

Completed on **18 October 2026**. Classifier implementation is prepared for the owner's next testing phase. This completes software preparation before website integration; it does not assert final performance or formal acceptance.

## Implemented

- Repaired anaphoric insurance/dispute follow-ups without discarding new unknown concerns.
- Distinguished government-employment complaints from incidental background, including bounded spelling aliases and Taglish wording.
- Added explicit work-duty/rest-schedule context, ordinary product-failure wording and case-outcome/union-scope boundaries with counterfactual controls.
- Preserved low-confidence clarification and inherited thresholds. All eleven previously inspected routing scenarios now take their expected routes in software checks.
- Added a pinned Python classifier service and loopback HTTP adapter: strict request/response schemas, original-text preservation, supported-only retrieval requests, explicit excluded components and referral candidates.
- Added model/runtime/dependency integrity checks, guarded inputs, predictable JSON errors, exact origin allowlists, bounded connections and read timeouts. The adapter emits no legal answers and writes no question access logs.
- Rebound the existing retrieval/verifier packages to the repaired classifier without changing index membership, cached vectors, ranking code, source eligibility, verification policy or real approvals.
- Prepared compatible bindings for the later development evaluator. The new performance run has not been executed.

## Software verification

| Suite | Passing checks |
|---|---:|
| Classifier | {counts['classifier']} |
| Local adapter/API | {counts['api']} |
| Retrieval dependency | {counts['retrieval']} |
| Verifier dependency | {counts['verifier']} |
| Evaluation harness | {counts['evaluation_harness']} |

API checks exercised actual temporary HTTP servers on 127.0.0.1 and shut them down. Sandbox restrictions blocked the first loopback attempt; the full suite passed with local socket permission. One unpublished classifier build was retained after a negative-control assertion incorrectly assumed that absence of a deterministic scope rule must be a consumer rule; the corrected assertion verifies the intended boundary without forcing a label. No failed build was made current.

These are implementation/regression checks. No new accuracy, F1, calibration or combined-confidence report was produced. Existing saved numeric results belong to their historical versions; the current classifier's performance remains to be evaluated.

## Preservation

Atomic weights, fitted feature vocabulary, calibration and thresholds match the parent package. Thresholds remain primary 0.80 / scope 0.85. No retraining or new question/source dataset was introduced. The audit matches {audit['parent_artifact_sha256_count']} parent-artifact bindings, {audit['immutable_data_and_prior_artifacts_sha256_count']} data/prior-artifact bindings and all {audit['ui_sha256_count']} UI files. No UI file was added, removed or changed.

Current implementation packages: classifier v1.5.6, retrieval v1.2.5 and verifier v1.0.3. API operator configuration and complete schemas are under `backend/classifier/`. The previous evaluated stack and its reports remain unchanged.

## Deferred at the owner's request

Interactive terminal testing, performance evaluation, metric presentation and final model acceptance come next. Website and LLM integration follow only after the owner is satisfied with testing/results. The prepared independent intake remains empty; no human authorship or approval has been invented. Legal-source/currentness/support reviews and the other project milestones retain their separate pending status.

The local API is a development adapter; external hosting needs the later agreed service/access/retention design. No persistent server is running as a result of this handoff. Answer generation and deployment remain disabled.

See [backend interface](C:/IA/backend/classifier/README.md), `implementation_status.json`, `current_issue_ledger.json`, `routing_implementation_audit.json`, `api_software_tests.log`, `CLASSIFIER_CHANGES.patch` and `preservation_audit.json`.
'''
    (PACKET/'IMPLEMENTATION_REPORT.md').write_text(report,encoding='utf-8')
    current=read(ROOT/'CURRENT_ARTIFACTS.json')
    previous_evaluation=current['system_evaluation']
    current.update(versions)
    current.update(classifier_backend='backend/classifier/config.json',
        classifier_preintegration='outputs/classifier-preintegration-v1.0.0',
        classifier_implementation_completed=True,classifier_performance_evaluation_pending=True,
        classifier_display_metrics_deferred=True,classifier_owner_terminal_testing_deferred=True,
        historical_system_evaluation=previous_evaluation,system_evaluation_stack_matches_current=False,
        item13_status='current_classifier_implementation_complete_performance_evaluation_deferred',
        item13_all_development_screens_met=None,item13_failed_development_screens=[],
        item13_screening_run_completed_for_current_stack=False,item13_formal_acceptance_completed=False,
        website_integration_completed=False,llm_integration_completed=False,
        all_project_issues_closed=False,answer_generation_allowed=False,current_guidance_allowed=False,deployment_allowed=False)
    audit_preservation()
    save(ROOT/'CURRENT_ARTIFACTS.json',current)
    save(PACKET/'current_artifacts_after.json',current)
    save(PACKET/'run_manifest.json',{'version':'classifier-preintegration-v1.0.0','as_of':'2026-10-18',
        'status':'implementation_complete_evaluation_deferred','classifier':versions['classifier'],
        'retrieval':versions['retrieval'],'verifier':versions['verifier'],
        'backend_config_sha256':sha(ROOT/'backend/classifier/config.json'),
        'runtime_source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'backend/classifier').iterdir() if p.is_file()},
        'future_evaluation_protocol_sha256':sha(ROOT/'dataset/pipelines/item13/protocol.json'),
        'software_test_counts':counts,'answer_generation_allowed':False,'deployment_allowed':False})
    save(PACKET/'artifact_checksums.json',{p.relative_to(PACKET).as_posix():sha(p) for p in sorted(PACKET.rglob('*')) if p.is_file()})
    print(json.dumps({'implementation_complete':True,'software_checks':counts,'preservation_passed':True,
        'formal_evaluation_deferred':True,'website_or_llm_changes':False},indent=2))


if __name__=='__main__':finalize()
