import struct, random
from unicorn import *; from unicorn.arm_const import *
rom = open('qol.gba','rb').read()
for h in (0x81d585,0x81eee3): print('cottage block', rom[h:h+18].hex(' '))
MAP = 0x02010000; SP = 0x03007d00
def run(tiles):
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x8000000, 0x1000000); u.mem_write(0x8000000, rom)
    u.mem_map(0x2000000, 0x40000); u.mem_map(0x3000000, 0x8000)
    u.mem_write(MAP + 4, b''.join(struct.pack('<H', t) for t in tiles))
    u.mem_write(SP + 0x30, struct.pack('<II', 0x00000507, 0x02030000))
    u.reg_write(UC_ARM_REG_R6, MAP); u.reg_write(UC_ARM_REG_SP, SP)
    u.emu_start(0x080A22D8 | 1, 0x080A22E0, count=100000)
    assert u.reg_read(UC_ARM_REG_R0) == 0x02030000 and u.mem_read(0x02030000, 4) == struct.pack('<I', 0x507)
    return list(struct.unpack('<784H', u.mem_read(MAP + 4, 1568)))
def T(x, y): return y * 28 + x
random.seed(1)
base = [random.choice([0x0000, 0x0004, 0x0104, 0x0000, 0x0800, 0x0c00, 0x3000, 0x0200]) for _ in range(784)]
m = list(base); m[T(5,5)] = 0x0003; m[T(6,6)] = 0x0c34; m[T(10,3)] = 0x0400; m[T(12,12)] = 0x0c00
out = run(m)
print('stairs-up', hex(out[T(5,5)]), ' lower-right (was 0x0c34 rock w/ berry):', hex(out[T(6,6)]))
print('hidden stairs left:', sum(1 for t in out if (t >> 10) == 1), '(before', sum(1 for t in m if (t >> 10) == 1), ')')
print('power berry kept:', hex(out[T(12,12)]), ' gold kept:', all(o == b for o, b in zip(out, m) if (b >> 10) == 2))
changed = [i for i in range(784) if out[i] != m[i] and (m[i] >> 10) != 1]
print('other tiles changed:', [(i % 28, i // 28, hex(m[i]), hex(out[i])) for i in changed])
# no hidden stairs -> untouched
m2 = [t for t in m]; m2 = [(t & 0x3ff) if (t >> 10) == 1 else t for t in m2]
print('floor w/o hidden stairs untouched:', run(m2) == m2)
# stairs-up on right edge -> no placement, but still no crash
m3 = list(m); m3[T(5,5)] = 0; m3[T(27,4)] = 3
o3 = run(m3); print('right-edge stairs: placed?', any(o3[i] & 15 == 2 and m3[i] & 15 != 2 for i in range(784)))
# real floor-0 map (no stairs up)
import sys; sys.path.insert(0,'.')
from gdbc import attach
g=attach(); P=struct.unpack('<I',g.mem(0x0300040C,4))[0]; G=struct.unpack('<I',g.mem(P+4,4))[0]
f0=list(struct.unpack('<784H',g.mem(G+0x2e94+4,1568))); g.cmd('c',wait=False)
o=run(f0)
d=[(i%28,i//28,hex(f0[i]),hex(o[i])) for i in range(784) if o[i]!=f0[i]]
print('floor0: stairs down at', [(x,y) for x,y,a,b in d if int(b,16)&15==2], ' hidden left', sum(1 for t in o if t>>10==1), ' tiles changed', len(d))
print('non-hidden tiles changed:', [x for x in d if int(x[2],16)>>10!=1])
