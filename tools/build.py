# Builds the stamina HUD patch on top of the TLE ROM.
# Output: stamina.gba (patched ROM) and stamina.ips (apply after TLE).
import subprocess, struct, sys

BASE_ROM = 'tle.gba'
HOOK_ADDR = 0x089DA000          # free space after TLE's credit string
TRAMP = 0x080098CC              # per-frame OAM flush: flush(0x80097E4) + clear(0x800989C)
GLOBAL = 0x0300040C            # static ptr -> obj; [obj+4] = game-state block
STAM_OFF = 0x1BE8 + 0x44       # player struct + stamina halfword
TILE = 1004                     # 20 OBJ tiles 1004-1023 (32x16 + 32x16 + 16x16)
VRAM = 0x06010000 + TILE * 32
PAL = 13                        # clock text palette
LLVM = '/opt/homebrew/opt/llvm/bin'

# ---------- font (6x7 bold, matching the clock's 2px strokes) ----------
DIGITS = {
 0: [".####.","##..##","##..##","##..##","##..##","##..##",".####."],
 1: ["..##..",".###..","..##..","..##..","..##..","..##..",".####."],
 2: [".####.","##..##","....##","...##.","..##..",".##...","######"],
 3: [".####.","##..##","....##","..###.","....##","##..##",".####."],
 4: ["...##.","..###.",".####.","##.##.","######","...##.","...##."],
 5: ["######","##....","#####.","....##","....##","##..##",".####."],
 6: [".####.","##....","#####.","##..##","##..##","##..##",".####."],
 7: ["######","....##","...##.","..##..","..##..","..##..","..##.."],
 8: [".####.","##..##","##..##",".####.","##..##","##..##",".####."],
 9: [".####.","##..##","##..##",".#####","....##","....##",".####."],
}
S_ = [".####.","##..##","##....",".####.","....##","##..##",".####."]
T_ = ["######","..##..","..##..","..##..","..##..","..##..","..##.."]
BODY, SHADOW, WHITE = 1, 2, 11

SL_ = ["....##","...##.","...##.","..##..",".##...",".##...","##...."]
F_ = ["######","##....","##....","#####.","##....","##....","##...."]
I_ = ["######","..##..","..##..","..##..","..##..","..##..","######"]
M_ = ["##..##","######","######","##..##","##..##","##..##","##..##"]
E_ = ["######","##....","##....","#####.","##....","##....","######"]
X_ = ["......","......","##..##",".####.","..##..",".####.","##..##"]
DOT_ = ["......","......","......","......","......","..##..","..##.."]

def canvas(w): return [[0]*w for _ in range(8)]
def stamp(c, glyph, x0, color, shadow):
    W = len(c[0])
    for y, row in enumerate(glyph):
        for x, ch in enumerate(row):
            if ch == '#': c[y][x0+x] = color
    if shadow:
        for y, row in enumerate(glyph):
            for x, ch in enumerate(row):
                if ch == '#':
                    for dx, dy in ((1,0),(0,1),(1,1)):
                        X, Y = x0+x+dx, y+dy
                        if X < W and Y < 8 and c[Y][X] == 0: c[Y][X] = shadow
def to_tiles(c):  # Wx8 canvas -> W/8 tiles, 4bpp
    out = bytearray()
    for t in range(len(c[0]) // 8):
        for y in range(8):
            for x in range(0, 8, 2):
                out.append(c[y][t*8+x] | (c[y][t*8+x+1] << 4))
    return bytes(out)

# glyph tiles (one char per 8px cell): 0-9 digits, 10 blank, 11 slash, 12 S, 13 T, 14 F (labels white)
GLYPH = b''
for d in range(20):
    c = canvas(8)
    if d < 10: stamp(c, DIGITS[d], 0, BODY, SHADOW)
    elif d == 11: stamp(c, SL_, 0, BODY, SHADOW)
    elif d == 12: stamp(c, S_, 1, WHITE, 0)
    elif d == 13: stamp(c, T_, 0, WHITE, 0)
    elif d == 14: stamp(c, F_, 1, WHITE, 0)
    elif d == 15: stamp(c, I_, 1, WHITE, 0)
    elif d == 16: stamp(c, M_, 1, WHITE, 0)
    elif d == 17: stamp(c, E_, 1, WHITE, 0)
    elif d == 18: stamp(c, X_, 1, BODY, SHADOW)
    elif d == 19: stamp(c, DOT_, 0, BODY, SHADOW)
    GLYPH += to_tiles(c)
B = 10
# 2 rows x 10 cells:  "ST nnn/mmm"  /  "FT fff/100"
TEMPLATE = bytes([12,13,B, B,B,B, 11, B,B,B,
                  14,13,B, B,B,B, 11, 1,0,0])
# row 2 while the clock-speed popup is up: 'TIME x1' / 'x1.25' / 'x1.5' / 'x2'
XX, DT = 18, 19
SPEEDROWS = bytes([13,15,16,17,B, B,B,B,XX,1,
                   13,15,16,17,B, XX,1,DT,2,5,
                   13,15,16,17,B, B,XX,1,DT,5,
                   13,15,16,17,B, B,B,B,XX,2])
TICKS = bytes([25, 31, 38, 50])          # game-minute length per speed (vanilla 25)
STATE = 0x0203FFF0                       # u16 prev keys, u8 popup timer (unused top of EWRAM)
SETTINGS = 0x224C                        # Diary settings byte in G; bits 4-5 = clock speed
# cell -> OBJ tile offset. Sprites: A 32x16 (tiles 0-7), B 32x16 (8-15), C 16x16 (16-19), 1D mapping
CELLMAP = bytes([(r*4 + c) if c < 4 else (8 + r*4 + c-4) if c < 8 else (16 + r*2 + c-8)
                 for r in range(2) for c in range(10)])

# ---------- hook ----------
asm = f"""
.syntax unified
.thumb
.text
start:
    push {{r4-r7, lr}}
    adds r7, r0, #0          @ OAM manager
    adds r6, r0, #4          @ shadow OAM

    ldr  r0, =0x080091A0     @ hold L + tap Select: cycle clock speed
    ldr  r0, [r0]            @ KEYINPUT address, read via the game's own literal
    ldrh r0, [r0]
    mvns r0, r0
    ldr  r1, =0x3ff
    ands r0, r1              @ r0 = keys held
    ldr  r3, ={STATE:#x}
    ldrh r1, [r3]            @ r1 = held last frame
    strh r0, [r3]
    ldrb r2, [r3, #2]
    cmp  r2, #0
    beq  k1
    subs r2, #1
    strb r2, [r3, #2]        @ popup timer
k1:
    adds r2, r0, #0
    bics r2, r1              @ newly pressed
    movs r1, #4
    tst  r2, r1              @ Select
    beq  keys_done
    ldr  r1, =0x200
    tst  r0, r1              @ L held
    beq  keys_done
    ldr  r0, ={GLOBAL:#x}
    ldr  r0, [r0]
    lsrs r1, r0, #24
    cmp  r1, #2
    bne  keys_done
    ldr  r0, [r0, #4]
    lsrs r1, r0, #24
    cmp  r1, #2
    bne  keys_done
    ldr  r1, ={SETTINGS:#x}
    adds r0, r0, r1
    ldrb r1, [r0]
    lsls r2, r1, #26
    lsrs r2, r2, #30
    adds r2, #1
    lsls r2, r2, #30
    lsrs r2, r2, #26         @ ((speed+1) & 3) << 4
    movs r3, #0x30
    bics r1, r3
    orrs r1, r2
    strb r1, [r0]
    ldr  r3, ={STATE:#x}
    movs r2, #120            @ show for 2 seconds
    strb r2, [r3, #2]
keys_done:
    movs r5, #0
find_clock:                  @ clock = 32x16, 32x16 (+32px), 16x16 (+64px), same row, pal 13
    lsls r1, r5, #3          @ (matched by layout: its tile numbers move with VRAM use)
    adds r1, r6, r1
    ldrh r2, [r1]            @ attr0
    lsrs r3, r2, #14
    cmp  r3, #1              @ wide
    bne  next_clock
    lsls r3, r2, #22
    lsrs r3, r3, #30
    cmp  r3, #2              @ hidden?
    beq  next_clock
    ldrh r3, [r1, #8]
    cmp  r3, r2              @ entry+1: same attr0
    bne  next_clock
    ldr  r0, =0x4000
    subs r2, r2, r0
    ldrh r3, [r1, #16]
    cmp  r3, r2              @ entry+2: same row, square
    bne  next_clock
    ldrh r2, [r1, #2]        @ attr1
    lsrs r3, r2, #14
    cmp  r3, #2              @ size 2
    bne  next_clock
    adds r2, #32
    ldrh r3, [r1, #10]
    cmp  r3, r2              @ entry+1: x+32, size 2
    bne  next_clock
    adds r2, #32
    subs r2, r2, r0
    ldrh r3, [r1, #18]
    cmp  r3, r2              @ entry+2: x+64, size 1
    bne  next_clock
    ldrh r2, [r1, #4]        @ attr2
    lsrs r3, r2, #12
    cmp  r3, #13             @ palette 13
    bne  next_clock
    ldrh r3, [r1, #12]       @ entry+1: palette 13 (its tile is NOT always +8:
    lsrs r3, r3, #12         @  after mine floor 2 -> exit it was 56 / 128 / 136)
    cmp  r3, #13
    bne  next_clock
    ldrh r3, [r1, #20]
    lsrs r3, r3, #12
    cmp  r3, #13
    bne  next_clock
    ldrh r2, [r1, #2]
    lsls r2, r2, #23
    lsrs r2, r2, #23
    cmp  r2, #82             @ need room on screen to the left
    bge  found_clock
next_clock:
    adds r5, #1
    cmp  r5, #126
    blt  find_clock
    b    done
found_clock:
    adds r5, r1, #0          @ clock entry
    ldr  r0, ={GLOBAL:#x}
    ldr  r0, [r0]
    lsrs r2, r0, #24
    cmp  r2, #2              @ must point into EWRAM
    bne  done
    ldr  r0, [r0, #4]        @ game-state block
    lsrs r2, r0, #24
    cmp  r2, #2
    bne  done
    ldr  r2, ={STAM_OFF:#x}
    adds r0, r0, r2
    ldr  r4, [r0]            @ r4 = player word: berries 0-3, stamina 7-14, fatigue 16-22
    ldrb r3, [r7]            @ slots used this frame; need 3
    cmp  r3, #126
    bhs  done
    adds r1, r3, #3
    strb r1, [r7]            @ claim them so the game's clear hides them next frame
    lsls r3, r3, #3
    adds r3, r6, r3          @ r3 = first new entry
    ldrb r1, [r5]            @ clock y
    strh r1, [r3, #16]       @ C: square
    ldr  r2, =0x4000         @ A, B: wide
    orrs r1, r2
    strh r1, [r3]
    strh r1, [r3, #8]
    ldrh r1, [r5, #2]
    lsls r1, r1, #23
    lsrs r1, r1, #23
    subs r1, #82             @ 80px box + 2px gap left of the clock
    ldr  r0, =0x8000         @ size 2 (32x16)
    lsls r2, r1, #23
    lsrs r2, r2, #23
    orrs r2, r0
    strh r2, [r3, #2]
    adds r1, #32
    lsls r2, r1, #23
    lsrs r2, r2, #23
    orrs r2, r0
    strh r2, [r3, #10]
    adds r1, #32
    lsls r2, r1, #23
    lsrs r2, r2, #23
    ldr  r0, =0x4000         @ size 1 (16x16)
    orrs r2, r0
    strh r2, [r3, #18]
    ldrh r1, [r5, #4]
    ldr  r2, =0x0C00         @ keep clock's priority
    ands r1, r2
    ldr  r2, ={(PAL << 12) | TILE:#x}
    orrs r1, r2
    strh r1, [r3, #4]
    adds r1, #8
    strh r1, [r3, #12]
    adds r1, #8
    strh r1, [r3, #20]

    sub  sp, #20             @ 20 glyph cells
    ldr  r0, tmpl_abs
    mov  r1, sp
    movs r2, #5
    bl   copyw
    lsls r0, r4, #17
    lsrs r0, r0, #24         @ stamina
    mov  r1, sp
    adds r1, #3
    bl   split3
    lsls r1, r4, #28
    lsrs r1, r1, #28         @ power berries
    lsls r0, r1, #2
    adds r0, r0, r1
    lsls r0, r0, #1
    adds r0, #150            @ max = 150 + 10*berries (game's formula, 0x0800E5A4)
    mov  r1, sp
    adds r1, #7
    bl   split3
    lsls r0, r4, #9
    lsrs r0, r0, #25         @ fatigue (0-100; game accessor 0x0800E584)
    mov  r1, sp
    adds r1, #13
    bl   split3
    ldr  r3, ={STATE:#x}
    ldrb r2, [r3, #2]
    cmp  r2, #0
    beq  nopop
    ldr  r0, ={GLOBAL:#x}
    ldr  r0, [r0]
    ldr  r0, [r0, #4]        @ validated above
    ldr  r1, ={SETTINGS:#x}
    ldrb r1, [r0, r1]
    lsls r1, r1, #26
    lsrs r1, r1, #30
    movs r2, #10
    muls r1, r2
    ldr  r0, spd_abs
    adds r0, r0, r1
    mov  r1, sp
    adds r1, #10
pop:
    ldrb r3, [r0]
    strb r3, [r1]
    adds r0, #1
    adds r1, #1
    subs r2, #1
    bne  pop
nopop:
    movs r5, #0
cells:
    mov  r0, sp
    ldrb r0, [r0, r5]
    lsls r0, r0, #5
    ldr  r1, glyph_abs
    adds r0, r1, r0
    ldr  r1, map_abs
    ldrb r1, [r1, r5]
    lsls r1, r1, #5
    ldr  r2, ={VRAM:#x}
    adds r1, r1, r2
    movs r2, #8
    bl   copyw
    adds r5, #1
    cmp  r5, #20
    blt  cells
    add  sp, #20
done:
    adds r0, r7, #0
    ldr  r3, =0x080097E5     @ original: flush shadow OAM
    bl   call_r3
    adds r0, r7, #0
    ldr  r3, =0x0800989D     @ original: clear shadow OAM
    bl   call_r3
    pop  {{r4-r7}}
    pop  {{r0}}
    bx   r0
call_r3:
    bx   r3

@ r0 = value (0-299), r1 = 3 cells; leading zeros -> blank
split3:
    movs r2, #0
s_h:
    cmp  r0, #100
    blt  s_t0
    subs r0, #100
    adds r2, #1
    b    s_h
s_t0:
    movs r3, #0
s_t:
    cmp  r0, #10
    blt  s_o
    subs r0, #10
    adds r3, #1
    b    s_t
s_o:
    strb r0, [r1, #2]
    cmp  r2, #0
    bne  s_w
    movs r2, #10
    cmp  r3, #0
    bne  s_w
    movs r3, #10
s_w:
    strb r2, [r1]
    strb r3, [r1, #1]
    bx   lr

@ r0 = src, r1 = dst, r2 = word count
copyw:
    ldm  r0!, {{r3}}
    stm  r1!, {{r3}}
    subs r2, #1
    bne  copyw
    bx   lr
.ltorg
.align 2
tmpl_abs:  .word {HOOK_ADDR:#x} + (tm_data - start)
map_abs:   .word {HOOK_ADDR:#x} + (mp_data - start)
glyph_abs: .word {HOOK_ADDR:#x} + (gl_data - start)
spd_abs:   .word {HOOK_ADDR:#x} + (sp_data - start)
.align 2
tm_data:
.incbin "template.bin"
mp_data:
.incbin "cellmap.bin"
sp_data:
.incbin "speedrows.bin"
.align 2
gl_data:
.incbin "glyph.bin"
"""
open('template.bin', 'wb').write(TEMPLATE)
open('cellmap.bin', 'wb').write(CELLMAP)
open('speedrows.bin', 'wb').write(SPEEDROWS)
open('glyph.bin', 'wb').write(GLYPH)

# ---------- key filter: while L is held, the game doesn't see Select (L+Select = clock speed) ----------
KEY_HOOK = 0x089DA880
KEY_SITE = 0x08009194          # ldr r0,=KEYINPUT; ldrh r1,[r0]; ldr r0,=0x3ff; bics r0,r1; bx lr
kasm = """
.syntax unified
.thumb
.text
    ldr  r0, =0x080091A0
    ldr  r0, [r0]            @ KEYINPUT (kept as the game's literal)
    ldrh r1, [r0]
    ldr  r0, =0x3ff
    bics r0, r1              @ pressed
    ldr  r1, =0x200
    tst  r0, r1
    beq  1f
    movs r1, #4
    bics r0, r1              @ L held: hide Select
1:
    bx   lr
.ltorg
"""
open('keys.s', 'w').write(kasm)
subprocess.run(['clang', '-target', 'armv4t-none-eabi', '-mthumb', '-c', 'keys.s', '-o', 'keys.o'], check=True)
subprocess.run([f'{LLVM}/llvm-objcopy', '-O', 'binary', '-j', '.text', 'keys.o', 'keys.bin'], check=True)
kcode = open('keys.bin', 'rb').read()

# ---------- clock speed hook ----------
# replaces 0x08017FC6..0x08017FD3: ldrb r0,[r5,#4]; adds r0,#1; cmp r0,#25; bhs 0x8017FDC;
#                                  strb r0,[r5,#4]; movs r0,#0; b 0x80180B2
CLOCK_HOOK = 0x089DA800
CLOCK_SITE = 0x08017FC6
casm = f"""
.syntax unified
.thumb
.text
    ldrb r0, [r5, #4]
    adds r0, #1
    push {{r0, r2}}
    movs r1, #25
    ldr  r0, ={GLOBAL:#x}
    ldr  r0, [r0]
    lsrs r2, r0, #24
    cmp  r2, #2
    bne  1f
    ldr  r0, [r0, #4]
    lsrs r2, r0, #24
    cmp  r2, #2
    bne  1f
    ldr  r2, ={SETTINGS:#x}
    ldrb r1, [r0, r2]
    lsls r1, r1, #26
    lsrs r1, r1, #30
    adr  r0, ticks
    ldrb r1, [r0, r1]
1:
    pop  {{r0, r2}}
    cmp  r0, r1
    bhs  2f
    strb r0, [r5, #4]
    movs r0, #0
    ldr  r1, =0x080180B3
    bx   r1
2:
    ldr  r1, =0x08017FDD
    bx   r1
.align 2
ticks: .byte {TICKS[0]}, {TICKS[1]}, {TICKS[2]}, {TICKS[3]}
.ltorg
"""
open('clock.s', 'w').write(casm)
subprocess.run(['clang', '-target', 'armv4t-none-eabi', '-mthumb', '-c', 'clock.s', '-o', 'clock.o'], check=True)
subprocess.run([f'{LLVM}/llvm-objcopy', '-O', 'binary', '-j', '.text', 'clock.o', 'clock.bin'], check=True)
ccode = open('clock.bin', 'rb').read()
open('hook.s', 'w').write(asm)
subprocess.run(['clang', '-target', 'armv4t-none-eabi', '-mthumb', '-c', 'hook.s', '-o', 'hook.o'], check=True)
subprocess.run([f'{LLVM}/llvm-objcopy', '-O', 'binary', '-j', '.text', 'hook.o', 'hook.bin'], check=True)
hook = open('hook.bin', 'rb').read()

# trampoline: ldr r3,[pc,#0]; bx r3; .word hook|1   (at 0x080098CC, 8 bytes; old fn is 20 bytes)
tramp = struct.pack('<HH', 0x4B00, 0x4718) + struct.pack('<I', HOOK_ADDR | 1)
assert (TRAMP + 4) & ~3 == TRAMP + 4

rom = bytearray(open(BASE_ROM, 'rb').read())
orig = bytes(rom)
off = HOOK_ADDR - 0x08000000
assert all(b == 0xFF for b in rom[off:off + len(hook)]), 'hook area not free'
rom[off:off + len(hook)] = hook
t = TRAMP - 0x08000000
assert rom[t:t+4] == bytes.fromhex('10b5041c'), rom[t:t+4].hex()   # push {r4,lr}; adds r4,r0,#0
rom[t:t + len(tramp)] = tramp
assert HOOK_ADDR + len(hook) <= CLOCK_HOOK, 'HUD hook overlaps clock hook'
co = CLOCK_HOOK - 0x08000000
assert all(b == 0xFF for b in rom[co:co + len(ccode)])
rom[co:co + len(ccode)] = ccode
cs = CLOCK_SITE - 0x08000000
assert rom[cs:cs+14] == bytes.fromhex('28790130192806d2287100206ee0'), rom[cs:cs+14].hex()
# ldr r0,[pc,#4]; bx r0; nop; .word hook|1   (literal at 0x08017FCC, word aligned)
rom[cs:cs+14] = struct.pack('<HHH', 0x4801, 0x4700, 0x46C0) + struct.pack('<I', CLOCK_HOOK | 1) + bytes.fromhex('c046c046')
assert CLOCK_HOOK + len(ccode) <= KEY_HOOK
ko = KEY_HOOK - 0x08000000
assert all(b == 0xFF for b in rom[ko:ko + len(kcode)])
rom[ko:ko + len(kcode)] = kcode
ks = KEY_SITE - 0x08000000
assert rom[ks:ks+16] == bytes.fromhex('02480188024888437047000030010004'), rom[ks:ks+16].hex()
# ldr r1,[pc,#4]; bx r1; nop; nop; .word hook|1   -- literal 0x080091A0 (KEYINPUT) left in place
rom[ks:ks+12] = struct.pack('<HHHH', 0x4901, 0x4708, 0x46C0, 0x46C0) + struct.pack('<I', KEY_HOOK | 1)
open('stamina.gba', 'wb').write(rom)

# IPS (relative to TLE ROM)
recs = []
i = 0
while i < len(rom):
    if rom[i] != orig[i]:
        j = i
        while j < len(rom) and j - i < 0xFFFF and (rom[j] != orig[j] or (j + 1 < len(rom) and rom[j+1] != orig[j+1])):
            j += 1
        recs.append((i, bytes(rom[i:j])))
        i = j
    else:
        i += 1
ips = bytearray(b'PATCH')
for o, d in recs:
    assert o != 0x454F46
    ips += o.to_bytes(3, 'big') + len(d).to_bytes(2, 'big') + d
ips += b'EOF'
open('stamina.ips', 'wb').write(ips)
print(f'hook {len(hook)} bytes, {len(recs)} IPS records, ips {len(ips)} bytes')
