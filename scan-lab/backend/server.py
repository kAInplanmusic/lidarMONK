#!/usr/bin/env python3
"""Local-first upload + jobs for lidarMONK; explicit LAN opt-in."""
import argparse, html, ipaddress, json, os, secrets, shutil, socket, subprocess, sys, threading, time, uuid, zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

TOKEN=secrets.token_urlsafe(24); ROOT=None; JOBS={}; LOCK=threading.Lock(); MAX_FILE=2*1024**3; MAX_EXTRACT=4*1024**3
PAGE='''<!doctype html><html lang="de"><meta name="viewport" content="width=device-width,initial-scale=1"><meta charset="utf-8"><title>lidarMONK Upload</title><style>body{background:#101a20;color:#e6f5ee;font:16px system-ui;max-width:760px;margin:2em auto;padding:0 1em}section{background:#1a2b30;border:1px solid #35544c;border-radius:12px;padding:1em;margin:1em 0}button,input,select{font:inherit;padding:.7em;margin:.3em 0}button{background:#7de4bc;border:0;border-radius:6px}small{color:#aac0b9}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>◈ lidarMONK</h1><p>Scans hochladen und kombinieren</p><section id="access" hidden><label>Zugangsschlüssel<br><input id="key" type="password" autocomplete="off"></label><button onclick="unlock()">Entsperren</button></section><section><h2>1 · Aufnahmen auswählen</h2><p>Stray oder SplatCapture als vollständiges ZIP; WurldCam als .webm.</p><input id="files" type="file" multiple accept=".zip,.webm,.mkv"><button onclick="upload()">Dateien hochladen</button><pre id="up"></pre></section><section><h2>2 · Rekonstruktion</h2><label>Aufnahme A<br><select id="a"></select></label><br><label>Aufnahme B<br><select id="b"></select></label><br><label>Aufnahme C (optional)<br><select id="c"></select></label><br><label>Motiv<br><select id="mode"><option value="object">Objekt</option><option value="person">Person · Bewegung möglich</option></select></label><br><label><input id="motion" type="checkbox"> Experimentelle starre Bewegungskorrektur (kann Ansichten verwerfen)</label><br><label><input id="tsdf" type="checkbox" checked> Experimentelle regionale TSDF-Fusion</label><br><label><input id="aligned" type="checkbox"> Unterschiedliche Bildgrößen: nur bei nachweislich gleichem Bildausschnitt skalieren</label><br><button onclick="start()">Verarbeitung starten</button><pre id="status"></pre></section><section><h2>3 · Ergebnis</h2><p id="downloads">Noch keine Verarbeitung abgeschlossen.</p><small>Die automatische Ausrichtung und das Mesh sind experimentell. Personen: starre Bewegungskorrektur ist experimentell; Atmung, Gelenke und Hintergrund können Fehler verursachen. Ohne Referenz keine Messgenauigkeit garantiert.</small></section><script>
let token=location.hash.slice(1)||sessionStorage.getItem('lidarmonk-token')||'';if(location.hash){sessionStorage.setItem('lidarmonk-token',token);history.replaceState(null,'',location.pathname)}if(!token)document.getElementById('access').hidden=false;function unlock(){sessionStorage.setItem('lidarmonk-token',document.getElementById('key').value);location.reload()}const headers={'X-Lidar-Token':token};let captures=[];async function api(url,opt={}){opt.headers={...headers,...opt.headers};let r=await fetch(url,opt),j=await r.json();if(!r.ok)throw Error(j.error||'Fehler');return j}
async function refresh(){let j=await api('/captures');captures=j.captures;for(let id of ['a','b','c']){let el=document.getElementById(id),old=el.value;el.replaceChildren();if(id==='c'){let none=document.createElement('option');none.value='';none.textContent='Keine dritte Aufnahme';el.append(none)}for(let c of captures){let o=document.createElement('option');o.value=c.id;o.textContent=c.name;el.append(o)}if(captures.some(x=>x.id===old))el.value=old;}if(captures.length===2)document.getElementById('b').value=captures[1].id}
async function upload(){let out=document.getElementById('up');try{for(const f of document.getElementById('files').files){out.textContent='Lade '+f.name+' …';await api('/upload?name='+encodeURIComponent(f.name),{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:f})}out.textContent='Upload abgeschlossen.';await refresh()}catch(e){out.textContent='Fehler: '+e.message}}
async function start(){let s=document.getElementById('status');try{let body={a:document.getElementById('a').value,b:document.getElementById('b').value,mode:document.getElementById('mode').value,motion:document.getElementById('motion').checked,c:document.getElementById('c').value,tsdf:document.getElementById('tsdf').checked,aligned:document.getElementById('aligned').checked};let j=await api('/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});let poll=async()=>{let q=await api('/jobs?id='+j.id);s.textContent=q.state+'\\n'+q.log;if(q.state==='running')setTimeout(poll,2000);else if(q.state==='completed'){let d=document.getElementById('downloads');d.replaceChildren();for(let f of q.files){let a=document.createElement('a');a.href='#';a.textContent=f;a.onclick=async(e)=>{e.preventDefault();let r=await fetch('/download?job='+j.id+'&file='+encodeURIComponent(f),{headers});if(!r.ok){s.textContent='Download fehlgeschlagen';return}let u=URL.createObjectURL(await r.blob()),link=document.createElement('a');link.href=u;link.download=f;link.click();setTimeout(()=>URL.revokeObjectURL(u),1000)};d.append(a,document.createElement('br'))}}};poll()}catch(e){s.textContent='Fehler: '+e.message}}
refresh().catch(e=>document.getElementById('up').textContent=e.message);
</script></html>'''

def unzip_checked(source,dest):
    with zipfile.ZipFile(source) as z:
        infos=z.infolist(); total=0
        if len(infos)>20000:raise ValueError('ZIP enthält zu viele Dateien.')
        for i in infos:
            path=Path(i.filename)
            if path.is_absolute() or '..' in path.parts or (i.external_attr>>16)&0o170000==0o120000:raise ValueError('ZIP enthält unsichere Dateipfade oder Links.')
            total+=i.file_size
            if total>MAX_EXTRACT:raise ValueError('Entpackte ZIP-Daten sind zu groß.')
        z.extractall(dest)
    matches=[p for p in [dest,*[x for x in dest.rglob('*') if x.is_dir()]] if is_capture(p)]
    if len(matches)!=1:raise ValueError('ZIP muss genau einen vollständigen Stray- oder SplatCapture-Ordner enthalten.')
    return matches[0]

def is_capture(p):
    stray=all((p/q).exists() for q in ('camera_matrix.csv','odometry.csv','rgb.mp4','depth'))
    splat=(p/'points.ply').is_file() and (p/'sparse'/'0').is_dir() and (p/'images').is_dir()
    return stray or splat

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def respond(self,code,data,ctype='application/json'):
        body=json.dumps(data,ensure_ascii=False).encode() if ctype=='application/json' else data.encode();self.send_response(code);self.send_header('Content-Type',ctype+'; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
    def authorized(self,q):return secrets.compare_digest(self.headers.get('X-Lidar-Token',''),TOKEN)
    def do_GET(self):
        u=urlsplit(self.path);q=parse_qs(u.query)
        if u.path=='/':return self.respond(200,PAGE,'text/html')
        if not self.authorized(q):return self.respond(403,{'error':'Zugriff verweigert'})
        if u.path=='/captures':
            captures=[]
            for p in (ROOT/'captures').iterdir():
                if p.is_dir() and (p/'meta.json').is_file():captures.append(json.loads((p/'meta.json').read_text()))
            return self.respond(200,{'captures':captures})
        if u.path=='/jobs':
            with LOCK:job=JOBS.get(q.get('id',[''])[0]);data=dict(job) if job else None
            return self.respond(200,data) if data else self.respond(404,{'error':'Unbekannter Auftrag'})
        if u.path=='/download':
            job=q.get('job',[''])[0];name=q.get('file',[''])[0]
            with LOCK:info=JOBS.get(job)
            if not info or info['state']!='completed' or name not in info['files']:return self.respond(404,{'error':'Nicht gefunden'})
            p=ROOT/'jobs'/job/name
            self.send_response(200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Disposition','attachment; filename="'+name+'"');self.send_header('Content-Length',str(p.stat().st_size));self.end_headers()
            with p.open('rb') as f:shutil.copyfileobj(f,self.wfile)
            return
        return self.respond(404,{'error':'Nicht gefunden'})
    def do_POST(self):
        u=urlsplit(self.path);q=parse_qs(u.query)
        if not self.authorized(q):return self.respond(403,{'error':'Zugriff verweigert'})
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<=0 or n>MAX_FILE:raise ValueError('Datei leer oder größer als 2 GiB.')
            if u.path=='/upload':
                name=Path(q.get('name',['upload'])[0]).name
                if not name.lower().endswith(('.zip','.webm','.mkv')):raise ValueError('Nur ZIP, WEBM oder MKV werden unterstützt.')
                cid=uuid.uuid4().hex;folder=ROOT/'captures'/cid;folder.mkdir();dest=folder/('upload'+Path(name).suffix.lower())
                try:
                    remaining=n
                    with dest.open('wb') as f:
                        while remaining:
                            chunk=self.rfile.read(min(1024*1024,remaining))
                            if not chunk:raise ValueError('Upload unterbrochen.')
                            f.write(chunk);remaining-=len(chunk)
                    if dest.suffix=='.zip':unzip_checked(dest,folder/'unpacked')
                    meta={'id':cid,'name':name,'size':n};(folder/'meta.json').write_text(json.dumps(meta,ensure_ascii=False))
                except Exception:shutil.rmtree(folder,ignore_errors=True);raise
                return self.respond(200,meta)
            if u.path=='/jobs':
                if n>4096:raise ValueError('Anfrage zu groß.')
                data=json.loads(self.rfile.read(n));ids=[data.get('a'),data.get('b')]; third=data.get('c'); ids += [third] if third else []
                if any(not isinstance(i,str) or len(i)!=32 or any(c not in '0123456789abcdef' for c in i) for i in ids):raise ValueError('Ungültige Aufnahmen.')
                if len(set(ids))!=len(ids):raise ValueError('Bitte unterschiedliche Aufnahmen auswählen.')
                mode=data.get('mode');
                if mode not in ('object','person'):raise ValueError('Ungültiger Modus.')
                with LOCK:
                    if any(j['state']=='running' for j in JOBS.values()):raise ValueError('Es läuft bereits ein Auftrag.')
                    jid=uuid.uuid4().hex;JOBS[jid]={'id':jid,'state':'running','log':'Vorbereitung …','files':[],'mode':mode}
                threading.Thread(target=run_job,args=(jid,ids,data),daemon=True).start()
                return self.respond(200,{'id':jid})
            return self.respond(404,{'error':'Nicht gefunden'})
        except (ValueError,OSError,zipfile.BadZipFile,json.JSONDecodeError) as e:return self.respond(400,{'error':str(e)})

def run_job(jid,ids,data):
    try:
        paths=[]
        for cid in ids:
            folder=ROOT/'captures'/cid
            if not (folder/'meta.json').is_file():raise ValueError('Aufnahme nicht gefunden.')
            zipfile_path=folder/'upload.zip'
            paths.append(unzip_checked_existing(folder/'unpacked') if zipfile_path.exists() else next(p for p in folder.glob('upload.*')))
        out=ROOT/'jobs'/jid
        cmd=[sys.executable,str(Path(__file__).with_name('lidarmonk_backend.py')),str(paths[0]),str(paths[1]),'--output',str(out)]
        if len(paths)>2:cmd+=['--capture-c',str(paths[2])]
        if data.get('motion') is True:cmd+=['--motion-correction']
        if data.get('tsdf'):cmd+=['--regional-tsdf','--voxel','0.08']
        if data.get('aligned'):cmd+=['--aligned-depth']
        # Person is an explicit warning, not an unimplemented motion correction.
        log='Personenmodus: keine nichtstarre Körperbewegungskorrektur; Ergebnisse prüfen.\n' if data['mode']=='person' else ''
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=7200)
        log+=(result.stdout+'\n'+result.stderr)[-12000:]
        files=sorted(p.name for p in out.iterdir() if p.is_file()) if out.exists() else []
        with LOCK:JOBS[jid].update(state='completed' if result.returncode==0 else 'failed',log=log,files=files if result.returncode==0 else [])
    except Exception as e:
        with LOCK:JOBS[jid].update(state='failed',log=str(e),files=[])

def unzip_checked_existing(dest):
    matches=[p for p in [dest,*[x for x in dest.rglob('*') if x.is_dir()]] if is_capture(p)]
    if len(matches)!=1:raise ValueError('Stray-Ordner nicht eindeutig.')
    return matches[0]

def lan_ipv4():
    """List candidate interface addresses; multiple interfaces may require a choice."""
    try:
        result=subprocess.run(['hostname','-I'],capture_output=True,text=True,check=True,timeout=3)
    except (OSError,subprocess.SubprocessError):
        return []
    addresses=[]
    for value in result.stdout.split():
        try: address=ipaddress.IPv4Address(value)
        except ipaddress.AddressValueError: continue
        if not (address.is_loopback or address.is_link_local or address.is_unspecified or address.is_multicast) and str(address) not in addresses:
            addresses.append(str(address))
    return addresses

def main():
    global ROOT, TOKEN
    p=argparse.ArgumentParser();p.add_argument('--data',default='lidarmonk-data');p.add_argument('--port',type=int,default=8765);p.add_argument('--lan',action='store_true',help='Im lokalen Netz über HTTP erreichbar machen; nur vertrauenswürdiges WLAN');p.add_argument('--cloud',action='store_true',help='Hosting hinter HTTPS: Zugriffsschlüssel aus LIDARMONK_ACCESS_TOKEN')
    a=p.parse_args()
    if a.cloud:
        TOKEN=os.environ.get('LIDARMONK_ACCESS_TOKEN','')
        if len(TOKEN)<32: p.error('LIDARMONK_ACCESS_TOKEN muss als geheimer Umgebungswert mindestens 32 Zeichen lang sein.')
    ROOT=Path(a.data).expanduser().resolve();(ROOT/'captures').mkdir(parents=True,exist_ok=True);(ROOT/'jobs').mkdir(exist_ok=True)
    host='0.0.0.0' if a.lan or a.cloud else '127.0.0.1';server=ThreadingHTTPServer((host,a.port),Handler);port=server.server_port
    if a.cloud: print('Cloud-Modus gestartet; Schlüssel wird nicht protokolliert.',flush=True)
    else: print('Lokal: http://127.0.0.1:'+str(port)+'/#'+TOKEN,flush=True)
    if a.lan and not a.cloud:
        print('LAN aktiv: HTTP ist unverschlüsselt. Nur im vertrauenswürdigen Heimnetz verwenden.',flush=True)
        addresses=lan_ipv4()
        if addresses:
            print('Am iPhone im selben WLAN öffnen (bei mehreren Adressen die WLAN-Adresse wählen):',flush=True)
            for address in addresses: print('  http://'+address+':'+str(port)+'/#'+TOKEN,flush=True)
        else:
            print('Keine LAN-Adresse automatisch gefunden. Rechner-IP mit hostname -I prüfen und http://<LINUX-IP>:'+str(port)+'/#'+TOKEN+' öffnen.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
