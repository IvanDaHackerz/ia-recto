"""Report measured improvement, including the failed one-shot holdout target."""
from __future__ import annotations
import os
os.environ.setdefault('MPLCONFIGDIR','C:/IA/tmp/item10-matplotlib')
import argparse,json,collections,shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from train_classifier import save,readrows,sha,ROOT,wilson

def pct(x):return f'{100*x:.1f}%'
def ci(v):return f"{pct(v['lower'])}–{pct(v['upper'])}"
def main():
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);a=p.parse_args();run=a.run_dir.resolve()
    names=['validation','ai_general_development','ai_typing_development','synthetic_test'];titles=['Seed validation','AI general development','AI typing development','Synthetic holdout']
    ms={n:json.loads((run/(n+'_metrics.json')).read_text()) for n in names};manifest=json.loads((run/'run_manifest.json').read_text());tests=json.loads((run/'software_tests.json').read_text());selection=json.loads((run/'selection_frozen.json').read_text())
    old=ROOT/'outputs/item10-classifier-v1.0.2';baseline={n:json.loads((old/(n+'_metrics.json')).read_text()) for n in names[:-1]}
    errors=[]
    for n in names:
        for r in readrows(run/(n+'_predictions.jsonl')):
            if r.get('expected_primary') is not None and (r['predicted_primary']!=r['expected_primary'] or r['predicted_scope']!=r['expected_scope']):
                errors.append({'partition':n,**r})
    save(run/'error_analysis.json',{'error_rows':errors,'synthetic_holdout_error_rows':5,'synthetic_holdout_error_families':len({r['scenario_family_id'] for r in errors if r['partition']=='synthetic_test'}),
        'observed_failure':'Four related consumer-plus-seafarer questions lost the excluded clause; one generic flawed-service question was classified unsupported.',
        'action':'Keep this model and holdout result frozen. Address these failure categories in a new version with new independent evaluation data; do not tune this frozen version on the opened test.',
        'human_independence_claim':False})
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout='constrained');x=np.arange(3);labels=['Validation\n102 rows','AI general\n100 rows','AI typing\n80 labeled rows']
    for ax,key,title in zip(axes,['accuracy','macro_f1'],['Primary-label accuracy','Scope macro F1']):
        head='primary' if key=='accuracy' else 'scope'
        ax.bar(x-.18,[baseline[n][head][key] for n in names[:-1]],width=.36,label='Earlier compositional baseline',color='#a7b2bd')
        ax.bar(x+.18,[ms[n][head][key] for n in names[:-1]],width=.36,label='Frozen improved candidate',color='#247e89')
        ax.set_xticks(x,labels);ax.set_ylim(0,1.08);ax.set_title(title);ax.set_ylabel('Score');ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    axes[0].legend(loc='lower right',fontsize=8);fig.suptitle('Development improvement — these benchmarks informed changes',fontsize=13)
    fig.savefig(run/'accuracy_improvement.png',dpi=180);fig.savefig(run/'accuracy_improvement.svg');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4.4),layout='constrained')
    for ax,head in zip(axes,['primary','scope']):
        for n,title in zip(['ai_general_development','synthetic_test'],['AI development','Synthetic holdout']):
            bins=ms[n][head]['reliability_bins'];ax.plot([b['mean_confidence'] for b in bins],[b['accuracy'] for b in bins],marker='o',label=title)
        ax.plot([0,1],[0,1],linestyle='--',color='#8c8c8c',label='Perfect calibration');ax.set(xlim=(0,1.02),ylim=(0,1.05),xlabel='Mean assigned confidence',ylabel='Observed label accuracy',title=head.capitalize()+' confidence');ax.grid(alpha=.15)
    axes[0].legend(fontsize=8);fig.suptitle('Confidence is conservative on these samples; sparse bins are unstable',fontsize=12);fig.savefig(run/'confidence_reliability.png',dpi=180);plt.close(fig)
    m=ms['synthetic_test'];fig,axes=plt.subplots(1,2,figsize=(12,4.4),layout='constrained')
    for ax,head in zip(axes,['primary','scope']):
        matrix=np.array(m[head]['confusion_matrix']);labels=m[head]['label_order'];ax.imshow(matrix,cmap='Blues');ax.set_xticks(range(len(labels)),[l.replace('_','\n') for l in labels],rotation=15);ax.set_yticks(range(len(labels)),[l.replace('_',' ') for l in labels]);ax.set(xlabel='Predicted',ylabel='Expected',title='Synthetic holdout: '+head)
        for i in range(len(labels)):
            for j in range(len(labels)):ax.text(j,i,str(matrix[i,j]),ha='center',va='center',color='white' if matrix[i,j]>matrix.max()/2 else '#263238')
    fig.savefig(run/'holdout_confusion_matrices.png',dpi=180);plt.close(fig)
    table=[]
    for n,t in zip(names,titles):
        m=ms[n];table.append(f"| {t} | {m['primary']['rows']} | {pct(m['primary']['accuracy'])} | {m['primary']['macro_f1']:.3f} | {m['scope']['macro_f1']:.3f} | {pct(m['routing']['decisive_coverage'])} |")
    hold=ms['synthetic_test'];pr=hold['primary']['classification_report'];sr=hold['scope']['classification_report'];partial=sr['partially_supported'];partial_count=round(partial['recall']*partial['support'])
    report=f'''# Classifier accuracy improvement — 17 October 2026

The improved classifier correctly labels **95/100 questions on the previously unscored synthetic holdout**: primary macro F1 **{hold['primary']['macro_f1']:.3f}**, scope macro F1 **{hold['scope']['macro_f1']:.3f}**. Its known AI development results improved from 68.0% / 68.8% to 100% / 100%. The development sets informed repeated code changes, so those perfect scores are not independent accuracy estimates.

**Acceptance remains incomplete.** The synthetic holdout passes 7 of 8 targets, but partial-support recall is **{partial_count}/{int(partial['support'])} ({pct(partial['recall'])})**, below the unchanged 80% target. Deployment remains disabled. This is an exploratory classifier package, not a verified legal-answering system.

| Evaluation set | Classifiable rows | Primary accuracy | Primary macro F1 | Scope macro F1 | Decisive routing coverage |
|---|---:|---:|---:|---:|---:|
{chr(10).join(table)}

Classification includes every labeled row, including routing abstentions. The typing set also has **20/20 relevant clarification outcomes**, across four underlying ambiguity scenarios. General development has 100 scenario groups; typing classification has 16 families with five variants each. Seed validation and synthetic holdout each have 32 leakage groups. The two new benchmarks are AI-authored and AI-reviewed; no independent human-gold claim is made.

![Development comparison](C:/IA/outputs/{run.name}/accuracy_improvement.png)

## What changed

1. Removed synthetic generator introductions/suffixes from model features while preserving the original stored questions.
2. Derived 571 atomic concern records from the 459 reviewed training parents. After deduplication and adding 42 existing scope-taxonomy definitions, the atomic classifier fits 222 unique texts. These are derived training material, not 613 independently reviewed human questions. No validation, test, general-development or typing-development question was fitted.
3. Compared lexical, fixed multilingual semantic, and hybrid features at three regularization settings. The selected model is **{selection['selected_candidate']}**, a word/character TF-IDF logistic classifier. The multilingual model was explored, but the selected lexical model requires no embedding download or external API at inference.
4. Added transparent constraints for the project's explicit scope boundaries. These AI-written rules are part of the classifier, not learned probability evidence or legal advice. Development error analysis informed this code. They distinguish, for example, telephone hardware warranties from telecom service charges and ordinary private employment from specialized employment categories.
5. Reworked segmentation so punctuation, background statements and generic follow-up questions do not automatically become extra legal concerns. Preserved supported/excluded component text and used their union to determine primary/scope labels.
6. Added component-level retrieval requests: supported concerns receive domain restrictions; identified excluded concerns are omitted from retrieval. This produces structured experimental routing only. Actual answers still require an eligible retrieval index, evidence and citation checks.

## Confidence and selection

Calibration uses **temperature scaling on three training-only grouped folds**. Shared normalized atomic facts are removed from each fold's fit data before calibration. Fold assignments, purges, input hashes and fitted membership are recorded. This controls group/exact-fact overlap; it does not establish semantic independence among synthetic scenarios. Vocabulary and IDF statistics are fitted only on that fold's training atoms plus the 42 predefined taxonomy descriptions.

The 102 validation rows select the candidate and cutoffs: primary **{selection['thresholds']['primary']:.2f}**, scope **{selection['thresholds']['scope']:.2f}**. The 200 AI benchmark rows informed logged development changes before the synthetic holdout was opened, but did not fit model parameters or calibration. Sigmoid and temperature calibration experiments are retained. Temperature reduced primary validation ECE from about 0.237 in v1.2.2 to {ms['validation']['primary']['top_label_expected_calibration_error_10_bins']:.3f} in the final candidate.

The chosen label follows explicit component logic and can differ from the highest-probability label. Its reported confidence is the calibrated probability mass assigned to that chosen label. One-hot scope-constraint evidence is separately identified as a deterministic rule signal; it is not presented as 100% model correctness. Confidence indicates label uncertainty under these training/evaluation distributions, not legal correctness.

Synthetic holdout primary ECE is **{hold['primary']['top_label_expected_calibration_error_10_bins']:.3f}**; scope ECE is **{hold['scope']['top_label_expected_calibration_error_10_bins']:.3f}**. Primary mean confidence is {pct(hold['primary']['mean_confidence'])} versus observed accuracy {pct(hold['primary']['accuracy'])}. Scores tend to understate accuracy on these synthetic samples; calibration is still imperfect.

![Confidence reliability](C:/IA/outputs/{run.name}/confidence_reliability.png)

## Statistics and their limits

- Synthetic holdout accuracy: 95/100; descriptive 95% Wilson interval **{ci(hold['primary']['accuracy_wilson_95'])}**. This row-level interval assumes independence and understates dependence among related synthetic variants.
- Primary macro F1 group bootstrap interval: **{hold['primary']['macro_f1_group_bootstrap_95']['lower']:.3f}–{hold['primary']['macro_f1_group_bootstrap_95']['upper']:.3f}**; scope interval **{hold['scope']['macro_f1_group_bootstrap_95']['lower']:.3f}–{hold['scope']['macro_f1_group_bootstrap_95']['upper']:.3f}**. Each uses 2,000 resamples of 32 leakage groups. Resamples lacking a class assign it zero F1, which can widen these intervals.
- Partial-support recall: {partial_count}/11; descriptive Wilson interval **{ci(wilson(partial_count,11))}**. Eleven rows are too few for a narrow estimate.
- Unsupported questions admitted to substantive retrieval: **0/26** on the synthetic holdout; Wilson upper bound **{pct(hold['routing']['unsupported_admission_wilson_95']['upper'])}**. Observing zero errors does not prove the true admission rate is below 5%.
- Holdout decisive coverage: **84/100**; 16 requests clarify. Correct primary and scope together among decisive routes: **80/84 ({pct(hold['routing']['correct_joint_labels_among_decisive'])})**.
- Out-of-scope recall: **{pct(pr['out_of_scope']['recall'])}**. Mixed recall: **{pct(pr['mixed']['recall'])}**. Per-class metrics, language breakdowns, reliability bins and all question-level predictions accompany this report.

## Tests used

**24/24 software tests passed**, including training/evaluation membership separation, fold coverage, atomic-fact purging, training-only IDF reconstruction, deterministic refitting, model persistence/replay over all development rows, probability normalization, confidence-to-label alignment, label coherence, metadata isolation, missing-context priority, invalid-pair blocking, threshold enforcement, mixed retrieval isolation, repeat/order stability, empty input, and no embedding download for the selected model.

One test also checks **19 AI-authored development regressions** involving private versus municipal employment, phone product versus telecom service, appliance versus utility billing, wage framework versus exact amounts, privacy, fraud, employment background, and negation. These are development regression checks; their success is not an independent gold-set score.

The frozen reviewed dataset again passed **59/59 provenance and consistency checks**. The original seed, frozen split files, five returned human reviews and 200 AI development questions were preserved. The validator's formal `training_ready=false` remains accurate because the original independent-human-gold/adviser prerequisite is still outstanding; exploratory authorization is recorded separately.

After development and software checks passed, the selected model, code, source hashes and thresholds were frozen in `final_evaluation_freeze.json`. The 100-row synthetic holdout was evaluated **once**, after freezing. No fitting or tuning followed its result. The evaluator rejects another attempt for this run.

## Remaining failures and next steps

Four related holdout examples lost the excluded seafarer-deployment concern beside a supported defective-product issue. One generic flawed-service example was classified unsupported. These five errors span two underlying families. They are retained in `error_analysis.json`; no labels were edited to make the model pass.

Keep this version frozen. For the next version, expand independently reviewed natural examples of partial-support cases, short service complaints, background statements and specialized employment. Lock a fresh independent human-written/labeled holdout before making renewed final accuracy claims; the opened synthetic test cannot serve as a new untouched final test. Retrieval/citation integration and source eligibility remain separate work before live use.

## Reproduce and inspect

Run source entry points from C:/IA with the isolated `.venv-item10` environment and this package's `requirements.lock.txt`:

```powershell
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item10/train_logical_classifier.py --scope-constraints --calibration temperature --run-dir C:/IA/outputs/<new-run-directory>
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item10/test_logical_classifier.py --run-dir C:/IA/outputs/<new-run-directory>
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item10/classifier_runtime.py --model C:/IA/outputs/{run.name}/classifier.joblib --text "My private employer owes overtime pay."
```

Rebuilding is a reproducibility operation, not a fresh independent experiment after seeing this holdout. The stored synthetic holdout results should be inspected directly. Source copies in output folders are provenance snapshots; executable entry points retain their project-relative layout.

Method references: [scikit-learn probability calibration](https://scikit-learn.org/stable/modules/calibration.html), [grouped stratification](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html). These describe methods, not endorsements of this model or its accuracy.
'''
    (run/'ACCURACY_REPORT.md').write_text(report,encoding='utf-8')
    save(run/'MODEL_CARD.json',{'model_version':run.name,'status':'experimental_holdout_partial_support_target_failed','intended_use':'Offline exploratory classification and structured routing for selected Philippine labor/consumer scope','deployment_allowed':False,'independent_human_gold_available':False,
        'selected_candidate':selection['selected_candidate'],'training_parent_rows':459,'raw_atomic_derivatives':571,'taxonomy_rows':42,'unique_atomic_fit_rows':222,'additional_material_provenance':'AI-derived training atoms and existing project taxonomy definitions, no new independent human review',
        'constraints':'AI-written scope constraints informed by development error analysis; part of measured classifier','ai_development_used_for_error_analysis':True,'synthetic_test_evaluations':1,'synthetic_test_primary_accuracy':hold['primary']['accuracy'],'synthetic_test_primary_macro_f1':hold['primary']['macro_f1'],'synthetic_test_scope_macro_f1':hold['scope']['macro_f1'],
        'failed_holdout_targets':[g for g in hold['targets'] if not g['passed']],'thresholds':selection['thresholds'],'confidence':manifest['confidence_method'],'confidence_limit':'Empirically conservative on synthetic samples; not legal correctness or real-user validation',
        'software_tests':tests,'data_validation_checks_passed':59,'further_tuning_on_opened_test_permitted':False,'limitations':['Synthetic origin and correlated variants','No independent human gold or real-user validation','Partial-support recall 7/11 on holdout','Incomplete real-world probability calibration','No live retrieval/answering integration','No automatic official referral selection']})
    for name in ['test_logical_classifier.py','evaluate_logical_holdout.py','write_accuracy_report.py']:shutil.copy2(Path(__file__).parent/name,run/name)
    files={str(f.relative_to(run)):sha(f) for f in run.rglob('*') if f.is_file() and f.name!='artifact_checksums.json'};save(run/'artifact_checksums.json',files)
    print(json.dumps({'report':str(run/'ACCURACY_REPORT.md'),'artifacts_hashed':len(files),'holdout_targets_passed':sum(g['passed'] for g in hold['targets']),'holdout_target_count':len(hold['targets'])}))
if __name__=='__main__':main()
