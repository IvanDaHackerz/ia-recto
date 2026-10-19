"""Fixed local multilingual embeddings. No project text is sent to an API."""
from __future__ import annotations
import json,hashlib,os
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
MODEL_NAME='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
CACHE=ROOT/'models/embedding_backbone'
os.environ.setdefault('HF_HOME',str(ROOT/'models/hf_home'))
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY','1')
os.environ.setdefault('HF_HUB_DISABLE_XET','1')
_model=None
_vectors={}

def encoder(allow_download=False):
    global _model
    if _model is None:
        from fastembed import TextEmbedding
        _model=TextEmbedding(model_name=MODEL_NAME,cache_dir=str(CACHE),threads=2,providers=['CPUExecutionProvider'],local_files_only=not allow_download)
    return _model

def encode(texts):
    missing=list(dict.fromkeys(t for t in texts if t not in _vectors))
    if missing:
        model=encoder()
        embeddings=np.array(list(model.embed(missing,batch_size=32)),dtype=np.float32)
        embeddings/=np.maximum(np.linalg.norm(embeddings,axis=1,keepdims=True),1e-12)
        _vectors.update(zip(missing,embeddings))
    return np.array([_vectors[t] for t in texts],dtype=np.float32)

def preload(path):
    path=Path(path)
    if path.exists():
        z=np.load(path,allow_pickle=False)
        _vectors.update(zip(z['texts'].tolist(),z['vectors']))

def save_cache(path):
    np.savez_compressed(path,texts=np.array(list(_vectors)),vectors=np.array(list(_vectors.values()),dtype=np.float32))

def prepare():
    CACHE.mkdir(parents=True,exist_ok=True)
    model=encoder(allow_download=True)
    registry=next(r for r in model.list_supported_models() if r['model']==MODEL_NAME)
    probe=encode(['Unpaid salary at a private employer.','Hindi pa bayad ang sahod ko sa private employer.'])
    files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in CACHE.rglob('*') if p.is_file() and p.suffix in ('.onnx','.json','.txt','.model')}
    report={'model':MODEL_NAME,'registry':registry,'files_sha256':files,'dimension':int(probe.shape[1]),'normalized':True,'fit_or_fine_tune_performed':False,'execution':'local CPU only','project_text_transmitted':False}
    (ROOT/'models/embedding_backbone_manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'model':MODEL_NAME,'dimension':int(probe.shape[1]),'files':len(files),'execution':'local CPU'},indent=2),flush=True)

if __name__=='__main__':prepare()
