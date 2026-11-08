import sys,struct
rom=open('tle.gba','rb').read()
for v in [int(x,16) for x in sys.argv[1:]]:
    b=struct.pack('<I',v); i=0; hits=[]
    while True:
        i=rom.find(b,i)
        if i<0: break
        if i%4==0: hits.append(hex(0x08000000+i))
        i+=1
    print(hex(v),len(hits),hits[:40])
