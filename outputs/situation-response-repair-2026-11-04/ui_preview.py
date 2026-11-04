"""Loopback-only UI replay of recorded fictional live results; no AI calls."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import copy
import json

HERE = Path(__file__).resolve().parent
DIST = HERE.parents[1] / 'UI/UX/app/dist'
PACKETS = [json.loads((HERE / f'confirmed-{name}.json').read_text(encoding='utf-8'))['packet']
           for name in ['cinema', 'consumer', 'unclear']]

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def send_json(self, value):
        raw = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == '/api/health':
            return self.send_json({'schema_version': '1.0', 'status': 'ready', 'test_replay': True})
        return super().do_GET()

    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))))
        packet = next((p for p in PACKETS if p['original_question_text'] == request.get('question_text')), None)
        if self.path != '/api/chat' or not packet:
            self.send_error(400, 'Only recorded test questions are available in this replay')
            return
        packet = copy.deepcopy(packet)
        packet['request_id'] = request['request_id']
        self.send_json(packet)

    def log_message(self, *args):
        pass

if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 5190), Handler).serve_forever()
