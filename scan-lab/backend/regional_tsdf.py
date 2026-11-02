"""CPU reference projective TSDF with explicit per-scan regional routing.
Experimental, bounded dense grid; measured confidence maps are not used.
"""
import numpy as np


def integrate(frames, origin, shape, voxel, trunc, max_depth):
    dims=tuple(map(int,shape)); total=int(np.prod(dims))
    if total>3000000: raise ValueError(f'TSDF-Raster {total} Voxel zu groß (Limit 3 Millionen). Größere --voxel oder engeren Bereich wählen.')
    accum=np.zeros(total,np.float32); weight=np.zeros(total,np.float32)
    for depth,K,c2w in frames:
        depth=np.asarray(depth,np.float32); h,w=depth.shape
        inv=np.linalg.inv(c2w)
        for start in range(0,total,100000):
            ids=np.arange(start,min(total,start+100000)); ijk=np.column_stack(np.unravel_index(ids,dims)); xyz=origin+(ijk+0.5)*voxel
            cam=(inv[:3,:3]@xyz.T).T+inv[:3,3]; z=cam[:,2]; valid=z>0
            u=np.rint(K[0,0]*cam[:,0]/np.maximum(z,1e-9)+K[0,2]).astype(np.int64); v=np.rint(K[1,1]*cam[:,1]/np.maximum(z,1e-9)+K[1,2]).astype(np.int64)
            valid &= (u>=0)&(u<w)&(v>=0)&(v<h)
            candidates=np.nonzero(valid)[0]
            if not len(candidates): continue
            d=depth[v[candidates],u[candidates]]; dist=d-z[candidates]
            good=np.isfinite(d)&(d>0)&(d<=max_depth)&(dist>=-trunc)&(dist<=trunc)
            sel=ids[candidates[good]]; tsdf=np.clip(dist[good]/trunc,-1,1)
            accum[sel]+=tsdf.astype(np.float32); weight[sel]+=1
    return accum.reshape(dims),weight.reshape(dims)


def route(a_sum,a_weight,b_sum,b_weight,block=4,conflict=.5):
    """Regional coverage-based selector; reject disagreement, do not call it sensor confidence."""
    if a_sum.shape!=b_sum.shape: raise ValueError('TSDF-Raster stimmen nicht überein.')
    shape=a_sum.shape; out=np.ones(shape,np.float32); support=np.zeros(shape,bool); owner=np.zeros(shape,np.uint8); conflicting=np.zeros(shape,bool)
    for x in range(0,shape[0],block):
        for y in range(0,shape[1],block):
            for z in range(0,shape[2],block):
                sl=np.s_[x:x+block,y:y+block,z:z+block]; wa=a_weight[sl]; wb=b_weight[sl]
                sa=a_sum[sl]/np.maximum(wa,1); sb=b_sum[sl]/np.maximum(wb,1); both=(wa>0)&(wb>0)
                conflict_mask=both&(np.abs(sa-sb)>conflict)
                score_a=float(wa.sum());score_b=float(wb.sum()); preferred=1 if score_a>=score_b else 2
                agree=both&~conflict_mask; onlya=(wa>0)&(wb==0);onlyb=(wb>0)&(wa==0)
                allowed=agree|onlya|onlyb
                vals=np.ones(wa.shape,np.float32); vals[onlya]=sa[onlya]; vals[onlyb]=sb[onlyb];vals[agree]=(a_sum[sl][agree]+b_sum[sl][agree])/(wa[agree]+wb[agree])
                out[sl]=vals;support[sl]=allowed;conflicting[sl]=conflict_mask
                labels=np.zeros(wa.shape,np.uint8);labels[onlya]=1;labels[onlyb]=2;labels[agree]=preferred;labels[conflict_mask]=3;owner[sl]=labels
    return out,support,owner,conflicting


def surface(field,support,origin,voxel):
    from skimage.measure import marching_cubes
    if not np.any(support) or not np.any((field<0)&support) or not np.any((field>0)&support): raise ValueError('Keine ausreichend unterstützte TSDF-Nulldurchquerung gefunden.')
    verts,faces,normals,_=marching_cubes(field,level=0,spacing=(voxel,)*3)
    # Keep only triangles whose neighboring eight voxels are measured; avoids artificial boundary closure.
    coords=np.floor(verts/voxel).astype(int); coords=np.minimum(np.maximum(coords,0),np.array(field.shape)-2)
    valid=np.ones(len(verts),bool)
    for dx in (0,1):
        for dy in (0,1):
            for dz in (0,1): valid &= support[coords[:,0]+dx,coords[:,1]+dy,coords[:,2]+dz]
    faces=faces[np.all(valid[faces],axis=1)]
    if not len(faces): raise ValueError('Keine vollständig durch Messungen unterstützten Dreiecke; Voxelgröße/Abdeckung prüfen.')
    return verts+origin+voxel*.5,faces,normals
