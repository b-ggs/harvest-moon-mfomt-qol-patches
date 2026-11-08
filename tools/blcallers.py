import struct,sys
rom=open('tle.gba','rb').read()
tg=[int(x,16) for x in sys.argv[1:]]
for a in range(0,0x400000,2):
    h1,h2=struct.unpack_from('<HH',rom,a)
    if (h1&0xF800)==0xF000 and (h2&0xF800)==0xF800:
        off=((h1&0x7FF)<<12)|((h2&0x7FF)<<1)
        if off&0x400000: off-=0x800000
        t=0x08000000+a+4+off
        if t in tg: print(hex(t),'<-',hex(0x08000000+a))
