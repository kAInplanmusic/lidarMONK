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
