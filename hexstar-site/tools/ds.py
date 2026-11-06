import openpyxl, sys
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from PIL import Image as PI
ATT='/mnt/user-data/attachments/f7805cd8-511d-5cfa-8e59-a9e60204497e/'
BOM={'EPS':ATT+'9a9520aa-EPS_BOM_1.xlsx','LoRa':ATT+'b23fdbdb-LoRa_BOM.xlsx','OBC':ATT+'c8baa1b8-OBC_BOM_purchase.xlsx'}
PUR=colors.HexColor('#6637ED'); INK=colors.HexColor('#111114'); MUTE=colors.HexColor('#6b6b70'); LINE=colors.HexColor('#e2e2e6')
st=lambda n,**k:ParagraphStyle(n,fontName=k.pop('f','Helvetica'),**k)
H1=st('h1',f='Helvetica-Bold',fontSize=24,leading=28,textColor=INK); H2=st('h2',f='Helvetica-Bold',fontSize=12.5,leading=16,textColor=INK,spaceBefore=10,spaceAfter=6)
B=st('b',fontSize=9.5,leading=14,textColor=colors.HexColor('#303034')); S=st('s',fontSize=7.6,leading=9.6,textColor=colors.HexColor('#303034'))
SB=st('sb',f='Helvetica-Bold',fontSize=7.6,leading=9.6,textColor=INK); K=st('k',f='Helvetica-Bold',fontSize=8,leading=10,textColor=PUR)
def bom(path):
    ws=openpyxl.load_workbook(path,data_only=True).worksheets[0]; rows=list(ws.iter_rows(values_only=True)); hd=[str(c) for c in rows[0]]
    ix={k:hd.index(k) for k in ['Reference','Qty / board','Value','Description','Package','Manufacturer','MPN','Fitted','Block']}
    out=[];sec=None
    for r in rows[1:]:
        if r[0] and all(c is None for c in r[1:]): sec=str(r[0]).title(); continue
        if not r[ix['Reference']]: continue
        if str(r[ix['Fitted']]).strip().lower() not in ('yes','y','true','1'): continue
        q=r[ix['Qty / board']]; q=int(float(q)) if q not in (None,'None') else 1
        out.append([str(r[ix[k]] or '').strip() for k in ['Reference','Value','Description','Package','Manufacturer','MPN']]+[q])
    return out
INFO={
'EPS':dict(title='EPS · Electrical Power System',sub='Charges, protects and measures every milliwatt',img='EPS_F_color.jpg',
  intro='The EPS is the bottom board of the Hexstar 1U stack. It holds the single 18650 Li-ion cell, charges it from USB-C with power-path management, protects it against over-charge, over-discharge and short circuit, and generates the regulated 3.3 V rail for every board above. An INA226 monitor reports bus voltage, current and power over I²C, so every milliwatt is in your telemetry.',
  feat=['BQ24074 1 A linear charger with power-path: run from USB while charging','DW01A + dual AO3400A cell protection, 1.5 A resettable PTC fuse','TPS62162 1 A synchronous buck converter for the 3V3 bus','INA226 current / voltage / power monitor with a 50 mΩ shunt','Remove-before-flight (RBF) key and an external slide switch','Charge, power-good, 3V3 and safety-live status LEDs','Keystone 1042 SMT 18650 holder on the underside'],
  spec=[('Cell','1 × 18650 Li-ion, 3.6 V nominal'),('Charge input','USB-C, 5 V, up to 1 A'),('Output rail','3.3 V, 1 A'),('Telemetry','INA226 over I²C'),('Board','90 × 90 mm, 1.6 mm FR4, 2-layer'),('Stack','2 × 20 female socket (bottom of stack)')]),
'OBC':dict(title='OBC · On-Board Computer',sub='Runs your code, reads every sensor, logs the mission',img='OBC_F_color.jpg',
  intro='The OBC is the brain of the satellite. An ATSAMD21 Cortex-M0+ microcontroller (Arduino Zero compatible) reads a 6-axis IMU, a 3-axis magnetometer, a barometer and a GNSS receiver, timestamps everything with the GNSS PPS pulse and logs it to microSD. It drives the LoRa radio above it over the stack bus.',
  feat=['ATSAMD21G18A, 48 MHz Arm Cortex-M0+, 256 KB flash, 32 KB RAM','ICM-42688-P 6-axis IMU (gyro + accelerometer)','MMC5983MA 3-axis magnetometer','BMP280 pressure and temperature sensor','ATGM336H GPS + BeiDou receiver with a U.FL patch-antenna input','Push-push microSD logger, magnetic buzzer beacon','USB-C programming with ESD protection, 5-pin SWD debug header','UART and external-magnetometer expansion headers'],
  spec=[('MCU','ATSAMD21G18A @ 48 MHz'),('Sensors','IMU, magnetometer, barometer, GNSS'),('Storage','microSD (SPI)'),('Programming','USB-C (UF2 / Arduino) and SWD'),('Board','90 × 90 mm, 1.6 mm FR4'),('Stack','2 × 20 stacking header')]),
'LoRa':dict(title='COM · LoRa Radio',sub='Long-range telemetry and command link',img='LoRa_F_color.jpg',
  intro='The communications board sits at the top of the stack. A Semtech SX1262 transceiver sends telemetry packets to the Hexstar ground station and listens for commands. A PE4259 RF switch shares one antenna between transmit and receive, a TCXO keeps the carrier on frequency across temperature, and a hand-tuned matching network couples the radio to the 868 MHz whip on the top plate.',
  feat=['Semtech SX1262 LoRa transceiver, up to +22 dBm','PE4259 SPDT RF switch for TX / RX','32 MHz TCXO frequency reference','Discrete harmonic filter and 50 Ω matching network','U.FL output to the top-plate whip, plus a printed backup antenna','Internal DC-DC mode for low receive current','TX activity LED'],
  spec=[('Transceiver','Semtech SX1262'),('Band','868 MHz ISM (region-tunable)'),('TX power','Up to +22 dBm'),('Interface','SPI + BUSY / DIO1 / RESET via the stack'),('Antenna','U.FL to whip; PCB backup antenna'),('Board','90 × 90 mm, 1.6 mm FR4')]),
}
def header(c,d):
    c.saveState();w,h=A4
    c.setFillColor(INK);c.rect(0,h-22*mm,w,22*mm,fill=1,stroke=0)
    c.drawImage('/home/claude/site/assets/logo.png',16*mm,h-17*mm,width=34*mm,height=12*mm,mask='auto',preserveAspectRatio=True)
    c.setFillColor(colors.white);c.setFont('Helvetica',8);c.drawRightString(w-16*mm,h-11*mm,'HEXSTAR 1U CUBESAT KIT · DATASHEET')
    c.setFillColor(colors.HexColor('#a9a9b0'));c.drawRightString(w-16*mm,h-15.5*mm,'Preliminary · Rev 0.1 · November 2026')
    c.setFillColor(MUTE);c.setFont('Helvetica',7.5);c.drawString(16*mm,10*mm,'© 2026 Hexstar Universe. Specifications are preliminary and may change before shipping.');c.drawRightString(w-16*mm,10*mm,f'Page {c.getPageNumber()}')
    c.restoreState()
def tbl(rows,widths,head=True,small=False):
    t=Table(rows,colWidths=widths,repeatRows=1 if head else 0)
    s=[('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.4,LINE),('TOPPADDING',(0,0),(-1,-1),3.5),('BOTTOMPADDING',(0,0),(-1,-1),3.5),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3)]
    if head: s+=[('LINEBELOW',(0,0),(-1,0),.9,INK)]
    t.setStyle(TableStyle(s));return t
def board(name):
    d=INFO[name];doc=SimpleDocTemplate(f'/home/claude/site/docs/Hexstar_{name}_datasheet.pdf',pagesize=A4,leftMargin=16*mm,rightMargin=16*mm,topMargin=30*mm,bottomMargin=18*mm,title=f'Hexstar {d["title"]} datasheet',author='Hexstar Universe')
    im=PI.open('/home/claude/site/assets/'+d['img']).convert('RGB').resize((1100,1100));p=f'/home/claude/x/dbg/{name}_ds.jpg';im.save(p,quality=88)
    E=[Paragraph(d['title'],H1),Spacer(1,3),Paragraph(d['sub'],st('x',fontSize=11,leading=14,textColor=PUR)),Spacer(1,10)]
    left=[Paragraph('Overview',H2),Paragraph(d['intro'],B),Paragraph('Key features',H2)]+[Paragraph('•&nbsp;&nbsp;'+f,B) for f in d['feat']]
    lt=Table([[left,Image(p,width=78*mm,height=78*mm)]],colWidths=[96*mm,82*mm]);lt.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('LEFTPADDING',(1,0),(1,0),6)]))
    E+=[lt,Paragraph('Specifications',H2),tbl([[Paragraph(a,SB),Paragraph(b,S)] for a,b in d['spec']],[45*mm,133*mm],head=False)]
    E+=[PageBreak(),Paragraph('Bill of materials',H2),Paragraph('Fitted parts only. Do-not-populate (DNP) options are omitted.',st('n',fontSize=8,leading=11,textColor=MUTE)),Spacer(1,6)]
    rows=[[Paragraph(h,SB) for h in ['Ref','Qty','Value','Description','Package','Manufacturer · MPN']]]
    for r in bom(BOM[name]): rows.append([Paragraph(r[0],SB),Paragraph(str(r[6]),S),Paragraph(r[1],S),Paragraph(r[2],S),Paragraph(r[3],S),Paragraph(f'{r[4]}<br/><font color="#6b6b70">{r[5]}</font>',S)])
    E.append(tbl(rows,[16*mm,8*mm,24*mm,58*mm,30*mm,42*mm]))
    doc.build(E,onFirstPage=lambda c,dd:header(c,d),onLaterPages=lambda c,dd:header(c,d)); print(name,len(rows)-1)
def system():
    doc=SimpleDocTemplate('/home/claude/site/docs/Hexstar_1U_CubeSat_overview.pdf',pagesize=A4,leftMargin=16*mm,rightMargin=16*mm,topMargin=30*mm,bottomMargin=18*mm,title='Hexstar 1U CubeSat kit overview',author='Hexstar Universe')
    E=[Paragraph('Hexstar 1U CubeSat kit',H1),Spacer(1,3),Paragraph('System overview',st('x',fontSize=11,leading=14,textColor=PUR)),Spacer(1,10),
       Paragraph('A real 1U CubeSat for your desk. Three flight-style boards stack on a single 40-pin bus inside a 3D-printed 1U frame with aluminium-style rails. Telemetry goes over LoRa to a pocket USB ground station and appears live in the Hexstar dashboard.',B),
       Paragraph('Architecture',H2)]
    E.append(tbl([[Paragraph(h,SB) for h in ['Layer','Board','Role']],
      [Paragraph('Top',S),Paragraph('COM · LoRa radio',S),Paragraph('SX1262 868 MHz link to the ground station, up to +22 dBm',S)],
      [Paragraph('Middle',S),Paragraph('OBC · On-board computer',S),Paragraph('ATSAMD21 MCU, IMU, magnetometer, barometer, GNSS, microSD logging',S)],
      [Paragraph('Bottom',S),Paragraph('EPS · Power system',S),Paragraph('18650 cell, USB-C charging, protection, 3.3 V buck, power telemetry',S)],
      [Paragraph('Roof',S),Paragraph('Top plate',S),Paragraph('GNSS patch antenna (U.FL to OBC), 868 MHz whip (SMA, U.FL to COM)',S)]],[22*mm,50*mm,106*mm]))
    E+=[Paragraph('Specifications',H2),tbl([[Paragraph(a,SB),Paragraph(b,S)] for a,b in [
      ('Form factor','1U CubeSat, 100 × 100 × 100 mm (excluding antenna)'),('Structure','3D-printed PETG panels and plates; 4 rails; M3 hardware'),
      ('Stack spacing','Brass standoffs between boards'),('Processor','ATSAMD21G18A, 48 MHz Cortex-M0+'),('Radio','Semtech SX1262 LoRa, 868 MHz'),
      ('Sensors','6-axis IMU, 3-axis magnetometer, barometer, GPS + BeiDou'),('Power','1 × 18650 Li-ion, USB-C charging, 3.3 V / 1 A bus'),
      ('Safety','Remove-before-flight key, slide switch, resettable fuse'),('Storage','microSD flight log'),('Programming','USB-C (Arduino compatible) and SWD')]],[45*mm,133*mm],head=False)]
    E+=[Paragraph('Kit options',H2),tbl([[Paragraph(h,SB) for h in ['Kit','Includes','Price (excl. GST)']],
      [Paragraph('Starter',S),Paragraph('EPS, OBC and LoRa boards (assembled and tested), frame files to print yourself, whip antenna and GNSS patch, example code and docs',S),Paragraph('₹25,000'.replace('₹','INR '),S)],
      [Paragraph('Mission',S),Paragraph('Everything in Starter + 1U frame with rails and panels, 18650 cell and RBF key, USB pocket ground station, telemetry dashboard and lessons',S),Paragraph('INR 39,000',S)],
      [Paragraph('Classroom',S),Paragraph('5 Mission kits, teacher guide and 10-week curriculum, live onboarding, priority support',S),Paragraph('INR 1,75,000',S)]],[24*mm,118*mm,36*mm]),
      Spacer(1,6),Paragraph('Pre-orders are reserved with a booking amount of INR 2,000. The balance is due before shipping. Prices exclude GST.',st('n',fontSize=8,leading=11,textColor=MUTE))]
    doc.build(E,onFirstPage=lambda c,dd:header(c,None),onLaterPages=lambda c,dd:header(c,None))
for b in ['EPS','OBC','LoRa']: board(b)
system()
