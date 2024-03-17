from functools import reduce

def exp_len(msg):
    return int(msg[:2], 16) * 3 - 1

def ints(s):
    return [int(p, 16) for p in s.split(':')]

def checksum(ints):
    return reduce(lambda a, b: a ^ b, ints)

def s_checksum(ints):
    return reduce(lambda a, b: a + b, ints) % 256

def add_checksum(raw):
    return bytes([*raw, 0, checksum(raw)])

def verify_cs(ints):
    return checksum(ints[:-1]) == ints[-1]

def words(ints, wl=2):
    assert len(ints) % wl == 0
    res = []
    for i, b in enumerate(ints):
        if i % wl == 0:
            res.append(b)
        else:
            res[-1] *= 256
            res[-1] += b
    return res

def _to_bytes(arg: str | int | bytes | None) -> bytes:
    if isinstance(arg, str):
        return bytes(ints(arg))
    elif isinstance(arg, int):
        return bytes([arg])
    elif isinstance(arg, bytes):
        return arg
    elif arg is None:
        return b''

def to_bytes(*args) -> bytes:
    return b''.join(_to_bytes(p) for p in args)

def safe_truncate(msg):
    elen = exp_len(msg)
    rest = msg[elen:]
    if len(rest) % 3 != 0 or rest != ':00' * (len(rest) // 3):
        raise ValueError("Can't truncate " + msg)
    return msg[:elen]

def join(*pcs):
    return ':'.join(pcs)

def pretty_hex(b): return ':'.join(f'{i:0>2x}' for i in b)

def split_i(i: int, sb: int, l: int) -> int:
    s1 = i >> sb
    return s1 & ((1 << l) - 1)


# msgs = {
#     'm0i': '08:01:00:02:60:2c:00:47',
#     'm0o': join(
#         '34:81:00:02:60:2c:80:0f:80:05:00:02:80:00:00:0f',
#         '80:00:00:05:80:00:0a:4d:00:0d:00:0b:00:00:00:00',
#         '00:00:90:6f:01:00:00:01:00:11:00:00:00:00:00:00',
#         'ec:13:00:29',
#     ),
#     'm1i': '08:01:00:02:8c:10:00:97',
#     'm1o': join(
#         '18:81:00:02:8c:10:a0:c0:00:03:00:00:00:00:01:18',
#         '00:10:17:30:2c:d3:00:b5:00:00:00:00:00:00:00:00',
#     ),
#     'm2i': join(
#         '18:01:c0:02:a4:10:80:0f:80:05:00:02:80:00:00:0f',
#         '80:00:00:05:80:00:00:ed',
#     ),
#     'm2o': join(
#         '18:81:c0:02:a4:10:80:0f:80:05:00:02:80:00:00:0f',
#         '80:00:00:05:80:00:00',
#     ),
#     'm3i': join(
#         '16:0e:01:00:00:01:00:13:00:00:00:00:01:c0:02:c2',
#         '00:00:ec:15:00:f3',
#     ),
#     'm3o': join(
#         '16:81:c0:02:c2:0e:01:00:00:01:00:13:00:00:00:00',
#         '00:00:ec:15:00:73',
#     ),
#     'm4i': '08:0f:00:00:00:00:00:07',
#     'm4o': '08:8f:00:00:00:00:00:87',
# }
