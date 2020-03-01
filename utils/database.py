# using lmdb since installing leveldb on windows is a nightmare
import lmdb
import sys

WINDOWS_BASE_MAP_SIZE = 1024**2
LINUX_BASE_MAP_SIZE = 1024**3


class Database:
    env: lmdb.Environment
    txn: lmdb.Transaction
    map_size = 0
    if sys.platform == 'linux':
        base_map_size = LINUX_BASE_MAP_SIZE
    else:
        base_map_size = WINDOWS_BASE_MAP_SIZE

    def __init__(self, path: str):
        self.env = lmdb.open(path)
        self.increase_map_size()
        self.txn = self.env.begin(write=True)

    def save(self):
        self.env.sync()

    def put(self, key: bytes, value: bytes) -> bool:
        try:
            return self.txn.put(key, value)
        except lmdb.MapFullError:
            self.txn.abort()
            self.increase_map_size()
            self.txn = self.env.begin(write=True)
            return self.put(key, value)

    def get(self, key: bytes) -> bytes:
        return self.txn.get(key)

    def delete(self, key: bytes) -> bool:
        return self.delete(key)

    def increase_map_size(self):
        self.map_size += self.base_map_size
        self.env.set_mapsize(self.map_size)
