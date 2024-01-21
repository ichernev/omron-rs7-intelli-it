from dataclasses import dataclass, field
from typing import Literal
from tools import ints

def b(s): return bytes.fromhex(s.replace(':', ''))
def pretty_hex(b): return ':'.join(f'{i:0>2x}' for i in b)

io_t = Literal['in', 'out', 'other']

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

    def to_json(self, short: bool):
        return {
            'raw': pretty_hex(self.raw),
            'int': list(self.raw),
            **({
                'start': self.start,
                'sz': self.sz,
                'end': self.end,
                'label': self.label,
            } if not short else {}),
        }

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
            **{chunk.label: chunk.to_json(short=True) for chunk in self.chunks}
        }

    @classmethod
    def build(cls, raw: bytes, chunks: list[ProtoChunk] = [], label: str | None = None, io: io_t | None = None):
        cbuild = Chunk.builder(raw)
        rchunks: list[Chunk] = []
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
        rchunks.append(cbuild(
            start=len(raw) - 1,
            sz=1,
            label='$msg_cs',
        ))
        return cls(raw=raw,
                   chunks=rchunks,
                   **({'label': label} if label is not None else {}),  # type: ignore[arg-type]
                   **({'io': io} if io is not None else {}),  # type: ignore[arg-type]
                   )


@dataclass(kw_only=True)
class MessageResM0(Message):
    io: io_t = 'out'
    label: str = 'M0'

    @classmethod
    def from_bytes(cls, raw: bytes):
        return cls.build(
            io=cls.io,
            raw=raw, chunks=[
                ProtoChunk(start=0x09, sz=1, label='last'),
                ProtoChunk(start=0x0c, sz=1, label='pend_pref'),
                ProtoChunk(start=0x0d, sz=1, label='pend'),
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
                ProtoChunk(start=0x0f, sz=6, label='ts'),
                ProtoChunk(start=0x14, sz=2, label='cs'),
            ])

@dataclass(kw_only=True)
class MessageBPItem(Message):
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
            ])


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
                ProtoChunk(start=0x09, sz=1, label='last'),
                ProtoChunk(start=0x13, sz=1, label='last2'),
            ])


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
                    ProtoChunk(start=0x22, sz=2, label='cs2'),
                ] if ilen == 0x1e else []),
            ])


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
        return [pair.to_json() for pair in self.pairs]

    @classmethod
    def from_hex_list(cls, hex_list: list[str]):
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
            elif req_b[2:4] == b('00:08'):
                label = 'BP'
                pairs.append(MessagePair(
                    label='BP',
                    req=Message.build(io='in', label=label, raw=req_b),
                    res=MessageResBP.from_bytes(raw=res_b),
                ))
            elif req_b[2:6] == b('c0:02:a4:10'):
                label = 'M2'
                assert req_b[2:-2] == res_b[2:-2]
                pairs.append(MessagePair(
                    label=label,
                    req=MessageReqM2.build(raw=req_b),
                    res=Message.build(io='out', label=label, raw=res_b),
                ))
            elif req_b[2:5] == b('c0:02:c2'):
                label = 'M3'
                assert req_b[2:-2] == res_b[2:-2]
                pairs.append(MessagePair(
                    label=label,
                    req=MessageReqM3.build(raw=req_b),
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

    # msgs = [
    #     MessagePair(
    #         label='M0',
    #         req=Message.build(io='in', label='M0', raw=b('08:01:00:02:60:2c:00:47')),
    #         res=MessageResM0.from_bytes(raw=b('34:81:00:02:60:2c:80:0f:00:0b:00:02:80:00:00:0f:80:00:00:0b:00:00:0a:4d:00:0d:00:0b:00:00:00:00:00:00:90:6f:01:00:00:01:00:17:00:00:00:00:00:00:e6:19:00:2f'))
    #     ),
    #     MessagePair(
    #         label='M1',
    #         req=Message.build(io='in', label='M1', raw=b('08:01:00:02:8c:10:00:97')),
    #         res=MessageResM1.from_bytes(raw=b('18:81:00:02:8c:10:a0:c0:00:03:00:00:00:00:01:18:12:14:26:38:ff:00:00:9a'))
    #     ),
    #     MessagePair(
    #         label='BP',
    #         req=Message.build(io='in', label='BP', raw=b('08:01:00:08:de:1c:00:c3')),
    #         res=MessageResBP.from_bytes(raw=b('24:81:00:08:de:1c:53:5c:58:47:06:92:1b:b2:01:00:00:0a:41:be:4c:64:58:46:06:92:0b:fb:00:00:00:0b:08:f7:00:10')),
    #     )
    # ]


