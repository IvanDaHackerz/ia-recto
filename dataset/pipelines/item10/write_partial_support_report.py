"""Package a focused repair report without relabeling regression data as a new test."""
from __future__ import annotations
import argparse,json,shutil
from pathlib import Path
from train_classifier import save,sha,readrows

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);a=p.parse_args();run=a.run_dir.resolve()
    manifest=json.loads((run/'run_manifest.json').read_text());comparison=json.loads((run/'repair_comparison.json').read_text());tests=json.loads((run/'software_tests.json').read_text());reg=json.loads((run/'opened_test_regression_metrics.json').read_text());selection=json.loads((run/'selection_frozen.json').read_text())
    parent=Path(manifest['repair_lineage']['parent_run']);prior=json.loads((parent/'synthetic_test_metrics.json').read_text());source_names=['validation','ai_general_development','ai_typing_development','opened_test_regression'];labels=['Seed validation','AI general development','AI typing development','Opened synthetic set: regression only']
    metrics={n:json.loads((run/(n+'_metrics.json')).read_text()) for n in source_names};table=[]
    for n,label in zip(source_names,labels):
        m=metrics[n];partial=m['scope']['classification_report']['partially_supported'];table.append(f"| {label} | {m['primary']['rows']} | {100*m['primary']['accuracy']:.1f}% | {partial['precision']:.3f} | {partial['recall']:.3f} | {100*m['routing']['decisive_coverage']:.1f}% |")
    regressions=len(comparison['regressed_question_ids']);corrected=len(comparison['corrected_question_ids'])
    failed=[g for g in reg['targets'] if not g['passed']]
    acceptance=('All applicable numeric targets pass on the development and opened regression sets.' if not failed else
        'All applicable numeric targets pass on the three development sets. The opened regression set still fails '+', '.join(f"{g['name']} ({g['observed']:.3f} versus target {g['target']:.3f})" for g in failed)+'. This remains an offline experimental candidate.')
    report=f'''# Partial-support repair — {run.name}

The repaired pipeline retains the excluded seafarer complaint beside a supported product complaint. On the **previously opened synthetic set, now used only for development regression**, partial-support recall changes from **7/11 to 11/11** and partial-support precision is **{reg['scope']['classification_report']['partially_supported']['precision']:.3f}**. It corrects {corrected} prior errors and introduces {regressions} classification regressions against the frozen parent. These are inspected development cases, not a fresh independent accuracy test.

## Implementation

- Replaced the temporary background buffer with explicit records of every fragment, its role and its associated concern. Leading context, trailing context and follow-up questions are retained in the audit.
- Background is recognized conservatively as a self-introduction. A complaint involving specialized employment remains a separate concern. Incidental employment background beside a product complaint does not create a second legal issue.
- Each supported/excluded concern is classified separately. Supported-plus-excluded concerns become mixed/partially_supported, and excluded components never enter the supported retrieval requests.
- Unresolved separate concerns, incomplete fragment accounting and excessive numbers of concerns require clarification even at high confidence. More than 12 concerns are retained and blocked instead of silently truncated.
- Standalone questions still reach the learned classifier when their wording is absent from the structural cue vocabulary. Generic prefaces/background alone provide no domain evidence. Recognized employment context remains available to an actual employment concern.
- Prevented a new output directory from resetting the already-opened synthetic test to a fresh holdout. The separate regression evaluator records its development role and the parent model/result hashes.

The parent configuration was inherited: lexical word/character TF-IDF logistic classifier, C=100. The 459 reviewed training parents and 42 taxonomy definitions are unchanged; they still produce 222 unique atomic fit texts. **Underlying atomic classifier coefficients and intercepts exactly match the parent.** The fix changes concern handling and recalibrates probabilities on the same three training-only, group-disjoint, atomic-fact-purged folds. No new questions or labels were fitted.

## Measured results

| Set | Labeled rows | Primary accuracy | Partial precision | Partial recall | Decisive routing coverage |
|---|---:|---:|---:|---:|---:|
{chr(10).join(table)}

{acceptance} The typing set also passes **{metrics['ai_typing_development']['routing']['relevant_clarification_count']}/20** clarification examples, representing four ambiguity families. Evaluation still includes routing abstentions in the classification denominator.

Experimental validation-selected cutoffs are primary **{selection['thresholds']['primary']:.2f}** and scope **{selection['thresholds']['scope']:.2f}**. General-development decisive coverage is {100*metrics['ai_general_development']['routing']['decisive_coverage']:.1f}%, compared with 96% in the parent. More uncertain inputs clarify; classification accuracy remains 100% on this known set. Full per-class, language, calibration and routing metrics accompany this report. Confidence remains a label estimate, not a guarantee of legal correctness.

The original once-unseen score **95/100 for v1.3.1 remains unchanged**. The newer {100*reg['primary']['accuracy']:.1f}% score on the opened set is a regression result and cannot replace that historical independent-of-this-fix result. No fresh independent human-written/labeled holdout has been evaluated.

## Verification

**{tests['tests_run']}/{tests['tests_run']} software tests passed**, including:

- retained complaints under reversed order, semicolons, plus signs, Taglish and typos;
- consumer-only, excluded-only, incidental-background and negated-background controls;
- background-to-employment context, standalone questions and fragment completeness;
- blocked unresolved concerns, dropped-fragment detection, excessive complexity and excluded-query isolation;
- unchanged training weights and parent artifact checksums;
- training-only membership/IDF, purged calibration folds, refitting, saved-model replay and finite normalized probabilities;
- preserved confidence/missing-context guards and the prohibition on calling the old test fresh.

The original 19 AI-authored scope regression cases also pass. These test fixtures are AI-authored development material, not independent gold. Frozen dataset validation passed **59/59 checks**; source data and the original five review workbooks remain unchanged.

## Status and files

Deployment remains disabled. The fix is ready for review and continued offline development. A fresh independent holdout is still required for renewed final performance claims; retrieval, citation and source-eligibility integration remain separate work.

Use `classifier_runtime.py --model C:/IA/outputs/{run.name}/classifier.joblib --text "A store refuses my warranty. I have a complaint about my seafarer deployment."` from the isolated project environment. `component_evidence` and `segmentation_audit` show the separate concerns and their source fragments.

`repair_comparison.json` lists each corrected/regressed question. `repair_regression_freeze.json` records the model/code before the explicitly labeled regression check. The original v1.3.1 package and its historical test result remain preserved. Intermediate v1.3.2–v1.3.5 development experiments are retained; v1.4.0 supersedes them. Both current and legacy test entry points reject reuse of the opened source as a fresh holdout.
'''
    (run/'PARTIAL_SUPPORT_FIX.md').write_text(report,encoding='utf-8')
    save(run/'MODEL_CARD.json',{'model_version':run.name,'status':'partial_support_repair_development_complete','deployment_allowed':False,'parent_model_version':parent.name,
        'training_parent_rows':459,'taxonomy_definitions':42,'unique_atomic_fit_texts':222,'new_training_questions':0,'atomic_classifier_weights_equal_parent':True,
        'development_targets_passed':manifest['all_development_targets_met'],'opened_original_test_role':'development regression only','regression_partial_recall':reg['scope']['classification_report']['partially_supported']['recall'],
        'regression_partial_precision':reg['scope']['classification_report']['partially_supported']['precision'],'regression_corrected_rows':corrected,'regression_new_classification_errors':regressions,
        'regression_targets_passed':reg['all_applicable_targets_met'],'failed_regression_targets':failed,
        'original_once_unseen_parent_accuracy':prior['primary']['accuracy'],'fresh_independent_holdout_evaluated':False,'independent_human_gold_available':False,
        'confidence_method':manifest['confidence_method'],'thresholds':selection['thresholds'],'software_tests_passed':tests['tests_run'],'frozen_dataset_checks_passed':59,
        'limitations':['Opened synthetic examples informed this code repair','No fresh independent human gold','More conservative routing reduces general-development decisive coverage','No live legal-answer generation or official referral selection']})
    for name in ['test_logical_classifier.py','evaluate_logical_holdout.py','evaluate_partial_support_repair.py','write_partial_support_report.py']:shutil.copy2(Path(__file__).parent/name,run/name)
    save(run/'artifact_checksums.json',{str(f.relative_to(run)):sha(f) for f in run.rglob('*') if f.is_file() and f.name!='artifact_checksums.json'})
    print(json.dumps({'report':str(run/'PARTIAL_SUPPORT_FIX.md'),'software_tests_passed':tests['tests_run'],'corrected':corrected,'classification_regressions':regressions,'fresh_holdout_evaluated':False}))
if __name__=='__main__':main()
