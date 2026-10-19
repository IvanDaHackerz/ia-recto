"""Package the offline Item 11 index, benchmark limits and source audit."""
from __future__ import annotations
import os
os.environ.setdefault('MPLCONFIGDIR','C:/IA/tmp/item11-matplotlib')
import argparse,collections,json,shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from common import ROOT,PIPELINE,readrows,save,jsonl,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--index',type=Path,required=True);a=p.parse_args();out=a.index.resolve()
    audit=json.loads((out/'source_audit.json').read_text());manifest=json.loads((out/'index_manifest.json').read_text());bench=json.loads((out/'benchmark_metrics.json').read_text());tests=json.loads((out/'software_tests.json').read_text())
    assert tests['passed'];records=readrows(out/'records.jsonl');excluded=readrows(out/'excluded_chunks.jsonl');extra=[r for r in excluded if r['item7_answer_eligible']];coverage=json.loads((out/'topic_coverage.json').read_text());results=readrows(out/'benchmark_results.jsonl')
    methods=bench['methods'];best=methods['bm25'];rows=[]
    for name in ['bm25','semantic','hybrid']:
        m=methods[name];rows.append(f"| {name} | {100*m['hit@1']:.1f}% | {100*m['hit@5']:.1f}% | {100*m['recall@5']:.1f}% | {m['mrr@10']:.3f} | {m['ndcg@10']:.3f} |")
    jsonl(out/'additional_quarantine.jsonl',extra)
    misses=[{'query_id':r['query_id'],'language_style':r['language_style'],'relevant_provision_ids':r['relevant_provision_ids'],'retrieved_top5':[h['provision_id'] for h in r['response']['hits'][:5]],'query':r['response']['query']} for r in results if r['method']=='bm25' and r.get('metrics',{}).get('hit@5')==0]
    save(out/'error_analysis.json',{'role':'AI development retrieval error analysis','bm25_misses_at_5':misses,'count':len(misses),'relevance_labels_exhaustive':False,
        'limitations':'Known relevant target absent from top five does not prove every returned provision irrelevant; labels are partial AI judgments.'})
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(10,4.4),layout='constrained');names=['bm25','semantic','hybrid'];colors=['#247e89','#92a2b0','#6786a1']
    for ax,key,title in zip(axes,['hit@5','mrr@10'],['Known-relevant provision in top five','Mean reciprocal rank @10']):
        values=np.array([methods[n][key] for n in names]);lower=np.array([methods[n]['scenario_bootstrap_95'][key]['lower'] for n in names]);upper=np.array([methods[n]['scenario_bootstrap_95'][key]['upper'] for n in names])
        ax.bar(names,values,color=colors);ax.errorbar(names,values,yerr=[values-lower,upper-values],fmt='none',ecolor='#34404b',capsize=4);ax.set_ylim(0,1.05);ax.set_title(title);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
    fig.suptitle('AI development retrieval benchmark: 56 queries / 28 scenario families',fontsize=12);fig.savefig(out/'retrieval_comparison.png',dpi=180);fig.savefig(out/'retrieval_comparison.svg');plt.close(fig)
    domains=dict(collections.Counter(d for r in records for d in r['domains']));ci=best['scenario_bootstrap_95']['hit@5'];quarantined_provisions=len({r['provision_id'] for r in extra})
    text=f'''# Item 11 — offline legal retrieval

Implemented **{manifest['index_version']}**: filtered BM25 keyword search, local multilingual semantic search and reciprocal-rank-fusion hybrid search, with a real offline classifier adapter. The working default is **BM25**, selected on the disclosed AI development benchmark.

The index contains **{len(records)} chunks from {manifest['indexed_provisions']} provisions and {audit['indexed_documents']} canonical documents** ({domains.get('labor',0)} labor chunks / {domains.get('consumer',0)} consumer chunks). It returns ranked source candidates with exact citations, source URLs, page/character locators, the matching chunk and full eligible provision text. **Answer generation and deployment remain disabled.**

## What entered the index

Item 7 has 2,001 chunks, of which 420 carried an answer-eligible flag. Item 11 rechecks the chunk, provision, document, canonical manifest, source registry, legal-use policy, extraction quality and MVP scope. The original 1,581 ineligible chunks remain excluded. A further **{len(extra)} flagged-eligible chunks covering {quarantined_provisions} provisions** are held out because of specialized scope or visible text corruption. They are recorded in `additional_quarantine.jsonl`; the full exclusion log is `excluded_chunks.jsonl`.

Examples include collective-bargaining passages, household-worker rules, specialized food/drug/credit passages and two visibly corrupted SEnA provisions. A regression test caught footnote digits attached to a heading (HOUSEHELPERS112); screening now recognizes that heading without editing the preserved text. These additional screens are AI-authored conservative code, not a new independent human or legal-professional review.

The original legal files, extraction records, existing review queues and classifier package remain unchanged. Every indexed source still has conditions: legal-status checks are recorded as of **29 September 2026**, and this task did **not** refresh or certify current law. Those dates, freshness requirements and related-authority relationships accompany each result. Unknown or restricted legal-use modes, pending review, blocking flags, unverified OCR and specialized-topic exclusions cannot enter the default index.

## Retrieval methods and context

- **BM25:** Unicode-normalized word tokens, corpus-only document statistics, k1=1.2 and b=0.75. Questions and relevance labels do not fit IDF or model weights.
- **Semantic:** the existing fixed local multilingual MiniLM encoder, with 384-dimensional normalized embeddings. Its 128-token input limit is enforced by **{manifest['semantic_windows']} overlapping windows**, including chunk tails. Queries are also windowed. Max cosine similarity ranks each chunk; no source text is silently truncated.
- **Hybrid:** reciprocal rank fusion, constant 60 and depth 50, combining provision-deduplicated lexical and semantic rankings. Long provisions cannot occupy several fusion ranks.

Results are unique provisions retaining the best matching chunk and full parent provision. The exact chunk offsets and original source locator remain available. Retrieval features use citation, heading and body, rather than blindly using inherited table-of-contents context prefixes. Original hierarchy metadata is retained for audit and scope screening. Ranking scores are **not confidence, legal correctness or evidence sufficiency**.

## Development benchmark

The 67 new query records comprise **56 positive questions across 28 scenario families** (28 English / 28 Taglish) and **11 excluded-scope or missing-evidence controls**. Codex authored the questions and identified expected provisions by reading the preserved text. These are source-grounded **AI development judgments**, not independent human-written/labeled gold or legal-professional validation. They are separate from the earlier classifier question datasets.

Positive evaluation supplies the correct labor/consumer domain, but **no oracle topic filter**. Relevance labels identify known passages and are not exhaustive; other useful passages may be unjudged. The separate classifier integration checks exercise actual domain/scope/clarification routing. Retrieval scores do not measure answer accuracy or current-law correctness.

| Method | Hit@1 | Hit@5 | Known-relevant Recall@5 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

BM25 found a known relevant provision in the first five results for **{round(best['hit@5']*56)}/56 queries ({100*best['hit@5']:.1f}%)**. Its English Hit@5 is {100*best['language']['en']['hit@5']:.1f}%; Taglish is {100*best['language']['en_tl']['hit@5']:.1f}%. The descriptive 95% scenario-family bootstrap interval is **{100*ci['lower']:.1f}%–{100*ci['upper']:.1f}%**, using 2,000 resamples of 28 families. It does not account for AI relevance-label error or selection bias.

All three methods passed **11/11 negative controls**. The default was chosen from the initial v1.0.2 development comparison by highest Hit@5 then MRR@10. Subsequent versions reuse those same disclosed development queries while closing source-screen and interface issues. The final figures are **not** an untouched test of the selected method. No query wording was copied into index features, and the encoder was not fine-tuned. The local multilingual paraphrase model performed worse than BM25 here; semantic/hybrid retrieval remains available for further comparison.

![Retrieval comparison](C:/IA/outputs/{out.name}/retrieval_comparison.png)

`error_analysis.json` retains the {len(misses)} BM25 misses at rank five. Recall@k measures the fraction of specified relevant provisions retrieved; Hit@k measures whether at least one appeared; MRR measures first relevant rank. The metrics are based on partial relevance judgments. Latency records include cold encoder loading and process-cache reuse, so they are diagnostics rather than a controlled speed comparison.

## Integration and tests

**{tests['tests_run']}/{tests['tests_run']} software tests passed.** Checks cover eligibility at every level, restricted and unknown policies, review/OCR gates, specialized scope, glyph corruption, footnote-number bypasses, original source hashes, changed raw files/runtime rejection, exact citation/text offsets, token-window completeness, normalized vectors, a numeric BM25 reference, deterministic rankings, provision deduplication, domain/topic isolation, invalid-filter rejection and zero evidence for final-pay/COE.

Seven AI-authored integration cases exercise the unchanged **classifier v1.4.0**: supported labor, supported consumer, fully supported mixed concerns, partial concerns, excluded-only concerns, missing deciding context and a final-pay/COE evidence gap. Excluded portions never become retrieval queries; clarification/referral routes return no retrieval candidates. The standalone classifier-plus-retrieval CLI is also tested in a fresh Python process.

## Gaps and next work

- **Final pay / COE:** zero eligible chunks. Explicit queries report `no_eligible_evidence`; the original advisory remains gated. A wage provision is not substituted as evidence for this missing topic.
- **Thirteenth-month pay:** only limited PD 851 sections are eligible; the original main coverage wording and the MO 28 copy are restricted. Nonzero topic counts do not establish sufficient evidence for general entitlement or computation.
- **Current DTI procedure and scanned IRRs:** relevant canonical documents still have pending extraction review. General Consumer Act complaint text is not a substitute for a verified current procedure.
- **Retrieval misses and Taglish:** the present benchmark is small and source-derived. Fresh human relevance judgments and more varied cases remain needed for stronger claims.
- **Item 12:** implement proposition/citation verification, related-authority and freshness checks, and sufficient-evidence/decline rules before generating answers. The classifier still has its previously disclosed 69% regression routing coverage versus a 70% target; this work does not remove that limitation.

Item 11 is complete as a reproducible **offline development retrieval pipeline**. It is ready to support Item 12 work, with the documented corpus and evaluation limits. It does not authorize live legal answering.

## Use and reproduce

Use C:/IA/.venv-item10 and the package's `requirements.lock.txt`. All source/runtime paths are project-relative; output source copies are provenance snapshots.

```powershell
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item11/retrieval.py --index C:/IA/outputs/{out.name} --domain consumer --query "The cashier charged more than the displayed price."
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item11/retrieval.py --index C:/IA/outputs/{out.name} --classifier C:/IA/outputs/item10-classifier-v1.4.0/classifier.joblib --query "A store refuses my warranty. I have a complaint about my seafarer deployment."
& C:/IA/.venv-item10/Scripts/python.exe C:/IA/dataset/pipelines/item11/test_retrieval.py --index C:/IA/outputs/{out.name}
```

Build a new directory with `build_index.py --output-dir <new-directory> --default-method bm25 --selection-evidence C:/IA/outputs/item11-retrieval-v1.0.2/benchmark_metrics.json`. `--reuse-vectors-from` may reuse checksum-verified embeddings of exact identical texts under the same model. Initial dependencies and weights must already be installed locally; ordinary retrieval does not download them. `create_benchmark.py`, `benchmark_retrieval.py`, and `write_report.py` record benchmark provenance, comparisons and this report. Rebuilding preserves provenance but does not create independent final evidence.

Method references: [original Okapi research](https://www.microsoft.com/en-us/research/publication/okapi-at-trec/), [Sentence Transformers semantic search documentation](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html), [original reciprocal-rank fusion paper](https://doi.org/10.1145/1571941.1572114). These describe retrieval methods, not endorsements of the project or its legal accuracy.
'''
    (out/'RETRIEVAL_REPORT.md').write_text(text,encoding='utf-8')
    save(out/'RETRIEVAL_CARD.json',{'index_version':out.name,'status':'offline_development_retrieval_complete','indexed_chunks':len(records),'indexed_provisions':manifest['indexed_provisions'],'indexed_documents':audit['indexed_documents'],
        'default_method':'bm25','default_selected_on_ai_development_queries':True,'bm25_hit_at_5':best['hit@5'],'bm25_mrr_at_10':best['mrr@10'],'positive_queries':56,'positive_families':28,'negative_controls_passed':11,'software_tests_passed':tests['tests_run'],
        'human_gold':False,'fresh_holdout_evaluated':False,'legal_currentness_refreshed':False,'recorded_status_as_of':'2026-09-29','source_data_modified':False,'classifier_modified':False,
        'deployment_allowed':False,'answer_generation_allowed':False,'additional_quarantine_chunks':len(extra),'additional_quarantine_provisions':quarantined_provisions,'corpus_gaps':['final_pay_coe','main_thirteenth_month_entitlement/current_related_authority','current_DTI_procedure/OCR-gated_IRRs'],
        'limitations':['AI-authored queries and partial relevance judgments','Oracle domain in main retrieval benchmark','Method selected using the same development benchmark','No generated-answer, legal-currentness or independent human validation','General-purpose multilingual semantic model','Classifier coverage limitation remains']})
    save(out/'dataset_inventory_addendum.json',{'layer':'Item 11 derived retrieval index, not new legal authorities','source_chunks':2001,'item7_flagged_eligible_chunks':420,'indexed_chunks':len(records),'indexed_provisions':manifest['indexed_provisions'],'indexed_documents':audit['indexed_documents'],
        'extra_quarantine_chunks':len(extra),'semantic_windows':manifest['semantic_windows'],'benchmark_queries':67,'benchmark_positive_queries':56,'benchmark_positive_scenario_families':28,'benchmark_negative_queries':11,
        'benchmark_origin':'AI-authored/source-grounded AI relevance labels, development only','new_human_gold_questions':0,'new_classifier_training_questions':0,'original_legal_sources_changed':False})
    for file in PIPELINE.glob('*.py'):
        if not (out/file.name).exists():shutil.copy2(file,out/file.name)
    save(out/'artifact_checksums.json',{str(f.relative_to(out)):sha(f) for f in out.rglob('*') if f.is_file() and f.name!='artifact_checksums.json'})
    print(json.dumps({'report':str(out/'RETRIEVAL_REPORT.md'),'indexed_chunks':len(records),'default':'bm25','hit@5':best['hit@5'],'tests_passed':tests['tests_run'],'live_answering':False}))
if __name__=='__main__':main()
