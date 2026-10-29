"""Build first, then python tests/integration.py. Executes the rebuilt GUI EXE."""
import hashlib
import json
import pathlib
import subprocess
import tempfile
import urllib.request
from fixtures import PNG, VIDEO

REPO = pathlib.Path(__file__).resolve().parents[1]
EXE = REPO / '2ch_downloader.exe'
server = subprocess.Popen(['python', str(REPO/'tests/fixtures.py')], stdout=subprocess.PIPE, text=True)
port = int(server.stdout.readline())
base = f'http://127.0.0.1:{port}'
evidence = []

def run(name, ids, root, **options):
    config = root.parent/(name+'.json')
    result_path = root.parent/(name+'-result.json')
    urls = [base+'/b/res/'+str(i)+'.html' for i in ids]
    if name == 'repeat': urls[1] += '?fixture=1#post'
    config.write_text(json.dumps(dict(Urls=urls,Root=str(root),ResultPath=str(result_path),**options)),encoding='utf-8-sig')
    proc = subprocess.Popen([str(EXE), '-TestConfiguration', str(config)])
    try:
        code = proc.wait(timeout=60)
        assert code == 0, (name, 'exit code', code)
        assert result_path.exists(), (name, 'no completion result', pathlib.Path(str(result_path)+'.error').read_text('utf-8-sig') if pathlib.Path(str(result_path)+'.error').exists() else '')
        result = json.loads(result_path.read_text(encoding='utf-8-sig'))
    finally:
        if proc.poll() is None: proc.kill(); proc.wait()
    if not isinstance(result,list): result=[result]
    if not options.get('CloseDuringDownload'):
        assert len(result)==len(ids), (name,result)
        assert all(r['ControlsEnabled'] and r['ActiveJobCount']==0 and r['JobRemoved'] is not False for r in result), (name,result)
    return result

try:
    with tempfile.TemporaryDirectory(prefix='2ch-neutral-tests-') as temp:
        parent = pathlib.Path(temp); root=parent/'output'; root.mkdir()
        rows=run('repeat',[100,100,100],root)
        assert [r['Result']['Downloaded'] for r in rows]==[2,0,0], rows
        assert [r['Result']['Skipped'] for r in rows]==[0,2,2], rows
        assert all(r['Result']['Ok'] and r['Result']['ErrorsFile'] is None for r in rows), rows
        assert (root/'thread_100/1.png').read_bytes()==PNG
        assert (root/'thread_100/2.webm').read_bytes()==VIDEO
        evidence.append('PASS clean success + query/fragment + three runs in one GUI: 2,0,0 downloaded; one result per run; byte-exact payloads; no active job/log')
        rows=run('redirect',[108],root)
        assert rows[0]['Result']['Ok'] and rows[0]['Result']['Downloaded']==3, rows
        links=(root/'thread_108/file_links.txt').read_text('utf-8-sig')
        assert f'http://localhost:{port}/b/src/108/1.png' in links,links
        assert f'http://127.0.0.1:{port}/b/src/108/2.webm' in links,links
        assert f'http://localhost:{port}/b/src/108/3.png' in links,links
        assert (root/'thread_108/1.png').read_bytes()==PNG
        assert (root/'thread_108/2.webm').read_bytes()==VIDEO
        evidence.append('PASS redirect to localhost: final page origin used; absolute media origin retained; protocol-relative URL works')
        rows=run('retry',[101],root)
        assert rows[0]['Result']['Ok'] and rows[0]['Result']['Downloaded']==1, rows
        evidence.append('PASS transient HTTP 503: third attempt succeeds')
        for tid,name in [(102,'persistent'),(103,'empty'),(105,'truncated')]:
            rows=run(name,[tid],root)
            assert not rows[0]['Result']['Ok'] and rows[0]['Result']['Failed']==1, rows
            assert not (root/f'thread_{tid}/1.png').exists()
            assert not list((root/f'thread_{tid}').glob('*.part'))
            evidence.append('PASS '+name+': failure reported; no final/partial file; controls restored; job removed')
        zero=root/'thread_104'; zero.mkdir(); (zero/'1.png').write_bytes(b''); (zero/'1.png.part').write_bytes(b'old partial')
        rows=run('zero',[104],root)
        assert rows[0]['Result']['Downloaded']==1 and (zero/'1.png').read_bytes()==PNG, rows
        assert not (zero/'1.png.part').exists()
        evidence.append('PASS empty existing file + stale .part: retried and replaced with complete bytes')
        for tid,name in [(404,'page404'),(107,'extension_guard')]:
            rows=run(name,[tid],root)
            assert rows[0]['Result']['Ok']==(tid==107),rows
            if tid==107: assert rows[0]['Result']['Downloaded']==0 and not (root/'thread_107/1.jpg').exists()
            evidence.append('PASS '+name+': expected result; controls restored; job removed')
        bad=parent/'not-a-directory'; bad.write_text('fixture')
        rows=run('invalid_folder',[100],bad)
        assert not rows[0]['Result']['Ok'],rows
        evidence.append('PASS file path rejected as output folder')
        rows=run('close',[106],root,CloseDuringDownload=True)
        assert rows[0]['Closed'] and rows[0]['ActiveJobCount']==0 and rows[0]['JobRemoved'],rows
        evidence.append('PASS close during request: GUI exits; active job stopped and removed')
        counts=json.load(urllib.request.urlopen(base+'/counts'))
        assert counts['/b/src/101/1.png']==3,counts
        for tid in [102,103,105]: assert counts[f'/b/src/{tid}/1.png']==3,counts
        assert counts['/b/src/100/1.png']==1 and counts['/b/src/100/2.webm']==1,counts
        evidence.append('PASS server request counts: retries exactly 3; repeated runs do not redownload')
    print('\n'.join(evidence))
    print('EXE SHA256 '+hashlib.sha256(EXE.read_bytes()).hexdigest())
finally:
    server.terminate(); server.wait(timeout=10)
