"""Create a new versioned Item 12 evidence packet; preserve all parent artifacts."""
from __future__ import annotations

import argparse
import importlib.metadata
import io
import json
import os
import platform
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from contracts import DRAFT_SCHEMA, PREFLIGHT_SCHEMA, RESULT_SCHEMA, REVIEW_STORE_SCHEMA
from development_cases import AS_OF, LABOR, MIXED, PRICE, ARTICLE_83, ARTICLE_81, excerpt
from evaluate_verifier import evaluate
from verification import EvidenceVerifier, HERE, ROOT, sha


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def suite(cls, output, name):
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    (output / (name + '.log')).write_text(stream.getvalue(), encoding='utf-8')
    return {'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
            'skipped': len(result.skipped), 'passed': result.wasSuccessful()}


def build(output):
    output.mkdir(parents=True, exist_ok=False)
    runtime = EvidenceVerifier(as_of=AS_OF)
    # Snapshot every parent checksum and source binding before any tests.
    parent_files = {str((ROOT / runtime.policy['classifier'] / name).relative_to(ROOT)).replace('\\', '/'): value
                    for name, value in runtime.parent_checksums.items()}
    index_dir = ROOT / runtime.policy['retrieval']
    for path in index_dir.iterdir():
        if path.is_file():
            parent_files[path.relative_to(ROOT).as_posix()] = sha(path)
    if runtime.policy.get('parent_verifier'):
        for path in (ROOT / runtime.policy['parent_verifier']).rglob('*'):
            if path.is_file():
                parent_files[path.relative_to(ROOT).as_posix()] = sha(path)
    source_files = {**runtime.source['source_sha256'], **runtime.source['raw_source_sha256']}
    from test_verifier import VerifierTests
    import test_logical_classifier
    import test_retrieval
    test_logical_classifier.RUN = ROOT / runtime.policy['classifier']
    test_retrieval.INDEX = index_dir
    tests = {'item12': suite(VerifierTests, output, 'item12_tests')}
    # One existing classifier test exports its regression predictions. Redirect
    # that export into this new packet instead of rewriting its frozen parent.
    with patch.object(test_logical_classifier, 'save', side_effect=lambda path, value: save(output / ('parent_' + Path(path).name), value)):
        tests['classifier_regression'] = suite(test_logical_classifier.LogicalTests, output, 'classifier_tests')
    # The historical Item 11 CLI expects UTF-8 mode in this Windows environment.
    with patch.dict(os.environ, {'PYTHONUTF8': '1'}):
        tests['retrieval_regression'] = suite(test_retrieval.RetrievalTests, output, 'retrieval_tests')
    save(output / 'software_tests.json', tests)
    fixtures, results, metrics = evaluate(runtime)
    save(output / 'development_cases.json', fixtures)
    save(output / 'development_results.json', results)
    save(output / 'metrics.json', metrics)
    changed = [path for path, expected in {**parent_files, **source_files}.items() if sha(ROOT / path) != expected]
    save(output / 'preservation_audit.json', {'parent_artifacts_checked': len(parent_files),
         'source_files_checked': len(source_files), 'changed_files': changed, 'passed': not changed,
         'parent_artifact_sha256': parent_files, 'source_sha256': source_files})
    if changed or not all(v['passed'] for v in tests.values()) or metrics['passed'] != metrics['total']:
        raise ValueError('Build checks failed; inspect logs. Current artifact pointers were not changed.')
    examples = []
    for q, preferred in [(LABOR, {'labor': ARTICLE_83}), (PRICE, {'consumer': ARTICLE_81}), (MIXED, None)]:
        draft = excerpt(runtime, q, preferred=preferred)
        examples.append({'question_text': q, 'draft': draft,
            'recorded_excerpt_verification': runtime.verify(q, draft, 'recorded_excerpt'),
            'current_guidance_preflight': runtime.preflight(q)})
    save(output / 'examples.json', examples)
    schemas = output / 'schemas'
    schemas.mkdir()
    for name, value in [('draft', DRAFT_SCHEMA), ('reviews', REVIEW_STORE_SCHEMA), ('preflight', PREFLIGHT_SCHEMA), ('result', RESULT_SCHEMA)]:
        save(schemas / (name + '.schema.json'), value)
    snapshot = output / 'source_snapshot'
    snapshot.mkdir()
    for path in HERE.iterdir():
        if path.is_file() and path.suffix in {'.py', '.json', '.md'}:
            shutil.copyfile(path, snapshot / path.name)
    card = {'version': runtime.policy['version'], 'as_of': AS_OF,
        'implementation': 'Deterministic citation/provenance/context checks plus scoped trusted-review gates.',
        'automated_paraphrase_entailment_model': False, 'current_guidance_real_reviews': 0,
        'source_data_modified': False, 'classifier_weights_modified': False, 'no_new_training_data': True,
        'development_fixture_count': len(fixtures), 'independent_human_gold': False,
        'software_reviews_are_simulated': True, 'review_identity_authenticated_by_software': False,
        'deployment_allowed': False, 'answer_generation_allowed': False, 'display_allowed': False,
        'source_currentness_refreshed': False,
        'supported_modes': ['recorded_excerpt', 'current_guidance'],
        'limitations': ['Exact quotes do not prove relevance, currentness or answer completeness.',
            'Arbitrary paraphrases need scoped operator-managed review; no automatic legal-entailment claim.',
            'No real current-guidance review exists; default gate therefore blocks.',
            'Minimum authority dependencies are incomplete by design; recorded conditions still need review.',
            'Hand-authored development controls cannot establish real-world accuracy.',
            'No external LLM adapter, frontend connection or production answering was enabled.']}
    save(output / 'VERIFIER_CARD.json', card)
    save(output / 'dataset_inventory_addendum.json', {
        'new_canonical_authorities': 0, 'new_training_questions': 0, 'new_independent_human_questions': 0,
        'ai_authored_development_controls': len(fixtures), 'simulated_review_positive_controls': 2,
        'same_legal_source_index': runtime.policy['retrieval'],
        'role': 'Software verification development; not a new independent evaluation set.'})
    manifest = {'version': runtime.policy['version'], 'status': 'offline_implementation_tested', 'as_of': AS_OF,
        'classifier': runtime.policy['classifier'], 'retrieval': runtime.policy['retrieval'],
        'source_snapshot_is_executable_in_original_project_layout_only': True,
        'python': platform.python_version(),
        'dependencies': {name: importlib.metadata.version(name) for name in ['numpy', 'scikit-learn', 'joblib', 'fastembed']},
        'tests': tests, 'development_cases': metrics['total'], 'development_cases_passed': metrics['passed'],
        'all_project_issues_closed': False, 'deployment_allowed': False, 'answer_generation_allowed': False,
        'live_llm_calls': 0, 'legal_status_refreshed': False, 'independent_human_evaluation': False,
        'parent_verifier': runtime.policy.get('parent_verifier'),
        'audit_repairs': ['Reject exponent-overflow JSON numbers.',
            'Reject unknown modes and sources in the direct source gate.',
            'Refresh the default date and recheck artifacts/review snapshot on every request.',
            'Require expected surviving component identities in development metrics.'],
        'implementation_authorization': 'Project owner explicitly requested: Ok build item 12. Earlier milestone hold superseded for offline development only.',
        'runtime_source_sha256': {p.name: sha(p) for p in HERE.iterdir() if p.is_file() and p.suffix in {'.py', '.json', '.md'}}}
    save(output / 'run_manifest.json', manifest)
    g = metrics['groups']
    report = f'''# Item 12 — offline citation and evidence verification

Built and tested on **{AS_OF}** around **{runtime.policy['classifier']}** and **{runtime.policy['retrieval']}**. No LLM API was called. Live answering, user display and deployment remain disabled.

## Implemented behavior

Preflight verifies pinned artifacts, reruns the actual classifier/retriever, checks source eligibility, exact citation/text/locator metadata, recorded conditions and minimum related-authority dependencies. It preserves clarification, evidence gaps and excluded concerns.

Postflight accepts only a strict claim/evidence contract. It checks document/provision/chunk identity, retrieval membership for the concern, exact full-provision quotation/offsets and context. Current-guidance claims additionally need scoped support, relevance, qualification and concern-coverage review. A missing citation or an altered/truncated quote fails. A draft cannot supply its own approval, citation label, confidence or unchecked free-form answer.

Each concern is withheld as a unit if any of its claims fail. Independently passing concerns can produce a partial development candidate, accompanied by explicit disclosures. Preview blocks use only checked claim text and trusted citation metadata.

This revision binds the focused classifier/retrieval repairs. Verification policy is unchanged apart from version and artifact bindings. It retains rejection of JSON exponent overflow and invalid source-gate modes/candidates, default-date refresh and file/review integrity checks on every request. Explicit historical dates remain available for reproducible offline evaluation. Development metrics verify which concerns survive, in addition to their count. The previous `{runtime.policy.get('parent_verifier')}` packet is preserved.

## Validation results

| Check | Result |
|---|---:|
| Item 12 software tests | {tests['item12']['tests_run']}/{tests['item12']['tests_run']} passed |
| Existing classifier regression tests | {tests['classifier_regression']['tests_run']}/{tests['classifier_regression']['tests_run']} passed |
| Existing retrieval regression tests | {tests['retrieval_regression']['tests_run']}/{tests['retrieval_regression']['tests_run']} passed |
| Total AI development scenarios | {metrics['passed']}/{metrics['total']} met expected behavior |
| Valid exact-excerpt controls | {g['valid_excerpt_control']['passed']}/{g['valid_excerpt_control']['total']} accepted as intended |
| Adversarial/withholding controls | {g['adversarial']['passed']}/{g['adversarial']['total']} handled as intended |
| Simulated review positive controls | {g['simulated_review_control']['passed']}/{g['simulated_review_control']['total']} exercised successful review paths |
| Real default current-guidance gate | Blocks without source/claim reviews, as required |
| Frozen parent and source files | {len(parent_files)} parent files + {len(source_files)} source files checked; 0 changed |

Controls cover fabricated citations, wrong documents/provisions, altered quotations, bad/boolean/fractional offsets, removed qualifications, invented remedies, negation, unchecked text, cross-domain citations, excluded concerns, missing mixed components, failing sibling claims, currentness gaps, expired/future reviews and mismatched source/condition/relationship/question/policy/index hashes. Positive controls prevent an always-blocking verifier from passing the suite. CLI execution was tested outside the repository, including UTF-8 output and rejection of simulated approvals. BM25 verification also passed with network/semantic calls disabled by test stubs.

These are **AI-authored, inspected software-development controls**, not independent human/legal gold. The descriptive Wilson 95% interval is {g['adversarial']['wilson_95_interval'][0]:.1%}–100% for the adversarial controls and {g['valid_excerpt_control']['wilson_95_interval'][0]:.1%}–100% for the four valid-excerpt controls. Related fixtures are dependent; these intervals do not measure legal accuracy, generator bias or real-world confidence. Existing label probabilities and retrieval ranking remain separate. No combined legal-answer confidence is reported.

## Current limits

**Recorded-excerpt mode verifies provenance only.** It does not determine whether a retrieved provision answers the question, applies today, or supplies enough evidence. Full provision text preserves local qualifications; broader applicability still needs judgment.

**Current-guidance mode currently blocks.** The normal trusted review store has zero reviews. A recent source status date is not certification of currentness. Two isolated positive tests use explicitly simulated review records; normal runtime/CLI rejects those records. No human review or professional approval was fabricated.

**Paraphrase checking is a review gate.** Arbitrary legal entailment is not automatically solved by this implementation. Current-guidance approval must bind the exact claim, evidence, concern, source conditions, index and policy. A future service must keep this operator configuration inaccessible to draft/end-user input and authenticate reviewers separately.

Final-pay/COE evidence remains unavailable. MO 28, thirteenth-month guidance, DTI procedure/source review, independent human evaluation, contact follow-up and formal approvals remain open as documented in the prior repair/follow-up packets. The original canonical files, reviewed seed, model weights and evaluated parent versions remain preserved. Frozen-workbook validation is performed separately from this packet builder; source preservation is checked here.

## Next step

Rerun **Item 13 system-level development evaluation** on the frozen cases and unchanged screening targets. Actual generated-answer scoring, independent human questions and licensed Philippine legal review remain separate pending work. An LLM adapter and UI integration are later work. The project owner's offline implementation authorization does not close the remaining legal/data/approval prerequisites.

## Files

- `metrics.json`, `development_cases.json`, `development_results.json`: full expectations, decisions and reasons.
- `software_tests.json` and three test logs: software/regression evidence.
- `examples.json`: real exact-quote previews and blocked current-guidance preflights.
- `schemas/`, `source_snapshot/`, `run_manifest.json`, `VERIFIER_CARD.json`: contracts, provenance and limits.
- `preservation_audit.json`, `artifact_checksums.json`: frozen-parent/source integrity and packet hashes.

Executable commands and review contracts: [pipeline README](C:/IA/dataset/pipelines/item12/README.md).
'''
    (output / 'VERIFICATION_REPORT.md').write_text(report, encoding='utf-8')
    save(output / 'artifact_checksums.json', {p.relative_to(output).as_posix(): sha(p) for p in sorted(output.rglob('*')) if p.is_file()})
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output.resolve()), indent=2))
