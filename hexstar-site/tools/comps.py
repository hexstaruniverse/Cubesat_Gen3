import json, math
d=json.load(open('/home/claude/x/dbg/comp.json'))
K=0.046582
def D(px,py): return (round(px*K-45,2), round(45-py*K,2))
def R(p1,p2):  # display rect -> mm rect (x0,y0,x1,y1)
    a=D(*p1); b=D(*p2); return (min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1]))
# materials: 0 ic black, 1 passive dark, 2 metal, 3 black plastic, 4 light ceramic/white, 6 graphite, 7 led white translucent
out={}
def box(L,x0,y0,x1,y1,z0,z1,m): L.append(['b',round((x0+x1)/2,3),round((y0+y1)/2,3),round((z0+z1)/2,3),round(abs(x1-x0),3),round(abs(y1-y0),3),round(abs(z1-z0),3),m])
def cyl(L,x,y,z,r,h,axis,m,seg=24): L.append(['c',x,y,z,r,h,axis,m,seg])
excl={'LoRa':[],'OBC':[],'EPS':[]}
def ex(b,r): excl[b].append(r)
def inside(c,r): return r[0]<=c[0]<=r[2] and r[1]<=c[1]<=r[3]
T=1.6
specials={'LoRa':[], 'OBC':[], 'EPS':[]}
# ---------- OBC
S=specials['OBC']
r=R((415,48),(690,300)); ex('OBC',r)
box(S,r[0],r[1],r[2],r[3],0,1.75,10)
box(S,r[0]+.6,r[1]+.6,r[2]-.6,r[1]+1.6,1.75,1.82,10); box(S,r[0]+.6,r[1]+5,r[2]-.6,r[1]+5.6,1.75,1.82,10)
cx=(r[0]+r[2])/2; box(S,cx-5.5,r[3]-12.5,cx+5.5,r[3]+3.2,.6,1.4,8)
box(S,cx-5.2,r[3]+.4,cx+5.2,r[3]+2.6,1.4,1.43,9); box(S,cx-5.2,r[3]+2.6,cx+5.2,r[3]+3.0,1.4,1.43,7)
r=R((1745,360),(1885,595)); ex('OBC',r); S.append(['u',round(r[0]+0.6,3),round(r[2]+2.2,3),round((r[1]+r[3])/2,3),1.62,8.94,3.24,11])
r=R((1360,1390),(1620,1615)); ex('OBC',r); box(S,r[0],r[1],r[2],r[3],0,2.4,10); box(S,r[0]+0.3,r[1]+0.3,r[2]-0.3,r[3]-0.3,2.4,2.45,4)
c=D(1550,1040); ex('OBC',R((1410,960),(1690,1130))); cyl(S,c[0],c[1],2.0,4.4,4.0,'z',3,40); cyl(S,c[0],c[1],4.02,1.0,0.05,'z',2,20)
# RA headers: J2 (pins +y), J7 (pins -x), J6 (pins +x)
r=R((955,140),(1230,200)); ex('OBC',R((950,10),(1235,250))); box(S,r[0],r[1],r[2],r[3],0,2.5,3)
for i in range(5):
    x=D(985+i*54.3,0)[0]; box(S,x-0.32,D(0,235)[1],x+0.32,D(0,10)[1],1.0,1.64,2)
r=R((140,665),(200,945)); ex('OBC',R((5,660),(250,945))); box(S,r[0],r[1],r[2],r[3],0,2.5,3)
for i in range(5):
    y=D(0,695+i*54.5)[1]; box(S,D(5,0)[0],y-0.32,D(235,0)[0],y+0.32,1.0,1.64,2)
r=R((1735,735),(1790,955)); ex('OBC',R((1680,735),(1925,955))); box(S,r[0],r[1],r[2],r[3],0,2.5,3)
for i in range(4):
    y=D(0,762+i*54.5)[1]; box(S,D(1690,0)[0],y-0.32,D(1925,0)[0],y+0.32,1.0,1.64,2)
r=R((1400,110),(1565,200)); ex('OBC',R((1380,100),(1580,210))); box(S,r[0],r[1],r[2],r[3],0,3.5,3); c=D(1482,105); cyl(S,c[0],c[1]+1.2,1.75,1.3,2.6,'y',4,20)
r=R((1660,1450),(1745,1525)); ex('OBC',r); cyl(S,(r[0]+r[2])/2,(r[1]+r[3])/2,0.6,1.3,1.2,'z',2,20)
# stack header J4 (stacking: socket on top + pins below)
r=R((420,1725),(1505,1830)); ex('OBC',r); box(S,r[0],r[1],r[2],r[3],0,8.5,3)
for i in range(20):
    for j in range(2):
        x=D(445+i*54.5,0)[0]; y=D(0,1750+j*54.5)[1]
        box(S,x-0.32,y-0.32,x+0.32,y+0.32,-12.5,-T,2); box(S,x-0.5,y-0.5,x+0.5,y+0.5,8.5,8.52,0)
# ---------- LoRa
S=specials['LoRa']
r=R((1170,485),(1240,575)); ex('LoRa',r); cyl(S,(r[0]+r[2])/2,(r[1]+r[3])/2,0.6,1.3,1.2,'z',2,20)
r=R((420,1725),(1520,1830))
for i in range(20):
    for j in range(2):
        x=D(453+i*54.5,0)[0]; y=D(0,1750+j*54.5)[1]
        box(S,x-0.32,y-0.32,x+0.32,y+0.32,-T-8.5,0.8,2)
box(S,r[0],r[1],r[2],r[3],-T-2.5,-T,3)
for rr in [R((1050,385),(1085,410)),R((1050,455),(1085,480)),R((1050,520),(1090,550))]: ex('LoRa',rr)
# ---------- EPS
S=specials['EPS']
r=R((420,1725),(1505,1830)); ex('EPS',r); box(S,r[0],r[1],r[2],r[3],0,8.5,3)
for i in range(20):
    for j in range(2):
        x=D(445+i*54.5,0)[0]; y=D(0,1750+j*54.5)[1]; box(S,x-0.5,y-0.5,x+0.5,y+0.5,8.5,8.52,0)
r=R((1755,655),(1885,890)); ex('EPS',r); S.append(['u',round(r[0]+0.6,3),round(r[2]+2.2,3),round((r[1]+r[3])/2,3),1.62,8.94,3.24,11])
r=R((1660,1130),(1910,1295)); ex('EPS',R((1655,1125),(1915,1300))); box(S,r[0],r[1],r[2],r[3],0,6.0,4); box(S,r[0]+5,r[1]+0.8,r[2]+0.3,r[3]-0.8,0.8,5.2,3)
r=R((1745,1390),(1830,1600)); ex('EPS',R((1740,1385),(1840,1610))); box(S,r[0],r[1],r[2],r[3],0,3.6,2); c=((r[0]+r[2])/2,(r[1]+r[3])/2); box(S,r[2],c[1]-0.6,r[2]+3.0,c[1]+0.6,1.3,2.5,3)
r=R((1325,1465),(1415,1560)); ex('EPS',r); box(S,r[0],r[1],r[2],r[3],0,2.0,6)
for p in [(810,405),(810,537),(943,400),(1100,985)]:
    c=D(*p); ex('EPS',(c[0]-2.8,c[1]-2.2,c[0]+2.8,c[1]+2.2))
# 18650 holder + cell on bottom, along x at y=25.5
yc=25.52; zc=-T-1.2-9.3
box(S,-43.5,yc-10.2,43.4,yc+10.2,-T-1.2,-T,3)
box(S,-43.5,yc-10.2,-39.5,yc+10.2,-T-19.5,-T,3); box(S,39.4,yc-10.2,43.4,yc+10.2,-T-19.5,-T,3)
cyl(S,0,yc,zc,9.25,64.0,'x',6,48)
cyl(S,-28,yc,zc,9.3,1.2,'x',4,48)
cyl(S,32.4,yc,zc,3.0,1.0,'x',2,24); cyl(S,-32.6,yc,zc,8.0,0.6,'x',2,24)
# ---------- auto
for b in ['LoRa','OBC','EPS']:
    L=specials[b]
    for side in 'FB':
        for c in d[b][side]:
            n=c['n']; bb=c['bb']; cx=(bb[0]+bb[2])/2; cy=(bb[1]+bb[3])/2
            if n<2 or any('ComponentPad' in f for f in c['f']): continue
            if any(inside((cx,cy),r) for r in excl[b]) and side=='F': continue
            z0,sgn=(0,1) if side=='F' else (-T,-1)
            def bx(x0,y0,x1,y1,h0,h1,m):
                if sgn>0: box(L,x0,y0,x1,y1,h0,h1,m)
                else: box(L,x0,y0,x1,y1,z0-h1,z0-h0,m)
            w=bb[2]-bb[0]; h=bb[3]-bb[1]
            if n==2 and max(w,h)<5:
                (ax,ay,aw,ah),(bxp,byp,_,_)=[p[:4] for p in c['pads']]
                horiz=abs(bxp-ax)>abs(byp-ay); dist=math.hypot(bxp-ax,byp-ay)
                pw=(ah if horiz else aw)
                Lh=dist*0.55+0.15; Wh=pw*0.42
                H=0.55 if pw<1.0 else 0.75
                capm=2
                if horiz:
                    bx(cx-Lh,cy-Wh,cx+Lh,cy+Wh,0,H,1); bx(cx-Lh-0.02,cy-Wh-0.02,cx-Lh*0.62,cy+Wh+0.02,0,H+0.02,capm); bx(cx+Lh*0.62,cy-Wh-0.02,cx+Lh+0.02,cy+Wh+0.02,0,H+0.02,capm)
                else:
                    bx(cx-Wh,cy-Lh,cx+Wh,cy+Lh,0,H,1); bx(cx-Wh-0.02,cy-Lh-0.02,cx+Wh+0.02,cy-Lh*0.62,0,H+0.02,capm); bx(cx-Wh-0.02,cy+Lh*0.62,cx+Wh+0.02,cy+Lh+0.02,0,H+0.02,capm)
            elif n<=3:
                bx(cx-w*0.36,cy-h*0.36,cx+w*0.36,cy+h*0.36,0,1.0,0)
            else:
                hs=any('Heatsink' in f for f in c['f'])
                s=0.12 if hs else (0.9 if n>=32 else 0.45)
                if not hs and n<12:
                    # two-row parts: shrink along longer pad axis
                    s=0.5
                bx(bb[0]+s,bb[1]+s,bb[2]-s,bb[3]-s,0,0.9 if hs else 1.1,0)
    out[b]=dict(prims=L,holes=[h for h in d[b]['holes'] if h['d']>=3.0])
# hotspots
HS={'LoRa':[
 ('U1','SX1262','LoRa transceiver','Semtech SX1262. Packs telemetry into long-range LoRa packets at 868 MHz and transmits at up to +22 dBm. It listens for commands from the ground in between.',(948,1003)),
 ('IC1','PE4259','RF switch','Flips the single antenna between the transmit and receive paths in microseconds, so one antenna does both jobs.',(952,657)),
 ('Y2','32 MHz TCXO','Frequency reference','A temperature-compensated oscillator, accurate to ±0.5 ppm. It keeps the radio on frequency as the satellite heats and cools.',(542,1190)),
 ('L2–L5','RF matching','TX / RX filter network','Hand-tuned inductors and capacitors that filter harmonics and match the radio to 50 Ω for maximum range.',(900,820)),
 ('J2','U.FL','Antenna connector','Feeds the 868 MHz whip on the top plate. It also serves as the test port for VNA tuning and conducted tests.',(1205,530)),
 ('AE1','PCB antenna','Printed backup antenna','An 866 MHz antenna etched straight into the copper, using TI SWRA416 geometry. It\'s a zero-cost fallback link.',(1030,110)),
 ('L1','15 µH','DC-DC inductor','Lets the SX1262 run its internal buck converter, which cuts receive current roughly in half.',(700,1415)),
 ('D1','TX LED','Transmit indicator','Blinks on every packet sent, driven by DIO2 on the transceiver.',(1785,805)),
 ('J1','2×20 header','Main stack bus','Plugs down into the OBC and carries SPI, reset, busy, IRQ and 3.3 V up the stack.',(970,1775)),
],'OBC':[
 ('U5','ATSAMD21G18A','Flight computer','A 48 MHz Arm Cortex-M0+ with 256 KB flash. It runs your mission code and is Arduino Zero compatible.',(1055,765)),
 ('U4','ICM-42688-P','6-axis IMU','Gyroscope plus accelerometer. It measures every tumble and spin for attitude estimation.',(965,1095)),
 ('U6','MMC5983MA','3-axis magnetometer','Senses Earth\'s magnetic field to work out which way the satellite is pointing.',(205,1265)),
 ('U3','BMP280','Barometer','Measures pressure and temperature. On a balloon flight it doubles as an altimeter.',(795,255)),
 ('U1','ATGM336H','GNSS receiver','Gets position, velocity and a PPS time pulse from GPS and BeiDou through the patch antenna on the roof.',(1490,1500)),
 ('J3','microSD','Flight logger','A push-push microSD socket. Every sensor reading is timestamped and logged here.',(550,180)),
 ('J1','USB-C','Program and power','Flash new firmware and stream live data straight from your laptop. ESD protection is provided by U7.',(1790,480)),
 ('LS1','Buzzer','Audible beacon','A magnetic buzzer driven by PWM. It chirps status codes and helps you find the sat after a landing.',(1550,1040)),
 ('J2','SWD','Debug header','A 5-pin Serial Wire Debug port for breakpoints, step-through debugging and bootloader recovery.',(1095,230)),
 ('SW1','Reset','Reset button','A right-angle tactile switch that you can reach through the +Y panel.',(1480,160)),
 ('J6 / J7','UART · Ext mag','Expansion headers','Right-angle headers for a UART console and an external magnetometer. They are reachable from the side panels.',(1700,840)),
 ('J4','2×20 stacking','Main stack bus','Stacking header that links the OBC to the EPS below and the LoRa board above.',(960,1775)),
],'EPS':[
 ('U1','BQ24074','Li-ion charger','A 1 A linear charger with power-path management, so the satellite runs from USB while the cell charges.',(1368,573)),
 ('U2','TPS62162','3.3 V buck converter','A 1 A step-down regulator that makes the clean 3.3 V rail every board runs on.',(1497,1520)),
 ('U3','INA226','Power monitor','Measures current, voltage and power over I²C through a 50 mΩ shunt. You get telemetry on every milliwatt.',(1357,1222)),
 ('U4','DW01A','Cell protection','Watches the 18650 for over-charge, over-discharge and short circuit, and drives the Q1/Q2 cut-off MOSFETs.',(383,465)),
 ('Q1 / Q2','AO3400A','Protection MOSFETs','A back-to-back N-MOSFET pair that disconnects the cell the moment the DW01A sees a fault.',(400,650)),
 ('F1','1.5 A PTC','Resettable fuse','Trips on a hard short and resets itself once it cools, with no replacement needed.',(1510,358)),
 ('J1','USB-C','Charge input','5 V charging input with TVS and ESD protection on the CC lines.',(1810,770)),
 ('J3','RBF','Remove-before-flight','The safety key. Pull the RBF plug and the satellite powers up, exactly like a real launch.',(1730,1215)),
 ('SW1','Slide switch','Power switch','Enables the 3.3 V buck converter from outside the +X panel.',(1785,1500)),
 ('D4–D7','Status LEDs','Power status','Charging, power-good, 3V3 and safety-live indicators that you can read at a glance.',(1470,960)),
 ('J5','2×20 socket','Main stack bus','The bottom of the stack. It receives the OBC header and distributes power upward.',(960,1775)),
]}
hs={}
for b,L in HS.items():
    hs[b]=[dict(ref=a,name=n,role=r,desc=t,x=D(*p)[0],y=D(*p)[1],z=1.2) for a,n,r,t,p in L]
for b in hs: out[b]['hotspots']=hs[b]

json.dump(out,open('/home/claude/site/assets/boards.json','w'),separators=(',',':'))
for b in out: print(b,len(out[b]['prims']))
