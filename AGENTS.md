# MFoMT ROM hacking — notes for agents

QoL patches for **Harvest Moon: More Friends of Mineral Town (USA)** with **True Love Edition v4.0** as the base. Every patch goes on top of TLE.

## Files in this folder

| File | What it is |
|---|---|
| `Harvest Moon - More Friends of Mineral Town (USA).gba` | Clean MFoMT ROM, CRC32 `0x1736b957`. Don't modify it. |
| `Harvest Moon - MFoMT (True Love Edition v4.0).ips` | TLE patch, applied to clean MFoMT. |
| `MFoMT Stamina HUD (apply after TLE v4.0).ips` | Our patch. Apply it after TLE. |
| `MFoMT Grind Reduction (apply after TLE v4.0).ips` | Our port of the Proofread grind-reduction tweaks. |
| `MFoMT Free Basket (apply after TLE v4.0).ips` | The free basket on its own. |
| `MFoMT Fast Tool Upgrades (apply after TLE v4.0).ips` | Every blacksmith upgrade takes 1 day. |
| `MFoMT Fast Tool XP (apply after TLE v4.0).ips` | Tools gain 5× XP. |
| `MFoMT Self-Watering Crops (apply after TLE v4.0).ips` | The farm is watered every night, as if it had rained. |
| `Harvest Moon - MFoMT (TLE v4.0 + Stamina HUD).gba` / `.sav` | The ROM the user plays (TLE + HUD + grind reduction; the filename was kept so the save stays linked) and **the user's real save**. Never overwrite the `.sav`; copy it for testing. |
| `….ss1` / `….ss2`, `Harvest Moon - More Friends of Mineral Town (USA).sav` | The user's mGBA save states and a save for the clean ROM. Keep them; copy before loading for debugging. |
| `test/test.gba` + `test/test.sav` | Test copy: TLE + all our patches, with a save converted from `harvest-moon-more-friends-of-mineral-town.8984.sps` (SharkPort; the first 32 KB of its payload after a 0x1C-byte header is the `.sav`). The vanilla 2005 save is at Fall 26, Year 1, with 99.9M G, 5 cows, 4 chickens and 3 sheep. Use this for testing instead of the user's real save. Rebuild `test.gba` from `qol.gba` when patches change. |
| `tools/` | Build and debug scripts (described below). |

## User preferences

- Use **uv** for Python, e.g. `uv run --with capstone --with pillow --with unicorn python tools/x.py`. No pip and no bare `python3`.
- **Ask the user to save in-game** (and make an mGBA save state) before restarting or reloading their emulator with a new ROM.
- Don't use per-frame GDB breakpoints while the user is watching. They drop mGBA to about 17 fps. Use the keypad-redirect input driver instead (below).
- The stamina HUD shows **raw values** ("126/150"), not a percentage. The user asked for this.

## Features

- **Always-run** needs no patch. It's built in: Diary → Options → "Buttons" type 2 makes the D-pad run and R walk. The game checks this at `0x0802F22C`: R held means run, and bit0 of `[[obj+0x34]+0x224C]` inverts that.
- **Stamina/fatigue HUD** is implemented in `tools/build.py`. It's two rows, "ST cur/max" over "FT fat/100", 80 px wide, just left of the clock.
- **Clock speed (L+Select):** in `tools/build.py`, so it's part of the HUD `.ips`. Hold L and tap Select to cycle 1× / 1.25× / 1.5× / 2× (ticks per game minute 25 / 31 / 38 / 50). The second HUD row shows "TIME x1.5" etc. for 2 s. Speed is stored in bits 4–5 of the Diary settings byte (`G+0x224C`), which nothing else uses; it's expected to persist with the save, but that hasn't been verified.
  - Clock hook: the 14 bytes at `0x08017FC6` become `ldr r0,[pc,#4]; bx r0` → `0x089DA800`, which looks up the threshold and jumps back to `0x080180B3` / `0x08017FDD`. Verified live: rolls over at 50 ticks when set to 2×.
  - Key filter: the game's key-read function `0x08009194` → `0x089DA880` hides Select while L is held (Select alone opens the Property screen). It reads KEYINPUT through the literal at `0x080091A0`, which is kept, so `drive2.py`'s redirect still works. The HUD hook reads keys the same way.
  - HUD state lives in RAM at `0x0203FFF0` (u16 previous keys, u8 popup timer), at the top of EWRAM, which appears unused.
- **Fast tool upgrades:** in `tools/upgrades.py`. Every upgrade takes 1 day. Checked in unicorn for every tool level and ore, and verified in game (2026-11-09): an Axe upgraded with Mystrile on Wednesday was ready Thursday (the shop is closed Thursdays, so it was picked up Friday).
- **Fast tool XP:** in `tools/toolxp.py`. ×5 (the user's choice). It rewrites the XP adder in place. Verified in game: four Hammer swings (three at rocks, one at the ground) took 29900 to 30900.
- **Self-watering crops:** in `tools/watering.py`. A 1-byte change that makes the nightly per-cell update always take the rain path. Verified in game: 231 dry tiles → 230 watered (one became untilled), untilled ground untouched. Growth over several days hasn't been seen yet.
- **Free basket:** in `tools/basket.py`, shipped as its own `.ips`. The Supermarket basket costs 0G instead of 5,000G. Built, but not yet tested by buying it in game.

## Key game facts (TLE ROM addresses)

- **Fatigue:** bits 15–22 of the same u32 at `player+0x44` hold fatigue in half-points (0–200). Accessor `0x0800E584` returns bits 16–22 (0–100), and `0x0800E58C` checks the 8-bit value > 199, which is the collapse point. Verified live: raw 14 means 7/100.
- **Clock / time:** the time-advance code is at `0x08017FC0`.
  - A tick byte at `[r8+0x1040]+4` counts up and adds a game minute when it reaches **25**: `cmp r0,#0x19` at ROM `0x17FCA`.
  - Time is a packed u32 at `[[r8+0x1040]]`: minutes in bits 21–26, hours in bits 16–20.
  - The function bails out early in some states (e.g. the house at 6:00 AM showed no time writes).
  - Configurable via L+Select (see Features). The user chose the shortcut over a Diary row.
- **Diary options menu:** the label table at `0x080F0C44` holds [Error, Diary, Save, Load, "", Data 1, Data 2, Buttons, 1, 2, Clock, ON, OFF, Face, ON, OFF, Name, ON, OFF]. Help strings are around `0x080F0D4D`. Settings are bits of `[[obj+0x34]+0x224C]` (bit0 = Buttons). Row count, layout and cursor are in code.
- **Script VM** (event scripts in `RIFF … SCR CODE` / `STR` chunks):
  - Opcodes: `23 xx` push imm8, `22 xxxx` push imm16, `13 xxxxxxxx` push imm32, `21 xxxxxxxx` call native, `12` compare, `1b`/`1d` conditional jump (absolute offset), `18` jump, `0d` logical and.
  - Natives: `0x3E` getvar, `0x3F` setvar, `0x22` show message n, `0xEF` get money, `0xF1` pay, `0x73` give basket, `0x74` has basket(?).
  - The native function table hasn't been located yet. (The table at `0x080F0348` is AI state handlers, not it.)
- **Blacksmith tool upgrades** (native menu code, not a script):
  - Days: `0x08096384(_, tool, ore)` returns the target level minus the current level (tool & 7; ore item `0x12`–`0x15` is levels 1–4, `0x1C` Mythic Stone is 7), or 2 for 6→7. Its only caller is the confirm-message builder (`0x0809705C`), whose result then flows through the job object (vtable `0x080EE354`, days at `+0x18`) to the commit.
  - Commit: `0x080A3FB4(G+0x1DBC, new tool item, days)`. The job is the u16 at `G+0x1DBC+0x14`: bits 0–5 tool item, bits 6–8 days left.
  - Ready check `0x080A3E74`: tool set and days == 0. The nightly decrement `0x080A3FE0` only subtracts when days ≠ 0. Pickup `0x080A3EF8` clears it.
  - Experience gate at `0x08096E2A`: the needed XP is 6000 / 18000 / 36000 / 65535 by ore, compared against `0x0800F044(0x0800EBCC(player, tool kind))`. The only XP adder is `0x0800F064(xp_ptr, amount)` (xp = min(xp+amount, 0xFFFF)). Its 7 callers (`0x08030392`…`0x08031C26`) pass 50, or 100 when a flag is set.
  - Messages at `0x107DFC`–`0x1090D0` ("That Tool is … and it will take N day(s).").
- **Tool XP:** u16 at `player + 0x2C + kind*4` (accessor `0x0800EBCC`, then `0x0800F044`). Kind = tool type with Sickle and Hoe swapped (`0x08096DE4`): kind 0 Hoe, 1 Sickle, 2 Axe, 3 Hammer, 4 Watering Can, 5 Fishing Rod. Tool item = type<<3 | level, with types in name-table order (Sickle, Hoe, Axe, Hammer, Can, Rod at `0xF1BB9`…). The maximum is 65535.
- **Rucksack:** container at `G+0x1C48`: u32 slot count (8 with the big rucksack), then 4-byte slots (`0x0800FDB8`). A slot with byte0 bit0 = 1 is a material, with its id in byte1 (`0x0800F1C4`); bit0 = 0 is an item, with its id in byte1 and > 0xAA meaning empty (`0x0800F148`). Ores: `0x12` Copper, `0x13` Silver, `0x14` Gold, `0x15` Mystrile, `0x1C` Mythic Stone. To give a Mystrile, write `01 15 00 00` to an empty slot. That worked in game.
- **Farm field:** `G+0x9EC`, 43×25 cells of u32 (ends at `G+0x1AB8`). Bits 0–1 hold the soil: 0 untilled, 1 tilled dry, 2 watered. Bits 8–11 are nonzero when something is on the cell (crop, grass, weed, stone…). `0x0800A190(cell, state)` sets the soil; the Watering Can's `0x0800A4A8(cell)` does 1 → 2.
  - The can's action (`0x08031BAC`) calls handler `0x0801D580` through `0x080DB53C` (`bx r2`); it reads the cell at `[[obj+0x1038]] + 0x9EC + (y*43 + x)*4`.
  - **Daily per-cell update:** the function ending at `0x0800AB76`. At `0x0800AB42`: if r8 (rain) == 0, watered → dry; otherwise dry → watered.
  - `0x0800AB78(cell, season)` (only caller: the loop at `0x08011270`) is the **season-change** pass. It runs only when bits 2–6 of `G+0x11` (day of the season) are 0. Don't hook it for daily effects.
  - `G+0x11`: bits 0–1 season, bits 2–6 day of the season (0-based).
  - The BG tilemap at `G+0x6000`-ish (rows of 0x100) is only the screen copy. Dry soil is `0x9349..4C`, wet is `0x934D..50`. It's updated by DMA, so watchpoints miss it.
- **Basket shop script:** `RIFF` at `0x765B94`. Money check at `0x767E3A` and payment at `0x767E91`, both `22 88 13` (5000). Text "Baskets are 5,000G." at `0x767FB6`.
- **Money:** the RAM location hasn't been found yet. FoMT used a fixed `0x02004080`; in MFoMT it's probably G-relative, like stamina. Find it by searching G for the balance the Property screen shows (Select), then confirm with a write watchpoint while buying something. The 100M/10M literals at `0x1FB34`/`0x2AFD4` are number-formatting constants. An "infinite money" plan was written up (either force the maximum each frame from the HUD hook, or make the pay routine a no-op behind an L+Start toggle); the user declined it (2026-11-08).
- **Text speed:** the user dropped this (2026-11-08). For reference: dialog glyphs are drawn into an EWRAM buffer (`0x0203B718` in one session) and DMA'd to OBJ VRAM, so VRAM watchpoints don't fire. Watch the RAM buffer instead.
- **Stamina is not at a fixed address.** The game-state block is heap-allocated. `0x02004205` only happened to work in one session.
  - `G = [[0x0300040C] + 4]` (check that both pointers are in EWRAM: top byte `0x02`)
  - `player = G + 0x1BE8`
  - `u16 at player+0x44`: bits 7–14 = stamina, bits 0–3 = power berries
  - max = `150 + 10*berries` (the game's own formula, at `0x0800E5A4`)
  - The stamina-change function is at `0x0800EA84`. A hoe swing costs 2.
- **OAM manager** (gameplay): `0x030078BC`. byte0 = slots used this frame. The shadow OAM entries are at `0x030078C0`.
  - Per-frame flush function `0x080098CC` calls flush `0x080097E5`, then clear `0x0800989D`.
  - To add a sprite, claim slot `[mgr]` and increment the count. Otherwise the game's clear won't hide it, and stale sprites pile up.
- **The clock sprite:** three pal-13 sprites on one row, usually at x=132 y=140 (bottom right):
  - a 32×16 sprite at x
  - a 32×16 sprite at x+32. Its tile is usually first+8, but **not always**: after leaving mine floor 2 by the stairs the three tiles were 56 / 128 / 136. So the HUD checks only shape, size, position and palette 13 for all three pieces, never tiles.
  - a 16×16 sprite at x+64
  - **Its tile numbers are not fixed.** They're usually 32/40/28, but after leaving the mine they were 136/144/132, because VRAM use varies by scene. So the HUD matches the clock by layout (attr0/attr1/attr2 relations), never by tile number.
  - Dialog text also uses pal-13 32×16 blocks in a row (first one at x=8), but its third block is 32×16, not 16×16, so the layout check rejects it.
- **Clock text colours (pal 13):** 1 = black body, 2 = tan shadow, 11 = white. The font is bold, with 2px strokes.
- **I/O register shadows:** `0x02005B28`. BG scroll is at +0x10 + bg*4.
- **Key read function:** `0x08009194`. It loads KEYINPUT through the literal at `0x080091A0`.
- **OBJ VRAM:** 1D mapping. The HUD uses OBJ tiles **1004–1023** (`0x06017D80`–`0x06017FFF`, 20 tiles). These haven't been checked against busy scenes (town, festivals, mine).
- **Free ROM space:** starts at `0x089DA000`, right after TLE's credit string; it's all `0xFF`. The ROM is 16 MB after TLE.

## Stamina HUD patch design (`tools/build.py`)

1. **Trampoline:** at `0x080098CC`, replace `push {r4,lr}; adds r4,r0,#0` (`10b5041c`) with `ldr r3,[pc,#0]; bx r3; .word hook|1`. The hook goes at `0x089DA000`.
2. **Find the clock:** the hook scans the shadow OAM for the three-sprite clock layout above. It skips the clock if hidden, or if there's no room to its left.
3. **Add the sprites:** it reads the player word through the pointer chain and claims **3** OAM slots: 32×16 at clock x − 82, 32×16 at x − 50, and 16×16 at x − 18 (80 px plus a 2 px gap). It keeps the clock's y and priority.
4. **Draw:** a 20-cell glyph grid (2 rows × 10 cells, 8 px each). `TEMPLATE` gives the static cells ("ST nnn/mmm" / "FT fff/100"), and `CELLMAP` maps each cell to an OBJ tile offset. Glyphs: 0–9, blank, slash, S, T, F, I, M, E, x, '.'. The digits are filled by `split3`, which blanks leading zeros. Every frame, all 20 cells are copied to OBJ VRAM.
   - Popup: for about 2 s after L+Select, row 2 becomes "TIME x1.25" etc. (`SPEEDROWS`).
5. **Finish:** it calls the original flush and clear, then returns.
6. **Other hooks in the same build:** the clock-speed hook at `0x089DA800` and the key filter at `0x089DA880` (see Features).

### Build pipeline

**One `.ips` per feature** (user's decision, 2026-11-09), so people can leave out the more generous ones. Every patch script reads `tle.gba` and writes its own `.ips` relative to TLE, using `tools/ipslib.py`. Rules for new patches:
- Give each one its own free-space block: HUD `0x089DA000`, mine stairs `0x089DB000`, and new ones from `0x089DC000` up, one 4 KB block each.
- Two patches must never hook the same instruction. If two features need the same hook site, hook different instructions, or ask the user whether to merge them.
- Ship as `MFoMT <Feature> (apply after TLE v4.0).ips`, and add it to the README's file table and features.

Run the scripts from a scratch dir holding copies of `tools/*.py` and `tle.gba` (clean MFoMT + the TLE ips, made with `applyips.py`).

1. `uv run python build.py` writes `stamina.ips` (HUD, fatigue, clock speed, key filter).
2. `uv run python tweaks.py` writes `tweaks.ips` (grind reduction). `uv run python basket.py` writes `basket.ips`. `uv run python upgrades.py` writes `upgrades.ips`. `uv run python toolxp.py` writes `toolxp.ips`. `uv run python watering.py` writes `watering.ips`.
3. `uv run python stack.py stamina.ips tweaks.ips basket.ips upgrades.ips toolxp.ips watering.ips …` checks that no two patches write the same byte (so any subset in any order gives the same result) and writes `qol.gba` (TLE + all of them).
4. Ship: copy `stamina.ips` → `MFoMT Stamina HUD (apply after TLE v4.0).ips`, `tweaks.ips` → `MFoMT Grind Reduction (apply after TLE v4.0).ips`, `basket.ips` → `MFoMT Free Basket (apply after TLE v4.0).ips`, `upgrades.ips` → `MFoMT Fast Tool Upgrades (apply after TLE v4.0).ips`, `toolxp.ips` → `MFoMT Fast Tool XP (apply after TLE v4.0).ips`, `watering.ips` → `MFoMT Self-Watering Crops (apply after TLE v4.0).ips`, and `qol.gba` → `Harvest Moon - MFoMT (TLE v4.0 + Stamina HUD).gba`. Keep that ROM filename so the user's `.sav` stays linked. Ask the user to save first.

## Tooling and gotchas

- **Assembler:** `clang -target armv4t-none-eabi -mthumb -c` plus `/opt/homebrew/opt/llvm/bin/llvm-objcopy -O binary -j .text`. Keystone is broken here (missing distutils, then the dylib failed to load).
  - On armv4t Thumb, `mov` between low registers is invalid. Use `adds rX, rY, #0`.
  - `ldr rX, =label` produces an unrelocated literal in a raw binary. Store `HOOK_ADDR + (label - start)` in a `.word` and load that pc-relative.
- **Debugger:** run `/Applications/mGBA.app/Contents/MacOS/mGBA -g rom.gba` (mGBA 0.10.5). Its GDB stub listens on port 2345.
  - `tools/gdbc.py` is a minimal RSP client. Register writes must be **little-endian** hex. Watchpoints don't fire on DMA writes.
  - If memory doesn't change over about a second, the mGBA UI is paused, and `c` won't advance it.
  - With `-g -t state`, the state loads only after the first `c`. Do attach, `c`, wait, break, then read/write, then `c`, all on **one connection**. Closing the socket while the target is stopped wedged the stub (connection resets), and only restarting mGBA fixed it. Killing a script while it's blocked waiting on a watchpoint also wedges it. The stub allows **one client at a time**, so never leave a watch script running when you need to read memory. Before restarting, ask the user to make a save state in the debug window.
  - Snapshot diffing of EWRAM is very noisy (NPCs, timers). A one-shot **breakpoint on the action's code path** (e.g. the tool's dispatch call) worked far better for finding data structures.
- **Input driver:** `tools/drive2.py` runs at full speed. It points the KEYINPUT literal at `0x080091A0` to RAM `0x0203FF00` and writes key bits there.
  - Restore the literal to `0x04000130` to give keyboard control back to the user.
- **Other tools:**
  - `tools/render.py` rebuilds a screenshot from VRAM/OAM/palette over GDB. It's approximate: it ignores windows and blending, so dialog scenes look noisy.
  - Any ROM bytes can be written into a running mGBA over GDB (`M` packet on `0x08xxxxxx`), which is handy for testing an in-place code patch without restarting.
  - `tools/hotswap.py` writes the hook region (`0x1300` bytes at `0x089DA000`) into a running ROM over GDB.
  - `tools/emutest2.py` runs the hook in **unicorn** against synthetic OAM and memory, then renders the sprites it produces to `raw_test.png`. Use it to check changes without a live emulator.
  - `tools/thumbdis.py <addr> <len>` is a capstone Thumb disassembler that resolves pc-relative literals.
  - `tools/findlit.py` searches for 32-bit literals; `tools/blcallers.py` finds BL call sites; `tools/applyips.py` applies an IPS.
- Don't name a script after a stdlib module. `dis.py` shadowed Python's `dis`.

## FoMT Proofread 1.22 (https://www.romhacking.net/hacks/9242/; no longer kept locally)

- The `.bps` text patches (JP-names or Natsume-names variants) have source CRC `0x8e923168`, which is **FoMT**. They can't be ported to MFoMT in any practical way: the script differs (female protagonist, different characters), and TLE also changes text.
- The optional `FOMT QOL.ips` (also FoMT-only) has three gameplay tweaks that *could* be ported to MFoMT+TLE by finding the matching code. The author's notes (`hmmt proofread raw notes.txt`) give the FoMT addresses:
  - Mines below level 0: the stairs down are always visible, placed one square down-right of the stairs up. Floor tile `$0200` = visible stairs, `$0004` = hidden stairs.
    - FoMT IPS records: a trampoline at ROM `0x09D150` (`ldr r1,[pc]; bx r1` to `0x0875C245`), 104 bytes of new code at `0x75C244`, and a 1-byte change at `0x093D88`.
  - Vacation house price: 100M becomes 2.5M. In FoMT the price is at ROM `0x0FF738` (`00e1f505` becomes `a0252600`).
    - ROM `0x0FF544` rewrites the price text "100,000,000G" in the building menu.
  - Mountain cottage: 50 years becomes 5. In FoMT this is ROM `0x392498` (`$32` becomes `$05`).
    - The many 2-byte `" 5"` records (around `0x338xxx`, `0x3769cd`, and `0x79xxxx`) change "50th wedding anniversary" to "5th" in dialog.
    - The `0x79xxxx` records point into text the Proofread `.bps` moved, so that `.ips` expects the proofread ROM, not a clean one.
- That `.ips` also changes the pointer at `0x093D88`. This only fixes a collision inside the proofread ROM (its code overwrote a relocated "Now communicating…" string), so MFoMT doesn't need it.

### Port to MFoMT + TLE (done, `tools/tweaks.py` → `MFoMT Grind Reduction (apply after TLE v4.0).ips`)

The user chose to stay on MFoMT+TLE and port all three tweaks. The patch stacks with the others in any order.

- **Vacation house price:**
  - u32 at ROM `0x108458`: 100,000,000 becomes 2,500,000. It's in the same building table layout as FoMT's.
  - Menu text at `0x108264`: "100,000,000G" becomes "  2,500,000G".
  - The code literals for 100M at `0x1FB34` and `0x2AFD4` are number-formatting constants. Leave them.
- **Cottage after 5 years:**
  - Script block `23 05 23 78 02 16 22 a6 02 21 3e 00 00 00 23 32 12 1b`. Variable `0x2A6` is years married, compared against 50. There are **8** copies in TLE (one per spouse, `0x81D585`–`0x81EEE3`), and all 8 now read 5.
  - FoMT has 6 copies and the Proofread patch changed only one.
  - Separate checks of `0x2A6` against 45/50 at `0x819FF7`, and a `0x2B0` 30–70 ladder, are unrelated. Leave them.
  - Dialog: 11 "50th"/"50 years" strings in the `0x7A8xxx`–`0x7E9xxx` range now say "5th"/"5 years". The `0` is dropped and a space is padded before the line break. The "Gold Anniversary / 50th anniversary." list at `0x121290` and the Alexandrite floor text were left alone.
- **Mine stairs:**
  - The floor generator is `0x080A20BC`, a byte-for-byte match with FoMT's `0x0809CF34`. It's called from 3 sites with map = `[obj+0x8C] + 0x2E94` (FoMT uses `+0x2E58`).
  - The trampoline at `0x080A22D8` (the 8 bytes `0c980d9908600d98`) jumps to a hook at `0x089DB000`.
  - At that point `r6` is the map struct, and r1–r7 are free because the epilogue restores them.
  - Tile halfwords are at `r6+4`, 28×28, 56 bytes per row:
    - bits 0–3: type (0 clear, 1 tilled, 2 stairs down, 3 stairs up, 4 rock)
    - bits 4–7: rock contents
    - bits 8–9: preserved by the generator, meaning unknown
    - byte1 bits 2–7: buried item (1 hidden stairs, 2 gold, 3 power berry, 0xC junk, 0x10 mithril …)
  - The hook acts only if the floor has hidden stairs. With a stairs-up tile (not on the right edge), it puts stairs down at up+58 bytes (one row down, one tile right), keeping bits 8–9.
  - **Floor 0 has no stairs-up tile** (you walk in through the entrance). Verified in RAM: 14 hidden stairs, 20 rocks, a 12×6 room at the top-left of the buffer. In that case, or when the stairs up sit on the edge, the hook reveals the bottom-most hidden stairs on open ground (type 0), the one closest to the entrance. Nothing is lost there.
  - Either way, it then clears only the tiles whose buried item is 1.
  - Floor 0 was verified live: after re-entering, one visible staircase and no hidden ones.
  - Map location: `G + 0x2E94` (tiles at +4), with `G = [[0x0300040C]+4]`. `tools/mapdump.py` prints it over GDB.
  - **FoMT's version had a bug:** it used `byte1 &= 0xFB`, which turns buried power berries (3) into gold (2). It also used fixed RAM addresses, which won't work on MFoMT's heap layout.
  - Tested in unicorn (`tools/minetest.py`), but **not yet in the real game.**

## Works without TLE (checked 2026-11-09)

Our `.ips` files (HUD, grind reduction, and free basket) also apply to clean MFoMT. For every record in each patch, the bytes being overwritten are identical in clean and TLE. TLE's only code change below `0x100000` is at `0x3F44`; the rest of what it changes is data, from `0x108FA3` up. That means the hooked functions, the Options menu, the always-run check, the cottage scripts, the dialog strings and the free space at `0x9DA000` are all vanilla. So always-run is a vanilla feature, not something TLE adds. None of this has been play-tested without TLE.

## Planned features (chosen by the user 2026-11-08, none started)

1. ~~Instant tool upgrades~~: done as 1 day, vanilla prices (`tools/upgrades.py`). The user picked the smallest change.
2. **Higher rare-ore drop rates** in the mine (Mithril, Adamantite, Orichalcum, Mythic Stone).
3. ~~Faster tool experience~~: done, ×5 (`tools/toolxp.py`).
4. **Faster animal affection** for cows, sheep and chickens.
5. ~~Self-watering crops~~: done (`tools/watering.py`).
6. **Automatic animal feeding:** troughs fill from the silo each morning.

Each one ships as its own `.ips` (see Build pipeline). Approach: find each value with a write watchpoint while the user does the action once, then patch the code that changes it. Ideas that were offered but not picked: villager friendship ×2, faster construction and crop growth, lumber, stamina costs, shops open every day, a shipping-price multiplier, accurate forecasts, faster fishing, no animal sickness, and others.

## Open items

- Check the mine-stairs hook on the Lake Mine and on special floors. Floors 1+ were confirmed by the user, and floor 0 was verified live.
- Debugging the user's situations: they make mGBA save states (Shift+F1/F2 → `.ss1`/`.ss2` next to the ROM). Load copies with `mGBA -g -t state.ssN rom.gba` in the scratchpad, then use `tools/mapdump.py` or dump the OAM. The HUD disappearing after the hot springs or mine was the moving clock tiles; fixed by matching on layout.

- Check OBJ tiles 1004–1023 against busy scenes (town, festivals, mine, cutscenes).
- Check the HUD when the clock is toggled off, and after starting a brand-new game. The pointer chain comes from the code, but has only been tested after loading a save.
