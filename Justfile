# Build MFoMT QoL patches and ROMs.
#
#   just              build everything from source -> build/mfomt-qol.gba (TLE + all patches)
#   just rom          same
#   just rom "hud tweaks ores"      only some patches (names below)
#   just ips          rebuild every .ips into build/
#   just ship         rebuild and copy the .ips files to the repo root (the published names)
#   just test         rebuild and refresh test/test.gba (the test ROM)
#   just apply "hud ores" out.gba   apply the shipped .ips files from the repo root (no toolchain needed)
#   just clean
#
# Needs: uv, clang + llvm (Homebrew), and these files in the repo root (not in git):
#   Harvest Moon - More Friends of Mineral Town (USA).gba    clean ROM, CRC32 1736B957
#   Harvest Moon - MFoMT (True Love Edition v4.0).ips        https://kataiki.tumblr.com/FOMT-TL
# Set base=clean to build on the unmodified game instead of TLE:  just base=clean rom

clean_rom := "Harvest Moon - More Friends of Mineral Town (USA).gba"
tle_ips   := "Harvest Moon - MFoMT (True Love Edition v4.0).ips"
base      := "tle"
build     := "build"
all       := "hud tweaks basket upgrades toolxp watering feeding affection ores lumber"

# patch name -> build script, script output, published file
# hud       tools/build.py      stamina.ips    MFoMT Stamina HUD
# tweaks    tools/tweaks.py     tweaks.ips     MFoMT Grind Reduction
# basket    tools/basket.py     basket.ips     MFoMT Free Basket
# upgrades  tools/upgrades.py   upgrades.ips   MFoMT Fast Tool Upgrades
# toolxp    tools/toolxp.py     toolxp.ips     MFoMT Fast Tool XP
# watering  tools/watering.py   watering.ips   MFoMT Self-Watering Crops
# feeding   tools/feeding.py    feeding.ips    MFoMT Automatic Animal Feeding
# affection tools/affection.py  affection.ips  MFoMT Faster Animal Affection
# ores      tools/ores.py       ores.ips       MFoMT Rare Ore Boost
# lumber    tools/lumber.py     lumber.ips     MFoMT More Lumber

default: rom

# The base ROM every patch is built against (tle.gba), from the clean ROM.
base-rom:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p {{build}}
    [ -f "{{clean_rom}}" ] || { echo "missing: {{clean_rom}}"; exit 1; }
    if [ "{{base}}" = "clean" ]; then
        cp "{{clean_rom}}" {{build}}/tle.gba
    else
        [ -f "{{tle_ips}}" ] || { echo "missing: {{tle_ips}} (get it from https://kataiki.tumblr.com/FOMT-TL)"; exit 1; }
        uv run python tools/applyips.py "{{tle_ips}}" "{{clean_rom}}" {{build}}/tle.gba
    fi

# Rebuild every patch's .ips into build/.
ips: base-rom
    #!/usr/bin/env bash
    set -euo pipefail
    cd {{build}}
    for script in build tweaks basket upgrades toolxp watering feeding affection ores lumber; do
        echo "== $script"
        uv run python ../tools/$script.py
    done

# Build a ROM with the given patches (default: all) -> build/mfomt-qol.gba
rom patches=all out=(build / "mfomt-qol.gba"): ips
    #!/usr/bin/env bash
    set -euo pipefail
    list=()
    for p in {{patches}}; do
        case $p in
            hud) list+=(stamina.ips) ;;
            tweaks|basket|upgrades|toolxp|watering|feeding|affection|ores|lumber) list+=("$p.ips") ;;
            *) echo "unknown patch: $p (known: {{all}})"; exit 1 ;;
        esac
    done
    out="$(cd "$(dirname "{{out}}")" && pwd)/$(basename "{{out}}")"
    cd {{build}}
    uv run python ../tools/stack.py "${list[@]}"
    cp qol.gba "$out"
    echo "wrote $out with: {{patches}}"

# Rebuild and copy the .ips files to the repo root under their published names.
ship: ips
    #!/usr/bin/env bash
    set -euo pipefail
    cd {{build}}
    uv run python ../tools/stack.py stamina.ips tweaks.ips basket.ips upgrades.ips toolxp.ips watering.ips feeding.ips affection.ips ores.ips lumber.ips
    cp stamina.ips   "../MFoMT Stamina HUD (apply after TLE v4.0).ips"
    cp tweaks.ips    "../MFoMT Grind Reduction (apply after TLE v4.0).ips"
    cp basket.ips    "../MFoMT Free Basket (apply after TLE v4.0).ips"
    cp upgrades.ips  "../MFoMT Fast Tool Upgrades (apply after TLE v4.0).ips"
    cp toolxp.ips    "../MFoMT Fast Tool XP (apply after TLE v4.0).ips"
    cp watering.ips  "../MFoMT Self-Watering Crops (apply after TLE v4.0).ips"
    cp feeding.ips   "../MFoMT Automatic Animal Feeding (apply after TLE v4.0).ips"
    cp affection.ips "../MFoMT Faster Animal Affection (apply after TLE v4.0).ips"
    cp ores.ips      "../MFoMT Rare Ore Boost (apply after TLE v4.0).ips"
    cp lumber.ips    "../MFoMT More Lumber (apply after TLE v4.0).ips"
    echo "shipped 10 patches"

# Rebuild and refresh the test ROM (test/test.gba; test.sav is left alone).
test: (rom all "test/test.gba")

# Apply the shipped .ips files from the repo root to the base ROM (no toolchain needed).
apply patches=all out=(build / "mfomt-qol.gba"): base-rom
    #!/usr/bin/env bash
    set -euo pipefail
    cp {{build}}/tle.gba "{{out}}.tmp"
    for p in {{patches}}; do
        case $p in
            hud) n="Stamina HUD" ;;              tweaks) n="Grind Reduction" ;;
            basket) n="Free Basket" ;;           upgrades) n="Fast Tool Upgrades" ;;
            toolxp) n="Fast Tool XP" ;;          watering) n="Self-Watering Crops" ;;
            feeding) n="Automatic Animal Feeding" ;; affection) n="Faster Animal Affection" ;;
            ores) n="Rare Ore Boost" ;;          lumber) n="More Lumber" ;;
            *) echo "unknown patch: $p (known: {{all}})"; exit 1 ;;
        esac
        uv run python tools/applyips.py "MFoMT $n (apply after TLE v4.0).ips" "{{out}}.tmp" "{{out}}.tmp"
    done
    mv "{{out}}.tmp" "{{out}}"
    echo "wrote {{out}} with: {{patches}}"

clean:
    rm -rf {{build}}
