import json, cv2, numpy as np
meta=json.load(open('/home/claude/x/dbg/meta.json'))
res={}
for name,m in meta.items():
    x0,y0,x1,y1=m['bbox']; res[name]={}
    for side in 'FB':
        fl=[f for f in m['flashes'][side] if f['func'] and ('SMDPad' in f['func'] or 'ComponentPad' in f['func'] or 'Heatsink' in f['func'] or 'Connector' in f['func'] or 'Testpoint' in f['func'] or 'WasherPad' in f['func'])]
        n=len(fl); par=list(range(n))
        def F(a):
            while par[a]!=a: par[a]=par[par[a]]; a=par[a]
            return a
        E=0.45
        bx=[(f['x']-f['sz'][0]/2-E,f['y']-f['sz'][1]/2-E,f['x']+f['sz'][0]/2+E,f['y']+f['sz'][1]/2+E) for f in fl]
        for i in range(n):
            for j in range(i+1,n):
                a,b=bx[i],bx[j]
                if a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]: par[F(i)]=F(j)
        groups={}
        for i in range(n): groups.setdefault(F(i),[]).append(i)
        cl=[]
        for g in groups.values():
            xs=[fl[i]['x']-fl[i]['sz'][0]/2 for i in g]+[fl[i]['x']+fl[i]['sz'][0]/2 for i in g]
            ys=[fl[i]['y']-fl[i]['sz'][1]/2 for i in g]+[fl[i]['y']+fl[i]['sz'][1]/2 for i in g]
            funcs=sorted(set(fl[i]['func'] for i in g))
            # local coords: origin board center, mm, y up
            cx,cy=(x0+x1)/2,(y0+y1)/2
            cl.append(dict(n=len(g),bb=[round(min(xs)-cx,2),round(min(ys)-cy,2),round(max(xs)-cx,2),round(max(ys)-cy,2)],f=funcs,
                pads=[[round(fl[i]['x']-cx,2),round(fl[i]['y']-cy,2),round(fl[i]['sz'][0],2),round(fl[i]['sz'][1],2)] for i in g]))
        cl.sort(key=lambda c:(-c['bb'][3],c['bb'][0]))
        res[name][side]=cl
        img=cv2.imread(f'/home/claude/site/assets/{name}_{side}_color.jpg'); W=img.shape[0]; s=W/90
        for k,c in enumerate(cl):
            a=c['bb']; 
            X=lambda v:int((v+45)*s) if side=='F' else int(W-(v+45)*s)
            p1=(X(a[0]),int((45-a[3])*s)); p2=(X(a[2]),int((45-a[1])*s))
            cv2.rectangle(img,p1,p2,(0,200,255),1)
            cv2.putText(img,str(k),(min(p1[0],p2[0]),p1[1]-2),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,0),2)
        cv2.imwrite(f'/home/claude/x/dbg/{name}_{side}_lab.jpg',img)
        print(name,side,len(cl))
    res[name]['holes']=[dict(x=round(h['x']-(x0+x1)/2,2),y=round(h['y']-(y0+y1)/2,2),d=h['d'],**({'x2':round(h['x2']-(x0+x1)/2,2),'y2':round(h['y2']-(y0+y1)/2,2)} if 'x2' in h else {})) for h in m['holes']]
json.dump(res,open('/home/claude/x/dbg/comp.json','w'))
