import argparse
import json
import sys
from pathlib import Path
from tools import verify_cs, exp_len, join, ints, safe_truncate

def parse_args(args):
    parser = argparse.ArgumentParser("Convert json bt packet dump to human readable")
    parser.add_argument("file", nargs=1, help="json packet dump file")
    parser.add_argument("--hex", action='store_true', help="output for hex editor")
    parser.add_argument("--json", action='store_true', help="output json msgs")
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

def stage_raw(packets):
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

def stage_hex(lines):
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

def stage_json(lines):
    lines = iter(lines)
    before = True
    for line in lines:
        if 'btatt.system_id.manufacturer_identifier' in line:
            break


    msgs = []
    def accum_val(val):
        if not msgs or exp_len(msgs[-1]) <= len(msgs[-1]):
            msgs.append(val)
        else:
            msgs[-1] = join(msgs[-1], val)

    for line in lines:
        if not line:
            continue
        op, cmd, svc, char, ccc, _, val = line.split()
        if val != '01:00:ff:ff':
            accum_val(val)

    msgs = [safe_truncate(msg) for msg in msgs]
    if not all(verify_cs(ints(msg)) for msg in msgs):
        raise ValueError("checksum invalid")

    return msgs

def main(opts):
    was_raw = None
    if opts.file[0].endswith('.json'):
        was_raw = True
        # packet capture?
        packets = json.loads(Path(opts.file[0]).read_bytes())
        parsed = stage_raw(packets)
    elif opts.file[0].endswith('.txt'):
        # raw parsed
        parsed = Path(opts.file[0]).read_text().split('\n')
        was_raw = False
    else:
        raise Exception("not sure what to do with input file")

    if opts.hex:
        res = stage_hex(parsed)
        fres = b''.join(res)
        sys.stdout.buffer.write(fres)
    elif opts.json or not was_raw:
        # assume we want json if the input is parsed
        res = stage_json(parsed)
        print(json.dumps(res, indent=2))
    elif was_raw:
        fres = '\n'.join(parsed)
        print(fres)
    else:
        raise Exception("don't know what to do")


if __name__ == '__main__':
    main(parse_args(sys.argv[1:]))
