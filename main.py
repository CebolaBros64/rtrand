from collections import namedtuple
from functools import partial
from pathlib import Path
from random import randrange
from sys import argv
import struct

import defs

if len(argv) >= 2:
    ROM_PATH = Path(argv[1])
else:
    ROM_PATH = Path("2462 - Rhythm Tengoku (J)(WRG).gba")

Entry = namedtuple('Entry', ['id', 'displayReq', 'unlockReq', 'targets', 'flags', 'delay'])
#            Level ID
#            |    Show Req
#            |    |  Open Req
#            |    |  |  Targets
#            |    |  |  |  Flags
#            |    |  |  |  | Delay
#            |    |  |  |  | |
# entry = "< h 2x 4s 4s 4s c h x"
# https://github.com/arthurtilly/rhythmtengoku/blob/d181e62c5e90c6083e02eb5977fa4a5cd301e306/src/scenes/game_select.h#L161
ENTRY_STRUCT = "< h 2x 4s 4s 4s B h x"


def print_entry_list(_l):
    """ For debugging purposes """
    for entry in _l:
        print('')
        for attrb in entry._fields:
            if attrb == 'id':
                val = get_level(entry.__getattribute__(attrb))

            elif attrb == 'displayReq' or attrb == 'unlockReq':
                val = get_requirements(entry.__getattribute__(attrb))

            elif attrb == 'flags':
                val = get_flags(entry.__getattribute__(attrb))

            else:
                val = entry.__getattribute__(attrb)

            print(f"{attrb}: {val}")


def get_gba_pointer(pointer_value):
    raw_pointer = pointer_value[:-1] + b'\x00'
    return struct.unpack('<I', raw_pointer)[0]


def get_level(level_value):
    levels = dict(enumerate(defs.LEVEL_NAMES, start=-1))

    return levels[level_value]


def get_requirements(req_value):
    if req_value == b'\x00\x00\x00\x00':
        return 0

    pointer = get_gba_pointer(req_value)

    raw_requirements = b''
    with open(ROM_PATH, 'rb') as rom:
        rom.seek(pointer)
        _bin = rom.read()

        for i, b in enumerate(_bin):
            if b == 255:  # Should really be -1 but python type conversion shenenigans
                rom.seek(pointer)
                raw_requirements = rom.read(i + 1)
                break

    requirements = []
    lvl_states = dict(enumerate(defs.LEVEL_STATES, start=-1))
    for i in range(0, len(raw_requirements), 3):
        state_index = struct.unpack('b', raw_requirements[i:i + 1])[0]

        # TODO: This could be written better
        if state_index == -1:
            requirements.append(['END_REQ'])
        else:
            requirements.append([
                lvl_states[state_index],
                raw_requirements[i + 1],
                raw_requirements[i + 2]
            ])

    return requirements


def get_flags(flag_value):
    flags_used = []

    for index, fl in enumerate(defs.LEVEL_FLAGS):
        if ((flag_value >> index) & 1) == 1:
            flags_used.append(fl)

    # If empty return 0
    if not flags_used:
        return 0

    return flags_used


def parse2list(_bin, unpack, length):
    """ https://stackoverflow.com/a/14216741 """
    _list = [Entry._make(unpack(chunk)) for chunk in iter(partial(_bin.read, length), b'')]

    return _list


if __name__ == '__main__':
    entry_size = struct.calcsize(ENTRY_STRUCT)

    with open(ROM_PATH, 'rb') as f, open("temp.bin", 'wb') as t, open("new_rom.gba", 'wb') as new_rom:
        # f.seek(0x9CEAFC)
        # f.read(0x9CEAFC + (entry_size * (15 * 12)))

        rom_bin = f.read()

        new_rom.write(rom_bin)

        t.write(rom_bin[0x9CEAFC:0x9CEAFC + (entry_size * (15 * 12))])

    with open("temp.bin", 'rb') as f:
        entry_list = parse2list(f, struct.Struct(ENTRY_STRUCT).unpack_from, entry_size)

        # print_entry_list(entry_list)

    # Shuffle
    new_entry_list = []
    game_id_pool = [*range(0, 41)]
    for entry in entry_list:
        if entry.id == -1:
            new_entry_list.append(entry)

        elif entry.id in range(0, 41):  # Rhythm Games
            new_id = game_id_pool.pop(randrange(len(game_id_pool)))

            new_entry_list.append(Entry(
                id=new_id,
                displayReq=entry.displayReq,
                unlockReq=entry.unlockReq,
                targets=entry.targets,
                flags=entry.flags,
                delay=entry.delay
            ))

        else:
            new_entry_list.append(entry)

    # Rewrite ROM
    with open("new_rom.gba", 'rb+') as new_rom:
        _bin = new_rom.read()

        cool = b''
        for entry in new_entry_list:
            # print(entry)
            cool += (struct.pack(ENTRY_STRUCT, *entry))

        new_rom.seek(0)
        new_rom.write(_bin[:0x9CEAFC] + cool + _bin[0x9CEAFC + (entry_size * (15 * 12)):])

    Path("temp.bin").unlink()
