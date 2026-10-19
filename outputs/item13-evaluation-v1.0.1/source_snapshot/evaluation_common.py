"""Local paths, strict input readers and immutable evaluation-packet helpers."""
from __future__ import annotations
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'dataset/pipelines/item12'))
sys.path.insert(0, str(ROOT / 'dataset/pipelines/item10'))
from contracts import ContractError, obj, validate, ID, TEXT, HASH


def decode(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ContractError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def finite(value):
        result = float(value)
        if not math.isfinite(result):
            raise ContractError('Non-finite number')
        return result
    def bad(value):
        raise ContractError('Non-finite number: ' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_float=finite, parse_constant=bad)


def read(path):
    return decode(Path(path).read_text(encoding='utf-8'))


def rows(path):
    return [decode(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def jsonl(path, values):
    Path(path).write_text(''.join(json.dumps(v, ensure_ascii=False, sort_keys=True, allow_nan=False) + '\n' for v in values), encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def normalize(text):
    import re
    return ' '.join(re.findall(r'\w+', text.casefold()))


PRIMARY = ['labor', 'consumer', 'mixed', 'out_of_scope']
SCOPE = ['fully_supported', 'partially_supported', 'unsupported']
PAIRS = {('labor', 'fully_supported'), ('consumer', 'fully_supported'), ('mixed', 'fully_supported'),
         ('mixed', 'partially_supported'), ('out_of_scope', 'unsupported')}
ROUTES = ['retrieve_supported_evidence', 'retrieve_supported_components', 'refer_out_of_scope', 'clarify']
CONCERN_SCHEMA = obj({'domain': {'enum': ['labor', 'consumer', 'excluded']},
    'anchors': {'type': 'array', 'minItems': 1, 'items': TEXT},
    'relevant_ids': {'type': 'array', 'items': ID}, 'evidence_gap': {'type': 'boolean'}})
CASE_SCHEMA = {'$schema': 'https://json-schema.org/draft/2020-12/schema', **obj({
    'case_id': ID, 'suite': {'enum': ['general', 'typing', 'retrieval', 'system']},
    'family_id': ID, 'question_text': TEXT, 'language': {'enum': ['en', 'en_tl']}, 'variation': ID,
    'origin': {'const': 'ai_authored'}, 'role': {'const': 'development'},
    'source_path': TEXT, 'source_record_id': ID,
    'expected_primary': {'enum': PRIMARY + [None]}, 'expected_scope': {'enum': SCOPE + [None]},
    'expected_route': {'enum': ROUTES}, 'expected_clarification_reason': {'enum': [None,
        'employment_category_missing', 'refund_transaction_missing', 'contract_relationship_missing', 'charge_context_missing']},
    'expected_domains': {'type': 'array', 'items': {'enum': ['labor', 'consumer']}},
    'expected_excluded': {'type': 'boolean'}, 'topic_ids': {'type': 'array', 'items': ID},
    'relevant_ids': {'type': 'array', 'items': ID},
    'retrieval_judgment': {'enum': ['known_relevant', 'no_candidates', 'unjudged']},
    'concerns': {'type': 'array', 'items': CONCERN_SCHEMA},
})}


def validate_cases(cases, eligible_ids=None):
    ids, texts, family_roles = set(), set(), {}
    if not cases:
        raise ContractError('Evaluation cases are empty')
    for case in cases:
        validate(case, CASE_SCHEMA)
        if (case['expected_primary'], case['expected_scope']) not in PAIRS | {(None, None)}:
            raise ContractError('Inconsistent primary/scope expectation')
        if case['expected_primary'] is None and case['expected_route'] != 'clarify':
            raise ContractError('Unlabeled questions must expect clarification')
        if case['case_id'] in ids or normalize(case['question_text']) in texts:
            raise ContractError('Duplicate case ID or normalized question')
        ids.add(case['case_id']); texts.add(normalize(case['question_text']))
        if case['family_id'] in family_roles and family_roles[case['family_id']] != case['role']:
            raise ContractError('Scenario family crosses evaluation roles')
        family_roles[case['family_id']] = case['role']
        if case['retrieval_judgment'] == 'known_relevant' and not case['relevant_ids']:
            raise ContractError('Known relevance needs provision IDs')
        if case['retrieval_judgment'] != 'known_relevant' and case['relevant_ids']:
            raise ContractError('Unjudged/negative cases cannot claim known relevant IDs')
        refs = set(case['relevant_ids']) | {p for c in case['concerns'] for p in c['relevant_ids']}
        if eligible_ids is not None and refs - set(eligible_ids):
            raise ContractError('Expected provision is absent/ineligible: ' + str(sorted(refs - set(eligible_ids))))


def verify_packet(path, runtime=False):
    path = Path(path)
    for name, expected in read(path / 'artifact_checksums.json').items():
        if sha(path / name) != expected:
            raise ValueError('Frozen packet changed: ' + str(path / name))
    if runtime:
        for name, expected in read(path / 'run_manifest.json')['runtime_source_sha256'].items():
            if sha(ROOT / 'dataset/pipelines/item12' / name) != expected:
                raise ValueError('Verifier runtime does not match pinned packet: ' + name)
