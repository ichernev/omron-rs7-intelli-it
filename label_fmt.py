import argparse
import json
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
    return parser.parse_args(args)

def load_data(inp: str):
    data = {}
    if Path(inp).is_dir():
        for file in sorted(Path(inp).glob('*.json')):
            id = file.name[:-5].replace('.', ':')
            data[id] = json.loads(file.read_bytes())
    else:
        assert file.endswith('.json')
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
        self._items = []

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

    def show(self, table: bool = True):
        if table:
            len_jpaths = [len('.'.join(path)) for path, data in self._items]
            space = max(len_jpaths)
            for path, data in self._items:
                jpath = '.'.join(path)
                padded = jpath + ' ' * (space - len(jpath))
                print(f"{padded} {data['raw']}")
        else:
            for path, data in self._items:
                print(f"{'.'.join(path)} {data['raw']}")

    def summary(self):
        nitems = len(self._items)
        uniq = len(set(data['raw'] for _, data in self._items))

        print(f"items={nitems} unique={uniq}")

def main(opts):
    data = load_data(opts.input)

    if opts.debug:
        print(json.dumps(data, indent=2))
        return
    obs = Observer(opts.filter)
    iter_leafs(data, level=0, cb=obs)
    obs.show()
    if opts.summary:
        obs.summary()

if __name__ == '__main__':
    import sys
    main(parse_args(sys.argv[1:]))
