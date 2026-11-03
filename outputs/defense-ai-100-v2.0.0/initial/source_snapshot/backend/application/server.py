"""Loopback website API. Run: python -m backend.application.server"""
from __future__ import annotations
import argparse
import re
import socket
import secrets
import hashlib
import hmac
from http.cookies import SimpleCookie
from urllib.parse import urlsplit
from backend.classifier.server import ClassifierHTTPServer, ClassifierHandler
from backend.classifier.contracts import MAX_BODY_BYTES, RequestError, strict_json
from .service import ApplicationService


class ApplicationServer(ClassifierHTTPServer):
    def __init__(self, address, service, **kwargs):
        kwargs.setdefault('maximum_connections',12)
        super().__init__(address, service, **kwargs)
        self.RequestHandlerClass = ApplicationHandler
        key=getattr(service,'session_key',None)
        self.session_key=key if type(key) is bytes and len(key)==32 else secrets.token_bytes(32)


class ApplicationHandler(ClassifierHandler):
    server_version = "RectoLocal/2.0"
    cors_methods='GET, POST, DELETE, OPTIONS'

    def end_headers(self):
        cookie=getattr(self,'_session_cookie',None)
        if cookie:self.send_header('Set-Cookie','recto_session='+cookie+'; Path=/api; HttpOnly; SameSite=Strict; Max-Age=2592000')
        self.send_header('Content-Security-Policy',"default-src 'none'; frame-ancestors 'none'")
        self.send_header('Referrer-Policy','no-referrer')
        super().end_headers()

    def browser_session(self):
        raw=self.headers.get('Cookie','')
        if len(raw)>4096:raise RequestError('invalid_cookie','Browser cookie exceeds its size limit.')
        try:
            cookie=SimpleCookie();cookie.load(raw);value=cookie['recto_session'].value if 'recto_session' in cookie else ''
        except Exception:value=''
        parts=value.split('.')
        valid=len(parts)==2 and all(re.fullmatch(r'[a-f0-9]{64}',v) for v in parts)
        if valid:valid=hmac.compare_digest(parts[1],hmac.new(self.server.session_key,parts[0].encode(),hashlib.sha256).hexdigest())
        if not valid:
            token=secrets.token_hex(32)
            value=token+'.'+hmac.new(self.server.session_key,token.encode(),hashlib.sha256).hexdigest()
            self._session_cookie=value
        return value.split('.',1)[0]

    def dispatch(self, method):
        try:
            hosts = self.headers.get_all("Host", [])
            port = self.server.server_address[1]
            if len(hosts) != 1 or hosts[0] not in {f"127.0.0.1:{port}", f"localhost:{port}"}:
                raise RequestError("host_not_allowed", "Use the local API address.", 403)
            origins = self.headers.get_all("Origin", [])
            if len(origins) > 1 or origins and origins[0] not in self.server.allowed_origins:
                raise RequestError("origin_not_allowed", "This origin is not allowed.", 403)
            parsed = urlsplit(self.path)
            if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
                raise RequestError("invalid_path", "Use an API path without query parameters.")
            history_match=re.fullmatch(r'/api/history/([a-f0-9]{32})(/export)?',parsed.path)
            is_history=parsed.path=='/api/history' or history_match is not None
            if parsed.path not in {"/api/health", "/api/chat", "/api/performance", "/api/status", "/api/cancel", "/api/history"} and not history_match:
                raise RequestError("not_found", "Endpoint not found.", 404)
            expected = "POST" if parsed.path in {"/api/chat","/api/cancel"} else "GET"
            allowed={expected}|({'DELETE'} if is_history and not (history_match and history_match[2]) else set())
            if method == "OPTIONS":
                if self.headers.get("Access-Control-Request-Method") not in allowed:
                    raise RequestError("method_not_allowed", "Unsupported preflight method.", 405)
                if any(h.strip().lower() != "content-type" for h in self.headers.get("Access-Control-Request-Headers", "").split(",") if h.strip()):
                    raise RequestError("headers_not_allowed", "Only Content-Type is supported.", 403)
                self.reply(200, {"status": "allowed"})
                return
            if method not in allowed:
                raise RequestError("method_not_allowed", f"Use {expected} for this endpoint.", 405)
            session=self.browser_session()
            if method=='DELETE':
                self.reply(200,self.server.service.delete_history(session,history_match[1] if history_match else None));return
            if method == "GET":
                if is_history:result=self.server.service.history(session,history_match[1] if history_match else None)
                elif parsed.path=='/api/status':result=self.server.service.status()
                else:result=self.server.service.health() if parsed.path=="/api/health" else self.server.service.performance()
                self.reply(200,result)
                return
            if self.headers.get_all("Transfer-Encoding") or self.headers.get_all("Content-Encoding"):
                raise RequestError("unsupported_encoding", "Send uncompressed JSON.", 415)
            lengths = self.headers.get_all("Content-Length", [])
            if not lengths:
                raise RequestError("length_required", "Content-Length is required.", 411)
            if len(lengths) != 1 or not re.fullmatch(r"[0-9]{1,10}", lengths[0]):
                raise RequestError("invalid_length", "One Content-Length is required.")
            length = int(lengths[0])
            if length > MAX_BODY_BYTES:
                raise RequestError("body_too_large", "Request body exceeds the size limit.", 413)
            types = self.headers.get_all("Content-Type", [])
            if len(types) != 1 or types[0].lower().strip() not in {"application/json", "application/json; charset=utf-8"}:
                raise RequestError("unsupported_content_type", "Send application/json.", 415)
            data = self.rfile.read(length)
            if len(data) != length:
                raise RequestError("incomplete_body", "Request body was incomplete.")
            try:
                payload = strict_json(data.decode("utf-8"))
            except UnicodeDecodeError:
                raise RequestError("invalid_encoding", "Send UTF-8 JSON.") from None
            if parsed.path=='/api/cancel':
                if type(payload) is not dict or set(payload)!={'request_id'}:raise RequestError('invalid_request','Use only request_id to cancel.')
                result=self.server.service.cancel(session,payload['request_id'])
            else:result = self.server.service.chat(payload,session=session)
            self.request_id = result["request_id"]
            self.reply(200, result)
        except RequestError as error:
            self.reply(error.status, {"request_id": self.request_id, "error": {"code": error.code, "message": str(error)}})
        except (TimeoutError, socket.timeout):
            self.reply(408, {"error": {"code": "request_timeout", "message": "Request timed out."}})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self.reply(503, {"request_id": self.request_id, "error": {"code": "runtime_unavailable", "message": "The local runtime or saved evaluation is unavailable. Check the backend and package integrity."}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument('--ui-port',type=int,action='append',help='Additional exact loopback UI port allowed by this development API')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Invalid port")
    if any(not 1024<=port<=65535 for port in (args.ui_port or [])):parser.error('Invalid UI port')
    origins = [f"http://{host}:{port}" for host in ("127.0.0.1", "localhost") for port in {5173,5174,*(args.ui_port or [])}]
    service = ApplicationService.configured()
    with ApplicationServer(("127.0.0.1", args.port), service, allowed_origins=origins) as server:
        print(f"Recto local API ready at http://127.0.0.1:{args.port} (development inspection; legal-answer gates unchanged)", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
