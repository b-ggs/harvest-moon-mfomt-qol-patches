# Free basket: the Supermarket basket costs 0G instead of 5,000G.
# Input: tle.gba.  Output: basket.ips (relative to TLE).
from ipslib import make_ips

tle = open('tle.gba', 'rb').read()
rom = bytearray(tle)

def patch(off, old, new):
    assert rom[off:off+len(old)] == old, (hex(off), rom[off:off+len(old)], old)
    assert len(old) == len(new)
    rom[off:off+len(new)] = new

# shop script (RIFF @0x765B94): money check  call 0xEF; push16 5000; cmp; jump   and
# purchase  call 0x73 (give basket); push16 5000; call 0xF1 (pay)
patch(0x767E3A, bytes.fromhex('228813'), bytes.fromhex('220000'))
patch(0x767E91, bytes.fromhex('228813'), bytes.fromhex('220000'))
patch(0x767FB6, b'Baskets are 5,000G.', b'Baskets are free!  ')

recs = make_ips(tle, rom, 'basket.ips')
print(f'{len(recs)} IPS records')
