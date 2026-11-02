import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import motion
class MotionTests(unittest.TestCase):
 def test_rigid_translation_and_large_shift_rejected(self):
  rng=np.random.default_rng(42);anchor=rng.uniform(-.3,.3,(1200,3));moving=anchor+np.array([.02,0,0]);bad=anchor+np.array([3.,0,0]);pose=np.eye(4);d=np.ones((4,4));k=np.eye(3)
  frames,rgbd,stats=motion.correct([anchor,moving,bad],[(d,k,pose)]*3,voxel=.03,max_shift=.1)
  self.assertEqual(len(frames),2);self.assertEqual(stats[1]['status'],'accepted');self.assertEqual(stats[2]['status'],'rejected');self.assertLess(np.linalg.norm(frames[1].mean(0)-anchor.mean(0)),.015);self.assertAlmostEqual(rgbd[1][2][0,3],-.02,delta=.015)
if __name__=='__main__':unittest.main()
