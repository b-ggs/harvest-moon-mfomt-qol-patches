# MFoMT QoL Patches

Quality-of-life patches for **Harvest Moon: More Friends of Mineral Town** (GBA, USA). They're made to sit on top of [True Love Edition v4.0](https://kataiki.tumblr.com/FOMT-TL), but they also apply to the unmodified game.

Each feature set is its own patch, so you can pick any combination:

- **Stamina HUD:** shows a stamina and fatigue meter next to the clock, and lets you speed up the game clock.
- **Grind Reduction:** a cheaper Vacation House, the mountain cottage after 5 years, and visible mine stairs. Based on the optional QoL patch in Mentil's [*FoMT Proofread 1.22*](https://www.romhacking.net/hacks/9242/).
- **Free Basket:** the Supermarket basket costs nothing. It's in its own patch because it's a bit generous.
- **Fast Tool Upgrades:** every blacksmith upgrade is ready the next day.
- **Fast Tool XP:** tools gain experience 5× faster.
- **Self-Watering Crops:** your field is watered every night, as if it had rained.
- **Automatic Animal Feeding:** troughs in the barn and coop are filled from storage every night.
- **Faster Animal Affection:** animals gain affection 5× faster.
- **Rare Ore Boost:** rare ores and jewels drop about twice as often in both mines.

## What you need

| File | Where to get it |
|---|---|
| A **Harvest Moon: More Friends of Mineral Town (USA)** ROM | Dump it from your own cartridge. It isn't included here. |
| `MFoMT Stamina HUD (apply after TLE v4.0).ips` | This repository |
| `MFoMT Grind Reduction (apply after TLE v4.0).ips` | This repository |
| `MFoMT Free Basket (apply after TLE v4.0).ips` | This repository |
| `MFoMT Fast Tool Upgrades (apply after TLE v4.0).ips` | This repository |
| `MFoMT Fast Tool XP (apply after TLE v4.0).ips` | This repository |
| `MFoMT Self-Watering Crops (apply after TLE v4.0).ips` | This repository |
| `MFoMT Automatic Animal Feeding (apply after TLE v4.0).ips` | This repository |
| `MFoMT Faster Animal Affection (apply after TLE v4.0).ips` | This repository |
| `MFoMT Rare Ore Boost (apply after TLE v4.0).ips` | This repository |
| `Harvest Moon - MFoMT (True Love Edition v4.0).ips` *(optional)* | [kataiki.tumblr.com/FOMT-TL](https://kataiki.tumblr.com/FOMT-TL) |
| An IPS patcher | [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/) runs in the browser. [Floating IPS (Flips)](https://github.com/Alcaro/Flips) is a desktop app. |

Check that your ROM is the clean USA release before you patch it:

| | |
|---|---|
| CRC32 | `1736B957` |
| SHA-1 | `3aa4d46cbbf152e440942acd5f5d37ddc7b05e1d` |
| Size | 16 MiB (16,777,216 bytes) |

The patches won't work on the original *Friends of Mineral Town* (the boy version) or on the European or Japanese releases.

## How to patch

1. Make a copy of your clean ROM and work on the copy.
2. **If you want True Love Edition**, apply `Harvest Moon - MFoMT (True Love Edition v4.0).ips` first.
3. Apply whichever of our patches you want. They don't overlap, so any combination works, in any order.
4. Play the patched ROM in your emulator or on a flash cart.

With Rom Patcher JS, pick the ROM, pick one `.ips`, then click **Apply patch** and save the result. To apply the next patch, load that saved file as the ROM.

### Is True Love Edition required?

No. The filenames say "apply after TLE v4.0" because that's what the patches were built and play-tested on, but none of them depends on it:

- Every byte our patches overwrite is the same in the original ROM and in TLE.
- TLE doesn't change any of the game code the patches hook into.

So on the original game you get the same features. Note that the patches have only been **played** on TLE so far; on the original game they've been checked by comparing bytes, not by playing.

### Existing saves

Your save file keeps working. Give the patched ROM the same name as your old one, or rename the `.sav` to match the new ROM, so your emulator finds it. As always, back up your `.sav` first.

## Features

### Stamina HUD patch

- **Stamina and fatigue meter.** A small panel to the left of the clock shows raw values:
  ```
  ST 126/150
  FT   7/100
  ```
  - Max stamina follows the game's own formula: 150, plus 10 for each Power Berry.
  - Fatigue is out of 100. You collapse when it goes over the limit.
  - The panel follows the clock: it hides when the clock is hidden or when there's no room.
- **Adjustable clock speed.** Hold **L** and tap **Select** to cycle the game clock through **x1 → x1.25 → x1.5 → x2**. "TIME x1.5" (and so on) shows in the meter for a couple of seconds.
  - A higher setting makes game minutes pass faster in real time.
  - The setting is stored with your Diary options in the save.
  - While L is held, Select doesn't open the Property screen.

### Grind Reduction patch

This patch is based on the optional `FOMT QOL.ips` that comes with **Mentil's [*FoMT Proofread 1.22*](https://www.romhacking.net/hacks/9242/)**. That patch targets the original *Friends of Mineral Town*, so it can't be applied to MFoMT directly. The Vacation House, cottage and mine-stairs changes below follow its design (using the author's notes), re-implemented at MFoMT's addresses. The Power Berry fix is our own addition.

- **The Vacation House costs 2,500,000G** instead of 100,000,000G. The building menu shows the new price.
- **The mountain cottage arrives after 5 years** of marriage instead of 50. This covers every spouse (8 checks), and the related "50th anniversary" dialog now says "5th".
- **Visible mine stairs.** On every mine floor, the stairs down are already uncovered.
  - On floors with stairs up, you arrive with the stairs up directly above you and the stairs down directly below you.
  - On floor 0, which has no stairs up, the hidden staircase nearest the entrance is revealed.
  - Other buried items aren't affected. This also fixes a bug in the original FoMT patch that turned buried Power Berries into gold.

### Free Basket patch

- **The Supermarket basket costs 0G** instead of 5,000G, and the clerk's line says so.

### Fast Tool Upgrades patch

- **Every tool upgrade at Saibara's takes 1 day,** whatever the ore. Normally it's one day per level jumped, up to 7 for a Mythic Stone upgrade. Prices and experience requirements are unchanged.

### Fast Tool XP patch

- **Tools gain 5× experience per use** (250 instead of 50). A Copper upgrade takes about 24 uses instead of 120, and full experience about 260 instead of 1,300. Experience still caps at the usual maximum.

### Self-Watering Crops patch

- **All tilled soil on the farm is watered overnight,** exactly as on a rainy day. Crops grow every night without the Watering Can.
  - Seeds planted on soil you tilled that same day start growing from the second night, as they would after rain.
  - The Watering Can still works, for example on the day you plant.

### Automatic Animal Feeding patch

- **Each night, troughs are filled from storage,** one per animal: Fodder from the silo in the barn, Chicken Feed in the coop.
  - They're topped up before the animals eat (so animals bought that day are fed) and refilled afterwards, so you'll see feed in the troughs during the day.
  - It uses one feed per animal per day, plus a one-time refill on the first night. Troughs you filled by hand count, so they don't use extra feed.
  - You still have to buy feed. If storage runs out, the remaining animals go hungry, as usual.
  - Animals left outside are counted too, so on grazing days a little feed may be used for them anyway.

### Faster Animal Affection patch

- **Every affection gain is 5× bigger** (brushing, talking, milking, feeding and so on). That applies to cows, sheep and chickens.
  - Penalties, such as hitting an animal or neglecting it, are unchanged.
  - Affection still caps at the usual maximum.

### Rare Ore Boost patch

- **In the Spring Mine, rocks hold rare ores about twice as often:** Gold, Mystrile, Orichalc, Adamantite and Mythic Stone.
  - Each ore still starts on the same floor as usual: Gold from floor 3, Mystrile from 6, Orichalc and Adamantite from 10. Mythic Stone only appears on special floors and floor 231 and below.
  - The extra chance comes out of empty rocks and Junk Ore first. On the deepest floors, Copper and Silver also become rarer, but never less than half as common as usual.
- **In the Lake Mine, the rarer jewels are about twice as common:** Kappa Jewel, Pink Diamond, Alexandrite, Moon Stone, Sand Rose, Diamond and Emerald.
  - They still appear on the same floors as usual. The common gems (Ruby, Topaz, Peridot, Fluorite, Agate, Amethyst) keep their chances, except on the deepest floors, where they make room.

## Status

**Tested in game (on TLE):**

- The stamina and fatigue meter, including after leaving the mine or the hot springs.
- Clock speed cycling, and the x2 rate.
- Visible stairs on floor 0 and on floors 1 and below.
- Fast tool upgrades: an Axe upgraded with Mystrile on a Wednesday was ready the next day.
- Fast tool XP: four Hammer swings gave 1,000 XP.
- Self-watering: after one night, all 230 tilled tiles on the test farm were watered.
- Automatic feeding: 4 chickens and 7 barn animals were fed overnight starting from empty troughs, with feed visible in the troughs the next day.
- Faster affection: brushing a cow raised its affection by 5 instead of 1.
- Rare ore boost: Spring Mine floor 22 had 20 rare-ore rocks out of 30 and no empty ones. The unmodified game averages about 12 rare and 12 empty. Lake Mine floors still generate normally.

**Not tested in game yet:**

- The clock-speed setting surviving a save and reload.
- Buying the free basket.
- Mine stairs in the Lake Mine and on special floors.
- The meter in busy scenes (festivals, cutscenes).
- Self-watering crops: crop growth over several days (the test save ran into Winter 1).
- Anything on the original game without TLE.

## Credits

- **True Love Edition v4.0:** its authors ([kataiki.tumblr.com/FOMT-TL](https://kataiki.tumblr.com/FOMT-TL)).
- **FoMT Proofread 1.22 by Mentil** ([romhacking.net/hacks/9242](https://www.romhacking.net/hacks/9242/)): its optional QoL patch is the basis for the Grind Reduction patch: the Vacation House price, the cottage after 5 years, and visible mine stairs. If you play the original *Friends of Mineral Town*, use the Proofread itself; it also fixes thousands of text errors.

### Building from source

With [just](https://github.com/casey/just), [uv](https://github.com/astral-sh/uv) and clang/LLVM installed, put the clean ROM and the TLE `.ips` in the repo root, then run:

```
just                              # TLE + all patches -> build/mfomt-qol.gba
just rom "hud tweaks ores"        # only some patches
just apply "hud ores" my.gba      # use the prebuilt .ips files instead (no clang needed)
just base=clean rom               # without True Love Edition
```

Patch names: `hud`, `tweaks` (Grind Reduction), `basket`, `upgrades`, `toolxp`, `watering`, `feeding`, `affection`, `ores`.

This repository contains only patches. No ROMs, and no third-party patches. Technical notes for anyone who wants to continue the work are in [`AGENTS.md`](AGENTS.md), and the build scripts are in [`tools/`](tools/).
