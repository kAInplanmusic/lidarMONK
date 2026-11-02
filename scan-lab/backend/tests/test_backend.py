import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np

spec=importlib.util.spec_from_file_location('backend',Path(__file__).resolve().parents[1]/'lidarmonk_backend.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class BackendTests(unittest.TestCase):
    def test_sample_frames_spans_capture(self):
        self.assertEqual(b.select_frames(1000, 10, 5), [0, 240, 490, 740, 990])
        self.assertEqual(b.select_frames(11, 5, 5), [0, 5, 10])
        self.assertEqual(b.select_frames(50, 2, 1), [0])

    def test_rigid_transform_validation(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'t.json';p.write_text(json.dumps(np.eye(4).tolist()));np.testing.assert_allclose(b.validate_transform(p),np.eye(4))
            m=np.eye(4);m[0,0]=2;p.write_text(json.dumps(m.tolist()))
            with self.assertRaises(ValueError): b.validate_transform(p)
    def test_strategies_align_known_translation(self):
        rng=np.random.default_rng(7); a=rng.uniform(-1,1,(500,3)); delta=np.array([.2,-.1,.3]); B=a-delta
        mat=np.eye(4);mat[:3,3]=delta
        for mode in ('separate','joint','incremental'):
            result=b.fusion([a],[B],mat,mode,.01)
            points=np.asarray(result.points)
            self.assertGreater(len(points),450)
            self.assertLess(np.linalg.norm(points.mean(axis=0)-a.mean(axis=0)),.01)
    def test_stray_rejects_missing_content(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(ValueError,'unvollständig'): b.prepare(t,t)

if __name__=='__main__': unittest.main()
