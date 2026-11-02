#!/usr/bin/env python3
"""Experimental local RGB-D fusion for Stray Scanner and WurldCam."""
import argparse, json, os, subprocess, sys, tempfile, time
from pathlib import Path
import numpy as np


def o3d():
    try:
        import open3d
        return open3d
    except ImportError as e:
        raise RuntimeError('Open3D fehlt: pip install -r requirements.txt') from e

def cloud(points, colors=None):
    lib=o3d(); p=lib.geometry.PointCloud(); p.points=lib.utility.Vector3dVector(np.asarray(points,dtype=float))
    if colors is not None and len(colors)==len(points): p.colors=lib.utility.Vector3dVector(np.asarray(colors,dtype=float))
    return p

def prepare(path, tmp):
    path=Path(path)
    if path.is_file() and path.suffix.lower()=='.zip':
        raise ValueError('ZIP-Dateien bitte zuerst in einen eigenen Ordner entpacken; automatische Archivverarbeitung ist nicht aktiviert.')
    if path.is_dir():
        for marker in ('camera_matrix.csv','odometry.csv','depth'):
            if not (path/marker).exists(): raise ValueError(f'Stray-Ordner unvollständig: {marker} fehlt')
        out=Path(tmp)/'capture.wurld.webm'
        subprocess.run([sys.executable,'-m','wurld.cli','convert',str(path),str(out)],check=True)
        return out,'stray'
    if not path.exists(): raise ValueError(f'Datei nicht gefunden: {path}')
    if not path.name.lower().endswith(('.webm','.mkv')): raise ValueError('Wurld-Datei (.webm/.mkv) oder entpackten Stray-Ordner angeben.')
    return path,'wurld'

def get_frames(path, max_frames, stride, depth_max, pixel_step):
    import wurld as wl
    seq=wl.read(str(path)); n=len(seq.frames)
    if n==0: raise ValueError('Keine Kameraposen/Frames gefunden; Datei ist kein auswertbarer Wurld-Datensatz.')
    selected=list(range(0,n,stride))[:max_frames]; output=[]; stats=[]
    for i in selected:
        frame=seq.frames[i]
        if hasattr(frame,'pose_valid') and not frame.pose_valid: continue
        try:
            depth=np.asarray(seq.depth_meters(i),dtype=float)
            pose=np.asarray(seq.c2w(i),dtype=float)
            camera_id=str(getattr(frame,'camera','0'))
            try: K=np.asarray(seq.K(camera_id,frame_index=i),dtype=float)
            except TypeError: K=np.asarray(seq.K(camera_id),dtype=float)
        except Exception as e: raise ValueError(f'Frame {i}: Tiefe, Pose oder Kalibrierung nicht lesbar: {e}') from e
        if depth.ndim!=2 or pose.shape!=(4,4) or K.shape!=(3,3) or not np.all(np.isfinite(pose)) or not np.all(np.isfinite(K)) or K[0,0]<=0 or K[1,1]<=0: raise ValueError(f'Frame {i}: ungültige Kalibrierung/Pose/Tiefenformat')
        good=np.isfinite(depth)&(depth>0)&(depth<=depth_max); stats.append({'frame':i,'pixels':int(depth.size),'valid_within_range':int(good.sum()),'percent_within_range':round(100*float(good.sum())/depth.size,2)})
        yy,xx=np.mgrid[0:depth.shape[0]:pixel_step,0:depth.shape[1]:pixel_step]; z=depth[::pixel_step,::pixel_step]; mask=np.isfinite(z)&(z>0)&(z<=depth_max); x=xx[mask]; y=yy[mask]; z=z[mask]
        # Depth and K must be at the same resolution; do not infer scaling silently.
        camera=seq.cameras[camera_id]
        if getattr(camera,'model','PINHOLE') not in ('PINHOLE','SIMPLE_PINHOLE'): raise ValueError(f'Frame {i}: Kameramodell {camera.model} wird noch nicht entzerrt; Verarbeitung abgebrochen.')
        cw=int(getattr(camera,'width',depth.shape[1])); ch=int(getattr(camera,'height',depth.shape[0]))
        if (cw,ch)!=(depth.shape[1],depth.shape[0]): raise ValueError(f'Frame {i}: Kameraauflösung {cw}x{ch} != Tiefenauflösung {depth.shape[1]}x{depth.shape[0]}; sichere Kalibrierung erforderlich.')
        pts=np.column_stack(((x-K[0,2])*z/K[0,0],(y-K[1,2])*z/K[1,1],z,np.ones(len(z))))
        pts=(pose@pts.T).T[:,:3]; output.append(pts)
    if not output or not sum(map(len,output)): raise ValueError('Keine gültigen Tiefenpunkte in ausgewählten Frames.')
    return output,{'frames_total':n,'frames_used':len(output),'depth_limit_m':depth_max,'frames':stats,'color':'nicht implementiert','confidence_filter':'nicht implementiert'}

def register(a,b,voxel):
    lib=o3d(); a=a.voxel_down_sample(voxel); b=b.voxel_down_sample(voxel)
    if len(a.points)<30 or len(b.points)<30: raise ValueError('Zu wenige Punkte für automatische Registrierung.')
    for p in (a,b): p.estimate_normals(lib.geometry.KDTreeSearchParamHybrid(radius=voxel*3,max_nn=30))
    af=lib.pipelines.registration.compute_fpfh_feature(a,lib.geometry.KDTreeSearchParamHybrid(radius=voxel*5,max_nn=100))
    bf=lib.pipelines.registration.compute_fpfh_feature(b,lib.geometry.KDTreeSearchParamHybrid(radius=voxel*5,max_nn=100))
    reg=lib.pipelines.registration
    # b -> a: global initialization followed by local geometric refinement.
    coarse=reg.registration_ransac_based_on_feature_matching(b,a,bf,af,True,voxel*2,reg.TransformationEstimationPointToPoint(False),3,[reg.CorrespondenceCheckerBasedOnEdgeLength(.9),reg.CorrespondenceCheckerBasedOnDistance(voxel*2)],reg.RANSACConvergenceCriteria(50000,.999))
    result=reg.registration_icp(b,a,voxel*1.5,coarse.transformation,reg.TransformationEstimationPointToPlane())
    m=np.asarray(result.transformation)
    if not np.isfinite(m).all() or result.fitness<.15: raise ValueError(f'Registrierung unsicher (Überlappung {result.fitness:.3f}); mehr gemeinsame Ansichten oder explizite Transformationsmatrix verwenden.')
    return m,{'fitness':float(result.fitness),'inlier_rmse_m':float(result.inlier_rmse),'threshold_m':voxel*1.5,'warning':'Fitness ist kein Beweis korrekter Ausrichtung; Symmetrien können falsche Übereinstimmungen erzeugen.'}

def validate_transform(path):
    m=np.asarray(json.loads(Path(path).read_text()),dtype=float)
    if m.shape!=(4,4) or not np.isfinite(m).all() or not np.allclose(m[3],[0,0,0,1],atol=1e-6) or not np.allclose(m[:3,:3].T@m[:3,:3],np.eye(3),atol=1e-3) or not np.isclose(np.linalg.det(m[:3,:3]),1,atol=1e-3): raise ValueError('Transformation muss eine starre 4x4-Matrix sein (Rotation, Translation, letzte Zeile 0 0 0 1).')
    return m

def transformed(points,m): return (m[:3,:3]@points.T).T+m[:3,3]

def fusion(frames_a,frames_b,m,method,voxel):
    lib=o3d()
    if method=='separate':
        a=cloud(np.concatenate(frames_a)).voxel_down_sample(voxel);b=cloud(np.concatenate(frames_b)).voxel_down_sample(voxel);b.transform(m);return (a+b).voxel_down_sample(voxel)
    if method=='joint': return cloud(np.concatenate(frames_a+[transformed(p,m) for p in frames_b])).voxel_down_sample(voxel)
    if method=='incremental':
        result=lib.geometry.PointCloud()
        for i in range(max(len(frames_a),len(frames_b))):
            if i<len(frames_a): result+=cloud(frames_a[i])
            if i<len(frames_b): result+=cloud(transformed(frames_b[i],m))
            result=result.voxel_down_sample(voxel)
        return result
    raise ValueError('Unbekannte Methode')

def write_cloud(path,p):
    if not o3d().io.write_point_cloud(str(path),p,write_ascii=False): raise RuntimeError(f'PLY konnte nicht geschrieben werden: {path}')

def main():
    p=argparse.ArgumentParser(description='lidarMONK: zwei RGB-D-Aufnahmen aus Stray/Wurld vergleichen und fusionieren')
    p.add_argument('capture_a');p.add_argument('capture_b');p.add_argument('--output',required=True);p.add_argument('--voxel',type=float,default=.02);p.add_argument('--max-depth',type=float,default=5);p.add_argument('--stride',type=int,default=10);p.add_argument('--max-frames',type=int,default=30);p.add_argument('--pixel-step',type=int,default=4);p.add_argument('--transform',help='JSON 4x4 starre Matrix von B nach A; ohne Angabe automatische Registrierung');p.add_argument('--mesh',action='store_true',help='optionales Poisson-Mesh: experimentell, kann Oberflächen erfinden')
    a=p.parse_args()
    if a.voxel<=0 or a.max_depth<=0 or a.stride<1 or a.max_frames<1 or a.pixel_step<1: p.error('Parameter müssen positiv sein')
    output=Path(a.output)
    if output.exists() and any(output.iterdir()): p.error('Ausgabeordner muss leer oder neu sein, damit nichts überschrieben wird.')
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='lidarmonk-') as temp:
        ta=Path(temp)/'a';tb=Path(temp)/'b';ta.mkdir();tb.mkdir()
        fa,ka=prepare(a.capture_a,ta);fb,kb=prepare(a.capture_b,tb)
        A,sa=get_frames(fa,a.max_frames,a.stride,a.max_depth,a.pixel_step);B,sb=get_frames(fb,a.max_frames,a.stride,a.max_depth,a.pixel_step)
        ca=cloud(np.concatenate(A)).voxel_down_sample(a.voxel);cb=cloud(np.concatenate(B)).voxel_down_sample(a.voxel)
        if a.transform: m=validate_transform(a.transform); registration={'method':'user_matrix','warning':'Benutzertransformation nicht automatisch validiert'}
        else: m,registration=register(ca,cb,a.voxel);registration['method']='FPFH RANSAC + point-to-plane ICP'
        write_cloud(output/'scan-a.ply',ca);write_cloud(output/'scan-b-local.ply',cb)
        report={'input_types':[ka,kb],'scan_a':sa,'scan_b':sb,'registration':registration,'transform_b_to_a':m.tolist(),'voxel_m':a.voxel,'strategies':{},'warnings':['Prototyp: keine Gerätevalidierung.','Ein gemeinsames Objekt und starre Szene werden vorausgesetzt.','Punktwolke ist nicht automatisch ein geschlossenes Mesh.','RGB-Farbe und Confidence werden bislang nicht fusioniert.']}
        for mode in ('separate','joint','incremental'):
            start=time.perf_counter();result=fusion(A,B,m,mode,a.voxel);write_cloud(output/f'{mode}.ply',result)
            report['strategies'][mode]={'points':len(result.points),'seconds':round(time.perf_counter()-start,3)}
        if a.mesh:
            result.estimate_normals(o3d().geometry.KDTreeSearchParamHybrid(radius=a.voxel*3,max_nn=30));result.orient_normals_consistent_tangent_plane(15)
            mesh,densities=o3d().geometry.TriangleMesh.create_from_point_cloud_poisson(result,depth=8)
            densities=np.asarray(densities);mesh.remove_vertices_by_mask(densities<np.quantile(densities,.03))
            if not o3d().io.write_triangle_mesh(str(output/'experimental-mesh.ply'),mesh): raise RuntimeError('Mesh-Export fehlgeschlagen')
            report['warnings'].append('Poisson-Mesh ist eine Schätzung und kann ungeprüfte Flächen schließen.')
        (output/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False));print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=='__main__':
    try: main()
    except (ValueError,RuntimeError,OSError,subprocess.CalledProcessError,ImportError) as e: print(f'Fehler: {e}',file=sys.stderr);sys.exit(1)
