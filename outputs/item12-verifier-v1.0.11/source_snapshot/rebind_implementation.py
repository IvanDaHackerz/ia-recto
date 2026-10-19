"""Rebind classifier dependencies with software checks; defer final evaluation."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
from unittest.mock import patch

from build_packet import save,suite
from verification import EvidenceVerifier,HERE,ROOT,sha


def build(output):
    if output.exists():raise ValueError('Use a new version directory')
    runtime=EvidenceVerifier(as_of='2026-10-19')
    output.mkdir(parents=True)
    parents={}
    for key in ['classifier','retrieval','parent_verifier']:
        for path in (ROOT/runtime.policy[key]).rglob('*'):
            if path.is_file():parents[path.relative_to(ROOT).as_posix()]=sha(path)
    sources={**runtime.source['source_sha256'],**runtime.source['raw_source_sha256']}
    from test_verifier import VerifierTests
    import test_logical_classifier,test_retrieval
    test_logical_classifier.RUN=ROOT/runtime.policy['classifier']
    test_retrieval.INDEX=ROOT/runtime.policy['retrieval']
    tests={'verifier':suite(VerifierTests,output,'verifier_tests')}
    with patch.object(test_logical_classifier,'save',side_effect=lambda path,value:save(output/('parent_'+Path(path).name),value)):
        tests['classifier']=suite(test_logical_classifier.LogicalTests,output,'classifier_tests')
    with patch.dict(os.environ,{'PYTHONUTF8':'1'}):
        tests['retrieval']=suite(test_retrieval.RetrievalTests,output,'retrieval_tests')
    save(output/'software_tests.json',tests)
    changed=[name for name,expected in {**parents,**sources}.items() if sha(ROOT/name)!=expected]
    save(output/'preservation_audit.json',{'passed':not changed,'changed_files':changed,
        'parent_artifact_sha256':parents,'source_sha256':sources})
    if changed or not all(t['passed'] for t in tests.values()):raise ValueError('Dependency software checks failed; inspect logs')
    snapshot=output/'source_snapshot';snapshot.mkdir()
    for path in HERE.iterdir():
        if path.is_file() and path.suffix in {'.py','.json','.md'}:shutil.copyfile(path,snapshot/path.name)
    runtime_hashes={p.name:sha(p) for p in HERE.iterdir() if p.is_file() and p.suffix in {'.py','.json','.md'}}
    save(output/'run_manifest.json',{'version':runtime.policy['version'],'as_of':'2026-10-19',
        'status':'dependency_rebind_software_checked_evaluation_deferred','classifier':runtime.policy['classifier'],
        'retrieval':runtime.policy['retrieval'],'parent_verifier':runtime.policy['parent_verifier'],
        'runtime_source_sha256':runtime_hashes,'software_tests':tests,'policy_behavior_changed':False,
        'formal_evaluation_completed':False,'answer_generation_allowed':False,'deployment_allowed':False})
    save(output/'VERIFIER_CARD.json',{'version':runtime.policy['version'],
        'role':'Dependency rebind for classifier preintegration implementation',
        'current_guidance_real_reviews':0,'new_legal_sources':0,'source_currentness_refreshed':False,
        'automated_paraphrase_entailment_model':False,'formal_evaluation_completed':False,
        'answer_generation_allowed':False,'display_allowed':False,'deployment_allowed':False})
    (output/'VERIFICATION_REPORT.md').write_text(
        '# Verifier dependency rebind\n\n' + runtime.policy['classifier'] + ' and ' + runtime.policy['retrieval'] + ' are pinned together. '
        'Verification behavior, source eligibility and trusted reviews are unchanged. '
        'Software regression checks pass; final system/generated-answer evaluation is deferred at the owner’s request. '
        'The prior v1.0.2 evaluation packet is preserved. No LLM, UI, legal approval or currentness refresh is added.\n',encoding='utf-8')
    save(output/'artifact_checksums.json',{p.relative_to(output).as_posix():sha(p) for p in sorted(output.rglob('*')) if p.is_file()})
    print(__import__('json').dumps({'version':runtime.policy['version'],'software_tests':tests,'evaluation_deferred':True},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    build(parser.parse_args().output.resolve())
