"""Small, dependency-free validators for the published Item 12 JSON contracts."""
from __future__ import annotations

import json
import math
from pathlib import Path


class ContractError(ValueError):
    pass


def strict_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ContractError('Duplicate JSON key: ' + key)
            result[key] = value
        return result

    def constant(value):
        raise ContractError('Non-finite JSON number: ' + value)

    def finite_float(value):
        result = float(value)
        if not math.isfinite(result):
            raise ContractError('Non-finite JSON number: ' + value)
        return result

    return json.loads(Path(path).read_text(encoding='utf-8'),
                      object_pairs_hook=pairs, parse_constant=constant, parse_float=finite_float)


def validate(value, schema, path='$'):
    """Validate the deliberately small JSON Schema subset used by this package.

    Published schemas also work with a full Draft 2020-12 validator. This is not
    a general JSON Schema implementation; unknown schema keywords are an error.
    """
    known = {'$schema', 'title', 'description', 'type', 'properties', 'required',
             'additionalProperties', 'items', 'minItems', 'maxItems', 'minLength',
             'maxLength', 'minimum', 'maximum', 'enum', 'const'}
    if set(schema) - known:
        raise ContractError('Unsupported schema keywords')
    kinds = {'object': lambda x: type(x) is dict, 'array': lambda x: type(x) is list,
             'string': lambda x: type(x) is str, 'integer': lambda x: type(x) is int,
             'boolean': lambda x: type(x) is bool, 'null': lambda x: x is None}
    kind = schema.get('type')
    if kind and (kind not in kinds or not kinds[kind](value)):
        raise ContractError(f'{path}: expected {kind}')
    if 'enum' in schema and value not in schema['enum']:
        raise ContractError(f'{path}: invalid enum value')
    if 'const' in schema and (type(value) is not type(schema['const']) or value != schema['const']):
        raise ContractError(f'{path}: invalid constant')
    if type(value) is dict:
        props = schema.get('properties', {})
        missing = set(schema.get('required', [])) - set(value)
        if missing:
            raise ContractError(f'{path}: missing {sorted(missing)}')
        if schema.get('additionalProperties') is False and set(value) - set(props):
            raise ContractError(f'{path}: unexpected fields {sorted(set(value) - set(props))}')
        for key in value.keys() & props.keys():
            validate(value[key], props[key], path + '.' + key)
    if type(value) is list:
        if len(value) < schema.get('minItems', 0) or len(value) > schema.get('maxItems', float('inf')):
            raise ContractError(f'{path}: invalid array length')
        for i, item in enumerate(value):
            validate(item, schema.get('items', {}), f'{path}[{i}]')
    if type(value) is str:
        if len(value) < schema.get('minLength', 0) or len(value) > schema.get('maxLength', float('inf')):
            raise ContractError(f'{path}: invalid string length')
    if type(value) is int:
        if value < schema.get('minimum', -float('inf')) or value > schema.get('maximum', float('inf')):
            raise ContractError(f'{path}: number outside bounds')


def obj(properties, required=None):
    return {'type': 'object', 'properties': properties, 'required': list(properties) if required is None else required,
            'additionalProperties': False}


TEXT = {'type': 'string', 'minLength': 1, 'maxLength': 100000}
ID = {'type': 'string', 'minLength': 1, 'maxLength': 200}
HASH = {'type': 'string', 'minLength': 64, 'maxLength': 64}
DATE = {'type': 'string', 'minLength': 10, 'maxLength': 10}
TRUE = {'type': 'boolean', 'const': True}
EVIDENCE_SCHEMA = obj({
    'chunk_id': ID, 'provision_id': ID, 'document_id': ID,
    'start': {'type': 'integer', 'minimum': 0},
    'end': {'type': 'integer', 'minimum': 1}, 'quote': TEXT,
})
CLAIM_SCHEMA = obj({
    'claim_id': ID, 'component_id': ID,
    'kind': {'type': 'string', 'enum': ['source_excerpt', 'paraphrase']},
    'text': TEXT,
    'evidence': {'type': 'array', 'minItems': 1, 'maxItems': 8, 'items': EVIDENCE_SCHEMA},
})
DRAFT_SCHEMA = {
    '$schema': 'https://json-schema.org/draft/2020-12/schema',
    'title': 'Item 12 structured draft (no unchecked free-form answer)',
    **obj({'schema_version': {'type': 'string', 'const': '1.0'},
           'question_text': {'type': 'string', 'minLength': 1, 'maxLength': 10000},
           'claims': {'type': 'array', 'minItems': 1, 'maxItems': 50, 'items': CLAIM_SCHEMA}}),
}

REVIEW_BASE = {
    'review_id': ID,
    'review_kind': {'type': 'string', 'enum': ['legal_professional_review', 'software_fixture']},
    'reviewer': ID, 'reviewed_on': DATE, 'valid_through': DATE,
    'index_version': ID, 'policy_sha256': HASH,
    'question_sha256': HASH, 'component_sha256': HASH, 'rationale': TEXT,
}
SOURCE_REVIEW_SCHEMA = obj({**REVIEW_BASE, 'document_id': ID, 'raw_source_sha256': HASH,
    'conditions_sha256': HASH, 'related_sources_sha256': HASH,
    'currentness_checked': TRUE, 'conditions_resolved': TRUE, 'relationships_checked': TRUE,
    'evidence_urls': {'type': 'array', 'minItems': 1, 'maxItems': 20, 'items': TEXT}})
CLAIM_REVIEW_SCHEMA = obj({**REVIEW_BASE, 'claim_sha256': HASH, 'evidence_sha256': HASH,
    'supports_claim': TRUE, 'relevant_to_concern': TRUE, 'qualifications_preserved': TRUE,
    'covers_concern': TRUE})
REVIEW_STORE_SCHEMA = {
    '$schema': 'https://json-schema.org/draft/2020-12/schema',
    'title': 'Operator-managed scoped reviews; never part of an LLM draft',
    **obj({'schema_version': {'type': 'string', 'const': '1.0'},
           'source_reviews': {'type': 'array', 'maxItems': 10000, 'items': SOURCE_REVIEW_SCHEMA},
           'claim_reviews': {'type': 'array', 'maxItems': 10000, 'items': CLAIM_REVIEW_SCHEMA}}),
}

# Output contracts pin the envelope. Nested diagnostics are emitted by trusted
# code; the input contracts above validate every untrusted claim/evidence field.
OUTPUT_BASE = {
    'schema_version': {'type': 'string', 'const': '1.0'}, 'verifier_version': ID,
    'question_text': TEXT, 'question_sha256': HASH,
    'mode': {'type': 'string', 'enum': ['current_guidance', 'recorded_excerpt']}, 'as_of': DATE,
    'classifier_version': ID, 'index_version': ID, 'policy_sha256': HASH, 'review_store_sha256': HASH,
    'software_fixture_mode': {'type': 'boolean'},
    'answer_generation_allowed': {'type': 'boolean', 'const': False},
    'deployment_allowed': {'type': 'boolean', 'const': False},
    'display_allowed': {'type': 'boolean', 'const': False}, 'confidence_meaning': TEXT,
    'routing': {'type': 'object'}, 'excluded_components': {'type': 'array'}, 'referral_ids': {'type': 'array'},
    'components': {'type': 'array', 'items': {'type': 'object'}}, 'decision': ID,
}
PREFLIGHT_SCHEMA = {'$schema': 'https://json-schema.org/draft/2020-12/schema',
    'title': 'Item 12 preflight envelope', **obj({**OUTPUT_BASE,
    'offline_drafting_allowed': {'type': 'boolean'}, 'all_supported_components_evidence_ready': {'type': 'boolean'}})}
RESULT_SCHEMA = {'$schema': 'https://json-schema.org/draft/2020-12/schema',
    'title': 'Item 12 postflight envelope', **obj({**OUTPUT_BASE,
    'claim_results': {'type': 'array', 'items': {'type': 'object'}}, 'coverage': {'type': 'object'},
    'offline_preview_allowed': {'type': 'boolean'}, 'preview': {'type': 'array', 'items': {'type': 'object'}},
    'legal_support_verified': {'type': 'boolean'}, 'legal_support_review_recorded': {'type': 'boolean'},
    'disclosures': {'type': 'array', 'items': TEXT}, 'contract_errors': {'type': 'array', 'items': TEXT}},
    required=list(OUTPUT_BASE) + ['claim_results', 'coverage', 'offline_preview_allowed', 'preview',
                                 'legal_support_verified', 'legal_support_review_recorded'])}
