from dataclasses import dataclass, field
from typing import Literal, Callable
from tools import ints, add_checksum, to_bytes, pretty_hex, s_checksum, split_i
import datetime

def b(s): return bytes.fromhex(s.replace(':', ''))

io_t = Literal['in', 'out', 'other']

def enc_ts(ts: datetime.datetime) -> bytes:
    return bytes([
        ts.month,
        ts.year - 2000,
        ts.hour,
        ts.day,
        ts.second,
        ts.minute,
    ])

def dec_ts(bts: bytes) -> datetime.datetime:
    assert len(bts) == 6
    month, year, hour, day, second, minute = bts
    return datetime.datetime(year=year+2000, month=month, day=day,
                             hour=hour, minute=minute, second=second)

@dataclass(kw_only=True)
class Chunk():
    start: int
    sz: int
    raw: bytes
    label: str

    @property
    def end(self): return self.start + self.sz

    @classmethod
    def builder(cls, raw: bytes):
        def init(start: int, sz: int, label: str):
            return cls(start=start,
                       sz=sz,
                       raw=raw[start:start+sz],
                       label=label)
        return init

    def to_json(self, short: bool = False):
        return {
            'raw': pretty_hex(self.raw),
            'int': list(self.raw),
            **({
                'start': self.start,
                'sz': self.sz,
                'label': self.label,
            } if not short else {}),
        }

    def to_i(self):
        res = 0
        for b in self.raw:
            res *= 256
            res += b
        return res

@dataclass(kw_only=True)
class ProtoChunk():
    start: int | None = None
    sz: int
    label: str

@dataclass(kw_only=True)
class Message():
    io: io_t
    raw: bytes
    chunks: list[Chunk] = field(default_factory=list)
    label: str

    def to_json(self):
        return {
            'io': self.io,
            'raw': pretty_hex(self.raw),
            'label': self.label,
            **{chunk.label: chunk.to_json() for chunk in self.chunks}
        }

    def get_chunk(self, label: str) -> Chunk | None:
        for chunk in self.chunks:
            if chunk.label == label:
                return chunk
        return None

    @classmethod
    def build(cls, raw: bytes, chunks: list[ProtoChunk] = [], label: str | None = None, io: io_t | None = None, complete: bool = False):
        cbuild = Chunk.builder(raw)
        rchunks: list[Chunk] = []
        last_end = 0
        if not complete:
            rchunks.append(cbuild(
                start=0,
                sz=1,
                label='$msg_size',
            ))
            rchunks.append(cbuild(
                start=1,
                sz=1,
                label='$msg_io',
            ))
            last_end = 2
        for i, pchunk in enumerate(chunks):
            rchunks.append(cbuild(
                start=pchunk.start if pchunk.start is not None else last_end,
                sz=pchunk.sz,
                label=pchunk.label))
            last_end = rchunks[-1].end
        if not complete:
            rchunks.append(cbuild(
                start=len(raw) - 1,
                sz=1,
                label='$msg_cs',
            ))
        rchunks.sort(key=lambda ch: ch.start)
        cls.add_const(rchunks, cbuild)
        return cls(raw=raw,
                   chunks=rchunks,
                   **({'label': label} if label is not None else {}),  # type: ignore[arg-type]
                   **({'io': io} if io is not None else {}),  # type: ignore[arg-type]
                   )

    @classmethod
    def add_const(cls, rchunks: list[Chunk], cbuild: Callable):
        const_id = 0
        start = 0
        cchunks: list[Chunk] = []
        for chunk in rchunks:
            if start < chunk.start:
                cchunks.append(cbuild(
                    start=start,
                    sz=chunk.start-start,
                    label=f'$c:{const_id:0>2}',
                ))
                const_id += 1
            start = chunk.end
        rchunks.extend(cchunks)
        rchunks.sort(key=lambda ch: ch.start)

    @classmethod
    def make_req(cls, label: str,
                 payload: bytes):
        while len(payload) < 4:
            # pad to 4
            payload = bytes([0, *payload])
        header = 0x01 if any(payload) else 0x0f
        length = len(payload) + 4

        return Message.build(io='in', label=label,
                             raw=add_checksum(bytes([length, header, *payload])))


@dataclass(kw_only=True)
class MessageResM0(Message):
    io: io_t = 'out'
    label: str = 'M0'

    @classmethod
    def from_bytes(cls, raw: bytes):
        return cls.build(
            io=cls.io,
            raw=raw, chunks=[
                ProtoChunk(start=0x08, sz=1, label='fl1'),
                ProtoChunk(start=0x09, sz=1, label='last'),
                ProtoChunk(start=0x0c, sz=1, label='fl2'),
                ProtoChunk(start=0x0d, sz=1, label='pend'),
                ProtoChunk(start=0x13, sz=1, label='last2'),
                ProtoChunk(start=0x14, sz=1, label='fl3'),
                ProtoChunk(start=0x29, sz=1, label='it'),
                ProtoChunk(start=0x30, sz=2, label='cs'),
            ])

@dataclass(kw_only=True)
class MessageResM1(Message):
    io: io_t = 'out'
    label: str = 'M1'

    @classmethod
    def from_bytes(cls, raw: bytes):
        return cls.build(
            io=cls.io,
            raw=raw, chunks=[
                ProtoChunk(start=0x0e, sz=6, label='ts'),
                ProtoChunk(start=0x14, sz=1, label='x'),
                ProtoChunk(start=0x15, sz=1, label='cs'),
            ])

@dataclass(kw_only=True)
class MessageBPItem(Message):
    @dataclass(kw_only=True)
    class BPHuman:
        sys: int
        dia: int
        pulse: int
        ts: datetime.datetime
        pos: int

    io: io_t = 'other'

    @classmethod
    def from_bytes(cls, idx: int, raw: bytes):
        return cls.build(
            label=f'bp-item:{idx:0>2d}',
            raw=raw, chunks=[
                ProtoChunk(start=0x00, sz=1, label='dia'),
                ProtoChunk(start=0x01, sz=1, label='sys'),
                ProtoChunk(start=0x02, sz=1, label='fl1'),
                ProtoChunk(start=0x03, sz=1, label='pulse'),
                ProtoChunk(start=0x04, sz=4, label='ts'),
                ProtoChunk(start=0x08, sz=1, label='fl2'),
                ProtoChunk(start=0x0b, sz=1, label='pos'),
                ProtoChunk(start=0x0c, sz=2, label='cs'),
            ],
            complete=True)

    def to_human(self):
        # TODO(Iskren): flags!
        tsi = self.get_chunk("ts").to_i()
        tsb = f'{tsi:0>32b}'
        month = split_i(tsi, 26, 4)
        day = split_i(tsi, 21, 5)
        hour = split_i(tsi, 16, 5)
        minute = split_i(tsi, 6, 6)
        sec = split_i(tsi, 0, 6)
        ts = datetime.datetime(year=datetime.datetime.now().year, month=month, day=day, hour=hour, minute=minute, second=sec)
        # print(f"{month} {day} {hour} {minute} {sec}")
        # print(f"ts {tsb[0:8]} {tsb[8:16]} {tsb[16:24]} {tsb[24:32]}")
        return self.BPHuman(
            sys=self.get_chunk('sys').to_i() + 25,
            dia=self.get_chunk('dia').to_i(),
            pulse=self.get_chunk('pulse').to_i(),
            ts=ts,
            pos=self.get_chunk('pos').to_i(),
        )


@dataclass(kw_only=True)
class MessageResBP(Message):
    io: io_t = 'out'
    label: str = 'BP'
    items: list[MessageBPItem]

    def to_json(self):
        return {
            'label': self.label,
            'items': [item.to_json() for item in self.items],
        }

    @classmethod
    def from_bytes(cls, raw: bytes):
        sz = raw[5] // 0x0e
        return cls(
            raw=raw,
            items=[MessageBPItem.from_bytes(i, raw[0x06+i*0x0e:0x06+(i+1)*0x0e])
                   for i in range(sz)]
        )


    def merge(self, other):
        self.items.extend(other.items)


@dataclass(kw_only=True)
class MessageReqM2(Message):
    io: io_t = 'in'
    label: str = 'M2'

    @classmethod
    def from_bytes(cls, raw: bytes):
        assert len(raw) == raw[0x05] + 8
        return cls.build(
            raw=raw,
            chunks=[
                ProtoChunk(start=0x05, sz=1, label='ilen'),
                ProtoChunk(start=0x08, sz=1, label='fl1'),
                ProtoChunk(start=0x09, sz=1, label='last'),
                ProtoChunk(start=0x13, sz=1, label='last2'),
                ProtoChunk(start=0x14, sz=1, label='fl2'),
            ])


    @classmethod
    def from_fields(cls, f1: int, l1: int, l2: int, f2: int):
        ilen = 0x10
        return cls.make_req(label='M2', payload=to_bytes(
            # 18:01
            'c0:02:a4', ilen, '80:0f', f1, l1, '00:02:80:00:00:0f',
            '80:00:00', l2, f2, '00',
        ))

@dataclass(kw_only=True)
class MessageReqM3(Message):
    io: io_t = 'in'
    label: str = 'M3'

    @classmethod
    def from_bytes(cls, raw: bytes):
        ilen = raw[0x05]

        assert ilen in (0x0e, 0x1e)
        assert len(raw) == ilen + 8
        return cls.build(
            raw=raw,
            chunks=[
                ProtoChunk(start=0x05, sz=1, label='ilen'),
                ProtoChunk(start=0x0b, sz=1, label='it'),
                ProtoChunk(start=0x12, sz=2, label='cs1'),
                *([
                    ProtoChunk(start=0x1c, sz=6, label='ts'),
                    ProtoChunk(start=0x22, sz=1, label='x'),
                    ProtoChunk(start=0x23, sz=1, label='cs2'),
                ] if ilen == 0x1e else []),
            ])


    @classmethod
    def from_fields(cls, it: int, ts: datetime.datetime | None, x: int | None):
        header = to_bytes('c0:02:c2', 0x1e if ts else 0x0e)
        pc1_a = to_bytes('01:00:00:01:00', it, '00:00:00:00:00:00')
        pc1 = to_bytes(pc1_a, (257 - sum(pc1_a) % 256) % 256, it + 2)
        if ts is not None and x is not None:
            pc2_a = to_bytes('a0:c0:00:03:00:00:00:00', enc_ts(ts))
            pc2 = to_bytes(pc2_a, x, s_checksum(pc2_a)) if ts else None
        else:
            pc2 = None
        return cls.make_req(label='M3', payload=to_bytes(header, pc1, pc2))


@dataclass(kw_only=True)
class MessagePair():
    req: Message
    res: Message
    label: str

    def to_json(self):
        return {
            'req': self.req.to_json(),
            'res': self.res.to_json(),
            'label': self.label,
        }

@dataclass(kw_only=True)
class Transaction():
    pairs: list[MessagePair]

    def to_json(self):
        return {pair.label: pair.to_json() for pair in self.pairs}

    @classmethod
    def from_hex_list(cls, hex_list: list[str], merge_bp: bool = True):
        pairs: list[MessagePair] = []
        for req_s, res_s in zip(hex_list[::2], hex_list[1::2]):
            req_b = b(req_s)
            res_b = b(res_s)
            if req_b[2:6] == b('00:02:60:2c'):
                label = 'M0'
                pairs.append(MessagePair(
                    label=label,
                    req=Message.build(io='in', label=label, raw=req_b),
                    res=MessageResM0.from_bytes(raw=res_b)
                ))
            elif req_b[2:6] == b('00:02:8c:10'):
                label = 'M1'
                pairs.append(MessagePair(
                    label=label,
                    req=Message.build(io='in', label=label, raw=req_b),
                    res=MessageResM1.from_bytes(raw=res_b),
                ))
            elif req_b[2] == 0x0 and 0x8 <= req_b[3] and req_b[3] <= 0xd:
                label = 'BP'
                mp = MessagePair(
                    label='BP',
                    req=Message.build(io='in', label=label, raw=req_b),
                    res=MessageResBP.from_bytes(raw=res_b),
                )
                if pairs[-1].label != 'BP' or not merge_bp:
                    pairs.append(mp)
                else:
                    # we combine all the BP measurements, and let the first req
                    # (it will be "wrong' but we don't really care.
                    assert isinstance(pairs[-1].res, MessageResBP)
                    pairs[-1].res.merge(mp.res)
            elif req_b[2:6] == b('c0:02:a4:10'):
                label = 'M2'
                assert req_b[2:-2] == res_b[2:-2]
                pairs.append(MessagePair(
                    label=label,
                    req=MessageReqM2.from_bytes(raw=req_b),
                    res=Message.build(io='out', label=label, raw=res_b),
                ))
            elif req_b[2:5] == b('c0:02:c2'):
                label = 'M3'
                assert req_b[2:-2] == res_b[2:-2]
                pairs.append(MessagePair(
                    label=label,
                    req=MessageReqM3.from_bytes(raw=req_b),
                    res=Message.build(io='out', label=label, raw=res_b),
                ))
            elif req_b[2:6] == b('00:00:00:00'):
                label = 'M4'
                assert req_b[2:-2] == res_b[2:-2]
                pairs.append(MessagePair(
                    label=label,
                    req=Message.build(io='in', label=label, raw=req_b),
                    res=Message.build(io='out', label=label, raw=res_b),
                ))
            else:
                raise ValueError("Failed to match message " + pretty_hex(req_b[:6]))
        return cls(pairs=pairs)


def res_builder_from_req(req: Message):
    if req.label == 'M0':
        return lambda raw: MessageResM0.from_bytes(raw=raw)
    elif req.label == 'M1':
        return lambda raw: MessageResM1.from_bytes(raw=raw)
    elif req.label == 'BP':
        return lambda raw: MessageResBP.from_bytes(raw=raw)
    elif req.label == 'M2':
        return lambda raw: Message.build(io='out', label='M2', raw=raw)
    elif req.label == 'M3':
        return lambda raw: Message.build(io='out', label='M3', raw=raw)
    elif req.label == 'M4':
        return lambda raw: Message.build(io='out', label='M4', raw=raw)


if __name__ == '__main__':
    import sys
    import json
    from pathlib import Path
    if len(sys.argv) <= 1:
        print("msg_parser.py FILE.json", file=sys.stderr)
        sys.exit(1)

    file = sys.argv[1]
    hex_lines = json.loads(Path(file).read_bytes())
    trans = Transaction.from_hex_list(hex_lines)
    print(json.dumps(trans.to_json(), indent=2))
