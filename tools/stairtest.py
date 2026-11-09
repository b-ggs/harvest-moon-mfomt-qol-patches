# Unit test for the mine-stairs hook (tweaks.py): stairs up above the arrival tile, stairs down below.
# Run from build/: uv run --with unicorn python ../tools/stairtest.py [rom]
import struct, random, sys
from unicorn import *; from unicorn.arm_const import *
rom = open(sys.argv[1] if len(sys.argv) > 1 else "qol.gba",'rb').read()
MAP = 0x02010000; SP = 0x03007d00
def run(mtype, tiles, spawn):
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.mem_map(0x8000000, 0x1000000); u.mem_write(0x8000000, rom)
    u.mem_map(0x2000000, 0x40000); u.mem_map(0x3000000, 0x8000)
    u.mem_write(MAP, struct.pack('<I', mtype))
    u.mem_write(MAP + 4, b''.join(struct.pack('<H', t) for t in tiles))
    u.mem_write(SP + 0x30, bytes([spawn[0], spawn[1], 0xAA, 0xBB]) + struct.pack('<I', 0x02030000))
    u.reg_write(UC_ARM_REG_R6, MAP); u.reg_write(UC_ARM_REG_SP, SP)
    u.emu_start(0x080A22D8 | 1, 0x080A22E0, count=100000)
    out = u.mem_read(0x02030000, 4)
    assert out[2:] == b'\xaa\xbb'
    return list(struct.unpack('<784H', u.mem_read(MAP + 4, 1568))), (out[0], out[1])
T = lambda x, y: y * 28 + x
H = {0: 6, 1: 28, 2: 14, 3: 6}; W = {0: 13, 1: 28, 2: 13, 3: 13}
random.seed(2); n = 0
for mtype in (0, 1, 2, 3):
    w, h = W[mtype], H[mtype]
    for trial in range(300):
        tiles = [0] * 784
        for y in range(h):
            for x in range(w):
                tiles[T(x, y)] = random.choice([0, 0, 0x4 | (random.randrange(0x24) << 4), 0x0800, 0x0c00, 0x0c04 | 0x30])
        ux, uy = random.randrange(1, w - 1), random.randrange(1, h - 1)
        if trial < 20: uy = h - 2
        tiles[T(ux, uy)] = 3
        sx, sy = random.choice([(ux-1, uy), (ux+1, uy), (ux, uy-1), (ux, uy+1)])
        tiles[T(sx, sy)] = 0
        while True:
            hx, hy = random.randrange(w), random.randrange(h)
            if (hx, hy) not in ((ux, uy), (sx, sy)): break
        tiles[T(hx, hy)] = 0x0400 | 4   # at least one hidden stairs
        o, sp = run(mtype, tiles, (sx, sy))
        px, py = sp
        assert o[T(px, py - 1)] == 3, (mtype, ux, uy, sp)
        assert o[T(px, py + 1)] == 2
        assert o[T(px, py)] & 0x3ff == 0 and o[T(px, py)] >> 10 != 1
        assert px == ux and py == min(uy, h - 3) + 1 and py + 1 <= h - 1
        assert sum(1 for t in o if t & 15 == 3) == 1 and sum(1 for t in o if t & 15 == 2) == 1
        assert all(t >> 10 != 1 for t in o)
        keep = {T(px, py - 1), T(px, py), T(px, py + 1), T(ux, uy)}
        bad = [i for i in range(784) if i not in keep and o[i] != (tiles[i] & 0x3ff if tiles[i] >> 10 == 1 else tiles[i])]
        assert not bad, bad
        n += 1
# no stairs up -> floor-0 path unchanged: reveals a hidden stairs, spawn untouched
tiles = [0] * 784; tiles[T(3, 4)] = 0x0400; tiles[T(5, 2)] = 0x0400
o, sp = run(0, tiles, (0, 0))
print('floor0: down at', [(i % 28, i // 28) for i in range(784) if o[i] & 15 == 2], 'spawn', sp)
print(n, 'random floors OK')
