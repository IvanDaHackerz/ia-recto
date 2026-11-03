"""Sequential immutable build and AI-off checks. No provider requests."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def run(args,name):
    print('Starting '+name,flush=True)
    with (HERE/name).open('w',encoding='utf-8') as stream:
        r=subprocess.run([sys.executable,*args],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError('Check '+name)
    print('Passed '+name,flush=True)
run(['outputs/website-field-repair-v1.0.0/bind_stack.py'],'binding-accepted.log')
run(['outputs/website-field-repair-v1.0.0/evaluate.py'],'evaluation-accepted.log')
run(['-m','backend.evaluate_local_pipeline','run','--cases','outputs/local-pipeline-cases-v1.1.0','--output','outputs/local-pipeline-evaluation-v1.6.6'],'historical-replay-accepted.log')
run(['outputs/website-field-repair-v1.0.0/refresh_metrics.py'],'metrics-binding.log')
