"""Consequential leakage, probability, persistence and routing tests for the saved experiment."""
from __future__ import annotations
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ.setdefault(k,'1')
import argparse,collections,json,sys,unittest
from pathlib import Path
import numpy as np
import joblib
from sklearn.base import clone
from classifier_runtime import predict_records,route,missing_context,strip_training_wrappers
from train_classifier import sources,evaluate,gates,readrows
RUN=None

class ClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle=joblib.load(RUN/'classifier.joblib');cls.parts,cls.general,cls.typing,cls.audit=sources()
        cls.policy=json.loads((RUN/'policy_snapshot.json').read_text())

    def test_source_versions_and_checksums_are_unchanged(self):
        self.assertEqual(self.audit['status'],'passed');self.assertEqual(self.audit['leakage_groups_crossing_partitions'],0)

    def test_fitting_membership_excludes_all_evaluation_rows(self):
        train=set(self.bundle['train_question_ids']);self.assertEqual(train,{r['question_id'] for r in self.parts['train']})
        self.assertFalse(train&{r['question_id'] for r in self.parts['validation']+self.parts['test']+self.general+self.typing})

    def test_calibration_groups_are_disjoint_and_cover_training_once(self):
        folds=json.loads((RUN/'calibration_folds.json').read_text());seen=set();expected=set(self.bundle['train_group_ids'])
        for f in folds:
            fit=set(f['fit_group_ids']);cal=set(f['calibration_group_ids']);self.assertFalse(fit&cal);self.assertFalse(seen&cal);self.assertEqual(fit|cal,expected);seen|=cal
        self.assertEqual(seen,expected);self.assertEqual(sum(f['calibration_rows'] for f in folds),459)

    def test_vectorizers_and_idf_equal_training_only_fit(self):
        texts=[r['question_text'] for r in self.parts['train']]
        for model in self.bundle['primary_model'].components.values():
            estimator=model.calibrated_classifiers_[0].estimator
            features=estimator.named_steps['features']
            vectors=[v for _,v in features.transformer_list] if hasattr(features,'transformer_list') else [features]
            for vectorizer in vectors:
                ref=clone(vectorizer).fit(texts);self.assertEqual(vectorizer.vocabulary_,ref.vocabulary_);np.testing.assert_allclose(vectorizer.idf_,ref.idf_,atol=1e-12)

    def test_serialized_model_replays_recorded_predictions(self):
        expected=readrows(RUN/'validation_predictions.jsonl');actual=predict_records(self.bundle,self.parts['validation'])
        for a,b in zip(actual,expected):
            for head in ('primary','scope'):
                self.assertEqual(a['predicted_'+head],b['predicted_'+head]);np.testing.assert_allclose(list(a[head+'_probabilities'].values()),list(b[head+'_probabilities'].values()),atol=1e-12)
            self.assertEqual(a['routing_action'],b['routing_action'])

    def test_training_reproduces_one_calibrated_component(self):
        model=self.bundle['primary_model'].components['excluded'];new=clone(model)
        texts=[r['question_text'] for r in self.parts['train']];y=['present' if r['excluded_topic_ids'] else 'absent' for r in self.parts['train']]
        new.fit(texts,y);val=[r['question_text'] for r in self.parts['validation']]
        np.testing.assert_allclose(new.predict_proba(val),model.predict_proba(val),atol=1e-10)

    def test_probabilities_finite_bounded_and_normalized(self):
        predictions=predict_records(self.bundle,self.general+self.typing)
        for r in predictions:
            for head in ('primary','scope'):
                p=np.array(list(r[head+'_probabilities'].values()));self.assertTrue(np.isfinite(p).all());self.assertTrue(((p>=0)&(p<=1)).all());self.assertAlmostEqual(float(p.sum()),1,places=10)

    def test_label_metadata_cannot_change_input_predictions(self):
        text=self.general[0]['question_text'];a=predict_records(self.bundle,[{'question_text':text,'primary_label':'labor'}])[0];b=predict_records(self.bundle,[{'question_text':text,'primary_label':'out_of_scope','scope_label':'unsupported','reviewer':'fake'}])[0]
        self.assertEqual(a['primary_probabilities'],b['primary_probabilities']);self.assertEqual(a['scope_probabilities'],b['scope_probabilities'])

    def test_missing_context_beats_high_confidence(self):
        cases=[('My employer has not paid my salary.','employment_category_missing'),('They refuse to refund my payment.','refund_transaction_missing'),('They ended my contract.','contract_relationship_missing'),('They charged me too much.','charge_context_missing')]
        for text,reason in cases:
            r=route(text,'labor','fully_supported',.999,.999,{'primary':.3,'scope':.4});self.assertEqual(r['routing_action'],'clarify');self.assertEqual(r['reason'],reason);self.assertFalse(r['substantive_answer_admitted'])

    def test_context_controls_do_not_trigger_missing_fact_guard(self):
        for text in ['My private company has not paid my salary.','The appliance store refuses to refund my blender purchase.','My private employment contract ended.','My bank charged a credit-card fee.']:
            self.assertIsNone(missing_context(text))

    def test_inconsistent_pair_blocks_answer(self):
        r=route('A bank credit-card fee.','out_of_scope','fully_supported',.99,.99,{'primary':.3,'scope':.4});self.assertEqual(r['reason'],'inconsistent_primary_scope');self.assertFalse(r['substantive_answer_admitted'])

    def test_low_confidence_blocks_answer(self):
        r=route('The appliance store sold me a broken blender.','consumer','fully_supported',.2,.9,{'primary':.3,'scope':.4});self.assertEqual(r['reason'],'low_confidence');self.assertFalse(r['substantive_answer_admitted'])

    def test_unresolved_mixed_components_block_partial_answer(self):
        r=route('My private employer owes overtime and a bank denied my credit claim.','mixed','partially_supported',.99,.99,{'primary':.3,'scope':.4});self.assertEqual(r['reason'],'mixed_components_not_resolved');self.assertFalse(r['substantive_answer_admitted'])

    def test_excluded_route_does_not_invent_advice_or_referrals(self):
        r=route('A bank credit-card dispute.','out_of_scope','unsupported',.99,.99,{'primary':.3,'scope':.4});self.assertEqual(r['routing_action'],'refer_out_of_scope');self.assertFalse(r['substantive_answer_admitted']);self.assertEqual(r['referral_ids'],[]);self.assertNotIn('answer',r)

    def test_supported_route_still_requires_evidence(self):
        r=route('The store sold me a broken blender.','consumer','fully_supported',.99,.99,{'primary':.3,'scope':.4});self.assertEqual(r['routing_action'],'retrieve_supported_evidence');self.assertEqual(r['reason'],'supported_candidate_requires_evidence');self.assertNotIn('answer',r)

    def test_abstaining_on_everything_cannot_pass_coverage(self):
        rows=self.parts['validation'];preds=[]
        for r in rows:
            p={'question_text':r['question_text'],'predicted_primary':r['primary_label'],'predicted_scope':r['scope_label'],'primary_confidence':1.,'scope_confidence':1.,'primary_probabilities':{c:float(c==r['primary_label']) for c in self.policy['primary_labels']},'scope_probabilities':{c:float(c==r['scope_label']) for c in self.policy['scope_labels']}}
            p.update(route(r['question_text'],r['primary_label'],r['scope_label'],1.,1.,{'primary':1.01,'scope':1.01}));preds.append(p)
        metrics=evaluate(rows,preds);self.assertEqual(metrics['primary']['accuracy'],1.);self.assertEqual(metrics['routing']['decisive_coverage'],0.)
        self.assertFalse(next(g for g in gates(metrics,self.policy) if g['name']=='decisive_coverage')['passed'])

    def test_normalization_preserves_deciding_facts(self):
        self.assertEqual(strip_training_wrappers('Can this service advise me if I work overseas?'),'i work overseas?')
        self.assertIn('private',strip_training_wrappers('What are my rights if my private employer has not paid wages?'))
        self.assertIn('not',strip_training_wrappers('What should I do if my employer does not pay overtime?'))

    def test_synthetic_test_is_still_unopened(self):
        m=json.loads((RUN/'run_manifest.json').read_text());self.assertFalse(m['synthetic_test_opened']);self.assertFalse((RUN/'synthetic_test_predictions.jsonl').exists());self.assertFalse((RUN/'synthetic_test_metrics.json').exists())

def main():
    global RUN
    p=argparse.ArgumentParser();p.add_argument('--run-dir',required=True,type=Path);a=p.parse_args();RUN=a.run_dir.resolve()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ClassifierTests);result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'status':'passed' if result.wasSuccessful() else 'failed','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'checks':[name for name in dir(ClassifierTests) if name.startswith('test_')],'scope':'Software correctness, leakage, calibration fitting, replay and routing guards; passing software tests does not mean model accuracy targets passed.'}
    (RUN/'software_tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)

if __name__=='__main__':main()
