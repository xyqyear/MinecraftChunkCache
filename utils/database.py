"""
tests for 1M number data
leveldb:
cpu: 16.5%, disk-io: 6mb/s,   disk-space: 27.7MB
lsm:
cpu: 16.9%, disk-io: 2.2mb/s, disk-space: 50.2MB
"""
import os

try:
    # windows: conda install python-leveldb
    import leveldb as db_lib
except ImportError:
    import lsm as db_lib


def makedir(path: str):
    if db_lib.__name__ == 'lsm':
        path = os.path.split(path)[0]
    if not os.path.exists(path):
        os.makedirs(path)


if db_lib.__name__ == 'leveldb':
    class Database:
        def __init__(self, path: str):
            makedir(path)
            self.db = db_lib.LevelDB(path)

        def get(self, key):
            try:
                return self.db.Get(key)
            except KeyError:
                return b''

        def put(self, key, value):
            self.db.Put(key, value)

        def delete(self, key):
            try:
                self.db.Delete(key)
                return True
            except KeyError:
                return False

elif db_lib.__name__ == 'lsm':
    class Database:
        def __init__(self, path: str):
            makedir(path)
            self.db = db_lib.LSM(path)

        def get(self, key):
            return self.db[key]

        def put(self, key, value):
            self.db[key] = value

        def delete(self, key):
            del self.db[key]
            return True
