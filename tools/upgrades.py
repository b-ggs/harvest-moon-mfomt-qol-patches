# Fast tool upgrades: every blacksmith upgrade takes 1 day (vanilla: 1-4 by ore level).
# Input: tle.gba.  Output: upgrades.ips (relative to TLE).
#
# 0x08096384(tool, ore) returns the upgrade time in days: target level (from the ore)
# minus current level, or 2 for Mythic Stone on a level-6 tool. The result goes into
# the job object and on to 0x080A3FB4, which stores it in bits 6-8 of [G+0x1DBC+0x14].
# Each night 0x080A3FE0 decrements it (only if nonzero); the tool is ready when it's 0.
# Making both "days = ..." results 1 puts every upgrade on the vanilla copper path.
from ipslib import make_ips

tle = open('tle.gba', 'rb').read()
rom = bytearray(tle)

def patch(off, old, new):
    assert rom[off:off+len(old)] == old, (hex(off), rom[off:off+len(old)], old)
    assert len(old) == len(new)
    rom[off:off+len(new)] = new

patch(0x0963FA, bytes.fromhex('e51a'), bytes.fromhex('0125'))   # subs r5,r4,r3  -> movs r5,#1
patch(0x096404, bytes.fromhex('0225'), bytes.fromhex('0125'))   # movs r5,#2     -> movs r5,#1

recs = make_ips(tle, rom, 'upgrades.ips')
print(f'{len(recs)} IPS records')
