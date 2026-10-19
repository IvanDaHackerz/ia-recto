"""Pinned, local, read-only classifier service used by future application code."""
from __future__ import annotations
import hashlib
import importlib.metadata
import math
from pathlib import Path
import sys
import threading
import uuid

from .contracts import SCHEMA_VERSION, RESPONSE_SCHEMA, strict_json, validate_contract, validate_request

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = Path(__file__).with_name('config.json')
RUNTIME_FILES = ['classifier_runtime.py', 'clause_classifier.py', 'logical_clause_model.py',
                 'scope_constraints.py', 'referral_routing.py', 'semantic_encoder.py']


class ArtifactError(RuntimeError):
    pass


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(root, name):
    if not isinstance(name, str) or not name:
        raise ArtifactError('Invalid artifact binding')
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ArtifactError('Artifact binding leaves its configured root')
    return path


class ClassifierService:
    def __init__(self, config=DEFAULT_CONFIG):
        self.config_path = Path(config).resolve()
        self.config = strict_json(self.config_path.read_text(encoding='utf-8'))
        if self.config['schema_version'] != SCHEMA_VERSION:
            raise ArtifactError('Unsupported adapter configuration')
        if self.config['python_major_minor'] != f'{sys.version_info.major}.{sys.version_info.minor}':
            raise ArtifactError('Use the pinned Python environment')
        for name, expected in self.config['dependencies'].items():
            if importlib.metadata.version(name) != expected:
                raise ArtifactError('Dependency version differs from classifier package: ' + name)
        self.model_dir = inside(ROOT, self.config['classifier'])
        manifest = self.model_dir / 'artifact_checksums.json'
        if sha(manifest) != self.config['artifact_checksums_sha256']:
            raise ArtifactError('Classifier checksum manifest differs from configured version')
        checks = strict_json(manifest.read_text(encoding='utf-8'))
        self.bindings = {inside(self.model_dir, name): expected for name, expected in checks.items()}
        self.bindings[manifest] = self.config['artifact_checksums_sha256']
        self.bindings[self.config_path] = sha(self.config_path)
        for name in RUNTIME_FILES:
            self.bindings[ROOT / 'dataset/pipelines/item10' / name] = checks[name]
        for name, expected in self.config['source_sha256'].items():
            self.bindings[inside(ROOT, name)] = expected
        self._lock = threading.RLock()
        self.assert_integrity()
        sys.path.insert(0, str(ROOT / 'dataset/pipelines/item10'))
        import classifier_runtime
        import joblib
        if Path(classifier_runtime.__file__).resolve() != ROOT / 'dataset/pipelines/item10/classifier_runtime.py':
            raise ArtifactError('Unexpected imported classifier runtime')
        self.bundle = joblib.load(self.model_dir / 'classifier.joblib')
        if self.bundle['model_version'] != self.config['model_version'] or self.bundle['thresholds'] != self.config['thresholds']:
            raise ArtifactError('Model identity or thresholds differ from configured package')
        if self.bundle['deployment_allowed']:
            raise ArtifactError('This adapter is restricted to offline development')
        self._predict = classifier_runtime.predict_records

    def assert_integrity(self):
        try:
            changed = any(not path.is_file() or sha(path) != expected for path, expected in self.bindings.items())
        except OSError:
            changed = True
        if changed:
            raise ArtifactError('Classifier artifacts changed; restore or explicitly rebuild and restart')

    def health(self):
        with self._lock:
            self.assert_integrity()
            return {'schema_version': SCHEMA_VERSION, 'status': 'ready', 'model_version': self.bundle['model_version'],
                'role': 'offline_development_classifier', 'formal_evaluation_completed': False,
                'website_integration_completed': False, 'llm_connected': False,
                'answer_generation_allowed': False, 'deployment_allowed': False}

    def classify(self, request):
        text, request_id = validate_request(request)
        with self._lock:
            self.assert_integrity()
            p = self._predict(self.bundle, [{'question_text': text}])[0]
            self.assert_integrity()
            response=self.response(p, request_id or uuid.uuid4().hex)
            try:
                validate_contract(response,RESPONSE_SCHEMA)
            except ValueError as error:
                raise ArtifactError('Classifier output violates the API contract') from error
            return response

    @staticmethod
    def response(p, request_id):
        # Preserve chosen-label probabilities; never substitute a larger maximum
        # or turn rule evidence into a probability of legal correctness.
        for head in ['primary', 'scope']:
            values = p[head + '_probabilities']
            if any(not math.isfinite(v) or not 0 <= v <= 1 for v in values.values()) or not math.isclose(sum(values.values()), 1, abs_tol=1e-8):
                raise ArtifactError('Invalid model probabilities')
            if p[head + '_confidence'] != values[p['predicted_' + head]]:
                raise ArtifactError('Confidence does not correspond to chosen label')
        valid_pairs={('labor','fully_supported'),('consumer','fully_supported'),('mixed','fully_supported'),
            ('mixed','partially_supported'),('out_of_scope','unsupported')}
        if (p['predicted_primary'],p['predicted_scope']) not in valid_pairs or p.get('deployment_allowed'):
            raise ArtifactError('Inconsistent or enabled classifier result')
        route = p['routing_action']
        if route not in {'retrieve_supported_evidence','retrieve_supported_components','refer_out_of_scope','clarify'}:
            raise ArtifactError('Unknown routing action')
        allowed = route in {'retrieve_supported_evidence', 'retrieve_supported_components'}
        if allowed and (p['predicted_scope']=='unsupported' or p.get('segmentation_audit',{}).get('requires_clarification')):
            raise ArtifactError('Unresolved or unsupported input was admitted')
        if route=='refer_out_of_scope' and p['predicted_primary']!='out_of_scope':
            raise ArtifactError('Referral-only route has supported labels')
        components, requests, excluded = [], [], []
        for i, c in enumerate(p.get('component_evidence', []), 1):
            cid = f'concern_{i:03}'
            components.append({'component_id': cid, 'text': c['text'], 'category': c['category'],
                'scope_constraint': c.get('constraint'), 'decision_source': c['decision_source']})
            if c['category'] == 'excluded':
                excluded.append({'component_id': cid, 'text': c['text'], 'scope_constraint': c.get('constraint'), 'retrieval_allowed': False})
            elif allowed and c['atomic_evidence_strength'] >= .5:
                requests.append({'component_id': cid, 'query': c['text'], 'allowed_domain': c['category'],
                    'requires_answer_eligible_evidence': True})
        if allowed and not requests:
            raise ArtifactError('Admitted route has no supported component')
        if allowed and any(c['atomic_evidence_strength']<.5 for c in p.get('component_evidence',[])):
            raise ArtifactError('Unreliable component was admitted')
        if route == 'clarify' and not p.get('clarification_question'):
            raise ArtifactError('Clarification route lacks a question')
        return {'schema_version': SCHEMA_VERSION, 'request_id': request_id, 'question_text': p['question_text'],
            'question_sha256': hashlib.sha256(p['question_text'].encode('utf-8')).hexdigest(),
            'model_version': p['model_version'], 'classification': {
                'primary_label': p['predicted_primary'], 'scope_label': p['predicted_scope'],
                **{key: p[key] for key in ['primary_confidence', 'scope_confidence', 'primary_probabilities',
                                          'scope_probabilities', 'confidence_meaning']}},
            'routing': {'action': route, 'reason': p['reason'], 'clarification_question': p['clarification_question'],
                'retrieval_requests': requests, 'excluded_components': excluded,
                'referral_candidates': p.get('referral_candidates', [])},
            'components': components, 'segmentation_audit': p.get('segmentation_audit', {}),
            'permissions': {'retrieval_allowed': allowed, 'answer_generation_allowed': False,
                'display_answer_allowed': False, 'deployment_allowed': False}}
