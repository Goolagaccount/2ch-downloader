"""Loopback-only HTTP fixtures. No imageboard or user content is accessed."""
import base64
import json
import threading
import time
import io
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')
VIDEO = b'neutral synthetic transport fixture, not a playable video\n'
def blank_pdf():
    data=bytearray(b'%PDF-1.4\n')
    offsets=[0]
    for obj in [b'<</Type/Catalog/Pages 2 0 R>>',b'<</Type/Pages/Kids[3 0 R]/Count 1>>',b'<</Type/Page/Parent 2 0 R/MediaBox[0 0 10 10]/Resources<<>>>>']:
        offsets.append(len(data));data.extend(f'{len(offsets)-1} 0 obj\n'.encode()+obj+b'\nendobj\n')
    xref=len(data);data.extend(b'xref\n0 4\n0000000000 65535 f \n')
    for offset in offsets[1:]:data.extend(f'{offset:010d} 00000 n \n'.encode())
    data.extend(f'trailer\n<</Size 4/Root 1 0 R>>\nstartxref\n{xref}\n%%EOF\n'.encode())
    return bytes(data)
PDF = blank_pdf()
TEXT = 'Neutral text fixture: document bytes.\n'.encode('utf-8')
_zip=io.BytesIO()
with zipfile.ZipFile(_zip,'w',zipfile.ZIP_DEFLATED) as z:z.writestr(zipfile.ZipInfo('notes.txt',(1980,1,1,0,0,0)),TEXT)
ZIP=_zip.getvalue()
_docx=io.BytesIO()
with zipfile.ZipFile(_docx,'w') as z:
    parts={'[Content_Types].xml':'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>', '_rels/.rels':'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>', 'word/document.xml':'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Neutral fixture</w:t></w:r></w:p></w:body></w:document>'}
    for name,data in parts.items():z.writestr(zipfile.ZipInfo(name,(1980,1,1,0,0,0)),data)
DOCX=_docx.getvalue()
ATTACHMENTS={'paper.pdf':PDF,'notes.txt':TEXT,'bundle.zip':ZIP,'document.docx':DOCX,'photo.png':PNG,'clip.webm':VIDEO,'custom.xyz':b'opaque attachment bytes','my notes.txt':TEXT}
def attachment_markup(links):
    return ''.join('<figure class="post__image"><figcaption class="post__file-attr"><a href="'+link+'">attachment</a></figcaption><a class="post__image-link" href="'+link+'">preview</a></figure>' for link in links)
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
        if path.startswith('/b/res/') or path.startswith('/pr/res/'):
            tid = path.rsplit('/', 1)[1].split('.')[0]
            if tid == '212':return self.send(200,attachment_markup(['/b/src/212/1.pdf']).encode())
            if tid in ('210','211'):
                board='b' if tid=='210' else 'pr'
                links=[f'/{board}/src/{tid}/'+name.replace(' ','%20') for name in ATTACHMENTS]
                page=attachment_markup(links)
                # Same-thread paths in ordinary post text are not declarations.
                page+=f'<blockquote><a href="/{board}/src/{tid}/not-attached.txt">post link</a></blockquote>'
                page+='<a href="/outside.pdf">external document</a><script src="/script.js"></script><a href="/b/res/999.html">navigation</a>'
                page+=attachment_markup([f'/{board}/src/999/wrong-thread.pdf',f'/{board}/src/{tid}/../escape.pdf',f'/{board}/src/{tid}/CON.txt',f'/{board}/src/{tid}/bad%2Fname.pdf',f'/{board}/src/{tid}/errors.txt'])
                return self.send(200,page.encode())
            if tid == '108' and 'redirected=1' not in self.path:
                self.send_response(302)
                self.send_header('Location', f'http://localhost:{self.server.server_port}/b/res/108.html?redirected=1')
                self.send_header('Content-Length','0')
                self.end_headers()
                return
            if tid == '108':
                port=self.server.server_port
                return self.send(200, attachment_markup([f'/b/src/108/1.png',f'http://127.0.0.1:{port}/b/src/108/2.webm',f'//localhost:{port}/b/src/108/3.png']).encode())
            if tid == '404': return self.send(404, b'neutral missing page')
            if tid == '106': time.sleep(5)
            names = ['1.png', '2.webm'] if tid == '100' else ['1.png']
            if tid == '107': names = ['1.jpg.exe', '2.pdf', '3.docx']
            return self.send(200, attachment_markup([f'/b/src/{tid}/{name}' for name in names]).encode())
        if path.startswith('/b/src/') or path.startswith('/pr/src/'):
            tid = path.split('/')[3]
            if tid == '212':return self.send(200,PDF)
            if tid in ('210','211'):
                from urllib.parse import unquote
                name=unquote(path.rsplit('/',1)[1])
                return self.send(200,ATTACHMENTS.get(name,b'UNEXPECTED NON-ATTACHMENT REQUEST'))
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
