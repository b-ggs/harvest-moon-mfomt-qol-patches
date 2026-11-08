import sys; sys.path.insert(0,'.')
from gdbc import attach
g=attach()
rom=open(sys.argv[1] if len(sys.argv)>1 else 'stamina.gba','rb').read()
off=0x9DA000; n=0x1300
data=rom[off:off+n]
for i in range(0,n,0x100):
    g.wmem(0x08000000+off+i,data[i:i+0x100])
assert g.mem(0x08000000+off,n)==data
print('swapped'); g.cmd('c',wait=False)
