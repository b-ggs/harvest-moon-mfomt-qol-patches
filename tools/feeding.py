# Automatic animal feeding: each night, troughs are filled from the silo / feed bin.
# Input: tle.gba.  Output: feeding.ips (relative to TLE).
#
# Barn  = G+0x600, nightly update 0x0800D624(barn).  Coop = G+0x420, nightly 0x0800CA60(coop).
# Each building's first u32:
#   bit 0      building size (big = 1)
#   bits 1-10  feed count (barn: Fodder in the silo, coop: Chicken Feed), max 999
#   barn bits 13-28 / coop bits 12-19: one "filled" flag per trough
# Troughs: barn 8 (+8 if big), coop 4 (+4 if big). Animal slot i (occupied if bit 0
# of its first byte is set) is at barn+0x2C+i*0x3C / coop+0x18+i*0x30.
# The nightly update counts the filled troughs (a shared food pool), clears them, and
# feeds animals from that pool. The hook wraps it: fill, run the original, fill again.
# A fill tops up empty troughs until filled >= number of animals, taking 1 feed per
# trough and stopping when feed runs out; troughs filled by hand count toward that.
# The first fill covers animals bought that day; the refill leaves the troughs visibly
# stocked for the day, so the next night's first fill normally takes nothing.
import subprocess, struct
from ipslib import make_ips

LLVM = '/opt/homebrew/opt/llvm/bin'
HOOK = 0x089DD000
PROLOGUE = bytes.fromhex('f0b557464e464546')   # push {r4-r7,lr}; mov r7,sl; mov r6,sb; mov r5,r8
SITES = {
    # name: (function, flag shift, troughs-per-size shift (8 -> 3, 4 -> 2), slot offset, slot stride)
    'barn': (0x0800D624, 13, 3, 0x2C, 0x3C),
    'coop': (0x0800CA60, 12, 2, 0x18, 0x30),
}

tle = open('tle.gba', 'rb').read()
rom = bytearray(tle)

def patch(off, old, new):
    assert rom[off:off+len(old)] == old, (hex(off), rom[off:off+len(old)].hex(), old.hex())
    assert len(old) == len(new)
    rom[off:off+len(new)] = new

def feeder(name, fn, sh, tsh, slot, stride):
    return f"""
{name}:                         @ replaces the original function's entry
    push {{r4, r5, r6, r7, lr}}
    adds r4, r0, #0             @ building
    bl   {name}_topup
    adds r0, r4, #0
    ldr  r3, =0x{fn + 8 + 1:08x}
    bl   {name}_orig            @ the original function, returning here
    push {{r0}}
    adds r0, r4, #0
    bl   {name}_topup
    pop  {{r0}}
    pop  {{r4, r5, r6, r7}}
    pop  {{r3}}
    bx   r3
{name}_orig:                    @ the replaced prologue, then the rest of the original
    push {{r4, r5, r6, r7, lr}}
    mov  r7, sl
    mov  r6, sb
    mov  r5, r8
    bx   r3
{name}_topup:                   @ r0 = building; preserves r4-r7
    push {{r4, r5, r6, r7, lr}}
    ldr  r1, [r0]               @ building word
    movs r2, #1
    ands r2, r1
    lsls r2, r2, #{tsh}
    adds r2, #{1 << tsh}        @ r2 = trough count
    movs r3, #0                 @ r3 = animals
    adds r4, r0, #0
    adds r4, #{slot}
    movs r5, #0
{name}_count:
    ldrb r6, [r4]
    lsls r6, r6, #31
    beq  1f
    adds r3, #1
1:
    adds r4, #{stride}
    adds r5, #1
    cmp  r5, r2
    blo  {name}_count
    lsls r4, r1, #21
    lsrs r4, r4, #22            @ r4 = feed count
    movs r5, #0
    movs r6, #0                 @ r6 = troughs already filled
{name}_filled:
    movs r7, #1
    lsls r7, r7, r5
    lsls r7, r7, #{sh}
    tst  r1, r7
    beq  2f
    adds r6, #1
2:
    adds r5, #1
    cmp  r5, r2
    blo  {name}_filled
    movs r5, #0
{name}_fill:
    cmp  r6, r3
    bhs  {name}_done
    cmp  r4, #0
    beq  {name}_done
    movs r7, #1
    lsls r7, r7, r5
    lsls r7, r7, #{sh}
    tst  r1, r7
    bne  3f
    orrs r1, r7
    subs r4, #1
    adds r6, #1
3:
    adds r5, #1
    cmp  r5, r2
    blo  {name}_fill
{name}_done:
    ldr  r7, =0xfffff801
    ands r1, r7
    lsls r4, r4, #1
    orrs r1, r4
    str  r1, [r0]
    pop  {{r4, r5, r6, r7}}
    pop  {{r3}}
    bx   r3
.ltorg
"""

asm = '.syntax unified\n.thumb\n.text\n' + ''.join(feeder(n, *v) for n, v in SITES.items())
open('feeding.s', 'w').write(asm)
subprocess.run(['clang', '-target', 'armv4t-none-eabi', '-mthumb', '-c', 'feeding.s', '-o', 'feeding.o'], check=True)
subprocess.run([f'{LLVM}/llvm-objcopy', '-O', 'binary', '-j', '.text', 'feeding.o', 'feeding.bin'], check=True)
subprocess.run([f'{LLVM}/llvm-nm', 'feeding.o'], check=True, stdout=open('feeding.sym', 'w'))
code = open('feeding.bin', 'rb').read()
syms = {l.split()[2]: int(l.split()[0], 16) for l in open('feeding.sym') if len(l.split()) == 3}

off = HOOK - 0x08000000
assert all(b == 0xFF for b in rom[off:off+0x1000]), 'hook block not free'
rom[off:off+len(code)] = code
for name, (fn, *_rest) in SITES.items():
    patch(fn - 0x08000000, PROLOGUE,
          struct.pack('<HH', 0x4B00, 0x4718) + struct.pack('<I', (HOOK + syms[name]) | 1))

recs = make_ips(tle, rom, 'feeding.ips')
print(f'hook {len(code)} bytes ({ {n: hex(HOOK + syms[n]) for n in SITES} }), {len(recs)} IPS records')
