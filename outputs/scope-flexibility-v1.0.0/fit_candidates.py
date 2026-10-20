"""Recalibrate on original training folds; diagnostic questions never fitted."""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ.setdefault(k,'1')
import json, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'dataset/pipelines/item10'))
import joblib, numpy as np
from sklearn.base import clone
from train_classifier import sources,evaluate
from clause_classifier import state_of
from logical_clause_model import LogicalClauseEngine,LogicalClauseHead
from classifier_runtime import predict_records

def main():
 old=joblib.load(ROOT/'outputs/item10-classifier-v1.5.16/classifier.joblib')
 parts,_,_,_=sources();train=parts['train'];texts=np.array([r['question_text'] for r in train]);y=np.array([state_of(r) for r in train])
 reports=[]
 for kind in ['lexical','hybrid']:
  start=time.perf_counter();b=joblib.load(ROOT/'outputs/item10-classifier-v1.5.16/classifier.joblib')
  model=clone(b['primary_model'].engine.joint_model)
  model.set_params(estimator__feature_kind=kind,estimator__semantic_weight=2. if kind=='hybrid' else 1.)
  model.fit(texts,y)
  e=LogicalClauseEngine(model,model.calibrated_classifiers_[0].estimator.atomic)
  b.update(primary_model=LogicalClauseHead('primary',e),scope_model=LogicalClauseHead('scope',e),model_version='scope-candidate-'+kind)
  b['config'].update(feature_kind=kind,semantic_weight=2. if kind=='hybrid' else 1.)
  target=HERE/'candidates'/kind;target.mkdir(parents=True,exist_ok=False);joblib.dump(b,target/'classifier.joblib')
  metrics=evaluate(parts['validation'],predict_records(b,parts['validation']))
  report={'kind':kind,'training_parent_count':len(train),'new_diagnostic_rows_fitted':0,'thresholds':b['thresholds'],
   'validation_primary_accuracy':metrics['primary']['accuracy'],'validation_scope_accuracy':metrics['scope']['accuracy'],
   'validation_primary_macro_f1':metrics['primary']['macro_f1'],'elapsed_seconds':time.perf_counter()-start}
  reports.append(report);print(json.dumps(report),flush=True)
 (HERE/'candidate_fit.json').write_text(json.dumps(reports,indent=2)+'\n')
if __name__=='__main__':main()
