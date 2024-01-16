import argparse
import json
import sys
from pathlib import Path

def parse_args(args):
    parser = argparse.ArgumentParser("Convert json bt packet dump to human readable")
    parser.add_argument("file", nargs=1, help="json packet dump file")
    parser.add_argument("--hex", action='store_true', help="output for hex editor")
    return parser.parse_args(args)

def get(obj, path, default=None):
    pcs = path.split('/')
    res = obj
    for pc in pcs:
        if pc in res:
            res = res[pc]
        else:
            return default
    return res

def fixup(svc, char, uuid):
    if svc is None:
        return (uuid, None, None)
    elif char is None:
        return (svc, uuid, None)
    else:
        return (svc, char, uuid)

def human_svc(svc):
    return {
        'ec:be:39:80:c9:a2:11:e1:b1:bd:00:02:a5:d5:c5:1b': 'ecbe-',
    }.get(svc, svc)

def human_char(char):
    return {
        '49:12:30:40:ae:e8:11:e1:a7:4d:00:02:a5:d5:c5:1b': 'o00',
        '4d:0b:f3:20:ae:e8:11:e1:a0:d9:00:02:a5:d5:c5:1b': 'o01',
        '51:28:ce:60:ae:e8:11:e1:b8:4b:00:02:a5:d5:c5:1b': 'o02',
        '56:0f:14:20:ae:e8:11:e1:81:84:00:02:a5:d5:c5:1b': 'o03',
        'db:5b:55:e0:ae:e7:11:e1:96:5e:00:02:a5:d5:c5:1b': 'i00',
        'e0:b8:a0:60:ae:e7:11:e1:92:f4:00:02:a5:d5:c5:1b': 'i01',
        '0a:e1:2b:00:ae:e8:11:e1:a1:92:00:02:a5:d5:c5:1b': 'i02',
        'b3:05:b6:80:ae:e7:11:e1:a7:30:00:02:a5:d5:c5:1b': 'setup',
    }.get(char, char)

def stage_01(packets):
    for packet in packets:
        btatt = get(packet, '_source/layers/btatt')
        op = get(btatt, 'btatt.opcode')
        cmd = {
            '0x12': 'write req',
            '0x13': 'write res',
            '0x52': 'write',
            '0x0a': 'read req',
            '0x0b': 'read res',
            '0x1b': 'notif',
        }.get(op)

        svc16 = get(btatt, 'btatt.handle_tree/btatt.service_uuid16')
        svc128 = get(btatt, 'btatt.handle_tree/btatt.service_uuid128')
        char16 = get(btatt, 'btatt.handle_tree/btatt.characteristic_uuid16')
        char128 = get(btatt, 'btatt.handle_tree/btatt.characteristic_uuid128')
        uuid16 = get(btatt, 'btatt.handle_tree/btatt.uuid16')
        uuid128 = get(btatt, 'btatt.handle_tree/btatt.uuid128')

        svc, char, ccc = fixup(svc16 or svc128, char16 or char128, uuid16 or uuid128)

        if cmd in ('write', 'write req') and ccc == '0x2902':
            cmd = 'req notif'

        if cmd == 'write res':
            continue
        elif cmd == 'write req':
            cmd = 'Write'

        if cmd in ('read res',):
            val_keys = [key for key in btatt.keys()
                        if key[6:] not in ('opcode', 'opcode_tree',
                                           'handle', 'handle_tree',
                                           'request_in_frame')]
            value = f'{val_keys[0]}: {btatt[val_keys[0]]}'
        else:
            value = get(btatt, 'btatt.value')


        yield f"{op} {cmd} {human_svc(svc)} {human_char(char)} {ccc} -- {value}"

def stage_02(lines):
    before = True
    for line in lines:
        if 'btatt.system_id.manufacturer_identifier' in line:
            break

    def pad(sth, pad_len=16):
        return sth + bytes([0]) * (pad_len - len(sth))

    def to_bin(txt):
        return pad(txt.encode('utf-8'))

    crnt = 'i'
    yield to_bin('input')
    for line in lines:
        io = line[17]
        if io != crnt:
            crnt = io
            yield to_bin('input' if io == 'i' else 'output')

        data = line[29:]
        raw_data = bytes(int(d, 16) for d in data.split(':'))
        yield pad(raw_data)

def main(opts):
    packets = json.loads(Path(opts.file[0]).read_bytes())

    res = stage_01(packets)
    if opts.hex:
        res = stage_02(res)
        fres = b''.join(res)
        sys.stdout.buffer.write(fres)
    else:
        fres = '\n'.join(res)
        print(fres)


if __name__ == '__main__':
    main(parse_args(sys.argv[1:]))
