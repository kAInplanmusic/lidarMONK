#!/usr/bin/env python3
"""Generiert synthetische Test-Daten für den Controller-End-to-End-Test."""
import numpy as np
import json
from pathlib import Path

def generate_test_data(base_dir: Path):
    """Erstellt Test-Captures mit synthetischen Punktwolken."""
    captures_dir = base_dir / 'captures'
    captures_dir.mkdir(parents=True, exist_ok=True)
    
    # 3 Quellen: Stray, Wurld, SplatCapture
    sources = ['stray', 'wurld', 'splatcapture']
    
    for i, src in enumerate(sources):
        capture_dir = captures_dir / f'test_{src}'
        capture_dir.mkdir(parents=True, exist_ok=True)
        
        # Generiere synthetische Punktwolke (Punkte auf einer Ebene bei z=1.0)
        n_points = 1000
        points = np.random.rand(n_points, 3) * 2.0  # 0-2m
        points[:, 2] = 1.0 + np.random.randn(n_points) * 0.05  # Ebene bei z=1.0
        
        # Speichere als PLY
        ply_path = capture_dir / 'upload.ply'
        with open(ply_path, 'w') as f:
            f.write(f'ply\n')
            f.write(f'format ascii 1.0\n')
            f.write(f'element vertex {n_points}\n')
            f.write(f'property float x\n')
            f.write(f'property float y\n')
            f.write(f'property float z\n')
            for p in points:
                f.write(f'{p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n')
        
        # Meta.json
        meta = {
            'source': src,
            'timestamp': '2026-11-02T18:00:00Z',
            'n_points': n_points,
            'bounds': {'min': [0, 0, 0.9], 'max': [2, 2, 1.1]}
        }
        with open(capture_dir / 'meta.json', 'w') as f:
            json.dump(meta, f, indent=2)
        
        print(f"  {src}: {n_points} Punkte -> {ply_path}")
    
    return captures_dir

if __name__ == '__main__':
    base = Path('/home/patrick/lidarMONK/scan-lab/test-data')
    print(f"Generiere Test-Daten in {base}...")
    generate_test_data(base)
    print("Fertig!")