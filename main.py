import struct
from functools import partial
from collections import namedtuple
from random import randrange

ROM_PATH = "2462 - Rhythm Tengoku (J)(WRG).gba"

LEVEL_NAMES = [
    'LEVEL_NULL',  # -1
    'LEVEL_KARATE_MAN',  # 0
    'LEVEL_KARATE_MAN_2',  # 1
    'LEVEL_CLAPPY_TRIO',  # 2
    'LEVEL_SNAPPY_TRIO',  # 3...
    'LEVEL_POLYRHYTHM',
    'LEVEL_POLYRHYTHM_2',
    'LEVEL_NIGHT_WALK',
    'LEVEL_NIGHT_WALK_2',
    'LEVEL_RHYTHM_TWEEZERS',
    'LEVEL_RHYTHM_TWEEZERS_2',
    'LEVEL_SICK_BEATS',
    'LEVEL_BOUNCY_ROAD',
    'LEVEL_BOUNCY_ROAD_2',
    'LEVEL_NINJA_BODYGUARD',
    'LEVEL_NINJA_REINCARNATE',
    'LEVEL_SNEAKY_SPIRITS',
    'LEVEL_SNEAKY_SPIRITS_2',
    'LEVEL_SAMURAI_SLICE',
    'LEVEL_SPACEBALL',
    'LEVEL_SPACEBALL_2',
    'LEVEL_TAP_TRIAL',
    'LEVEL_TAP_TRIAL_2',
    'LEVEL_MARCHING_ORDERS',
    'LEVEL_MARCHING_ORDERS_2',
    'LEVEL_WIZARDS_WALTZ',
    'LEVEL_BUNNY_HOP',
    'LEVEL_FIREWORKS',
    'LEVEL_POWER_CALLIGRAPHY',
    'LEVEL_POWER_CALLIGRAPHY_2',
    'LEVEL_TOSS_BOYS',
    'LEVEL_TOSS_BOYS_2',
    'LEVEL_RAT_RACE',
    'LEVEL_TRAM_PAULINE',
    'LEVEL_SHOWTIME',
    'LEVEL_SPACE_DANCE',
    'LEVEL_COSMIC_DANCE',
    'LEVEL_RAP_MEN',
    'LEVEL_RAP_WOMEN',
    'LEVEL_QUIZ_SHOW',
    'LEVEL_BON_ODORI',
    'LEVEL_BON_DANCE',
    'LEVEL_REMIX_1',
    'LEVEL_REMIX_2',
    'LEVEL_REMIX_3',
    'LEVEL_REMIX_4',
    'LEVEL_REMIX_5',
    'LEVEL_REMIX_6',
    'LEVEL_REMIX_7',
    'LEVEL_REMIX_8',
    'LEVEL_CAFE',
    'LEVEL_RHYTHM_TOYS',
    'LEVEL_ENDLESS_GAMES',
    'LEVEL_DRUM_LESSONS',
    'LEVEL_STAFF_CREDIT',
    'LEVEL_LIVE_MENU'
]

LEVEL_STATES = [
    'LEVEL_STATE_NULL',  # -1
    'LEVEL_STATE_HIDDEN',  # 0
    'LEVEL_STATE_APPEARING',  # 1
    'LEVEL_STATE_CLOSED',  # 2
    'LEVEL_STATE_OPEN',  # 3...
    'LEVEL_STATE_CLEARED',
    'LEVEL_STATE_HAS_MEDAL'
]

LEVEL_FLAGS = [
    'TARGET_ON_SHOW',  # 0
    'MOVE_CURSOR',  # 1
    'CLEAR_BY_DEFAULT',  # 2
    'DELAY_CLEAR',  # 3...
    'DELAY_OPEN',
    'DELAY_SHOW',
    'TARGET_ON_OPEN'
]

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
    levels = dict(enumerate(LEVEL_NAMES, start=-1))

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
    lvl_states = dict(enumerate(LEVEL_STATES, start=-1))
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

    for index, fl in enumerate(LEVEL_FLAGS):
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
