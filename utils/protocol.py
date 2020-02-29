import socket
import struct

# 1.7 buffer is good enough to recognize packet
from quarry.types.buffer.v1_7 import Buffer1_7
from quarry.types.buffer.v1_14 import Buffer1_14
from quarry.types.buffer import BufferUnderrun

from typing import *


def no_process(buff: Buffer1_7) -> bytes:
    return Buffer1_7.pack_packet(buff.buff)


def iter_packets_from_socket(source: socket.socket) -> Iterator[Buffer1_7]:
    """
    return: Buffer1_7 (without the first 'length' varint)
    separate packets from data received
    """
    recv_buff = Buffer1_7()
    while True:
        # handling network outside of network.py, but can not figure out a better way of doing this
        data = source.recv(1024)
        if not data:
            break

        # reference: quarry.net.protocol
        recv_buff.add(data)
        while True:
            recv_buff.save()
            try:
                packet_buff: Buffer1_7 = recv_buff.unpack_packet(Buffer1_7)
                yield packet_buff
            except BufferUnderrun:
                recv_buff.restore()
                break


def unpack_original_chunk_data_1_15(data: bytes) -> Tuple[int, int, List[bytes]]:
    """
    return: x, y, sections (a list of bytes, len=16)

    origin:
    https://github.com/barneygale/quarry/blob/master/docs/data_types/chunks.rst
    """
    buff = CustomOriginalBuffer114(data)

    x, z, full = buff.unpack('ii?')
    bitmask = buff.unpack_varint()
    buff.unpack_nbt()  # heightmap
    if full:
        buff.read(4*1024)  # biomes
    buff.unpack_varint_bytes()  # section_length
    sections: List[bytes] = buff.unpack_chunk(bitmask)
    for _ in range(buff.unpack_varint()):
        buff.unpack_nbt()

    return x, z, sections


class CustomOriginalBuffer114(Buffer1_14):
    def unpack_chunk_section_palette(self, value_width):
        """
        origin: quarry.types.buffer.v1_13.Buffer1_13
        """
        if value_width > 8:
            return
        else:
            palette_num = self.unpack_varint()
            palette_bytes = b''
            for _ in range(palette_num):
                palette_bytes += self.unpack_varint_bytes()

            palette_num_bytes = self.pack_varint(palette_num)
            return palette_num_bytes + palette_bytes

    def unpack_varint_bytes(self):
        """
        # origin: quarry.types.buffer.v1_7.Buffer1_7
        """

        varint_bytes = b''
        for _ in range(10):
            b = self.read(1)
            varint_bytes += b
            u_char = struct.unpack("B", b)[0]
            if not u_char & 0x80:
                break
        return varint_bytes

    def unpack_chunk_section(self, overworld=True):
        """
        Unpacks a chunk section. Returns bytes.
        origin: quarry.types.buffer.v1_9.Buffer1_9
        """

        non_air_bytes = self.read(2)
        value_width_bytes = self.read(1)
        value_width = struct.unpack('B', value_width_bytes)[0]
        palette = self.unpack_chunk_section_palette(value_width)
        array = self.unpack_chunk_section_array(value_width)

        return non_air_bytes + value_width_bytes + palette + array
