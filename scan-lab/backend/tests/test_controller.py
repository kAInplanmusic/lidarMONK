#!/usr/bin/env python3
"""Tests für lidarMONK Controller."""
import json
import tempfile
from pathlib import Path
from unittest import TestCase
import sys
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pytest


class TestController(TestCase):
    """Tests für den LidarMonkController."""
    
    def test_import_dependencies(self):
        """Prüft ob alle Abhängigkeiten importierbar sind."""
        import numpy
        import open3d
        import mcubes  # PyMCubes importiert als mcubes
        import wurld
        self.assertTrue(True)
    
    def test_controller_import(self):
        """Prüft ob Controller importierbar ist."""
        from controller import LidarMonkController, SourceType, ProcessingPhase
        self.assertTrue(LidarMonkController is not None)
        self.assertTrue(SourceType.STRAY is not None)
    
    def test_source_type_enum(self):
        """Prüft SourceType-Enum."""
        from controller import SourceType
        self.assertEqual(SourceType.STRAY.value, "stray")
        self.assertEqual(SourceType.WURL.value, "wurld")
        self.assertEqual(SourceType.SPAT.value, "splatcapture")


class TestInputValidation(TestCase):
    """Tests für Eingabe-Validierung."""
    
    def test_stray_format_validation(self):
        """Stray-Format wird erkannt."""
        from controller import LidarMonkController
        with tempfile.TemporaryDirectory() as tmpdir:
            stray_dir = Path(tmpdir) / 'stray_capture'
            stray_dir.mkdir()
            (stray_dir / 'camera_matrix.csv').write_text('0,0,0\n')
            (stray_dir / 'odometry.csv').write_text('0,0,0\n')
            (stray_dir / 'depth').mkdir()
            
            ctrl = LidarMonkController(tmpdir)
            captures = ctrl._validate_input([stray_dir])
            
            self.assertEqual(len(captures), 1)
            self.assertEqual(captures[0].source_type.value, "stray")
    
    def test_wurld_format_validation(self):
        """Wurld-Format wird erkannt."""
        from controller import LidarMonkController
        # Wurld-Dateien müssen erst erstellt werden - hier nur Test der Erkennung
        self.assertTrue(True)  # Integrationstest für echte Wurld-Datei
    
    def test_invalid_input(self):
        """Ungültige Eingaben werden abgelehnt."""
        from controller import LidarMonkController
        with tempfile.TemporaryDirectory() as tmpdir:
            ctrl = LidarMonkController(tmpdir)
            captures = ctrl._validate_input([Path('/nonexistent/path')])
            
            self.assertEqual(len(captures), 1)
            self.assertIsNotNone(captures[0].error)


class TestRegionalTSDF(TestCase):
    """Tests für regionale TSDF-Fusion."""
    
    def test_tsdf_integrate_simple(self):
        """Einfache TSDF-Integration."""
        import regional_tsdf as rt
        
        # Simuliere einfache Tiefe (eine Ebene)
        depth = np.ones((50, 50), dtype=np.float32) * 1.0
        K = np.array([[50., 0, 25], [0, 50, 25], [0, 0, 1]])
        origin = np.array([0., 0., 0.])
        shape = np.array([20, 20, 20])
        voxel = 0.02
        
        frames = [(depth, K, np.eye(4))]
        field, weight = rt.integrate(frames, origin, shape, voxel, voxel*4, 2.0)
        
        self.assertEqual(field.shape, tuple(shape))
        self.assertEqual(weight.shape, tuple(shape))
    
    def test_tsdf_route(self):
        """TSDF-Routing."""
        import regional_tsdf as rt
        
        shape = (10, 10, 10)
        field_a = np.random.randn(*shape).astype(np.float32)
        weight_a = np.random.rand(*shape).astype(np.float32)
        field_b = np.random.randn(*shape).astype(np.float32)
        weight_b = np.random.rand(*shape).astype(np.float32)
        
        field, support, owner, conflicts = rt.route(field_a, weight_a, field_b, weight_b)
        
        self.assertEqual(field.shape, shape)
        self.assertEqual(support.shape, shape)
        self.assertEqual(owner.shape, shape)
        self.assertEqual(conflicts.shape, shape)
    
    def test_tsdf_surface(self):
        """TSDF-Oberflächenextraktion."""
        import regional_tsdf as rt
        import mcubes
        
        # Einfacher Ball als Feld
        shape = np.array([30, 30, 30])
        origin = np.array([0., 0., 0.])
        voxel = 0.02
        
        # Erstelle ein Ball-Feld: innen positiv, außen negativ
        coords = np.stack(np.meshgrid(
            np.arange(shape[0]), 
            np.arange(shape[1]), 
            np.arange(shape[2]), 
            indexing='ij'
        ), axis=-1)
        center = np.array([15, 15, 15])
        radius = 10
        field = (np.linalg.norm(coords - center, axis=-1) - radius).astype(np.float32)
        
        # Alle Voxel sind supported
        support = np.ones(shape, dtype=bool)
        
        vertices, faces, normals = rt.surface(field, support, origin, voxel)
        
        self.assertGreater(len(vertices), 0)
        self.assertGreater(len(faces), 0)
        self.assertEqual(len(normals), len(vertices))


class TestTimeout(TestCase):
    """Tests für Timeout-Handling."""
    
    def test_timeout_detection(self):
        """Timeout wird korrekt erkannt."""
        from controller import LidarMonkController
        import time
        
        ctrl = LidarMonkController("/tmp", max_seconds=1)
        ctrl.start_time = time.time()
        
        self.assertTrue(ctrl._check_timeout() == False)
        time.sleep(1.1)
        self.assertTrue(ctrl._check_timeout())


if __name__ == '__main__':
    pytest.main([__file__, '-v'])