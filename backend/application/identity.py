"""Cheap process identity for safe local launcher reuse; no credentials/model load."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def identity():
    paths=[ROOT/'CURRENT_ARTIFACTS.json',ROOT/'backend/normalization.py',ROOT/'backend/normalization_provider.py']
    paths+=sorted((ROOT/'backend/application').glob('*.py'))
    digest=hashlib.sha256()
    for p in paths:
        if not p.name.startswith('test_'):digest.update(p.relative_to(ROOT).as_posix().encode());digest.update(p.read_bytes())
    return {'project_id':'recto-local-ia','application_version':'2.0.0','runtime_signature':digest.hexdigest()}

if __name__=='__main__':print(json.dumps(identity()))
