# bg-save-editor

A simple Python script for editing Baldur's Gate: Enhanced Edition save files (`BALDUR.gam`) on any platform.

## Features

- View all party member stats (STR, DEX, CON, INT, WIS, CHA, HP, XP)
- Edit individual stats for the protagonist or all party members
- Set party gold
- No dependencies beyond Python 3

## Requirements

- Python 3.6+

## Installation

```bash
git clone https://github.com/Zei204/bg-save-editor.git
cd bg-save-editor
```

## Usage

### View party stats

```bash
python3 bgedit.py info path/to/BALDUR.gam
```

Example output:
```
Party gold: 764  |  Members: 4
  [0] "*1FIGHT"  slot=0  ver=V1.0
      STR=18/12  DEX=18  CON=18  INT=17  WIS=10  CHA=10
      HP=10/10  XP=669
```

### Edit stats

All flags are optional — only the values you specify will be changed.

```bash
python3 bgedit.py edit BALDUR.gam BALDUR_new.gam [options]
```

| Option | Description |
|--------|-------------|
| `--str N` | Strength (1-18) |
| `--strx N` | Exceptional strength bonus (0-100, only meaningful if STR=18) |
| `--dex N` | Dexterity |
| `--con N` | Constitution |
| `--int N` | Intelligence |
| `--wis N` | Wisdom |
| `--cha N` | Charisma |
| `--hp N` | Set current and max HP |
| `--xp N` | Experience points |
| `--gold N` | Party gold |
| `--all-members` | Apply changes to all party members (default: protagonist only) |

### Examples

```bash
# Give yourself 99999 gold
python3 bgedit.py edit BALDUR.gam BALDUR_new.gam --gold 99999

# Max stats for protagonist
python3 bgedit.py edit BALDUR.gam BALDUR_new.gam --str 18 --strx 100 --dex 18 --con 18 --int 18 --wis 18 --cha 18

# Set XP and HP
python3 bgedit.py edit BALDUR.gam BALDUR_new.gam --xp 500000 --hp 200
```

> **Always back up your original save before editing.**

## Using on Android via Termux

Termux lets you run the script directly on your Android device without a PC.

```bash
# Install Termux from F-Droid, then:
pkg install python git

git clone https://github.com/Zei204/bg-save-editor.git
cd bg-save-editor

# BG:EE saves are located at:
# /sdcard/Android/data/com.beamdog.baldursgateenhancededition/files/save/

python3 bgedit.py info /sdcard/Android/data/com.beamdog.baldursgateenhancededition/files/save/000000001-Quick-Save/BALDUR.gam

python3 bgedit.py edit \
  /sdcard/Android/data/com.beamdog.baldursgateenhancededition/files/save/000000001-Quick-Save/BALDUR.gam \
  /sdcard/Android/data/com.beamdog.baldursgateenhancededition/files/save/000000001-Quick-Save/BALDUR.gam \
  --gold 99999
```

Note: Termux needs storage permission. Run `termux-setup-storage` once before accessing `/sdcard`.

## How it works

`BALDUR.gam` is a binary file in the Infinity Engine GAM v2.0 format. It contains party member structs, each with an embedded CRE (creature) block holding the character's stats. This script reads the offsets from the GAM header, locates each CRE block, and patches the relevant bytes directly.

Format reference: [IESDP — GAM v2.0](https://gibberlings3.github.io/iesdp/file_formats/ie_formats/gam_v2.0.htm)

## License

MIT
