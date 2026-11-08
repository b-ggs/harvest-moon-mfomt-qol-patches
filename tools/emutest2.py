import sys,struct; sys.path.insert(0,'.')
from unicorn import *; from unicorn.arm_const import *
from PIL import Image
iw=bytearray(0x8000); ew=bytearray(0x40000)
struct.pack_into('<I',iw,0x40c,0x02010000); struct.pack_into('<I',ew,0x10004,0x02020000)
PAL={1:(16,16,16),2:(200,170,100),11:(255,255,255)}
def dlg_entry(y,x,t): return struct.pack('<HHHH',0x5000|y,0x8000|x,0xd000|t,0)
rom=open('stamina.gba','rb').read()
G=struct.unpack_from('<I',ew,struct.unpack_from('<I',iw,0x40c)[0]-0x2000000+4)[0]
SA=G+0x1BE8+0x44-0x2000000
def c15(v): return ((v&31)<<3,((v>>5)&31)<<3,((v>>10)&31)<<3)
def entry(y,x,shape,size,tile,pal=13,mos=0x1000): return struct.pack('<HHHH',y|mos|(shape<<14),x|(size<<14),tile|(pal<<12),0)
def run(name,entries,stam=None,berries=None):
    e=bytearray(ew)
    if stam is not None:
        v=struct.unpack_from('<H',e,SA)[0]; v=(v&~0x7f8f)|(stam<<7)|berries; struct.pack_into('<H',e,SA,v)
    u=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
    u.mem_map(0x8000000,0x1000000); u.mem_write(0x8000000,rom)
    u.mem_map(0x2000000,0x40000); u.mem_write(0x2000000,bytes(e))
    u.mem_map(0x3000000,0x8000); u.mem_write(0x3000000,bytes(iw))
    u.mem_map(0x6000000,0x18000); u.mem_map(0,0x4000)
    sh=b''.join(entries)+struct.pack('<HHHH',0x200,0,0,0)*(128-len(entries))
    u.mem_write(0x30078bc,bytes([len(entries),0,0,0])+sh)
    u.reg_write(UC_ARM_REG_R0,0x30078bc); u.reg_write(UC_ARM_REG_SP,0x3007e00); u.reg_write(UC_ARM_REG_LR,0x1001)
    u.emu_start(0x89da001,0x80097e4,count=50000)
    n=u.mem_read(0x30078bc,1)[0]; out=u.mem_read(0x30078c0,8*n)
    added=[struct.unpack_from('<HHH',out,i*8) for i in range(len(entries),n)]
    print(name,'-> added:',[tuple(hex(v) for v in a) for a in added])
    if not added: return None
    vr=u.mem_read(0x6010000,0x8000)
    img=Image.new('RGB',(70,16),(90,160,60)); px=img.load()
    x0=added[0][1]&511
    for a0,a1,a2 in added:
        bx=(a1&511)-x0; t0=a2&1023; p=a2>>12
        for ty in range(2):
            for tx in range(4):
                t=t0+ty*4+tx
                for y in range(8):
                    for x in range(8):
                        b=vr[t*32+y*4+x//2]; ci=(b>>4) if x&1 else b&15
                        if ci: px[bx+tx*8+x,ty*8+y]=PAL.get(ci,(255,0,255))
    return img
clock=[entry(140,132,1,2,32),entry(140,164,1,2,40),entry(140,196,0,1,28,mos=0x1000)]
dlg=[struct.pack('<HHHH',0x1098,0xe9,0xd01c,0)]+[dlg_entry(107,8+32*i,t) for i,t in enumerate((32,40,48,128,136,144,152))]
run('dialog',dlg)
run('moved clock 136/144/132',[entry(140,132,1,2,136),entry(140,164,1,2,144),entry(140,196,0,1,132,mos=0x1000)],80,0)
imgs=[run(f'clock {s}/{150+10*b}',clock,s,b) for s,b in ((126,0),(7,0),(0,0),(250,10))]
W=Image.new('RGB',(70,16*len(imgs)+3*len(imgs)))
for i,im in enumerate(imgs): W.paste(im,(0,i*19))
W.resize((W.width*6,W.height*6),Image.NEAREST).save('raw_test.png')
