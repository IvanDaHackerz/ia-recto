"""Bounded fictional live probes; preserve provider results without credentials."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.application.service import ApplicationService
from backend.application.development_explanation import TogetherDevelopmentExplanation

OUT = Path(__file__).resolve().parent
CASES = {
    'cinema': 'A private cinema requires ticket staff to count their cash drawers before clocking in. Does this required preparation count as working time?',
    'overtime': 'I pack parcels for a private seller. My supervisor requires two extra hours after my ordinary eight-hour shift but says a monthly salary means no overtime pay. What general rule applies?',
    'consumer': 'Bagong rice cooker ang binili ko sa store pero hindi nagla-lock ang lid. Ano ang ibig sabihin nito para sa concern ko?',
    'excluded': 'Regular employee ako ng city treasurer\'s office. May salary deduction na gusto kong i-dispute. Anong rules ang puwede mong i-apply?',
    'unclear': 'Hindi nila ibinibigay ang bayad ko. Ano ang puwede kong gawin?',
}

class RecordingProvider(TogetherDevelopmentExplanation):
    records = []

    def _send(self, body):
        result = super()._send(body)
        self.records.append({'schema': body['response_format']['json_schema']['name'], 'result': result})
        return result

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    label = sys.argv[1]
    names = sys.argv[2:] or ['cinema']
    service = ApplicationService.configured()
    original = service.development_provider
    if original:
        service.development_provider = RecordingProvider(original.model, original._key)
    print(json.dumps({'provider_configured': original is not None, 'usage_before': service.ledger.summary()}), flush=True)
    for name in names:
        RecordingProvider.records = []
        packet = service.chat({'question_text': CASES[name], 'use_ai': True, 'save_history': False})
        (OUT / f'{label}-{name}.json').write_text(json.dumps({'packet': packet, 'provider_results': RecordingProvider.records}, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'case': name, 'explanation': {k: v for k, v in packet['explanation'].items() if k not in {'claims'}}, 'claims': [c['text'] for c in packet['explanation']['claims']], 'response': packet['response'], 'ms': packet['total_query_ms']}, ensure_ascii=False), flush=True)
