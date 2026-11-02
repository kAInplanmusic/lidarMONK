import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import regional_tsdf as rt

class RegionalTests(unittest.TestCase):
    def test_plane_reconstructs_at_one_meter(self):
        depth=np.ones((80,100),np.float32);K=np.array([[90.,0,50],[0,90,40],[0,0,1]])
        origin=np.array([-.2,-.15,.8]);shape=np.array([20,15,20]);v=.02
        sums,weights=rt.integrate([(depth,K,np.eye(4))],origin,shape,v,v*4,2)
        field,support,_,_=rt.route(sums,weights,np.zeros_like(sums),np.zeros_like(weights))
        vertices,faces,_=rt.surface(field,support,origin,v)
        self.assertGreater(len(faces),10);self.assertLess(abs(float(vertices[faces].reshape(-1,3)[:,2].mean())-1),.02)
    def test_conflicts_excluded_and_missing_filled(self):
        a=np.array([[[.8,.2,0]]],dtype=np.float32);aw=np.array([[[1,1,0]]],dtype=np.float32)
        b=np.array([[[-.8,.2,.4]]],dtype=np.float32);bw=np.array([[[1,1,1]]],dtype=np.float32)
        value,support,owner,conflict=rt.route(a,aw,b,bw)
        np.testing.assert_array_equal(conflict,[[[True,False,False]]]);np.testing.assert_array_equal(support,[[[False,True,True]]]);self.assertAlmostEqual(float(value[0,0,2]),.4,places=6)
    def test_memory_limit(self):
        with self.assertRaisesRegex(ValueError,'zu groß'):rt.integrate([],np.zeros(3),(200,200,200),.01,.04,5)
if __name__=='__main__': unittest.main()
