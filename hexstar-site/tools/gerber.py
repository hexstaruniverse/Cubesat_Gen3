import re, math, sys, json
import numpy as np, cv2

def ev(expr, vars):
    e = expr.replace('x','*').replace('X','*')
    e = re.sub(r'\$(\d+)', lambda m: '(%s)'%vars.get(int(m.group(1)),0.0), e)
    return float(eval(e, {"__builtins__":{}}))

class Gerber:
    def __init__(self, path):
        self.txt = open(path).read()
        self.ap = {}; self.macros = {}; self.flashes=[]; self.ops=[]
        self.parse()
    def parse(self):
        t = self.txt
        # extended commands
        blocks = re.findall(r'%[^%]*%|[^%*]+\*', t, re.S)
        fx, fy = 4, 6
        cur_func = None; cur_net=None
        x=y=0.0; ap=None; interp='G01'; region=False; contour=[]; pol='D'
        for b in blocks:
            b=b.strip()
            if b.startswith('%'):
                body=b[1:-1].strip()
                for cmd in [c.strip() for c in body.split('*') if c.strip()]:
                    pass
                if body.startswith('FS'):
                    m=re.search(r'X(\d)(\d)',body); fx,fy=int(m.group(1)),int(m.group(2))
                elif body.startswith('AM'):
                    parts=[p.strip() for p in body.split('*') if p.strip()]
                    name=parts[0][2:]; prims=[p for p in parts[1:] if not p.startswith('0 ')]
                    self.macros[name]=prims
                elif body.startswith('AD'):
                    m=re.match(r'ADD(\d+)([A-Za-z_0-9]+?)(?:,(.*))?\*?$',body.rstrip('*'))
                    code=int(m.group(1)); typ=m.group(2); params=[float(v) for v in m.group(3).split('X')] if m.group(3) else []
                    self.ap[code]=(typ,params,cur_func)
                elif body.startswith('TA.AperFunction'):
                    cur_func=body.split(',',1)[1].rstrip('*')
                elif body.startswith('TD'):
                    cur_func=None
                elif body.startswith('LP'):
                    pol=body[2]
                continue
            s=b[:-1]
            if s.startswith('G04') or not s: continue
            for g in re.findall(r'G(\d+)',s):
                g=int(g)
                if g in (1,2,3): interp='G0%d'%g
                elif g==36: region=True; contour=[]
                elif g==37:
                    if len(contour)>2: self.ops.append(('region',pol,contour))
                    region=False; contour=[]
            m=re.search(r'D(\d+)$',s)
            if m and int(m.group(1))>=10 and 'X' not in s and 'Y' not in s:
                ap=int(m.group(1)); continue
            if 'X' not in s and 'Y' not in s and not m: continue
            mx=re.search(r'X(-?\d+)',s); my=re.search(r'Y(-?\d+)',s)
            mi=re.search(r'I(-?\d+)',s); mj=re.search(r'J(-?\d+)',s)
            nx=int(mx.group(1))/10**fy if mx else x
            ny=int(my.group(1))/10**fy if my else y
            i=int(mi.group(1))/10**fy if mi else 0; j=int(mj.group(1))/10**fy if mj else 0
            d=int(m.group(1)) if m else 1
            if d==1:
                if interp=='G01': pts=[(nx,ny)]
                else:
                    cx,cy=x+i,y+j; a0=math.atan2(y-cy,x-cx); a1=math.atan2(ny-cy,nx-cx); r=math.hypot(x-cx,y-cy)
                    if interp=='G02':
                        while a1>=a0-1e-9: a1-=2*math.pi
                    else:
                        while a1<=a0+1e-9: a1+=2*math.pi
                    if abs(nx-x)>1e-9 or abs(ny-y)>1e-9:
                        pass
                    else:
                        a1 = a0 + (-2*math.pi if interp=='G02' else 2*math.pi)
                    n=max(8,int(abs(a1-a0)*r*8)+2)
                    pts=[(cx+r*math.cos(a0+(a1-a0)*k/n), cy+r*math.sin(a0+(a1-a0)*k/n)) for k in range(1,n+1)]
                if region:
                    if not contour: contour=[(x,y)]
                    contour+=pts
                else:
                    self.ops.append(('stroke',pol,ap,[(x,y)]+pts))
            elif d==2:
                if region and len(contour)>2:
                    self.ops.append(('region',pol,contour)); contour=[]
            elif d==3:
                self.ops.append(('flash',pol,ap,(nx,ny)))
                typ,params,func=self.ap[ap]
                self.flashes.append(dict(x=nx,y=ny,ap=ap,func=func,typ=typ,params=params))
            x,y=nx,ny

    def ap_shapes(self, code):
        """return list of (exposure, kind, data) in mm relative to center. kinds: circle(r,cx,cy), poly(pts)"""
        typ,p,_=self.ap[code]
        out=[]
        if typ=='C': out.append((1,'circle',(p[0]/2,0,0)))
        elif typ=='R':
            w,h=p[0]/2,p[1]/2; out.append((1,'poly',[(-w,-h),(w,-h),(w,h),(-w,h)]))
        elif typ=='O':
            w,h=p[0],p[1]
            if w>h:
                r=h/2;d=w/2-r; out+= [(1,'circle',(r,-d,0)),(1,'circle',(r,d,0)),(1,'poly',[(-d,-r),(d,-r),(d,r),(-d,r)])]
            else:
                r=w/2;d=h/2-r; out+= [(1,'circle',(r,0,-d)),(1,'circle',(r,0,d)),(1,'poly',[(-r,-d),(r,-d),(r,d),(-r,d)])]
        elif typ=='P':
            r=p[0]/2;n=int(p[1]);rot=p[2] if len(p)>2 else 0
            out.append((1,'poly',[(r*math.cos(math.radians(rot+360*k/n)),r*math.sin(math.radians(rot+360*k/n))) for k in range(n)]))
        elif typ in self.macros:
            vars={k+1:v for k,v in enumerate(p)}
            for prim in self.macros[typ]:
                if '=' in prim and not prim[0].isdigit():
                    k,v=prim.split('='); vars[int(k[1:])]=ev(v,vars); continue
                a=[ev(v,vars) for v in prim.replace('\n','').split(',')]
                c=int(a[0])
                def rot(pts,ang):
                    ca,sa=math.cos(math.radians(ang)),math.sin(math.radians(ang))
                    return [(px*ca-py*sa,px*sa+py*ca) for px,py in pts]
                if c==1:
                    r=a[2]/2; cx,cy=a[3],a[4]; ang=a[5] if len(a)>5 else 0
                    cx,cy=rot([(cx,cy)],ang)[0]; out.append((int(a[1]),'circle',(r,cx,cy)))
                elif c==20:
                    e,w,x1,y1,x2,y2,ang=a[1:8]; dx,dy=x2-x1,y2-y1; L=math.hypot(dx,dy) or 1
                    nx,ny=-dy/L*w/2,dx/L*w/2
                    out.append((int(e),'poly',rot([(x1+nx,y1+ny),(x2+nx,y2+ny),(x2-nx,y2-ny),(x1-nx,y1-ny)],ang)))
                elif c==21:
                    e,w,h,cx,cy,ang=a[1:7]
                    out.append((int(e),'poly',rot([(cx-w/2,cy-h/2),(cx+w/2,cy-h/2),(cx+w/2,cy+h/2),(cx-w/2,cy+h/2)],ang)))
                elif c==4:
                    e=int(a[1]);n=int(a[2]); pts=[(a[3+2*k],a[4+2*k]) for k in range(n+1)]; ang=a[3+2*(n+1)]
                    out.append((e,'poly',rot(pts,ang)))
                elif c==5:
                    e,n,cx,cy,d,ang=a[1:7]; n=int(n)
                    pts=[(cx+d/2*math.cos(2*math.pi*k/n),cy+d/2*math.sin(2*math.pi*k/n)) for k in range(n)]
                    out.append((int(e),'poly',rot(pts,ang)))
        return out

    def ap_size(self, code):
        xs=[];ys=[]
        for e,k,d in self.ap_shapes(code):
            if k=='circle': r,cx,cy=d; xs+=[cx-r,cx+r]; ys+=[cy-r,cy+r]
            else: xs+=[q[0] for q in d]; ys+=[q[1] for q in d]
        return (max(xs)-min(xs), max(ys)-min(ys)) if xs else (0,0)

class Canvas:
    def __init__(self, bbox, W, mirror=False):
        self.x0,self.y0,self.x1,self.y1=bbox; self.W=W; self.s=W/(self.x1-self.x0); self.H=int(round((self.y1-self.y0)*self.s))
        self.mirror=mirror
        self.img=np.zeros((self.H,self.W),np.uint8)
    def P(self,x,y):
        px=(x-self.x0)*self.s
        if self.mirror: px=self.W-px
        return (int(round(px*16)), int(round((self.y1-y)*self.s*16)))
    def draw(self, g, ops=None):
        for op in g.ops:
            if op[0]=='region':
                _,pol,cont=op; col=255 if pol=='D' else 0
                cv2.fillPoly(self.img,[np.array([self.P(*q) for q in cont],np.int32)],col,cv2.LINE_AA,4)
            elif op[0]=='stroke':
                _,pol,ap,pts=op; col=255 if pol=='D' else 0
                w=max(g.ap_size(ap)[0],0.02)*self.s
                arr=np.array([self.P(*q) for q in pts],np.int32)
                cv2.polylines(self.img,[arr],False,col,max(1,int(round(w))),cv2.LINE_AA,4)
            elif op[0]=='flash':
                _,pol,ap,(x,y)=op
                for e,k,d in g.ap_shapes(ap):
                    col=(255 if pol=='D' else 0) if e==1 else (0 if pol=='D' else 255)
                    if k=='circle':
                        r,cx,cy=d; cv2.circle(self.img,self.P(x+cx,y+cy),int(round(r*self.s*16)),col,-1,cv2.LINE_AA,4)
                    else:
                        cv2.fillPoly(self.img,[np.array([self.P(x+q[0],y+q[1]) for q in d],np.int32)],col,cv2.LINE_AA,4)
        return self.img

def drills(path):
    tools={}; holes=[]; cur=None; mode=None
    for line in open(path):
        line=line.strip()
        m=re.match(r'T(\d+)C([\d.]+)',line)
        if m: tools[int(m.group(1))]=float(m.group(2)); continue
        m=re.match(r'^T(\d+)$',line)
        if m: cur=int(m.group(1)); continue
        m=re.match(r'(G0[01])?X(-?[\d.]+)Y(-?[\d.]+)',line)
        if m and cur:
            if m.group(1)=='G01' and holes:
                holes[-1]['x2']=float(m.group(2)); holes[-1]['y2']=float(m.group(3))
            else:
                holes.append(dict(x=float(m.group(2)),y=float(m.group(3)),d=tools[cur]))
    return holes
