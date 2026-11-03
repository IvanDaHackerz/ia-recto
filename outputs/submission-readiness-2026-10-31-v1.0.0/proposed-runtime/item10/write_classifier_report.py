"""Generate research figures, an acceptance report and model card from saved measurements."""
from __future__ import annotations
import os,argparse,json,hashlib,shutil
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);a=p.parse_args();run=a.run_dir.resolve();root=Path(__file__).resolve().parents[3]
    os.environ['MPLCONFIGDIR']=str(run/'plot-cache')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})
    names=['validation','ai_general_development','ai_typing_development'];labels=['Seed validation\n102 questions','General development\n100 questions','Typing development\n80 labeled questions']
    metrics={n:json.loads((run/(n+'_metrics.json')).read_text()) for n in names}
    experiments=[root/'outputs'/('item10-classifier-v1.0.'+str(i)) for i in range(3)]
    exp_labels=['Original wrappers','Wrappers removed','Component signals']
    colors=['#8797A8','#D3973B','#245A81']
    fig,axes=plt.subplots(1,2,figsize=(12,5.5),layout='constrained')
    for ax,head,title in zip(axes,['primary','scope'],['Primary-label macro F1','Scope-label macro F1']):
        x=np.arange(3)
        for j,(folder,label,color) in enumerate(zip(experiments,exp_labels,colors)):
            values=[json.loads((folder/(n+'_metrics.json')).read_text())[head]['macro_f1'] for n in names]
            bars=ax.bar(x+(j-1)*.24,values,width=.22,label=label,color=color)
            ax.bar_label(bars,labels=[f'{v:.2f}' for v in values],padding=3,fontsize=9)
        ax.axhline(.8,color='#B44444',linestyle='--',linewidth=1,label='Target 0.80');ax.set_ylim(0,1.12);ax.set_xticks(x,labels);ax.set_title(title);ax.set_ylabel('Macro F1');ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    handles,leglabels=axes[0].get_legend_handles_labels();fig.legend(handles,leglabels,loc='outside lower center',ncol=4,frameon=False);fig.suptitle('High seed scores do not carry over to natural development questions',fontsize=14)
    fig.savefig(run/'experiment_comparison.png',dpi=180);fig.savefig(run/'experiment_comparison.svg');plt.close(fig)

    fig,axes=plt.subplots(1,2,figsize=(11,5),layout='constrained');m=metrics['ai_general_development']
    for ax,head,title in zip(axes,['primary','scope'],['General development: primary labels','General development: scope labels']):
        cm=np.array(m[head]['confusion_matrix']);order=m[head]['label_order'];short={'fully_supported':'Full','partially_supported':'Partial','unsupported':'Unsupported','out_of_scope':'Out of scope','labor':'Labor','consumer':'Consumer','mixed':'Mixed'}
        ax.imshow(cm,cmap='Blues',vmin=0,vmax=max(25,cm.max()));ax.set_xticks(range(len(order)),[short[l] for l in order],rotation=25,ha='right');ax.set_yticks(range(len(order)),[short[l] for l in order]);ax.set_xlabel('Predicted');ax.set_ylabel('Expected');ax.set_title(title)
        for i in range(len(order)):
            for j in range(len(order)):ax.text(j,i,str(cm[i,j]),ha='center',va='center',color='white' if cm[i,j]>cm.max()/2 else '#142535')
    fig.savefig(run/'general_confusion_matrices.png',dpi=180);plt.close(fig)

    fig,axes=plt.subplots(1,2,figsize=(11,5),layout='constrained')
    for ax,head,title in zip(axes,['primary','scope'],['Primary-label confidence','Scope-label confidence']):
        ax.plot([0,1],[0,1],color='#9B9B9B',linestyle='--',label='Perfect agreement')
        for name,label,color in zip(names,['Seed validation','General development','Typing development'],colors):
            bins=metrics[name][head]['reliability_bins'];ax.plot([b['mean_confidence'] for b in bins],[b['accuracy'] for b in bins],marker='o',label=label,color=color)
        ax.set_xlim(0,1);ax.set_ylim(0,1);ax.set_xlabel('Mean predicted confidence within bin');ax.set_ylabel('Observed label accuracy within bin');ax.set_title(title);ax.grid(alpha=.15)
    axes[1].legend(loc='lower right',fontsize=9);fig.suptitle('Confidence reliability on these small samples',fontsize=14);fig.savefig(run/'confidence_reliability.png',dpi=180);plt.close(fig)

    manifest=json.loads((run/'run_manifest.json').read_text());selection=json.loads((run/'selection_frozen.json').read_text());tests=json.loads((run/'software_tests.json').read_text())
    assert tests['status']=='passed' and tests['tests_run']==18 and not manifest['synthetic_test_opened']
    failures={n:[g for g in metrics[n]['targets'] if not g['passed']] for n in names}
    manifest.update(acceptance_status='not_ready',deployment_allowed=False,failed_targets=failures,
        synthetic_test_disposition='100 test rows remain unopened because development acceptance targets failed',
        experiment_design_informed_prior_development_errors=True,
        within_run_candidate_selection_data='102 validation rows only',software_tests_passed=18,
        confidence_limit='Binary component detectors are sigmoid-calibrated on grouped training folds. Combined probabilities use an independence approximation and are not jointly calibrated.',
        follow_up='Improve natural training-only scenarios and compositional mixed/partial coverage; never fit the current development benchmarks or synthetic test.')
    (run/'run_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    for f in ['train_classifier.py','classifier_runtime.py','test_classifier.py','write_classifier_report.py']:
        shutil.copyfile(root/'dataset/pipelines/item10'/f,run/f)
    mgen=metrics['ai_general_development'];mtype=metrics['ai_typing_development'];val=metrics['validation']
    fmt=lambda v:f'{v:.1%}'
    ci=lambda m,h:f"{m[h]['macro_f1_group_bootstrap_95']['lower']:.3f}–{m[h]['macro_f1_group_bootstrap_95']['upper']:.3f}"
    lines=['# Classifier training and evaluation report','',
        '17 October 2026. **Outcome: not ready for live use.** The approved evaluation policy was applied without lowering targets. Exploratory training and the software checks are complete; accuracy and scope handling still fail acceptance. The 100-row synthetic test remains unopened.',
        '', '## Results for the latest component-based candidate','',
        '| Evaluation data | Primary accuracy | Primary macro F1 | Scope accuracy | Scope macro F1 |',
        '|---|---:|---:|---:|---:|']
    for name,label in zip(names,['Seed validation (102)','AI general development (100)','AI typing development (80 labeled)']):
        m=metrics[name];lines.append(f"| {label} | {fmt(m['primary']['accuracy'])} | {m['primary']['macro_f1']:.3f} | {fmt(m['scope']['accuracy'])} | {m['scope']['macro_f1']:.3f} |")
    lines+=['','The additional 20 incomplete typing questions are evaluated for clarification, not forced into a primary class. They passed 20/20 relevant-follow-up checks across four scenario families. Those checks exercise authored missing-context rules, not learned understanding or independent human validation.',
        '', '**The main failure is mixed/partial handling.** On general development questions, mixed recall is '+fmt(mgen['primary']['classification_report']['mixed']['recall'])+' and partially-supported recall is '+fmt(mgen['scope']['classification_report']['partially_supported']['recall'])+'. On typing examples they are '+fmt(mtype['primary']['classification_report']['mixed']['recall'])+' and '+fmt(mtype['scope']['classification_report']['partially_supported']['recall'])+'. Scope accuracy looks higher because fully supported and unsupported questions dominate; the per-class metrics reveal the missed partial cases.',
        '', '![Experiment comparison](C:/IA/outputs/'+run.name+'/experiment_comparison.png)',
        '', '## What was trained','',
        '- Fitting used only the 459 reviewed training questions. The 102 validation rows selected candidates and confidence thresholds. Neither the new 200 development questions nor the synthetic test supplied fitted text features, weights or calibration examples.',
        '- Compared a dummy prior baseline, logistic regression with words, logistic regression with words/character fragments at two regularization settings, and linear SVM with words/character fragments at two settings. Repeated that fixed six-candidate comparison for three documented experiments.',
        '- Experiment 1 kept the original question wrappers. It reached 100% primary accuracy on seed validation but only 56% on general development, with 24% of unsupported general questions admitted to the supported-answer candidate route. This is evidence of generator-style dependence, not a usable 100%-accurate classifier.',
        '- Experiment 2 removed class-correlated boilerplate such as “Can this service advise me if…” and “My question involves both issues…”. Patterns came from the generator and training questions; facts and labels were preserved. General primary accuracy improved to 70%, but scope and mixed handling still failed.',
        '- Experiment 3 used three training-annotation targets: supported labor present, supported consumer present, and excluded content present. The selected SVM detects these separately and combines the signals using the project definitions. It restores much of seed validation performance and improves excluded-topic routing, but does not solve natural mixed/partial questions.',
        '- Within each experiment, model selection used validation metrics only. The later experiment designs were informed by earlier development errors. Therefore all 200 AI questions are development data, not an independent final test.',
        '', '## Tests and statistics, in plain language','',
        '1. **Leakage checks:** verified frozen/source checksums, unique input IDs, no training/exact evaluation-text matches, and no leakage group crossing train/validation/test. All five related typing variants remain a family. This does not prove semantic or AI-writing-style independence.',
        '2. **Baseline comparisons:** measured all classifiable questions, including those the router would clarify. Reported accuracy, macro/micro F1, per-class precision/recall/F1 and confusion matrices for primary and scope separately. Macro F1 gives each class equal weight.',
        '3. **Language and typing checks:** separate English/Taglish results and clear wording, misspellings, abbreviations, reordering and punctuation groups. Variants combine some writing changes; this is not an isolated causal experiment on each typo type.',
        '4. **Confidence calibration:** used three grouped folds inside the training data to obtain out-of-fold scores for sigmoid calibration. No validation or test labels fitted calibration. Reported log loss, multiclass Brier score and ten-bin confidence reliability. The component probabilities are calibrated individually; their combined scores use an independence approximation and are not jointly calibrated.',
        '5. **Confidence intervals:** used 2,000 scenario/leakage-group bootstrap draws for macro F1. General development has 100 assigned scenario IDs; labeled typing has only 16 families. Intervals describe these development samples and are affected by small groups, AI origin and model selection; they do not establish real-user performance.',
        '6. **Routing safety/coverage:** counted unsupported questions admitted for substantive-answer retrieval, decisive routes, low-confidence clarifications, inconsistent predictions and unresolved mixed components. Zero unsafe observations in a small sample is not proof of a zero error rate.',
        '7. **Eighteen software tests:** tested training-only vectorizer vocabularies/IDF, disjoint calibration folds, source preservation, saved-model replay, reproducible refitting of a calibrated component, finite normalized probabilities, independence from label metadata, high-confidence missing-context handling, low-confidence and conflicting-label blocks, partial-answer blocking, evidence requirements, no invented referrals, abstain-all rejection and the unopened test.',
        '', '| Data | Primary macro F1: descriptive 95% grouped interval | Scope macro F1: descriptive 95% grouped interval |','|---|---:|---:|']
    for name,label in zip(names,['Validation','General development','Typing development']):lines.append(f'| {label} | {ci(metrics[name],"primary")} | {ci(metrics[name],"scope")} |')
    lines+=['','## Confidence and routing results','',
        f"Validation selected primary confidence ≥ {selection['thresholds']['primary']:.2f} and scope confidence ≥ {selection['thresholds']['scope']:.2f}. These are **experimental cutoffs, not production-approved confidence levels**: the candidate fails other targets and coverage constraints. Explicit missing facts and conflicting label pairs override confidence. Mixed components are not yet reliably mapped to topics, so recognized mixed questions clarify instead of receiving an invented partial answer.",
        '', '| Data | Mean primary confidence | Mean confidence on wrong primary labels | Primary calibration error (ECE) | Decisive coverage | Unsupported admission |','|---|---:|---:|---:|---:|---:|']
    for name,label in zip(names,['Validation','General development','Typing development']):
        m=metrics[name];r=m['routing'];lines.append(f"| {label} | {fmt(m['primary']['mean_confidence'])} | {fmt(m['primary']['mean_confidence_when_wrong'])} | {m['primary']['top_label_expected_calibration_error_10_bins']:.3f} | {fmt(r['decisive_coverage'])} | {r['unsupported_answer_admitted_count']}/{r['unsupported_count']} ({fmt(r['unsupported_admission_rate'])}) |")
    lines+=['','ECE compares confidence and observed accuracy within probability bins; lower is better, but an aggregate ECE can hide class-specific failures. A 0.90 score means a model-derived label estimate; it does not mean 90% legal correctness. Composed probabilities and out-of-distribution wording need particular caution.',
        '', 'General development admitted 1/25 unsupported questions (4% observed). Its row-wise Wilson 95% interval is approximately '+fmt(mgen['routing']['unsupported_admission_wilson_95']['lower'])+'–'+fmt(mgen['routing']['unsupported_admission_wilson_95']['upper'])+'. Typing admitted 0/20, but these rows belong to only four out-of-scope families; a row-independent interval would be optimistic. Neither small sample certifies that real-world unsafe admission is below 5%.',
        '', '![Confidence reliability](C:/IA/outputs/'+run.name+'/confidence_reliability.png)',
        '', '## Acceptance failures','', '| Dataset | Failed approved targets |','|---|---|']
    for name,label in zip(names,['Validation','General development','Typing development']):lines.append('| '+label+' | '+', '.join(f['name'] for f in failures[name])+' |')
    lines+=['','![General development confusion matrices](C:/IA/outputs/'+run.name+'/general_confusion_matrices.png)',
        '', '## What happens next','',
        'Keep the current model experimental. Build a new training-only version with more varied natural English/Taglish situations, especially supported-plus-excluded concerns and labor-plus-consumer combinations. Reduce generator-specific class cues and add scope-changing counterexamples. Do not move the current 200 development examples or their siblings into training. Preserve their AI provenance and the existing human-reviewed seed.',
        '', 'Retrain and repeat development checks before opening the 100-row synthetic test. For formal final claims, create and lock the independent human-written/labeled holdout still required by the project. Passing a classifier score also leaves retrieval, citations, source freshness and legal-professional system review to be completed.',
        '', '## Reproducing the work','',
        'Environment versions and exact installed packages are in requirements.lock.txt. Use the project Python environment, source scripts under dataset/pipelines/item10, the approved policy, and an unused run directory.',
        '', '```powershell',
        r"& 'C:\IA\.venv-item10\Scripts\python.exe' 'C:\IA\dataset\pipelines\item10\train_classifier.py' --stage develop --experiment compositional --run-dir 'C:\IA\outputs\item10-classifier-new-run'",
        r"& 'C:\IA\.venv-item10\Scripts\python.exe' 'C:\IA\dataset\pipelines\item10\test_classifier.py' --run-dir 'C:\IA\outputs\item10-classifier-new-run'",
        '```','',
        'The separate test stage refuses to overwrite an opened test and verifies the frozen model hash. It has deliberately not been run for these failing candidates. No UI/backend integration or live answering was enabled.',
        '', 'Implementation references: [scikit-learn probability calibration](https://scikit-learn.org/stable/modules/generated/sklearn.calibration.CalibratedClassifierCV.html) and [grouped stratified folds](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html).',
        '', 'Machine-readable evidence: candidate_comparison.json, calibration_folds.json, selection_frozen.json, the three *_metrics.json files, per-question *_predictions.jsonl, data_audit.json, software_tests.json and run_manifest.json.']
    (run/'TRAINING_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    card={'model_version':run.name,'intended_use':'local exploratory classification research only','acceptance_status':'not_ready','deployment_allowed':False,
        'training_data':'reviewed_v1.0.0 train partition only: 459 questions','training_origin':'synthetic seed with one human review per row and disclosed owner-authorized AI cleanup',
        'development_data':'102 seed validation; 100 AI general; 80 labeled AI typing; 20 AI clarification tests','independent_human_gold_available':False,
        'synthetic_test_opened':False,'selected_config':manifest['selected_candidate'],'thresholds':selection['thresholds'],'confidence_method':manifest['confidence_limit'],
        'known_failures':['Natural mixed-domain recall is low.','Natural partially-supported recall is zero on these development sets.','Validation decisive coverage misses the target.','Synthetic/AI style and small family counts limit generalization.'],
        'outputs':['primary/scope labels and probability vectors','clarification or evidence-retrieval candidate route','no generated legal advice','no automatic referral agency guessing'],
        'software_tests_passed':18,'report':'TRAINING_REPORT.md','versions':manifest['versions']}
    (run/'MODEL_CARD.json').write_text(json.dumps(card,indent=2)+'\n',encoding='utf-8')
    files={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in run.iterdir() if f.is_file() and f.name!='artifact_checksums.json'}
    (run/'artifact_checksums.json').write_text(json.dumps(files,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(run/'TRAINING_REPORT.md'),'status':'not_ready','software_tests':18,'synthetic_test_opened':False},indent=2))

if __name__=='__main__':main()
