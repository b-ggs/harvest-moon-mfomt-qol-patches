# Self-watering crops: every night the farm field is watered, as if it had rained.
# Input: tle.gba.  Output: watering.ips (relative to TLE).
#
# Farm field: G+0x9EC, 43x25 cells of u32 (ends at G+0x1AB8). Bits 0-1 = soil:
# 0 untilled, 1 tilled dry, 2 watered (the can's 0x0800A4A8 does 1 -> 2;
# 0x0800A190(cell, state) sets it).
# The daily per-cell update ends at 0x0800AB42 with
#     if (r8 == 0) { if soil == 2: soil = 1 }    clear day: watered soil dries
#     else         { if soil == 1: soil = 2 }    rain: dry soil is watered
# where r8 is the rain flag. Making the branch at 0x0800AB46 unconditional takes the
# rain path every night, after the crops have grown, so all tilled soil starts
# each day watered.
# (0x0800AB78, called from 0x08011276, is the season-change pass, not the daily one.)
from ipslib import make_ips

tle = open('tle.gba', 'rb').read()
rom = bytearray(tle)

def patch(off, old, new):
    assert rom[off:off+len(old)] == old, (hex(off), rom[off:off+len(old)].hex(), old.hex())
    assert len(old) == len(new)
    rom[off:off+len(new)] = new

patch(0x00AB44, bytes.fromhex('002809d1'), bytes.fromhex('002809e0'))   # cmp r0,#0; bne -> b

recs = make_ips(tle, rom, 'watering.ips')
print(f'{len(recs)} IPS records')
