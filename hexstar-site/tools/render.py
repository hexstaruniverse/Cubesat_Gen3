import sys, json, math, os
sys.path.insert(0, os.path.dirname(__file__))
from gerber import *
X='/home/claude/x'
boards={'LoRa':X+'/9c276bec-gerber_LoRa/gerber_LoRa/LoRa','OBC':X+'/991896bf-Gerber_OBC_1/Gerber_OBC/OBC','EPS':X+'/4181ce41-gerber_EPS/gerber_EPS/EPS'}
W=int(sys.argv[1]) if len(sys.argv)>1 else 2048
out='/home/claude/site/assets'; dbg='/home/claude/x/dbg'; os.makedirs(dbg,exist_ok=True)
meta={}
for name,base in boards.items():
    edge=Gerber(base+'-Edge_Cuts.gbr')
    pts=[q for op in edge.ops if op[0]=='stroke' for q in op[3]]
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    bbox=(min(xs),min(ys),max(xs),max(ys))
    holes=drills(base+'-PTH.drl')+[dict(h,npth=1) for h in drills(base+'-NPTH.drl')]
    m=dict(bbox=bbox,holes=holes,flashes={})
    for side,mir in (('F',False),('B',True)):
        L={}
        for lay in ('Cu','Mask','Silkscreen'):
            g=Gerber(f'{base}-{side}_{lay}.gbr'); c=Canvas(bbox,W*2,mir); L[lay]=cv2.resize(c.draw(g),(W,W),interpolation=cv2.INTER_AREA).astype(np.float32)/255
            if lay=='Cu':
                m['flashes'][side]=[dict(x=f['x'],y=f['y'],func=f['func'],sz=g.ap_size(f['ap'])) for f in g.flashes]
        inner=[]
        c=Canvas(bbox,W*2,mir)
        hole=np.zeros((W*2,W*2),np.uint8)
        for h in holes:
            r=int(round(h['d']/2*c.s*16))
            if 'x2' in h: cv2.line(hole,c.P(h['x'],h['y']),c.P(h['x2'],h['y2']),255,max(1,int(h['d']*c.s)),cv2.LINE_AA)
            else: cv2.circle(hole,c.P(h['x'],h['y']),r,255,-1,cv2.LINE_AA,4)
        hole=cv2.resize(hole,(W,W),interpolation=cv2.INTER_AREA).astype(np.float32)/255
        # outline mask
        oc=Canvas(bbox,W*2,mir); cont=np.array([oc.P(*q) for q in pts],np.int32)
        cv2.fillPoly(oc.img,[cont],255,cv2.LINE_AA,4); board=cv2.resize(oc.img,(W,W),interpolation=cv2.INTER_AREA).astype(np.float32)/255
        cu,mask,silk=L['Cu'],L['Mask'],L['Silkscreen']
        silk=silk*(1-mask)  # silk clipped by mask openings
        pad=cu*mask; bare=(1-cu)*mask
        def col(h): h=h.lstrip('#'); return np.array([int(h[i:i+2],16) for i in (4,2,0)],np.float32)/255  # BGR
        C=np.ones((W,W,3),np.float32)*col('0b4a26')
        C=C*(1-cu[...,None])+col('1f7a3c')*cu[...,None]          # copper under mask
        C=C*(1-bare[...,None])+col('8a7446')*bare[...,None]
        C=C*(1-pad[...,None])+col('e0b45a')*pad[...,None]        # HASL silver
        C=C*(1-silk[...,None])+col('f4f4ee')*silk[...,None]
        C=C*(1-hole[...,None])+col('050505')*hole[...,None]
        # ORM: R=ao(1) G=roughness B=metalness
        rough=0.26*np.ones((W,W),np.float32); rough=rough*(1-pad)+0.2*pad; rough=rough*(1-silk)+0.7*silk; rough=rough*(1-hole)+1*hole
        metal=pad*0.95
        big=np.zeros((W*2,W*2),np.uint8)
        for h in holes:
            if h['d']>=3.0 and 'x2' not in h: cv2.circle(big,c.P(h['x'],h['y']),int(round(h['d']/2*c.s*16)),255,-1,cv2.LINE_AA,4)
        big=cv2.resize(big,(W,W),interpolation=cv2.INTER_AREA).astype(np.float32)/255
        orm=np.dstack([metal,rough,board*(1-big)])  # BGR -> B=metal,G=rough,R=1
        height=np.clip(cu*0.5+silk*0.35+pad*0.25-hole,0,1)
        sz=W if side=='F' else W//2
        rs=lambda a: cv2.resize(a,(sz,sz),interpolation=cv2.INTER_AREA)
        cv2.imwrite(f'{out}/{name}_{side}_color.jpg',rs((np.clip(C,0,1)*255).astype(np.uint8)),[cv2.IMWRITE_JPEG_QUALITY,88])
        cv2.imwrite(f'{out}/{name}_{side}_orm.png',rs((orm*255).astype(np.uint8)),[cv2.IMWRITE_PNG_COMPRESSION,9])
        cv2.imwrite(f'{out}/{name}_{side}_h.jpg',rs(cv2.GaussianBlur((height*255).astype(np.uint8),(3,3),0)),[cv2.IMWRITE_JPEG_QUALITY,85])
    m['outline']=pts[::max(1,len(pts)//200)]
    meta[name]=m
    print(name,bbox, bbox[2]-bbox[0], bbox[3]-bbox[1], len(m['flashes']['F']), len(holes))
json.dump(meta,open(dbg+'/meta.json','w'))
