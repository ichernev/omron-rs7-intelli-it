import msg_parser as msg
from typing_extensions import Self
from dataclasses import dataclass, field
from tools import to_bytes, pretty_hex
import datetime

# NOTES:
# - verify expected consts

BP_ITEM_LEN = 0x0e
BP_START_ADDR = 0x08 * 256 + 0x60

@dataclass
class Exchange:
    pairs: list[msg.MessagePair] = field(default_factory=list)
    req: msg.Message | None = None

    def to_hex_list(self):
        return [pretty_hex(msg.raw)
                for pair in self.pairs
                for msg in (pair.req, pair.res)]

    def get_req(self: Self) -> bytes | None:
        if self.req is None:
            self.req = self._build_next()
        return self.req.raw if self.req else None

    def set_res(self: Self, raw: bytes) -> None:
        if self.req is None:
            raise ValueError("Didn't expect set_repl, req is None")

        build_res = msg.res_builder_from_req(self.req)
        self.pairs.append(msg.MessagePair(req=self.req, res=build_res(raw),
                                             label=self.req.label))
        if self.pairs[-1].label == 'BP':
            assert isinstance(self.pairs[-1].res, msg.MessageResBP)
            for bp_item in self.pairs[-1].res.items:
                print(f"bp -- {bp_item.to_human()}")

        self.req = None

    def _get(self, path) -> int:
        label, io, chunk = path.split('.')

        f_pairs = [p for p in self.pairs if p.label == label]
        assert len(f_pairs) == 1
        assert io in ('in', 'out')
        msg = getattr(f_pairs[0], 'req' if io == 'in' else 'res')
        chunk = msg.get_chunk(chunk)
        assert chunk
        assert len(chunk.raw) == 1
        return chunk.raw[0]

    def _build_next(self) -> msg.Message | None:
        last_req = self.pairs[-1].req if self.pairs else None
        if last_req is None:
            req = msg.Message.make_req(label='M0', payload=to_bytes('02:60:2c'))
        elif last_req.label == 'M0':
            req = msg.Message.make_req(label='M1', payload=to_bytes('02:8c:10'))
        elif last_req.label == 'M1' or last_req.label == 'BP':
            if self._total_bp_fetched() < self._get('M0.out.pend'):
                # fetch more
                req = self._build_req_bp()
            else:
                req = self._build_req_m2()
        elif last_req.label == 'M2':
            req = self._build_req_m3()
        elif last_req.label == 'M3':
            req = msg.Message.make_req(label='M4', payload=to_bytes('00:00:00'))
        elif last_req.label == 'M4':
            req = None

        return req

    def _total_bp_fetched(self: Self) -> int:
        total = 0
        for pair in self.pairs:
            if pair.req.label == 'BP':
                total += pair.req.raw[5] // BP_ITEM_LEN
        return total

    def _build_req_bp(self: Self) -> msg.Message:
        # last is counted from 1, so it's actually upper-bound if 0-based
        unread_ub = self._get('M0.out.last')
        unread_lb = unread_ub - self._get('M0.out.pend')
        fetch_lb = unread_lb + self._total_bp_fetched()
        fetch_ub = min(fetch_lb + 4, unread_ub)

        print(f"-- fetch {fetch_lb} {fetch_ub}")

        fetch_addr = BP_START_ADDR + fetch_lb * BP_ITEM_LEN
        fetch_len = (fetch_ub - fetch_lb) * BP_ITEM_LEN

        return msg.Message.make_req(label='BP',
                                payload=bytes([
                                    fetch_addr // 256,
                                    fetch_addr % 256,
                                    fetch_len]))

    def _build_req_m2(self) -> msg.MessageReqM2:
        l1 = self._get('M0.out.last')
        l2 = self._get('M0.out.last2')
        f1 = self._get('M0.out.fl1')
        f3 = self._get('M0.out.fl3')

        return msg.MessageReqM2.from_fields(f1=f1, l1=l1, l2=l2, f2=f3)

    def _build_req_m3(self) -> msg.MessageReqM3:
        it = self._get('M0.out.it')
        ts: datetime.datetime | None = datetime.datetime.now()
        x: int | None = self._get('M1.out.x')

        # TODO: How does it handle overflow?
        if self._total_bp_fetched() == 0:
            ts = None
            x = None
        return msg.MessageReqM3.from_fields(it=(it+2) % 256, ts=ts, x=x)


def compare(a, b, msg):
    ph = pretty_hex
    print(f'comparing {ph(a[:5])} {len(a)} {ph(b[:5])} {len(b)} {msg}')
    print(f'{ph(a)}')
    print(f'{ph(b)}')
    if a != b:
        for ax, bx in zip(a, b):
            if ax == bx:
                print('   ', end='')
            else:
                print('XX ', end='')
    print(f'{a == b}')


def simulate(logfile: str):
    from pathlib import Path
    import json

    msgs = None
    with open(logfile, 'r') as lf:
        msgs = json.load(lf)

    t = msg.Transaction.from_hex_list(msgs, merge_bp=False)

    e = Exchange()
    idx = 0
    while True:
        req = e.get_req()
        if req is None:
            break
        if idx >= len(t.pairs):
            print(f"out-of-bounds idx: {idx}")
            break
        compare(t.pairs[idx].req.raw, req, f'{idx} {t.pairs[idx].label}')
        e.set_res(t.pairs[idx].res.raw)
        idx += 1

    assert idx == len(t.pairs)

    hex_list = e.to_hex_list()
    fn = f'exchange_{datetime.datetime.now().isoformat()}.json'
    Path(fn).write_text(
        json.dumps(e.to_hex_list(), indent=2))
    print(f"log written to {fn}")


if __name__ == '__main__':
    import sys
    simulate(sys.argv[1])
