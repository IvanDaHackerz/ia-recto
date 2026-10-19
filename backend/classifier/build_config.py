"""Pin an operator-chosen project classifier before starting the local adapter."""
from __future__ import annotations
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys
from .service import ROOT, RUNTIME_FILES, inside, sha


def build(classifier, output):
    directory=inside(ROOT,classifier)
    checks=json.loads((directory/'artifact_checksums.json').read_text(encoding='utf-8'))
    for name,expected in checks.items():
        if sha(inside(directory,name))!=expected:raise ValueError('Classifier artifact changed: '+name)
    for name in RUNTIME_FILES:
        if sha(ROOT/'dataset/pipelines/item10'/name)!=checks[name]:raise ValueError('Runtime differs from classifier snapshot: '+name)
    selection=json.loads((directory/'selection_frozen.json').read_text(encoding='utf-8'))
    source_paths=['dataset/processed/item10/reviewed_v1.0.0/referral_directory.csv',
        'backend/__init__.py','backend/classifier/__init__.py','backend/classifier/contracts.py',
        'backend/classifier/service.py','backend/classifier/server.py']
    config={'schema_version':'1.0','role':'offline_development_classifier','classifier':directory.relative_to(ROOT).as_posix(),
        'model_version':directory.name,'artifact_checksums_sha256':sha(directory/'artifact_checksums.json'),
        'thresholds':selection['thresholds'],'python_major_minor':f'{sys.version_info.major}.{sys.version_info.minor}',
        'dependencies':{name:importlib.metadata.version(name) for name in ['numpy','scikit-learn','scipy','joblib','fastembed']},
        'source_sha256':{name:sha(ROOT/name) for name in source_paths},
        'formal_evaluation_completed':False,'website_integration_completed':False,
        'answer_generation_allowed':False,'deployment_allowed':False}
    with Path(output).open('x',encoding='utf-8') as stream:json.dump(config,stream,ensure_ascii=False,indent=2);stream.write('\n')
    return config


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classifier',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(build(args.classifier,args.output),indent=2))
