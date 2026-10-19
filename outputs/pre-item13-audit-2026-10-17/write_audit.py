"""Assemble the pre-Item-13 audit from executed check receipts and frozen packets."""
import csv
import difflib
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


current = read(ROOT / 'CURRENT_ARTIFACTS.json')
packet = ROOT / current['verifier']
manifest = read(packet / 'run_manifest.json')
metrics = read(packet / 'metrics.json')
preservation = read(packet / 'preservation_audit.json')
checks = read(OUT / 'session_checks.json')
foundation = read(OUT / 'foundation_checks.json')
integration = read(OUT / 'integration_summary.json')
policy = read(ROOT / 'dataset/pipelines/item12/policy.json')
assert packet.name == policy['version'] == manifest['version']
assert current['classifier'] == policy['classifier'] == manifest['classifier']
assert current['retrieval'] == policy['retrieval'] == manifest['retrieval']
assert not any(current[k] for k in ['deployment_allowed', 'answer_generation_allowed', 'current_guidance_allowed', 'item13_started'])
assert all(v['passed'] and v['failures'] == v['errors'] == 0 for v in manifest['tests'].values())
assert metrics['passed'] == metrics['total'] == 50
assert all(v['passed'] for v in foundation.values())
assert checks['frozen_reviewed_dataset']['status'] == 'passed'
assert all(v['passed'] for v in checks['supporting_tests'])
assert all(checks['frontend_checks'][name]['passed'] for name in ['typescript_build', 'vite_build', 'lint'])
assert integration['passed'] == integration['total'] == 67
assert integration['current_guidance_candidates_permitted'] == 0

groups = {
    'current_verifier_packet': (packet, read(packet / 'artifact_checksums.json')),
    'current_verifier_runtime': (ROOT / 'dataset/pipelines/item12', manifest['runtime_source_sha256']),
    'preserved_parent_artifacts': (ROOT, preservation['parent_artifact_sha256']),
    'legal_source_files': (ROOT, preservation['source_sha256']),
}
seed = ROOT / 'dataset/processed/item10/reviewed_v1.0.0'
seed_manifest = read(seed / 'dataset_manifest.json')
groups['frozen_reviewed_seed'] = (seed, seed_manifest['files_sha256'])
groups['cleaned_human_review_workbooks'] = (ROOT / 'outputs/item10-review-cleaned', seed_manifest['cleaned_workbooks_sha256'])
integrity = {}
for name, (base, hashes) in groups.items():
    mismatches = [path for path, expected in hashes.items() if not (base / path).is_file() or sha(base / path) != expected]
    integrity[name] = {'checked': len(hashes), 'mismatches': mismatches, 'passed': not mismatches}
assert all(v['passed'] for v in integrity.values()), integrity
save('final_integrity.json', integrity)

sys.path.insert(0, str(ROOT / 'dataset/pipelines/item10'))
from validate_independent_gold import validate
intake_path = ROOT / 'outputs/pre-item12-repair-2026-10-17/human_gold_intake.jsonl'
intake = [json.loads(line) for line in intake_path.read_text(encoding='utf-8').splitlines() if line.strip()]
intake_result = validate(intake)
assert sum(bool(r.get('question_text')) for r in intake) == 0 and not intake_result['passed']
save('independent_intake_check.json', {'rows': len(intake), 'authored_questions': 0,
    'correctly_withheld_from_final_evaluation': True, 'validator_result': intake_result})
reviews = read(ROOT / 'dataset/pipelines/item12/trusted_reviews.json')
assert not reviews['source_reviews'] and not reviews['claim_reviews']

old = ROOT / 'outputs/item12-verifier-v1.0.0/source_snapshot'
changes = []
for path in sorted(old.iterdir()):
    if path.is_file() and (ROOT / 'dataset/pipelines/item12' / path.name).is_file():
        changes.extend(difflib.unified_diff(path.read_text(encoding='utf-8').splitlines(True),
            (ROOT / 'dataset/pipelines/item12' / path.name).read_text(encoding='utf-8').splitlines(True),
            fromfile='v1.0.0/' + path.name, tofile='v1.0.1/' + path.name))
(OUT / 'ITEM12_CHANGES.patch').write_text(''.join(changes), encoding='utf-8')

readiness = {'as_of': '2026-10-17', 'verifier': current['verifier'],
    'audited_software_checks_passed': True, 'item13_offline_evaluation_ready': True,
    'item13_started': False, 'item13_full_generated_answer_evaluation_ready': False,
    'all_project_issues_closed': False, 'production_ready': False,
    'deployment_allowed': False, 'answer_generation_allowed': False,
    'independent_human_questions_available': 0, 'trusted_source_reviews': 0, 'trusted_claim_reviews': 0,
    'remaining_work': [
        {'issue': 'Independent human evaluation and real-world calibration', 'status': 'open',
         'detail': 'The 200 existing AI-reviewed questions remain development material. The 100-row independent intake is blank.'},
        {'issue': 'Source coverage/extraction approval', 'status': 'open',
         'detail': 'Final pay/COE has no eligible evidence; MO 28 and applicable thirteenth-month guidance remain unresolved. DTI/final-pay AI copies remain gated; the original 258-entry human queue remains.'},
        {'issue': 'Legal currentness and proposition support', 'status': 'open',
         'detail': 'No real scoped source/claim reviews exist. Exact-source previews verify provenance only; arbitrary paraphrases are a review gate, not automatic entailment.'},
        {'issue': 'Actual generated-answer evaluation', 'status': 'not_yet_ready',
         'detail': 'No LLM drafter is connected. Prepare the offline evaluation protocol now; generated-answer quality needs a controlled drafter and the relevant source/support conditions resolved.'},
        {'issue': 'Referral-contact completion and application integration', 'status': 'partial_or_future_work',
         'detail': 'The refreshed directory corroborates 36 fields across 15 of 19 entries; four remain unresolved. The classifier still uses its frozen directory. UI/backend/history integration is future Item 14 work.'},
        {'issue': 'Independent legal review and formal acceptance', 'status': 'external_review_pending',
         'detail': 'Licensed Philippine legal review of selected generated answers and required team/adviser acceptance are not recorded.'}
    ]}
save('readiness.json', readiness)
ledger = read(ROOT / 'outputs/pre-item12-repair-2026-10-17/issue_ledger.json')
ledger.update(as_of='2026-10-17', historical_parent='outputs/pre-item12-repair-2026-10-17/issue_ledger.json',
              item12_started=True, proceed_to_item12_under_owner_instruction=True,
              item13_started=False, item13_offline_evaluation_ready=True,
              item13_full_generated_answer_evaluation_ready=False,
              current_verifier=current['verifier'], all_issues_closed=False)
for issue in ledger['issues']:
    if issue['id'] == 11:
        issue.update(status='offline_verifier_implemented_and_audited', software_tests=37,
                     development_scenarios=50, real_current_guidance_reviews=0)
    if issue['id'] == 10:
        issue.update(status='partial_followup_currentness_and_four_contacts_still_open',
                     corroborated_contact_fields=36, agencies_with_confirmed_fields=15, total_agencies=19)
ledger['remaining_work'] = readiness['remaining_work']
save('current_issue_ledger.json', ledger)

report = f'''# Pre-Item-13 project audit — 17 October 2026

**The audited software is ready to begin offline Item 13 evaluation. Full generated-answer evaluation, formal acceptance and deployment are not ready. Item 13 has not started.**

Current artifacts: classifier **v1.5.4**, retrieval **v1.2.3**, verifier **v1.0.1**. The preceding v1.0.0 verifier packet, legal sources, model artifacts and frozen reviewed data are preserved. No LLM API calls, invented human approvals or source promotions occurred.

## Issues found and repaired

1. Strict JSON parsing rejected literal Infinity/NaN but allowed an exponent such as `1e1000` to overflow. It now rejects overflow while retaining finite JSON numbers.
2. The direct source-check helper treated an unknown mode as excerpt mode and raised an unstructured key error for unknown sources. It now explicitly rejects both. Normal CLI modes were already constrained; this repair hardens direct use.
3. Default verifier dates and artifact integrity were checked only at construction. Each new request now refreshes the default date, verifies source/index/model/runtime files and detects review-store mutation. Tests confirm expired approvals stop passing after date rollover and that changed files fail even if their timestamp is preserved. Explicit historical dates still work for reproducible offline evaluation.
4. Development acceptance checks compared concern counts. They now compare the surviving concern IDs too, so accepting the wrong side of a mixed question cannot satisfy the expectation.

These repairs are saved in a new version. [Review the code changes](C:/IA/outputs/pre-item13-audit-2026-10-17/ITEM12_CHANGES.patch). Historical status records remain unchanged; the new current ledger supersedes their old Item 12 hold.

## Checks executed

| Area | Result |
|---|---:|
| Item 7 source/provision/chunk contracts | Passed; reports redirected out of frozen data |
| Item 8 discovery-only gates and tables | Passed |
| Item 9 original seed/referral contracts | Passed |
| Frozen reviewed seed, splits, workbook formulas/native structure/provenance | 59/59 checks passed |
| Current classifier regression suite | 49/49 passed |
| Current retrieval regression suite | 38/38 passed |
| Repaired verifier software suite | 37/37 passed |
| Source/parser/contact/independent-intake supporting suites | 17/17 passed |
| AI verifier development scenarios | 50/50 met expected behavior |
| Existing retrieval cases through actual classifier → retrieval → verifier | 56/56 positive and 11/11 negative cases passed |
| Frontend TypeScript, Vite production build and lint | Passed |
| Independent human intake | Correctly rejected: 100 blank forms, 0 authored questions |
| Default current-guidance permissions on reused 67 cases | 0 permitted, because actual scoped reviews are missing |

The 56 positive retrieval cases reuse 28 English/Taglish scenario families. The same existing questions and inspected AI relevance judgments were reused, not converted into new independent data. For the audit's positive excerpt path, a known-relevant retrieved provision was selected using the existing development label; passing proves text/citation integrity, not automatic semantic selection or legal-answer correctness.

`final_integrity.json` confirms {integrity['current_verifier_packet']['checked']} current packet files, {integrity['current_verifier_runtime']['checked']} current verifier source/configuration files, {integrity['preserved_parent_artifacts']['checked']} preserved parent files and {integrity['legal_source_files']['checked']} legal-source files match their hashes. The frozen seed and all five cleaned human-review workbooks also match their manifest hashes. No mismatches were found. Legacy validators' reports were redirected into this audit folder; original validation reports were not overwritten.

Frontend checks establish compilation/lint success for the existing scripted prototype. No new browser visual/accessibility audit, production backend connection or deployment was performed. The broad discovery corpus was not recrawled, and official legal/contact pages were not newly certified current by this audit.

## Remaining work and readiness

- **Independent human evaluation:** zero fresh independent questions have been supplied. The existing 200 AI-reviewed questions remain development material. Real-world accuracy and calibration still need independent evidence.
- **Legal sources:** final-pay/COE, MO 28, applicable thirteenth-month guidance and DTI/Consumer IRR review gaps remain. AI-repaired copies have not been silently promoted; the original 258-entry human source queue remains.
- **Currentness and support:** zero real scoped source/claim approvals exist. Current-guidance mode deliberately blocks. Exact excerpt checks do not establish relevance, currentness or sufficient legal support; arbitrary paraphrase checking is a review gate.
- **Answer generation:** there is no connected LLM drafter. Software/citation/decline evaluation can start now; substantive generated-answer metrics cannot be completed until a controlled drafting component and relevant source/support approvals are available.
- **Contacts and application:** 36 fields across 15 of 19 agencies have corroboration; four entries remain unresolved, and the current classifier still uses its frozen directory. Live UI/backend/history integration belongs to Item 14.
- **Acceptance:** required team/adviser acceptance and the proposal's licensed Philippine legal review of selected generated answers remain pending.

An all-declining system cannot be called accurate merely because no unsupported answer was emitted. Item 13 must report answer coverage and false declines, and leave substantive answer metrics unavailable when their denominator is zero. Classifier probabilities, retrieval ranking and legal-support judgments stay separate.

## What can happen next

Prepare Item 13's offline evaluation protocol, grouped scenarios/expected authorities, runner and result table. Keep development material separate from the final independent holdout and freeze final-test criteria before opening results. Evaluate classification, retrieval, citation consistency, mixed concerns and clarification/referral behavior first. Add actual generated-answer evaluation only when its stated dependencies are satisfied.

[Item 13 explained](C:/IA/outputs/pre-item13-audit-2026-10-17/ITEM13_EXPLAINED.md). [Readiness status](C:/IA/outputs/pre-item13-audit-2026-10-17/readiness.json). [Current issue ledger](C:/IA/outputs/pre-item13-audit-2026-10-17/current_issue_ledger.json). [Verifier report](C:/IA/outputs/item12-verifier-v1.0.1/VERIFICATION_REPORT.md).
'''
(OUT / 'PRE_ITEM13_AUDIT.md').write_text(report, encoding='utf-8')
save('audit_manifest.json', {'as_of': '2026-10-17', 'current_artifacts': current,
    'current_artifacts_sha256': sha(ROOT / 'CURRENT_ARTIFACTS.json'),
    'documentation_sha256': {name: sha(ROOT / name) for name in ['README.md', 'dataset/DATASET_INVENTORY.md']},
    'verifier_manifest_sha256': sha(packet / 'run_manifest.json'),
    'ready_for_offline_item13': True, 'ready_for_full_generated_answer_evaluation': False,
    'new_independent_gold_questions': 0, 'live_llm_calls': 0, 'deployment_allowed': False})
save('artifact_checksums.json', {p.relative_to(OUT).as_posix(): sha(p) for p in sorted(OUT.rglob('*'))
    if p.is_file() and p.name != 'artifact_checksums.json'})
print(json.dumps({'offline_item13_ready': True, 'item13_started': False,
                  'full_generated_answer_evaluation_ready': False, 'integrity_groups': integrity}, indent=2))
