import sys,struct; sys.path.insert(0,'.')
from gdbc import attach
g=attach()
u32=lambda a: struct.unpack('<I',g.mem(a,4))[0]
P=u32(0x0300040C); G=u32(P+4); Q=u32(P+0x8c)
print('P',hex(P),'G',hex(G),'[P+8c]',hex(Q))
for name,base in (('P+8c',Q),('G',G)):
    if base>>24!=2: continue
    m=g.mem(base+0x2e94+4,1568); t=struct.unpack('<784H',m)
    types=[x&15 for x in t]; items=[(x>>10) for x in t]
    print(name, 'type counts',{k:types.count(k) for k in set(types)}, 'buried',{k:items.count(k) for k in set(items)})
    if name==sys.argv[1] if len(sys.argv)>1 else True:
        for y in range(28):
            print(''.join('.TVU#56789abcdef'[x&15] if (x>>10)!=1 else 'h' for x in t[y*28:y*28+28]))
g.cmd('c',wait=False)
