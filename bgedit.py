#!/usr/bin/env python3
"""
BG:EE BALDUR.gam editor
CRE data is embedded inside BALDUR.gam for each party member.

Usage:
  python3 bgedit.py info  BALDUR.gam
  python3 bgedit.py edit  BALDUR.gam OUT.gam  [options]

Edit options (all optional, only specified values are changed):
  --str  N     Strength (1-255)
  --strx N     Strength bonus / exceptional (0-100, used only if str=18)
  --dex  N     Dexterity (1-255)
  --con  N     Constitution (1-255)
  --int  N     Intelligence (1-255)
  --wis  N     Wisdom (1-255)
  --cha  N     Charisma (1-255)
  --hp   N     Current + Max HP set to N (0-65535)
  --xp   N     Experience points (0-4294967295)
  --gold N     Party gold (stored in GAM header, 0-4294967295)
  --all-members  Apply stat changes to ALL party members (default: protagonist only)

Examples:
  python3 bgedit.py info  save/BALDUR.gam
  python3 bgedit.py edit  save/BALDUR.gam  save/BALDUR_new.gam  --gold 99999
  python3 bgedit.py edit  save/BALDUR.gam  save/BALDUR_new.gam  --str 18 --strx 100 --xp 500000
"""

import sys
import struct
import argparse
import os

GAM_SIG         = b'GAME'
GAM_GOLD_OFF    = 0x0018
GAM_NPC_OFF     = 0x0020
GAM_NPC_CNT     = 0x0024
NPC_STRUCT_SIZE = 0x160
NPC_CRE_OFF     = 0x0004
NPC_CRE_SIZE    = 0x0008
NPC_NAME        = 0x000C
NPC_PARTY_ORDER = 0x0002

CRE_SIG  = b'CRE '
OFF_XP      = 0x0018
OFF_CUR_HP  = 0x0024
OFF_MAX_HP  = 0x0026
OFF_STR     = 0x0238
OFF_STR_X   = 0x0239
OFF_INT     = 0x023A
OFF_WIS     = 0x023B
OFF_DEX     = 0x023C
OFF_CON     = 0x023D
OFF_CHA     = 0x023E

# Valid ranges for stats
STAT_MIN = 1
STAT_MAX = 255
STRX_MIN, STRX_MAX = 0, 100
HP_MIN, HP_MAX = 0, 65535
XP_MIN, XP_MAX = 0, 4294967295
GOLD_MIN, GOLD_MAX = 0, 4294967295


def validate_stat(name, value, min_val, max_val):
    if not (min_val <= value <= max_val):
        raise ValueError(f"{name} must be between {min_val} and {max_val}, got {value}")
    return value


def read_gam(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    with open(path, 'rb') as f:
        data = bytearray(f.read())
    if data[:4] != GAM_SIG:
        raise ValueError(f"Not a GAM file (got {data[:4]})")
    return data


def get_party(data):
    npc_base  = struct.unpack_from('<I', data, GAM_NPC_OFF)[0]
    npc_count = struct.unpack_from('<I', data, GAM_NPC_CNT)[0]
    members = []
    for i in range(npc_count):
        off      = npc_base + i * NPC_STRUCT_SIZE
        order    = struct.unpack_from('<H', data, off + NPC_PARTY_ORDER)[0]
        cre_off  = struct.unpack_from('<I', data, off + NPC_CRE_OFF)[0]
        cre_size = struct.unpack_from('<I', data, off + NPC_CRE_SIZE)[0]
        name     = data[off+NPC_NAME:off+NPC_NAME+8].rstrip(b'\x00').decode('latin-1')
        members.append({'index': i, 'order': order,
                        'cre_off': cre_off, 'cre_size': cre_size, 'name': name})
    return members


def read_cre_stats(data, cre_off):
    if bytes(data[cre_off:cre_off+4]) != CRE_SIG:
        return None
    ver    = bytes(data[cre_off+4:cre_off+8]).decode('latin-1')
    xp     = struct.unpack_from('<I', data, cre_off+OFF_XP)[0]
    cur_hp = struct.unpack_from('<H', data, cre_off+OFF_CUR_HP)[0]
    max_hp = struct.unpack_from('<H', data, cre_off+OFF_MAX_HP)[0]
    return {
        'ver': ver, 'xp': xp, 'cur_hp': cur_hp, 'max_hp': max_hp,
        'str':   data[cre_off+OFF_STR],
        'str_x': data[cre_off+OFF_STR_X],
        'int':   data[cre_off+OFF_INT],
        'wis':   data[cre_off+OFF_WIS],
        'dex':   data[cre_off+OFF_DEX],
        'con':   data[cre_off+OFF_CON],
        'cha':   data[cre_off+OFF_CHA],
    }


def patch_cre(data, cre_off, patches):
    if 'xp'     in patches: struct.pack_into('<I', data, cre_off+OFF_XP,     patches['xp'])
    if 'cur_hp' in patches: struct.pack_into('<H', data, cre_off+OFF_CUR_HP, patches['cur_hp'])
    if 'max_hp' in patches: struct.pack_into('<H', data, cre_off+OFF_MAX_HP, patches['max_hp'])
    if 'str'    in patches: data[cre_off+OFF_STR]   = patches['str']
    if 'str_x'  in patches: data[cre_off+OFF_STR_X] = patches['str_x']
    if 'int'    in patches: data[cre_off+OFF_INT]   = patches['int']
    if 'wis'    in patches: data[cre_off+OFF_WIS]   = patches['wis']
    if 'dex'    in patches: data[cre_off+OFF_DEX]   = patches['dex']
    if 'con'    in patches: data[cre_off+OFF_CON]   = patches['con']
    if 'cha'    in patches: data[cre_off+OFF_CHA]   = patches['cha']


def fmt_member(m, s):
    order_s = str(m['order']) if m['order'] != 0xFFFF else 'not-in-party'
    str_s = f"{s['str']}/{s['str_x']:02d}" if s['str'] == 18 else str(s['str'])
    return (f"  [{m['index']}] \"{m['name']}\"  slot={order_s}  ver={s['ver']}\n"
            f"      STR={str_s}  DEX={s['dex']}  CON={s['con']}  "
            f"INT={s['int']}  WIS={s['wis']}  CHA={s['cha']}\n"
            f"      HP={s['cur_hp']}/{s['max_hp']}  XP={s['xp']}")


def cmd_info(gam_path):
    data = read_gam(gam_path)
    gold = struct.unpack_from('<I', data, GAM_GOLD_OFF)[0]
    members = get_party(data)
    print(f"Party gold: {gold}  |  Members: {len(members)}")
    for m in members:
        s = read_cre_stats(data, m['cre_off'])
        if s:
            print(fmt_member(m, s))
        else:
            print(f"  [{m['index']}] \"{m['name']}\" - invalid CRE at {m['cre_off']:#x}")


def cmd_edit(gam_path, out_path, patches, all_members=False):
    # Protection against overwriting the source file
    if os.path.abspath(gam_path) == os.path.abspath(out_path):
        print("Error: Output file cannot be the same as input file.", file=sys.stderr)
        print("Please specify a different output filename.", file=sys.stderr)
        sys.exit(1)

    data = read_gam(gam_path)
    if 'gold' in patches:
        struct.pack_into('<I', data, GAM_GOLD_OFF, patches.pop('gold'))
        print(f"Gold set.")
    members = get_party(data)
    targets = members if all_members else [m for m in members if m['order'] == 0]
    if not targets:
        targets = members[:1]
    for m in targets:
        s = read_cre_stats(data, m['cre_off'])
        if not s:
            print(f"  [{m['index']}] skipped"); continue
        print(f"Patching \"{m['name']}\" ...")
        patch_cre(data, m['cre_off'], patches)
        print(fmt_member(m, read_cre_stats(data, m['cre_off'])))
    with open(out_path, 'wb') as f:
        f.write(data)
    print(f"Saved -> {out_path}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd')

    pi = sub.add_parser('info')
    pi.add_argument('gam')

    pe = sub.add_parser('edit')
    pe.add_argument('gam')
    pe.add_argument('out')
    pe.add_argument('--str',  type=int, dest='str_')
    pe.add_argument('--strx', type=int)
    pe.add_argument('--dex',  type=int)
    pe.add_argument('--con',  type=int)
    pe.add_argument('--int',  type=int, dest='int_')
    pe.add_argument('--wis',  type=int)
    pe.add_argument('--cha',  type=int)
    pe.add_argument('--hp',   type=int)
    pe.add_argument('--xp',   type=int)
    pe.add_argument('--gold', type=int)
    pe.add_argument('--all-members', action='store_true')

    args = parser.parse_args()
    if args.cmd == 'info':
        cmd_info(args.gam)
    elif args.cmd == 'edit':
        patches = {}
        try:
            if args.str_  is not None: 
                validate_stat("STR", args.str_, STAT_MIN, STAT_MAX)
                patches['str'] = args.str_
            if args.strx  is not None: 
                validate_stat("STRX (exceptional strength)", args.strx, STRX_MIN, STRX_MAX)
                patches['str_x'] = args.strx
            if args.dex   is not None: 
                validate_stat("DEX", args.dex, STAT_MIN, STAT_MAX)
                patches['dex'] = args.dex
            if args.con   is not None: 
                validate_stat("CON", args.con, STAT_MIN, STAT_MAX)
                patches['con'] = args.con
            if args.int_  is not None: 
                validate_stat("INT", args.int_, STAT_MIN, STAT_MAX)
                patches['int'] = args.int_
            if args.wis   is not None: 
                validate_stat("WIS", args.wis, STAT_MIN, STAT_MAX)
                patches['wis'] = args.wis
            if args.cha   is not None: 
                validate_stat("CHA", args.cha, STAT_MIN, STAT_MAX)
                patches['cha'] = args.cha
            if args.xp    is not None: 
                validate_stat("XP", args.xp, XP_MIN, XP_MAX)
                patches['xp'] = args.xp
            if args.gold  is not None: 
                validate_stat("Gold", args.gold, GOLD_MIN, GOLD_MAX)
                patches['gold'] = args.gold
            if args.hp    is not None: 
                validate_stat("HP", args.hp, HP_MIN, HP_MAX)
                patches['cur_hp'] = patches['max_hp'] = args.hp
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        
        if not patches:
            print("Nothing to patch."); sys.exit(1)
        cmd_edit(args.gam, args.out, patches, args.all_members)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
