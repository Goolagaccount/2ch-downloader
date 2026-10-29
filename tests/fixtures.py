"""Loopback-only HTTP fixtures. No imageboard or user content is accessed."""
import base64
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')
VIDEO = b'neutral synthetic transport fixture, not a playable video\n'
counts = {}
lock = threading.Lock()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def send(self, status, data, length=None):
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8' if '/res/' in self.path else 'application/octet-stream')
        self.send_header('Content-Length', str(len(data) if length is None else length))
        self.end_headers()
        try: self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError): pass
    def do_GET(self):
        path = self.path.split('?')[0]
        with lock:
            counts[path] = counts.get(path, 0) + 1
            count = counts[path]
        if path == '/counts': return self.send(200, json.dumps(counts).encode())
        if path.startswith('/b/res/'):
            tid = path.rsplit('/', 1)[1].split('.')[0]
            if tid == '108' and 'redirected=1' not in self.path:
                self.send_response(302)
                self.send_header('Location', f'http://localhost:{self.server.server_port}/b/res/108.html?redirected=1')
                self.send_header('Content-Length','0')
                self.end_headers()
                return
            if tid == '108':
                port=self.server.server_port
                return self.send(200, f'<a href="/b/src/108/1.png">root</a><a href="http://127.0.0.1:{port}/b/src/108/2.webm">absolute</a><img src="//localhost:{port}/b/src/108/3.png">'.encode())
            if tid == '404': return self.send(404, b'neutral missing page')
            if tid == '106': time.sleep(5)
            names = ['1.png', '2.webm'] if tid == '100' else ['1.png']
            if tid == '107': names = ['1.jpg.exe', '2.pdf', '3.docx']
            return self.send(200, ''.join(f'<a href="/b/src/{tid}/{name}">fixture</a>' for name in names).encode())
        if path.startswith('/b/src/'):
            tid = path.split('/')[3]
            if tid == '101' and count < 3: return self.send(503, b'transient fixture')
            if tid == '102': return self.send(503, b'persistent fixture')
            if tid == '103': return self.send(200, b'')
            if tid == '105':
                self.send(200, b'truncated', 500)
                self.close_connection = True
                return
            return self.send(200, VIDEO if path.endswith('.webm') else PNG)
        self.send(404, b'unknown fixture')

if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    print(server.server_address[1], flush=True)
    server.serve_forever()
