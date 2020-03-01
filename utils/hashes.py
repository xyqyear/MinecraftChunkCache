import mmh3
import struct


def hash32(data: bytes) -> bytes:
    return struct.pack('i', mmh3.hash(data))
