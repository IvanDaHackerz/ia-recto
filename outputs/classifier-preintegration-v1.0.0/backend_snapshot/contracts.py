"""Strict versioned classifier API input and JSON schemas."""
from __future__ import annotations
import json
import math
import re

MAX_CHARACTERS = 8000
MAX_BODY_BYTES = 65536
SCHEMA_VERSION = '1.0'


class RequestError(ValueError):
    def __init__(self, code, message, status=400):
        super().__init__(message)
        self.code, self.status = code, status


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise RequestError('invalid_json', 'Duplicate JSON keys are not allowed.')
            result[key] = value
        return result
    def finite(value):
        number = float(value)
        if not math.isfinite(number):
            raise RequestError('invalid_json', 'Non-finite JSON numbers are not allowed.')
        return number
    def bad(value):
        raise RequestError('invalid_json', 'Non-finite JSON numbers are not allowed.')
    try:
        return json.loads(text, object_pairs_hook=pairs, parse_float=finite, parse_constant=bad)
    except (json.JSONDecodeError, RecursionError, UnicodeError, ValueError) as error:
        if isinstance(error, RequestError):
            raise
        raise RequestError('invalid_json', 'Request must contain valid UTF-8 JSON.') from None


def validate_request(value):
    if not isinstance(value, dict) or set(value) - {'question_text', 'request_id'}:
        raise RequestError('invalid_request', 'Use only question_text and an optional request_id.')
    text = value.get('question_text')
    if not isinstance(text, str):
        raise RequestError('invalid_question', 'question_text must be a string.')
    if len(text) > MAX_CHARACTERS:
        raise RequestError('question_too_long', f'question_text exceeds {MAX_CHARACTERS} characters.', 413)
    if any((ord(c) < 32 and c not in '\t\n\r') or 0xD800 <= ord(c) <= 0xDFFF or ord(c) == 127 for c in text):
        raise RequestError('invalid_question', 'question_text contains unsupported control characters.')
    rid = value.get('request_id')
    if 'request_id' in value and (not isinstance(rid, str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,64}', rid)):
        raise RequestError('invalid_request_id', 'request_id must be 1–64 letters, digits, dots, colons, underscores or hyphens.')
    return text, rid


def validate_contract(value, schema, path='$'):
    """Validate the exact schema subset published by this adapter."""
    kinds={'object': lambda v:type(v) is dict, 'array':lambda v:type(v) is list,
        'string':lambda v:type(v) is str, 'null':lambda v:v is None,
        'boolean':lambda v:type(v) is bool,
        'number':lambda v:type(v) in {int,float} and math.isfinite(v)}
    kind=schema.get('type')
    if kind and not any(kinds[k](value) for k in (kind if isinstance(kind,list) else [kind])):
        raise ValueError(path+': invalid type')
    if 'const' in schema and (type(value) is not type(schema['const']) or value!=schema['const']):
        raise ValueError(path+': invalid constant')
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError(path+': invalid value')
    if type(value) is dict:
        props=schema.get('properties',{})
        if set(schema.get('required',[]))-set(value) or schema.get('additionalProperties') is False and set(value)-set(props):
            raise ValueError(path+': invalid object fields')
        for key in value.keys() & props.keys():validate_contract(value[key],props[key],path+'.'+key)
    if type(value) is list:
        for i,item in enumerate(value):validate_contract(item,schema.get('items',{}),f'{path}[{i}]')
    if type(value) is str:
        if len(value)>schema.get('maxLength',float('inf')) or 'pattern' in schema and not re.search(schema['pattern'],value):
            raise ValueError(path+': invalid string')
    if type(value) in {float,int} and (not math.isfinite(value) or value<schema.get('minimum',-float('inf')) or value>schema.get('maximum',float('inf'))):
        raise ValueError(path+': invalid number')


REQUEST_SCHEMA = {'$schema': 'https://json-schema.org/draft/2020-12/schema', 'type': 'object',
    'additionalProperties': False, 'required': ['question_text'], 'properties': {
        'question_text': {'type': 'string', 'maxLength': MAX_CHARACTERS},
        'request_id': {'type': 'string', 'pattern': '^[A-Za-z0-9_.:-]{1,64}$'}}}

RESPONSE_SCHEMA = {'$schema': 'https://json-schema.org/draft/2020-12/schema', 'type': 'object',
    'additionalProperties': False,
    'required': ['schema_version', 'request_id', 'question_text', 'question_sha256', 'model_version',
                 'classification', 'routing', 'components', 'segmentation_audit', 'permissions'],
    'properties': {
        'schema_version': {'const': SCHEMA_VERSION}, 'request_id': {'type': 'string'},
        'question_text': {'type': 'string'}, 'question_sha256': {'type': 'string', 'pattern': '^[a-f0-9]{64}$'},
        'model_version': {'type': 'string'},
        'classification': {'type': 'object', 'additionalProperties': False,
            'required': ['primary_label', 'scope_label', 'primary_confidence', 'scope_confidence',
                         'primary_probabilities', 'scope_probabilities', 'confidence_meaning'],
            'properties': {
                'primary_label': {'enum': ['labor', 'consumer', 'mixed', 'out_of_scope']},
                'scope_label': {'enum': ['fully_supported', 'partially_supported', 'unsupported']},
                'primary_confidence': {'type': 'number', 'minimum': 0, 'maximum': 1},
                'scope_confidence': {'type': 'number', 'minimum': 0, 'maximum': 1},
                'primary_probabilities': {'type': 'object', 'additionalProperties': False,
                    'required': ['labor', 'consumer', 'mixed', 'out_of_scope'],
                    'properties': {k: {'type': 'number', 'minimum': 0, 'maximum': 1}
                        for k in ['labor', 'consumer', 'mixed', 'out_of_scope']}},
                'scope_probabilities': {'type': 'object', 'additionalProperties': False,
                    'required': ['fully_supported', 'partially_supported', 'unsupported'],
                    'properties': {k: {'type': 'number', 'minimum': 0, 'maximum': 1}
                        for k in ['fully_supported', 'partially_supported', 'unsupported']}},
                'confidence_meaning': {'type': 'string'}}},
        'routing': {'type': 'object', 'additionalProperties': False,
            'required': ['action', 'reason', 'clarification_question', 'retrieval_requests', 'excluded_components', 'referral_candidates'],
            'properties': {
                'action': {'enum': ['retrieve_supported_evidence', 'retrieve_supported_components', 'refer_out_of_scope', 'clarify']},
                'reason': {'type': 'string'}, 'clarification_question': {'type': ['string', 'null']},
                'retrieval_requests': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
                    'required': ['component_id', 'query', 'allowed_domain', 'requires_answer_eligible_evidence'],
                    'properties': {'component_id': {'type': 'string'}, 'query': {'type': 'string'},
                        'allowed_domain': {'enum': ['labor', 'consumer']}, 'requires_answer_eligible_evidence': {'const': True}}}},
                'excluded_components': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
                    'required': ['component_id', 'text', 'scope_constraint', 'retrieval_allowed'],
                    'properties': {'component_id': {'type': 'string'}, 'text': {'type': 'string'},
                        'scope_constraint': {'type': ['string', 'null']}, 'retrieval_allowed': {'const': False}}}},
                'referral_candidates': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
                    'required': ['referral_id', 'agency', 'service', 'portal_url', 'information_url', 'topic',
                        'selection_source', 'last_contact_verification', 'requires_contact_refresh', 'candidate_only'],
                    'properties': {**{k: {'type': 'string'} for k in ['referral_id', 'agency', 'service', 'portal_url',
                        'information_url', 'topic', 'selection_source', 'last_contact_verification']},
                        'requires_contact_refresh': {'const': True}, 'candidate_only': {'const': True}}}}}},
        'components': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
            'required': ['component_id', 'text', 'category', 'scope_constraint', 'decision_source'],
            'properties': {'component_id': {'type': 'string'}, 'text': {'type': 'string'},
                'category': {'enum': ['labor', 'consumer', 'excluded']},
                'scope_constraint': {'type': ['string', 'null']}, 'decision_source': {'type': 'string'}}}},
        'segmentation_audit': {'type': 'object'},
        'permissions': {'type': 'object', 'additionalProperties': False,
            'required': ['retrieval_allowed', 'answer_generation_allowed', 'display_answer_allowed', 'deployment_allowed'],
            'properties': {'retrieval_allowed': {'type': 'boolean'},
                **{k: {'const': False} for k in ['answer_generation_allowed', 'display_answer_allowed', 'deployment_allowed']}}}}}
