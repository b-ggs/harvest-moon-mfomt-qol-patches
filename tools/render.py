import struct
from PIL import Image
def c15(v): return ((v&31)<<3,((v>>5)&31)<<3,((v>>10)&31)<<3)
def render(g,path,scroll=None):
    io=g.mem(0x4000000,0x60); vram=b''.join(g.mem(0x6000000+i,0x4000) for i in range(0,0x18000,0x4000))
    pal=g.mem(0x5000000,0x400); oam=g.mem(0x7000000,0x400)
    P=[c15(struct.unpack_from('<H',pal,i*2)[0]) for i in range(512)]
    sh=g.mem(0x2005b28,0x54)
    if scroll is None: scroll={b:(struct.unpack_from('<H',sh,0x10+b*4)[0]&511,struct.unpack_from('<H',sh,0x12+b*4)[0]&511) for b in range(4)}
    disp=struct.unpack_from('<H',io,0)[0]
    img=Image.new('RGB',(240,160),P[0]); px=img.load()
    layers=[]
    for bg in range(4):
        if not disp&(0x100<<bg): continue
        cnt=struct.unpack_from('<H',io,8+bg*2)[0]; layers.append((cnt&3,bg,cnt))
    for prio,bg,cnt in sorted(layers,reverse=True):
        cb=((cnt>>2)&3)*0x4000; sb=((cnt>>8)&31)*0x800; c256=cnt&0x80; size=cnt>>14
        sx,sy=(scroll or {}).get(bg,(0,0))
        w=256*(2 if size&1 else 1); h=256*(2 if size&2 else 1)
        for y in range(160):
            for x in range(240):
                X=(x+sx)%w; Y=(y+sy)%h
                blk=0
                if X>=256: blk+=1
                if Y>=256: blk+= 2 if w==512 else 1
                e=struct.unpack_from('<H',vram,sb+blk*0x800+((Y%256)//8*32+(X%256)//8)*2)[0]
                t=e&0x3ff; tx=X%8; ty=Y%8
                if e&0x400: tx=7-tx
                if e&0x800: ty=7-ty
                if c256:
                    ci=vram[cb+t*64+ty*8+tx] if cb+t*64+ty*8+tx<0x10000 else 0
                    if ci: px[x,y]=P[ci]
                else:
                    a=cb+t*32+ty*4+tx//2
                    if a>=0x10000: continue
                    b=vram[a]; ci=(b>>4) if tx&1 else (b&15)
                    if ci: px[x,y]=P[(e>>12)*16+ci]
    if disp&0x1000:
        SZ={(0,0):(8,8),(0,1):(16,16),(0,2):(32,32),(0,3):(64,64),(1,0):(16,8),(1,1):(32,8),(1,2):(32,16),(1,3):(64,32),(2,0):(8,16),(2,1):(8,32),(2,2):(16,32),(2,3):(32,64)}
        for i in range(127,-1,-1):
            a0,a1,a2=struct.unpack_from('<HHH',oam,i*8)
            if a0&0x300==0x200: continue
            sh=a0>>14; sz=a1>>14
            if sh==3: continue
            w,h=SZ[(sh,sz)]; y0=a0&255; x0=a1&511
            if y0>=160: y0-=256
            if x0>=240: x0-=512
            t=a2&0x3ff; pb=a2>>12; c256=a0&0x2000; hf=a1&0x1000 and not a0&0x100; vf=a1&0x2000 and not a0&0x100
            for yy in range(h):
                for xx in range(w):
                    X=x0+xx;Y=y0+yy
                    if not(0<=X<240 and 0<=Y<160): continue
                    tx=w-1-xx if hf else xx; ty=h-1-yy if vf else yy
                    if disp&0x40: tile=t+(ty//8)*(w//8)*(2 if c256 else 1)+(tx//8)*(2 if c256 else 1)
                    else: tile=t+(ty//8)*32+(tx//8)*(2 if c256 else 1)
                    base=0x10000+tile*32
                    if c256:
                        ci=vram[base+(ty%8)*8+tx%8] if base<0x18000 else 0
                        if ci: px[X,Y]=P[256+ci]
                    else:
                        if base>=0x18000: continue
                        b=vram[base+(ty%8)*4+(tx%8)//2]; ci=(b>>4) if tx&1 else b&15
                        if ci: px[X,Y]=P[256+pb*16+ci]
    img.resize((480,320),Image.NEAREST).save(path)
