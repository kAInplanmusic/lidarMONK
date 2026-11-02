import io,json,os,subprocess,sys,tempfile,time,unittest,urllib.request,urllib.error,zipfile
from pathlib import Path

class ServerTest(unittest.TestCase):
 def test_upload_auth_and_zip_rejection(self):
  with tempfile.TemporaryDirectory() as t:
   p=subprocess.Popen([sys.executable,str(Path(__file__).resolve().parents[1]/'server.py'),'--port','0','--data',t],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   try:
    line=p.stdout.readline().strip();url=line.split('Lokal: ')[1];base,token=url.split('/#');
    with self.assertRaises(urllib.error.HTTPError) as err:urllib.request.urlopen(base+'/captures')
    self.assertEqual(err.exception.code,403)
    data=b'fake webm';req=urllib.request.Request(base+'/upload?name=test.webm',data=data,headers={'X-Lidar-Token':token});j=json.load(urllib.request.urlopen(req));self.assertEqual(j['size'],len(data))
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,'w') as z:z.writestr('../escape','bad')
    req=urllib.request.Request(base+'/upload?name=evil.zip',data=mem.getvalue(),headers={'X-Lidar-Token':token})
    with self.assertRaises(urllib.error.HTTPError) as err:urllib.request.urlopen(req)
    self.assertEqual(err.exception.code,400);self.assertFalse((Path(t).parent/'escape').exists())
    req=urllib.request.Request(base+'/captures',headers={'X-Lidar-Token':token});self.assertEqual(len(json.load(urllib.request.urlopen(req))['captures']),1)
   finally:p.terminate();p.wait(timeout=5);p.stdout.close();p.stderr.close()
if __name__=='__main__':unittest.main()

class JobOptionsTest(unittest.TestCase):
 def test_motion_is_opt_in(self):
  import importlib.util
  from unittest.mock import patch
  spec=importlib.util.spec_from_file_location('local_server',Path(__file__).resolve().parents[1]/'server.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
  with tempfile.TemporaryDirectory() as t:
   s.ROOT=Path(t);ids=['a'*32,'b'*32];(s.ROOT/'jobs').mkdir()
   for cid in ids:
    folder=s.ROOT/'captures'/cid;folder.mkdir(parents=True);(folder/'meta.json').write_text('{}');(folder/'upload.webm').write_bytes(b'demo')
   captured=[]
   class Result: returncode=0;stdout='';stderr=''
   def fake_run(cmd,**kwargs):captured.append(cmd);return Result()
   with patch.object(s.subprocess,'run',side_effect=fake_run):
    s.JOBS['one']={};s.run_job('one',ids,{'mode':'person','motion':False})
    s.JOBS['two']={};s.run_job('two',ids,{'mode':'person','motion':True})
   self.assertNotIn('--motion-correction',captured[0]);self.assertIn('--motion-correction',captured[1])

class CloudModeTest(unittest.TestCase):
 def test_cloud_rejects_missing_key(self):
  with tempfile.TemporaryDirectory() as t:
   env=os.environ.copy();env.pop('LIDARMONK_ACCESS_TOKEN',None)
   p=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'server.py'),'--cloud','--data',t],capture_output=True,text=True,env=env,timeout=5)
   self.assertNotEqual(p.returncode,0);self.assertIn('LIDARMONK_ACCESS_TOKEN',p.stderr)
 def test_cloud_requires_header_and_does_not_log_secret(self):
  with tempfile.TemporaryDirectory() as t:
   token='test-key-'+('a'*40);env=os.environ.copy();env['LIDARMONK_ACCESS_TOKEN']=token
   p=subprocess.Popen([sys.executable,str(Path(__file__).resolve().parents[1]/'server.py'),'--cloud','--port','0','--data',t],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
   try:
    line=p.stdout.readline();self.assertNotIn(token,line);self.assertIn('Cloud-Modus',line)
   finally:p.terminate();p.wait(timeout=5);p.stdout.close();p.stderr.close()

class LanAddressTest(unittest.TestCase):
 def test_ipv4_candidates_and_fallback(self):
  import importlib.util
  from unittest.mock import patch
  spec=importlib.util.spec_from_file_location('local_server_addresses',Path(__file__).resolve().parents[1]/'server.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
  class Result: stdout='127.0.0.1 192.168.1.22 192.168.1.22 fe80::1 172.17.0.1 invalid'
  with patch.object(s.subprocess,'run',return_value=Result()):
   self.assertEqual(s.lan_ipv4(),['192.168.1.22','172.17.0.1'])
  with patch.object(s.subprocess,'run',side_effect=FileNotFoundError()):
   self.assertEqual(s.lan_ipv4(),[])
