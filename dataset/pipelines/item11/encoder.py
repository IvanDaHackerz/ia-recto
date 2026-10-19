"""Local fixed multilingual encoder with token-bounded windows, never silent truncation."""
from __future__ import annotations
import json,os
import numpy as np
from common import ROOT,sha,readrows
from tokenizers import Tokenizer

MODEL_NAME='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
MAX_TOKENS=128
os.environ.setdefault('HF_HOME',str(ROOT/'models/hf_home'))
os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY','1')
os.environ.setdefault('HF_HUB_DISABLE_XET','1')
os.environ.setdefault('HF_HUB_OFFLINE','1')
_tokenizer=None;_model=None;_vectors={}

def reuse_index_vectors(path):
    from pathlib import Path
    path=Path(path);manifest=json.loads((path/'index_manifest.json').read_text())
    if manifest['semantic_model_manifest_sha256']!=sha(ROOT/'models/embedding_backbone_manifest.json'):raise ValueError('Encoder changed; cannot reuse vectors')
    for name,h in json.loads((path/'index_checksums.json').read_text()).items():
        if sha(path/name)!=h:raise ValueError('Previous index checksum mismatch')
    rows=readrows(path/'semantic_windows.jsonl');z=np.load(path/'semantic_vectors.npz',allow_pickle=False)
    if len(rows)!=len(z['vectors']):raise ValueError('Vector reuse length mismatch')
    _vectors.update((r['text'],v) for r,v in zip(rows,z['vectors']))
    return len(rows)

def tokenizer():
    global _tokenizer
    if _tokenizer is None:
        m=json.loads((ROOT/'models/embedding_backbone_manifest.json').read_text())
        for name,h in m['files_sha256'].items():
            if sha(ROOT/name)!=h:raise ValueError('Local encoder checksum mismatch: '+name)
        path=next(ROOT/name for name in m['files_sha256'] if name.endswith('tokenizer.json'))
        _tokenizer=Tokenizer.from_file(str(path));_tokenizer.no_truncation();_tokenizer.no_padding()
    return _tokenizer

def windows(text,prefix=''):
    tok=tokenizer();p=tok.encode(prefix,add_special_tokens=False)
    prefix=tok.decode(p.ids[:24]) if len(p.ids)>24 else prefix
    prefix=(prefix+'\n') if prefix else ''
    encoding=tok.encode(text,add_special_tokens=False);offsets=encoding.offsets
    if not offsets:return []
    budget=MAX_TOKENS-len(tok.encode(prefix,add_special_tokens=False).ids)-4
    result=[];start=0
    while start<len(offsets):
        end=min(start+budget,len(offsets));a=offsets[start][0];b=offsets[end-1][1]
        while len(tok.encode(prefix+text[a:b]).ids)>MAX_TOKENS:
            end-=1
            if end<=start:raise ValueError('Cannot fit semantic window')
            b=offsets[end-1][1]
        result.append({'char_start':a,'char_end':b,'text':prefix+text[a:b],'token_count':len(tok.encode(prefix+text[a:b]).ids)})
        if end==len(offsets):break
        start=max(start+1,end-20)
    if result[0]['char_start']>len(text)-len(text.lstrip()) or text[result[-1]['char_end']:].strip():raise ValueError('Window coverage failure')
    return result

def encode(texts):
    global _model
    if not texts:return np.zeros((0,384),dtype=np.float32)
    tok=tokenizer()
    if any(len(tok.encode(t).ids)>MAX_TOKENS for t in texts):raise ValueError('Unwindowed overlong encoder input')
    missing=list(dict.fromkeys(t for t in texts if t not in _vectors))
    if missing:
        if _model is None:
            from fastembed import TextEmbedding
            _model=TextEmbedding(MODEL_NAME,cache_dir=str(ROOT/'models/embedding_backbone'),threads=2,providers=['CPUExecutionProvider'],local_files_only=True)
        x=np.array(list(_model.embed(missing,batch_size=32)),dtype=np.float32);x/=np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
        _vectors.update(zip(missing,x))
    return np.array([_vectors[t] for t in texts],dtype=np.float32)
