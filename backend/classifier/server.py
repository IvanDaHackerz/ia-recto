"""Bounded loopback HTTP adapter for later integration; no website or LLM."""
from __future__ import annotations
import argparse
import json
import re
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
from urllib.parse import urlsplit
import uuid

from .contracts import MAX_BODY_BYTES, REQUEST_SCHEMA, RESPONSE_SCHEMA, RequestError, strict_json
from .service import ArtifactError, ClassifierService, DEFAULT_CONFIG


class ClassifierHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 16

    def __init__(self, address, service, *, allowed_origins=(), maximum_connections=4, request_timeout=5):
        if address[0] != '127.0.0.1':
            raise ValueError('Development classifier server must bind to 127.0.0.1')
        self.service = service
        self.allowed_origins = frozenset(validate_origin(o) for o in allowed_origins)
        self.request_timeout = request_timeout
        self.slots = threading.BoundedSemaphore(maximum_connections)
        super().__init__(address, ClassifierHandler)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            body = b'{"error":{"code":"server_busy","message":"Classifier is busy. Retry later."}}'
            try:
                request.settimeout(self.request_timeout)
                request.sendall(b'HTTP/1.0 503 Service Unavailable\r\nContent-Type: application/json\r\nConnection: close\r\nRetry-After: 1\r\nContent-Length: '
                    + str(len(body)).encode('ascii') + b'\r\n\r\n' + body)
            except OSError:
                pass
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()

    def handle_error(self, request, client_address):
        # Avoid tracebacks containing request content or operator filesystem paths.
        pass


def validate_origin(value):
    parsed = urlsplit(value)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
        raise ValueError('Allowed origins must be exact http(s) origins without paths or credentials')
    try:
        parsed.port
    except ValueError:
        raise ValueError('Invalid allowed-origin port') from None
    if any(ord(c) < 33 or ord(c) > 126 for c in value) or '*' in value:
        raise ValueError('Wildcard or invalid origins are not allowed')
    return value


class ClassifierHandler(BaseHTTPRequestHandler):
    server_version = 'RectoClassifier/1.0'
    sys_version = ''

    def setup(self):
        super().setup()
        self.connection.settimeout(self.server.request_timeout)
        self.request_id = uuid.uuid4().hex

    def log_message(self, format, *args):
        # Questions, URLs and payloads are not written to access logs.
        pass

    def send_error(self, code, message=None, explain=None):
        self.reply(code, {'error': {'code': 'http_error', 'message': 'Unsupported or malformed HTTP request.'},
                          'request_id': self.request_id})

    def reply(self, status, value):
        body = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Request-ID', self.request_id)
        self.send_header('Connection', 'close')
        origins = self.headers.get_all('Origin', []) if hasattr(self, 'headers') else []
        if len(origins) == 1 and origins[0] in self.server.allowed_origins:
            self.send_header('Access-Control-Allow-Origin', origins[0])
            self.send_header('Vary', 'Origin')
            self.send_header('Access-Control-Allow-Methods', getattr(self,'cors_methods','POST, GET, OPTIONS'))
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.close_connection = True
        if self.command != 'HEAD':
            self.wfile.write(body)

    def dispatch(self, method):
        try:
            origins = self.headers.get_all('Origin', [])
            if len(origins) > 1 or origins and origins[0] not in self.server.allowed_origins:
                raise RequestError('origin_not_allowed', 'This origin is not allowed.', 403)
            parsed = urlsplit(self.path)
            if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
                raise RequestError('invalid_path', 'Use an API path without query parameters.')
            if parsed.path not in {'/health', '/v1/contract', '/v1/classify'}:
                raise RequestError('not_found', 'Endpoint not found.', 404)
            if method == 'OPTIONS':
                if parsed.path != '/v1/classify' or self.headers.get('Access-Control-Request-Method') != 'POST':
                    raise RequestError('method_not_allowed', 'Preflight must request POST /v1/classify.', 405)
                headers = self.headers.get('Access-Control-Request-Headers', '')
                if any(h.strip().lower() != 'content-type' for h in headers.split(',') if h.strip()):
                    raise RequestError('headers_not_allowed', 'Only Content-Type is supported.', 403)
                self.reply(200, {'status': 'allowed'})
                return
            expected = 'POST' if parsed.path == '/v1/classify' else 'GET'
            if method != expected:
                raise RequestError('method_not_allowed', f'Use {expected} for this endpoint.', 405)
            if method == 'GET':
                health=self.server.service.health()
                self.reply(200, health if parsed.path == '/health' else {
                    'schema_version': '1.0', 'request': REQUEST_SCHEMA, 'response': RESPONSE_SCHEMA})
                return
            if self.headers.get_all('Transfer-Encoding'):
                raise RequestError('unsupported_encoding', 'Chunked request bodies are not supported.')
            lengths = self.headers.get_all('Content-Length', [])
            if not lengths:
                raise RequestError('length_required', 'Content-Length is required.', 411)
            if len(lengths) != 1 or not re.fullmatch(r'[0-9]{1,10}', lengths[0]):
                raise RequestError('invalid_length', 'Content-Length must be one non-negative integer.')
            length = int(lengths[0])
            if length > MAX_BODY_BYTES:
                raise RequestError('body_too_large', 'Request body exceeds the size limit.', 413)
            types = self.headers.get_all('Content-Type', [])
            if len(types) != 1 or types[0].lower().strip() not in {'application/json', 'application/json; charset=utf-8'}:
                raise RequestError('unsupported_content_type', 'Use application/json with UTF-8 encoding.', 415)
            if self.headers.get_all('Content-Encoding'):
                raise RequestError('unsupported_encoding', 'Compressed request bodies are not supported.', 415)
            data = self.rfile.read(length)
            if len(data) != length:
                raise RequestError('incomplete_body', 'Request body was incomplete.')
            try:
                text = data.decode('utf-8')
            except UnicodeDecodeError:
                raise RequestError('invalid_encoding', 'Request body must be UTF-8.') from None
            result = self.server.service.classify(strict_json(text))
            self.request_id = result['request_id']
            self.reply(200, result)
        except RequestError as error:
            self.reply(error.status, {'request_id': self.request_id, 'error': {'code': error.code, 'message': str(error)}})
        except ArtifactError:
            self.reply(503, {'request_id': self.request_id, 'error': {'code': 'classifier_unavailable',
                'message': 'Classifier integrity check failed. An operator must restore or reload the configured package.'}})
        except (TimeoutError, socket.timeout):
            self.reply(408, {'request_id': self.request_id, 'error': {'code': 'request_timeout', 'message': 'Request timed out.'}})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self.reply(500, {'request_id': self.request_id, 'error': {'code': 'internal_error', 'message': 'Classification could not be completed.'}})

    def do_GET(self): self.dispatch('GET')
    def do_POST(self): self.dispatch('POST')
    def do_OPTIONS(self): self.dispatch('OPTIONS')
    def do_HEAD(self): self.dispatch('HEAD')
    def do_PUT(self): self.dispatch('PUT')
    def do_DELETE(self): self.dispatch('DELETE')
    def do_PATCH(self): self.dispatch('PATCH')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=str, default=str(DEFAULT_CONFIG))
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--allow-origin', action='append', default=[])
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('port must be between 1 and 65535')
    service = ClassifierService(args.config)
    with ClassifierHTTPServer(('127.0.0.1', args.port), service, allowed_origins=args.allow_origin) as server:
        print(json.dumps({'status': 'ready', 'address': f'http://127.0.0.1:{args.port}',
                          'model_version': service.bundle['model_version'], 'role': 'offline_classifier_only'}), flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
