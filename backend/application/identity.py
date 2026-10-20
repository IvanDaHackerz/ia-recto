"""Cheap process/configuration identity; no model load or credential decryption."""
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def identity():
    paths=[ROOT/'CURRENT_ARTIFACTS.json',ROOT/'backend/normalization.py',ROOT/'backend/normalization_provider.py']
    paths+=sorted((ROOT/'backend/application').glob('*.py'))
    digest=hashlib.sha256()
    for p in paths:
        if not p.name.startswith('test_'):digest.update(p.relative_to(ROOT).as_posix().encode());digest.update(p.read_bytes())
    # A server started before key setup (or with AI disabled) must not be reused
    # after configuration changes. Only a digest is exposed; never key contents.
    for name in ['provider.json','together.key.dpapi','openai.key.dpapi']:
        path=ROOT/'.local/normalizer'/name
        digest.update(name.encode())
        digest.update(path.read_bytes() if path.is_file() else b'not-configured')
    for name in ['RECTO_ENABLE_NORMALIZATION','RECTO_ENABLE_EXPLANATIONS','RECTO_NORMALIZER_PROVIDER',
                 'RECTO_NORMALIZER_MODEL','RECTO_EXPLANATION_MODEL','TOGETHER_API_KEY','OPENAI_API_KEY',
                 'RECTO_MAX_DAILY_CALLS','RECTO_MAX_DAILY_USD']:
        digest.update(json.dumps([name,os.environ.get(name)],separators=(',',':')).encode())
    return {'project_id':'recto-local-ia','application_version':'2.0.0','runtime_signature':digest.hexdigest()}

if __name__=='__main__':print(json.dumps(identity()))
