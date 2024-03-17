import argparse
import json
import re
from pathlib import Path
from typing import Callable

def parse_args(args):
    parser = argparse.ArgumentParser("display message/chunk labels in a nicer way")
    parser.add_argument('-i', '--input', type=str, default="parsed2",
                        help="directory or file with chunked messages")
    parser.add_argument('--debug', action='store_true',
                        help="just print all data as json")
    parser.add_argument('-f', '--filter', type=str, action='append',
                        help='key=val1,val2 where key in (id,io,msg,label,path)')
    parser.add_argument('--summary', action='store_true',
                        help="Display overall stats")
    parser.add_argument('--addr', action='store_true',
                        help="Display chunk address")
    parser.add_argument('--line', type=int,
                        help="put a few matches per line (matching that many path components)")
    parser.add_argument('--int', action='store_true',
                        help="Output ints, not hex")
    parser.add_argument('--table', action='store_true',
                        help="Align columns")
    return parser.parse_args(args)

def load_data(inp: str):
    data = {}
    if Path(inp).is_dir():
        for file in sorted(Path(inp).glob('*.json')):
            id = file.name[:-5].replace('.', ':')
            data[id] = json.loads(file.read_bytes())
    else:
        assert inp.endswith('.json')
        file = Path(inp)
        id = file.name[:-5].replace('.', ':')
        data[id] = json.loads(file.read_bytes())
    return data

iter_exc = ('io', 'raw', 'label')
def iter_leafs(data: dict, level: int, cb: Callable, path: list[str] = []):
    if level < 4:
        # 'BP' has multiple sub-messages
        if level == 3 and 'items' in data:
            for i, item in enumerate(data['items']):
                iter_leafs(item, level=level, cb=cb, path=[*path, f'{i:0>2}'])
        else:
            for k, v in data.items():
                if k in iter_exc:
                    continue
                iter_leafs(v, level=level+1, cb=cb, path=[*path, k])
    else:
        cb(path, data)

class Observer():
    def __init__(self, filters: list[str]):
        self.filters = filters
        self._items: list[tuple[list[str], dict]] = []

    def __call__(self, path: list[str], leaf: dict):
        bpid = None
        if len(path) == 4:
            id, msg, io, label = path
        else:
            id, msg, io, bpid, label = path

        for filter in self.filters:
            k, mss = filter.split('=', 1)
            ms = mss.split(',')
            if k == 'id' and id not in ms:
                return
            if k == 'io' and io not in ms:
                return
            if k == 'msg' and msg not in ms:
                return
            if k == 'label' and label not in ms:
                return
            if k == 'path' and not re.match(ms[0].replace('*', '.*'), '.'.join(path)):
                return
        self._items.append((path, leaf))
        # print(f'{".".join(path)}  {leaf["raw"]}')

    def show(self, pad: bool = True, pad_dirs: str = '<', addr: bool = False, line: int | None = None, ints: bool = False):
        tdata = []
        if line is None:
            for path, data in self._items:
                jpath = '.'.join(path)
                d_raw = [data['raw']] if not ints else list(map(str, data['int']))
                if addr:
                    addr_s = f"{data['start']:0>2x}:{data['start'] + data['sz']:0>2x}"
                    items = [jpath, addr_s, *d_raw]
                else:
                    items = [jpath, *d_raw]
                tdata.append(items)
        else:
            last_match = None
            for path, data in self._items:
                jpath = '.'.join(path)
                d_raw = [data['raw']] if not ints else list(map(str, data['int']))
                addr_s = f" {data['start']:0>2x}:{data['start'] + data['sz']:0>2x}" if addr else ''

                match = '.'.join(path[:line])
                if match == last_match:
                    if addr_s:
                        tdata[-1].append(addr_s)
                    tdata[-1].extend(d_raw)
                else:
                    last_match = match
                    if addr_s:
                        tdata.append([match, addr_s, *d_raw])
                    else:
                        tdata.append([match, *d_raw])
        max_col_w = [0] * (max(len(tdata_line) for tdata_line in tdata)
                           if tdata
                           else 1)
        for tdata_line in tdata:
            for i, item in enumerate(tdata_line):
                max_col_w[i] = max(max_col_w[i], len(item))

        for i, tdata_line in enumerate(tdata):
            res_line = []
            for i, item in enumerate(tdata_line):
                padding = ' ' * (max_col_w[i] - len(item)) if pad else ''
                pad_dir = pad_dirs[i] if i < len(pad_dirs) else pad_dirs[-1]
                res_line.append((padding + item) if pad_dir == '>' else (item + padding))
            print(' '.join(res_line))

        self._tdata = tdata
        self._max_col_w = max_col_w

    def summary(self, pad: bool = True):
        tdata = self._tdata
        max_col_w = self._max_col_w
        items = [f'{len(self._tdata)}']
        for col in range(1, len(max_col_w)):
            uniq = len(set(tdata[i][col] for i in range(len(tdata))
                           if col < len(tdata[i])))
            items.append(f'{uniq}')

        line = []
        for i, item in enumerate(items):
            padding = ' ' * (max_col_w[i] - len(item)) if pad else ''
            line.append(padding + item)
        print(' '.join(line))

def main(opts):
    data = load_data(opts.input)

    if opts.debug:
        print(json.dumps(data, indent=2))
        return
    obs = Observer(opts.filter or [])
    iter_leafs(data, level=0, cb=obs)
    obs.show(pad=opts.table, addr=opts.addr, line=opts.line, ints=opts.int)
    if opts.summary:
        obs.summary()

if __name__ == '__main__':
    import sys
    main(parse_args(sys.argv[1:]))
