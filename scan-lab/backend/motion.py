"""Conservative rigid frame-to-anchor motion refinement, not nonrigid tracking."""
import numpy as np
import open3d as o3d


def correct(frames, rgbd=None, voxel=.02, max_shift=.10, max_angle_deg=12., min_fitness=.35):
    if not frames: raise ValueError('Keine Frames für Bewegungskorrektur.')
    # First usable frame anchors the local rigid approximation. Background may dominate.
    def pcd(points):
        p=o3d.geometry.PointCloud();p.points=o3d.utility.Vector3dVector(points);return p.voxel_down_sample(voxel)
    anchor=pcd(frames[0]);output=[frames[0]];out_rgbd=[rgbd[0]] if rgbd is not None else None
    stats=[{'frame_index':0,'status':'anchor','translation_m':0.,'angle_deg':0.}]
    for i,frame in enumerate(frames[1:],1):
        p=pcd(frame)
        if len(anchor.points)<30 or len(p.points)<30:
            stats.append({'frame_index':i,'status':'rejected_too_few_points'});continue
        r=o3d.pipelines.registration.registration_icp(p,anchor,voxel*3,np.eye(4),o3d.pipelines.registration.TransformationEstimationPointToPoint(),o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=35))
        T=np.asarray(r.transformation);shift=float(np.linalg.norm(T[:3,3]));angle=float(np.degrees(np.arccos(np.clip((np.trace(T[:3,:3])-1)/2,-1,1))))
        valid=np.isfinite(T).all() and r.fitness>=min_fitness and shift<=max_shift and angle<=max_angle_deg
        row={'frame_index':i,'status':'accepted' if valid else 'rejected','fitness':float(r.fitness),'rmse_m':float(r.inlier_rmse),'translation_m':shift,'angle_deg':angle};stats.append(row)
        if not valid:continue
        output.append((T[:3,:3]@frame.T).T+T[:3,3])
        if out_rgbd is not None:
            d,K,pose=rgbd[i];out_rgbd.append((d,K,T@pose))
    return output,out_rgbd,stats
