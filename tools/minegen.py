# Runs the game's own mine floor generator (0x080A20BC) in unicorn for every floor of both
# mines and checks the mine-stairs hook (tweaks.py): stairs up directly above the arrival
# tile, stairs down directly below, no hidden stairs left, everything inside the room.
# Floors without stairs down after the hook had no hidden stairs to begin with (floor 255,
# some Lake Mine rolls); the hook leaves those alone, so they're counted, not failed.
# Run from build/: uv run --with unicorn python ../tools/minegen.py [rom] [first] [last] [seeds]
# About 4 ms per floor (all 256 floors x 2 mines x 10 seeds: ~20 s).
import struct, sys, time
from unicorn import *; from unicorn.arm_const import *
a = sys.argv[1:]
rom = open(a[0] if a else 'qol.gba', 'rb').read()
floors = range(int(a[1]) if len(a) > 1 else 0, (int(a[2]) if len(a) > 2 else 255) + 1)
seeds = [0x1234 + k * 0x9E3779B1 & 0xffffffff for k in range(int(a[3]) if len(a) > 3 else 10)]
SEED = struct.unpack('<I', rom[0xD8E20:0xD8E24])[0]       # LCG state used by 0x080D8E0C
MAP, OUT, SP, RET = 0x02010000, 0x02020000, 0x03007d00, 0x0A000000
H = {1: 28, 2: 14}                                          # room height by map type (0x080A2A40), else 6
W = {1: 28}                                                 # room width (0x080A2A2C), else 13
u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
u.mem_map(0x8000000, 0x1000000); u.mem_write(0x8000000, rom)
u.mem_map(0x2000000, 0x40000); u.mem_map(0x3000000, 0x8000); u.mem_map(RET, 0x1000)
def s32(x): return x - (1 << 32) if x >> 31 else x
def swi(u, no, _):
    pc = u.reg_read(UC_ARM_REG_PC); num = u.mem_read(pc - 2, 2)[0]
    if num != 6: raise SystemExit(f'unhandled swi {num:#x} at {pc:#x}')
    n, d = s32(u.reg_read(UC_ARM_REG_R0)), s32(u.reg_read(UC_ARM_REG_R1))   # BIOS Div
    q = abs(n) // abs(d) * (1 if (n < 0) == (d < 0) else -1)
    u.reg_write(UC_ARM_REG_R0, q & 0xffffffff); u.reg_write(UC_ARM_REG_R1, (n - q * d) & 0xffffffff)
    u.reg_write(UC_ARM_REG_R3, abs(q))
u.hook_add(UC_HOOK_INTR, swi)
def gen(mine, floor, seed):
    u.mem_write(SEED, struct.pack('<I', seed)); u.mem_write(MAP, b'\0' * 0x700)
    u.mem_write(SP, struct.pack('<II', 0, 0))              # no fixed objects
    for r, v in ((UC_ARM_REG_R0, OUT), (UC_ARM_REG_R1, MAP), (UC_ARM_REG_R2, mine), (UC_ARM_REG_R3, floor),
                 (UC_ARM_REG_SP, SP), (UC_ARM_REG_LR, RET | 1)):
        u.reg_write(r, v)
    u.emu_start(0x080A20BC | 1, RET, count=5_000_000)
    mtype = struct.unpack('<I', u.mem_read(MAP, 4))[0]
    px, py = u.mem_read(OUT, 2)
    return mtype, struct.unpack('<784H', u.mem_read(MAP + 4, 1568)), px, py
t0 = time.time(); n = 0; bad = []; untouched = []
for mine in (0, 1):
    for f in floors:
        for seed in seeds:
            mtype, t, px, py = gen(mine, f, seed); n += 1
            ups = [i for i in range(784) if t[i] & 15 == 3]
            downs = [i for i in range(784) if t[i] & 15 == 2]
            hidden = sum(1 for x in t if x >> 10 == 1)
            if f == 0:                                      # no stairs up: one revealed stairs down
                if len(downs) != 1 or hidden: bad.append((mine, f, hex(seed), 'floor 0', len(downs), hidden))
                continue
            if not downs and not hidden:
                untouched.append((mine, f)); continue
            h, w = H.get(mtype, 6), W.get(mtype, 13)
            if not (ups == [(py - 1) * 28 + px] and downs == [(py + 1) * 28 + px] and t[py * 28 + px] & 15 == 0
                    and hidden == 0 and py - 1 >= 1 and py + 1 <= h - 1 and 1 <= px <= w - 2):
                bad.append((mine, f, hex(seed), mtype, (px, py), [(i % 28, i // 28) for i in ups + downs], hidden))
dt = time.time() - t0
print(f'{n} floors in {dt:.1f}s ({dt / n * 1000:.1f} ms/floor); failures: {len(bad)}; '
      f'no hidden stairs to reveal (left alone): {len(untouched)}, e.g. {sorted(set(untouched))[:6]}')
for b in bad[:20]: print(b)
sys.exit(1 if bad else 0)
