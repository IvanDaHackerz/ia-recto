"""Create and verify an explicit source/runtime checkpoint without private state."""
import argparse,hashlib,json,zipfile,re,subprocess
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
EXCLUDED={'node_modules','__pycache__','.git','.local','.venv-item10','vendor','.agents','.codex','dist'}
def allowed(path):
    relative=path.relative_to(ROOT)
    return (not (set(relative.parts)&EXCLUDED)
        and not any(part.startswith('.venv') for part in relative.parts)
        and not path.name.startswith('.env')
        and path.suffix.lower() not in {'.pyc','.dpapi','.sqlite3','.env','.zip','.key','.pem','.p12','.pfx'}
        and '.sqlite3' not in path.name
        and (path.suffix.lower()!='.log' or relative.parts[0]=='outputs'))
def collect_paths(include_model=False):
    current=json.loads((ROOT/'CURRENT_ARTIFACTS.json').read_text(encoding='utf-8'))
    trees=['backend','scripts','docs','dataset/pipelines','dataset/data_contract','dataset/canonical_sources',
        'dataset/processed','UI/UX/app/src','UI/UX/app/public','UI/UX/app/scripts','UI/UX/app/.impeccable']
    # Only canonical/processed legal and development data, not the bulk discovery
    # corpus or original returned reviewer workbooks with personal identifiers.
    versions={current[k] for k in ['classifier','retrieval','verifier','local_pipeline_evaluation']}
    versions.update(['outputs/normalization-evaluation-v2.0.0','outputs/local-pipeline-cases-v1.1.0','outputs/item10-human-gold-intake-v1.0.0'])
    for key,value in current.items():
        if 'diagnostic' not in key and isinstance(value,str) and value.startswith('outputs/') and (ROOT/value).is_dir():versions.add(value)
    trees.extend(sorted(versions))
    paths=set()
    for name in trees:
        directory=ROOT/name
        if directory.is_dir():paths.update(p for p in directory.rglob('*') if p.is_file() and allowed(p))
    for directory in [ROOT,ROOT/'UI/UX',ROOT/'UI/UX/app',ROOT/'dataset',ROOT/'models']:
        paths.update(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in {'.md','.json','.csv','.ps1','.ts','.js','.html','.txt'} and allowed(p))
        if (directory/'.gitignore').exists():paths.add(directory/'.gitignore')
    paths.update(p for p in (ROOT/'.github').rglob('*') if p.is_file() and allowed(p))
    paths.add(ROOT/'.gitattributes')
    if include_model:
        manifest=json.loads((ROOT/'models/embedding_backbone_manifest.json').read_text(encoding='utf-8'))
        paths.update(ROOT/p for p in manifest['files_sha256'])
        # FastEmbed's content-addressed blobs/refs accompany its pinned snapshot;
        # they contain public model data, never HF credentials or global cache.
        paths.update(p for p in (ROOT/'models/embedding_backbone').rglob('*') if p.is_file() and '.locks' not in p.parts)
    # Include and scan integrity dependencies, including older manifests.
    from backend.terminal_test import load_runtime
    verifier=load_runtime()
    paths.update(p for p in verifier.integrity_files if allowed(p))
    paths={p for p in paths if allowed(p)}
    credential_pattern=re.compile(rb'\b(?:tgp_v1_[A-Za-z0-9_-]{30,}|sk-proj-[A-Za-z0-9_-]{20,})\b')
    for p in paths:
        if p.suffix.lower() in {'.py','.json','.jsonl','.md','.ts','.tsx','.js','.txt','.ps1','.log'} and credential_pattern.search(p.read_bytes()):
            raise ValueError('Credential-like literal found in checkpoint input: '+p.relative_to(ROOT).as_posix())
    return paths
def github_list(output):
    """Check an explicit upload list; never stage, commit, or contact GitHub."""
    paths=sorted(collect_paths())
    nested=set()
    for path in paths:
        for parent in path.parents:
            if parent==ROOT:break
            if (parent/'.git').exists():nested.add(parent.relative_to(ROOT).as_posix())
    if nested:
        raise ValueError('Nested Git repositories would prevent a complete project upload: '
            +', '.join(sorted(nested))+'. Preserve their Git metadata outside the source tree before staging.')
    names=[p.relative_to(ROOT).as_posix() for p in paths]
    oversized=[name for p,name in zip(paths,names) if p.stat().st_size>100*1024*1024]
    if oversized:raise ValueError('Files exceed GitHub regular-Git limit: '+', '.join(oversized))
    ignored=subprocess.run(['git','check-ignore','--stdin'],input='\n'.join(names)+'\n',
        cwd=ROOT,text=True,capture_output=True,check=False)
    if ignored.returncode not in {0,1}:raise ValueError('Could not verify Git ignore rules')
    if ignored.stdout.strip():raise ValueError('Required upload files are ignored:\n'+ignored.stdout)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text('\n'.join(names)+'\n',encoding='utf-8',newline='\n')
    meta={'files':{name:sha(p) for p,name in zip(paths,names)},
        'total_bytes':sum(p.stat().st_size for p in paths),
        'largest_file_bytes':max(p.stat().st_size for p in paths),
        'created_at_utc':datetime.now(timezone.utc).isoformat(),
        'private_state_included':False,'bulk_discovery_included':False,
        'public_encoder_download_required':True,
        'credential_check':'Known provider-key literals checked; review staged files before pushing.'}
    output.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'upload_list':str(output),'files':len(paths),
        'total_mib':round(meta['total_bytes']/1024**2,2),
        'largest_file_mib':round(meta['largest_file_bytes']/1024**2,2),
        'git_index_changed':False,'uploaded':False}))
def github_check(output):
    """Verify every selected file is present in Git with its exact current bytes."""
    manifest=json.loads(output.with_suffix('.json').read_text(encoding='utf-8'))
    result=subprocess.run(['git','ls-files','--stage','-z'],cwd=ROOT,capture_output=True,check=True)
    entries={}
    for row in result.stdout.decode('utf-8').split('\0'):
        if row:
            metadata,name=row.split('\t',1)
            mode,oid,stage=metadata.split()
            if stage=='0':entries[name]=(mode,oid)
    algorithm=subprocess.run(['git','rev-parse','--show-object-format'],cwd=ROOT,
        capture_output=True,text=True,check=True).stdout.strip()
    failures=[]
    for name,expected in manifest['files'].items():
        data=(ROOT/name).read_bytes()
        blob=hashlib.new(algorithm,b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if hashlib.sha256(data).hexdigest()!=expected:
            failures.append('Changed since list generation: '+name)
        elif name not in entries:
            failures.append('Missing from Git index: '+name)
        elif entries[name][0] not in {'100644','100755'} or entries[name][1]!=blob:
            failures.append('Git bytes differ from selected file: '+name)
    if failures:raise ValueError('\n'.join(failures))
    print(json.dumps({'git_files_byte_verified':len(manifest['files']),
        'ui_app_files':sum(name.startswith('UI/UX/app/') for name in manifest['files']),
        'git_index_changed':False,'uploaded':False}))
def create(output,include_model=False):
    if output.exists():raise ValueError('Checkpoint already exists; choose a new path')
    paths=collect_paths(include_model)
    output.parent.mkdir(parents=True,exist_ok=True)
    manifest={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
    meta={'created_at_utc':datetime.now(timezone.utc).isoformat(),'files':manifest,'includes_public_model':include_model,
        'private_state_included':False,'bulk_discovery_included':False,'fresh_dependency_install_tested':False,
        'note':'Recoverable local checkpoint, not a public deployment or legal approval. Original bulk discovery and historical outputs remain in the workspace.'}
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as archive:
        for p in sorted(paths):archive.write(p,p.relative_to(ROOT).as_posix())
        archive.writestr('RELEASE_MANIFEST.json',json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    output.with_suffix('.sha256').write_text(sha(output)+'  '+output.name+'\n',encoding='utf-8')
    verify(output)
def verify(output):
    with zipfile.ZipFile(output) as archive:
        manifest=json.loads(archive.read('RELEASE_MANIFEST.json'))
        for name,expected in manifest['files'].items():
            p=Path(name)
            if p.is_absolute() or '..' in p.parts or set(p.parts)&{'.local','.git','node_modules'}:raise ValueError('Unsafe checkpoint path')
            if hashlib.sha256(archive.read(name)).hexdigest()!=expected:raise ValueError('Checkpoint integrity failure: '+name)
    print(json.dumps({'archive':str(output),'files_verified':len(manifest['files']),'bytes':output.stat().st_size,'private_state_included':False}))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['create','verify','github-list','github-check']);parser.add_argument('path',type=Path);parser.add_argument('--include-model',action='store_true');args=parser.parse_args()
    if args.action=='create':create(args.path.resolve(),args.include_model)
    elif args.action=='github-list':github_list(args.path.resolve())
    elif args.action=='github-check':github_check(args.path.resolve())
    else:verify(args.path.resolve())
