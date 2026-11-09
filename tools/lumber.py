# More lumber: branches and stumps drop 10x the lumber (branch 1 -> 10, stump 6 -> 60).
# Input: tle.gba.  Output: lumber.ips (relative to TLE).
#
# Lumber is the 10-bit count at G+0x24 (u16 at obj+0x10 with obj = G+0x14): getter
# 0x08009B64, adder 0x08009BD4(obj, n) = min(count + n, 999). Its axe callers each pass the
# amount as `movs r1, #n` right before the bl, so the patch only changes those immediates:
#   0x0801D016 / 0x0801D048  farm-field cell, normal swing: branch +1 / stump +6
#                            (0x0801CE68 returns 1 = branch cut, 2 = stump cut)
#   0x08017714 / 0x08017708  map objects 0x12 / 0x15 (0x08017654): +1 / +6
#   0x0801D18E               whole-field mode (0x0801D13C with r1 == 2): +1 per branch or
#                            stump that 0x0800A3AC clears (1 = branch, 2 = stump, 3 = hit)
# Not touched: 0x08089EA2 (buying lumber, variable amount) and 0x0804AF64 (a transfer).
import struct
from ipslib import make_ips

MULT = 10
ADDER = 0x08009BD4
SITES = [(0x0801D016, 1), (0x0801D048, 6), (0x08017714, 1), (0x08017708, 6), (0x0801D18E, 1)]

tle = open('tle.gba', 'rb').read()
rom = bytearray(tle)

def bl_target(addr):
    o = addr - 0x08000000
    hi, lo = struct.unpack('<HH', rom[o:o + 4])
    assert hi >> 11 == 0x1E and lo >> 11 == 0x1F, hex(addr)
    off = ((hi & 0x7FF) << 12 | (lo & 0x7FF) << 1)
    if off & 0x400000: off -= 0x800000
    return addr + 4 + off

for addr, n in SITES:
    o = addr - 0x08000000
    assert rom[o:o + 2] == bytes([n, 0x21]), (hex(addr), rom[o:o + 2].hex())   # movs r1, #n
    assert bl_target(addr + 2) == ADDER, hex(addr)
    assert n * MULT <= 255
    rom[o] = n * MULT

recs = make_ips(tle, rom, 'lumber.ips')
print(f'{len(recs)} IPS records')
