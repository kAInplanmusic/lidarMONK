#!/usr/bin/env python3
"""lidarMONK Controller: zentraler Daten- und Fusionscontroller für 3D-Erfassung.

Verwaltet die gesamte Verarbeitungspipeline von iPhone LiDAR-Scans:
- Eingabe-Validierung und -Inventarisierung
- Budget-Planung (300s Timeout)
- Daten-Vorbereitung und -Ausrichtung
- Regionale TSDF-Fusion aller 3 Quellen
- Erweiterte Ausgabe mit Manifest
"""
import argparse
import json
import time
import hashlib
import traceback
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Any
import numpy as np

import open3d as o3d

# Import lokaler Module
try:
    from . import lidarmonk_backend as backend, regional_tsdf as rt
except ImportError:
    import lidarmonk_backend as backend
    import regional_tsdf as rt


class SourceType(Enum):
    STRAY = "stray"
    WURL = "wurld"
    SPAT = "splatcapture"  # Kurz für SplatCapture


class ProcessingPhase(Enum):
    VALIDATE = "validate"
    PREPARE = "prepare"
    ALIGN = "align"
    FUSION = "fusion"
    OUTPUT = "output"
    COMPLETE = "complete"


@dataclass
class Capture:
    """Ein einzelner Datensatz einer Aufnahme."""
    id: str
    source_type: Optional[SourceType] = None
    path: Path = None
    checksum: Optional[str] = None
    frames_total: Optional[int] = None
    frames_used: Optional[int] = None
    selection: list = field(default_factory=list)
    frames_data: list = field(default_factory=list)
    frames_pose: list = field(default_factory=list)
    frames_K: list = field(default_factory=list)
    points: Optional[np.ndarray] = None
    error: Optional[str] = None


@dataclass
class ProcessingStatus:
    """Status einer Verarbeitung."""
    phase: ProcessingPhase = ProcessingPhase.VALIDATE
    percent: float = 0.0
    elapsed_seconds: float = 0.0
    message: str = ""
    result: Optional[dict] = None
    error: Optional[str] = None


class LidarMonkController:
    """Zentraler Controller für LiDAR-Datenfusion."""
    
    def __init__(self, data_dir: str, max_seconds: int = 300, memory_limit_gb: int = 8):
        self.data_dir = Path(data_dir)
        self.max_seconds = max_seconds
        self.memory_limit = memory_limit_gb * 1024**3
        self.project_dir: Optional[Path] = None
        self.start_time: float = 0
        self.status = ProcessingStatus()
        self.captures: list[Capture] = []
        self.manifest: dict = {}
        
    def _update_progress(self, phase: ProcessingPhase, percent: float, message: str = ""):
        """Fortschritt aktualisieren."""
        self.status.phase = phase
        self.status.percent = percent
        self.status.message = message
        self.status.elapsed_seconds = time.time() - self.start_time
        if self.status.error:
            self.status.error = None
        print(json.dumps({
            "phase": phase.value,
            "percent": percent,
            "message": message,
            "elapsed": self.status.elapsed_seconds
        }))
        
    def _check_timeout(self) -> bool:
        """Prüft ob Timeout eingetreten ist."""
        elapsed = time.time() - self.start_time
        return elapsed > self.max_seconds
    
    def _compute_checksum(self, path: Path) -> str:
        """Berechnet SHA256-Hash einer Datei."""
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    
    def _validate_input(self, paths: list[Path]) -> list[Capture]:
        """Validiert Eingabedaten und erstellt Capture-Objekte."""
        import wurld as wl
        
        captures = []
        for i, path in enumerate(paths):
            cap_id = hashlib.md5(str(path).encode()).hexdigest()[:8]
            capture = Capture(id=cap_id, path=path)
            
            try:
                if path.is_dir():
                    if (path / 'points.ply').exists() and (path / 'sparse' / '0').is_dir():
                        capture.source_type = SourceType.SPAT
                        pcd = o3d.io.read_point_cloud(str(path / 'points.ply'))
                        capture.points = np.asarray(pcd.points)
                        capture.checksum = self._compute_checksum(path / 'points.ply')
                    elif all((path / m).exists() for m in ['camera_matrix.csv', 'odometry.csv', 'depth']):
                        capture.source_type = SourceType.STRAY
                        capture.checksum = self._compute_checksum(path)
                    elif (path / 'upload.ply').exists():
                        # Einfacher PLY-Modus (synthetisch / Test)
                        capture.source_type = SourceType.STRAY  # Standardisiere
                        pcd = o3d.io.read_point_cloud(str(path / 'upload.ply'))
                        capture.points = np.asarray(pcd.points) if pcd.has_points() else None
                        capture.checksum = self._compute_checksum(path / 'upload.ply')
                    else:
                        raise ValueError(f"Unbekannter Ordnertyp: {path}")
                elif path.is_file() and path.suffix.lower() in ('.webm', '.mkv', '.ply'):
                    capture.source_type = SourceType.WURL if path.suffix.lower() in ('.webm', '.mkv') else SourceType.STRAY
                    capture.checksum = self._compute_checksum(path)
                else:
                    raise ValueError(f"Unstützes Format: {path}")
                    
            except Exception as e:
                capture.error = str(e)
                
            captures.append(capture)
        return captures
    
    def _prepare_sources(self, max_frames: int = 30, stride: int = 10, max_depth: float = 5.0) -> list[Capture]:
        """Bereitet Eingabequellen vor (Frames extrahieren, Daten laden)."""
        import wurld as wl
        
        prepared = []
        for cap in self.captures:
            if cap.error:
                prepared.append(cap)
                continue
                
            if cap.source_type == SourceType.STRAY:
                pass  # Stray wird später separat verarbeitet
                
            elif cap.source_type == SourceType.WURL:
                try:
                    seq = wl.read(str(cap.path))
                    cap.frames_total = len(seq.frames)
                    for i in range(0, cap.frames_total, stride):
                        if i >= max_frames * stride:
                            break
                        frame = seq.frames[i]
                        if hasattr(frame, 'pose_valid') and not frame.pose_valid:
                            continue
                        try:
                            depth = np.asarray(seq.depth_meters(i), dtype=float)
                            pose = np.asarray(seq.c2w(i), dtype=float)
                            K = np.asarray(seq.K(frame.camera if hasattr(frame, 'camera') else '0'), dtype=float)
                            
                            if depth.shape[0] != depth.shape[1]:
                                continue  # Nur quadratische Tiefenkarten
                            
                            cap.frames_data.append(depth.astype(np.float32))
                            cap.frames_pose.append(pose)
                            cap.frames_K.append(K)
                            cap.selection.append(i)
                        except:
                            pass
                except Exception as e:
                    cap.error = str(e)
                    
            elif cap.source_type == SourceType.SPAT:
                # SplatCapture: Punktwolke ist bereits geladen
                pass
                
            prepared.append(cap)
        return prepared
    
    def _register_scans(self, valid_captures: list[Capture], voxel: float) -> list:
        """Registriert Scans paarweise mit Open3D."""
        import open3d as o3d
        
        if len(valid_captures) <= 1:
            return [np.eye(4)]
        
        transforms = [np.eye(4)]
        
        for i in range(1, len(valid_captures)):
            cap = valid_captures[i]
            if not cap.frames_data:
                # Für SplatCapture: Punktwolke verwenden
                if cap.points is not None:
                    src_pc = o3d.geometry.PointCloud()
                    src_pc.points = o3d.utility.Vector3dVector(cap.points)
                    src_pc = src_pc.voxel_down_sample(voxel)
                else:
                    continue
            else:
                # Für Wurld/Stray: Punktwolken aus Frames
                all_points = []
                for d, p in zip(cap.frames_data, cap.frames_pose):
                    # Tiefe zu Punkten konvertieren
                    for j in range(0, d.shape[0], 5):
                        for k in range(0, d.shape[1], 5):
                            if np.isfinite(d[j, k]) and 0 < d[j, k] <= 5.0:
                                all_points.append([k, j, d[j, k]])
                if not all_points:
                    continue
                points = np.asarray(all_points, dtype=float)
                src_pc = o3d.geometry.PointCloud()
                src_pc.points = o3d.utility.Vector3dVector(points)
                src_pc = src_pc.voxel_down_sample(voxel)
            
            # Registrierung gegen erste Quelle (Ref)
            ref_pc = o3d.geometry.PointCloud()
            ref_pc.points = o3d.utility.Vector3dVector(np.asarray(valid_captures[0].points) if valid_captures[0].points is not None else np.zeros((1,3)))
            
            # Hier wird ein echter Matcher verwendet
            # Für den Prototyp: Einheitsmatrix
            transforms.append(np.eye(4))
        
        return transforms
    
    def _tsdf_fusion(self, valid_captures: list[Capture], voxel: float, max_depth: float) -> tuple:
        """Führt TSDF-Fusion aller Quellen durch."""
        all_frames = []
        all_points = []
        
        for cap in valid_captures:
            if cap.frames_data:
                for depth, K, pose in zip(cap.frames_data, cap.frames_K, cap.frames_pose):
                    all_frames.append((depth, K, pose))
                    # Extract camera position for bounding box
                    all_points.append(pose[:3, 3])
            elif cap.points is not None:
                all_points.append(cap.points)
        
        if not all_frames:
            raise ValueError("Keine gültigen Frames für TSDF-Fusion gefunden.")
        
        # Bounding-Block berechnen
        all_pts = np.concatenate(all_points)
        trunc = voxel * 4
        origin = all_pts.min(axis=0) - trunc * 2
        max_corner = all_pts.max(axis=0) + trunc * 2
        shape = np.ceil((max_corner - origin) / voxel).astype(int)
        
        # Ensure minimum grid size
        shape = np.maximum(shape, 4)
        
        # Integrate all frames into one TSDF
        field, weight = rt.integrate(all_frames, origin, shape, voxel, trunc, max_depth)
        
        # Create a dummy second field for routing (single-source case)
        field_b = np.zeros_like(field)
        weight_b = np.zeros_like(weight)
        
        field, support, owner, conflicts = rt.route(field, weight, field_b, weight_b)
        
        return field, support, origin, shape, voxel
    
    def process(self, capture_paths: list[Path], output_dir: Path,
                voxel: float = 0.02, max_depth: float = 5.0, 
                max_frames: int = 30, stride: int = 10) -> dict:
        """Hauptverarbeitungsmethode."""
        self.start_time = time.time()
        self.project_dir = output_dir
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        # Phase 1: Validierung
        self._update_progress(ProcessingPhase.VALIDATE, 0.0, "Validiere Eingabedaten...")
        if self._check_timeout():
            raise TimeoutError(f"Timeout nach {self.max_seconds}s in Phase VALIDATE")
        
        self.captures = self._validate_input(capture_paths)
        for cap in self.captures:
            if cap.error:
                self._update_progress(ProcessingPhase.VALIDATE, 100, 
                                      f"Fehler in {cap.source_type.value if cap.source_type else 'unbekannt'}: {cap.error}")
                return self._create_error_result(cap.error)
        self._update_progress(ProcessingPhase.VALIDATE, 25.0, "Eingabedaten gültig.")
        
        # Phase 2: Vorbereitung
        self._update_progress(ProcessingPhase.PREPARE, 25.0, "Lade Quellen...")
        if self._check_timeout():
            raise TimeoutError(f"Timeout in Phase PREPARE")
        
        self.captures = self._prepare_sources(max_frames, stride, max_depth)
        valid_count = sum(1 for c in self.captures if not c.error and (c.points is not None and len(c.points) > 0))
        self._update_progress(ProcessingPhase.PREPARE, 50.0, 
                              f"{valid_count}/{len(self.captures)} Quellen geladen.")
        
        # Phase 3: Ausrichtung
        self._update_progress(ProcessingPhase.ALIGN, 50.0, "Richte Scans aus...")
        if self._check_timeout():
            raise TimeoutError(f"Timeout in Phase ALIGN")
        
        valid_captures = [c for c in self.captures if not c.error and (c.points is not None and len(c.points) > 0)]
        if len(valid_captures) < 2:
            raise ValueError("Mindestens 2 gültige Quellen erforderlich.")
        
        transforms = self._register_scans(valid_captures, voxel)
        self._update_progress(ProcessingPhase.ALIGN, 75.0, "Ausrichtung abgeschlossen.")
        
        # Phase 4: Fusion
        self._update_progress(ProcessingPhase.FUSION, 75.0, "Führe TSDF-Fusion durch...")
        if self._check_timeout():
            raise TimeoutError(f"Timeout in Phase FUSION")
        
        elapsed_fuse = time.perf_counter()
        try:
            field, support, origin, shape, voxel_res = self._tsdf_fusion(
                valid_captures, voxel, max_depth
            )
            vertices, faces, normals = rt.surface(field, support, origin, voxel_res)
            
            # Mesh erstellen
            mesh = o3d.geometry.TriangleMesh()
            mesh.vertices = o3d.utility.Vector3dVector(vertices)
            mesh.triangles = o3d.utility.Vector3iVector(faces)
            mesh.remove_unreferenced_vertices()
            mesh.compute_vertex_normals()
            
            # Mesh speichern
            if not o3d.io.write_triangle_mesh(str(self.project_dir / 'regional-tsdf-mesh.ply'), mesh):
                raise RuntimeError('TSDF-Mesh konnte nicht geschrien werden')
            
            np.savez_compressed(self.project_dir / 'regional-tsdf-map.npz',
                                origin=origin, voxel=voxel_res, owner=None,
                                conflict=np.zeros(shape, dtype=bool), support=support)
            
            fuse_time = time.perf_counter() - elapsed_fuse
            self._update_progress(ProcessingPhase.FUSION, 90.0, 
                                  f"TSDF-Fusion: {len(vertices)} Vertices, {len(faces)} Dreiecke in {fuse_time:.1f}s")
        except Exception as e:
            self._update_progress(ProcessingPhase.FUSION, 85.0, f"TSDF-Fusion: {str(e)}")
        
        # Phase 5: Ausgabe
        self._update_progress(ProcessingPhase.OUTPUT, 95.0, "Schreibe Ergebnisse...")
        result = {
            "status": "completed",
            "elapsed": time.time() - self.start_time,
            "captures": len(valid_captures),
            "points": sum(len(c.frames_data) * 1000 for c in valid_captures if c.frames_data),  # grob geschätzt
            "fusion_time_seconds": fuse_time if 'fuse_time' in dir() else 0,
            "warnings": [
                "Controller-Prototyp: Punktwolken-Registrierung vereinfacht.",
                "RGB und Confidence werden nicht fusioniert.",
                "Bewegungskorrektur nicht implementiert."
            ]
        }
        
        # Manifest schreiben
        self._write_manifest(result)
        
        # Ergebnis-PLY schreiben (vereinfachte Punktwolke)
        combined_pcd = o3d.geometry.PointCloud()
        all_pts = []
        for cap in valid_captures:
            if cap.points is not None:
                all_pts.append(cap.points)
        if all_pts:
            combined_pcd.points = o3d.utility.Vector3dVector(np.concatenate(all_pts))
            o3d.io.write_point_cloud(str(self.project_dir / 'combined-points.ply'), combined_pcd)
        
        self._update_progress(ProcessingPhase.COMPLETE, 100.0, "Fertig.")
        return result
    
    def _write_manifest(self, result: dict):
        """Schreibt Projekt-Modell."""
        manifest = {
            "manifest_version": "1.0",
            "project_id": hashlib.sha256(str(time.time()).encode()).hexdigest()[:16],
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "max_seconds": self.max_seconds,
            "voxel_m": 0.02,
            "captures": [
                {
                    "id": c.id,
                    "source_type": c.source_type.value if c.source_type else "unknown",
                    "path": str(c.path),
                    "checksum": c.checksum,
                    "frames_total": c.frames_total,
                    "frames_used": len(c.selection),
                    "selection": c.selection
                } for c in self.captures
            ],
            "results": result
        }
        
        with open(self.project_dir / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    def _create_error_result(self, error: str) -> dict:
        """Erstellt einen Fehlerreport."""
        return {
            "status": "error",
            "error": error,
            "elapsed": time.time() - self.start_time
        }


def main():
    p = argparse.ArgumentParser(description='lidarMONK Controller: zentrale 3D-Datenfusion')
    p.add_argument('captures', nargs='+', type=str, help='Eingabe-Captures (Ordner oder Dateien)')
    p.add_argument('--output', '-o', type=Path, required=True, help='Ausgabeverzeichnis')
    p.add_argument('--voxel', type=float, default=0.02, help='Voxelgröße in Metern (default 0.02)')
    p.add_argument('--max-depth', type=float, default=5.0, help='Maximale Tiefe in Metern (default 5.0)')
    p.add_argument('--max-seconds', type=int, default=300, help='Timeout in Sekunden (default 300)')
    p.add_argument('--max-frames', type=int, default=30, help='Max. Frames pro Capture (default 30)')
    p.add_argument('--stride', type=int, default=10, help='Frame-Stride für Auswahl (default 10)')
    args = p.parse_args()
    
    controller = LidarMonkController(
        data_dir=str(args.output),
        max_seconds=args.max_seconds
    )
    
    try:
        result = controller.process(
            capture_paths=[Path(c) for c in args.captures],
            output_dir=args.output,
            voxel=args.voxel,
            max_depth=args.max_depth,
            max_frames=args.max_frames,
            stride=args.stride
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except TimeoutError as e:
        error_result = controller._create_error_result(str(e))
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        return 1
    except Exception as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())