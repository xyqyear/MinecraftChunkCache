import socket

from quarry.types.buffer import BufferUnderrun
from quarry.types.buffer.v1_7 import Buffer1_7
from quarry.types.nbt import TagRoot

from typing import *

from utils.buffers import CustomBaseBuffer, CustomOriginalBuffer114


def no_process(buff: bytes) -> bytes:
    return buff


def iter_packets_from_socket(source: socket.socket) -> Iterator[bytes]:
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
                packet = recv_buff.unpack_packet(CustomBaseBuffer)
                yield packet
            except BufferUnderrun:
                recv_buff.restore()
                break


class PacketChunkData:
    def __init__(self, data: bytes):
        """
        origin:
        https://github.com/barneygale/quarry/blob/master/docs/data_types/chunks.rst
        """
        self.buff = CustomOriginalBuffer114(data)
        self.x: int
        self.z: int
        self.full: bool
        self.x, self.z, self.full = self.buff.unpack('ii?')
        self.bitmask: int = self.buff.unpack_varint()
        self.heightmap: TagRoot = self.buff.unpack_nbt()
        if self.full:
            self.biomes: bytes = self.buff.read(4*1024)  # biomes
        self.section_length: int = self.buff.unpack_varint()  # section_length
        self.sections: List[bytes] = self.buff.unpack_chunk(self.bitmask)
        self.block_entities = [self.buff.unpack_nbt() for _ in range(self.buff.unpack_varint())]

    def pack_packet_data(self):
        data1: bytes = self.buff.pack('ii?', self.x, self.z, self.full)
        data_bitmask: bytes = self.buff.pack_varint(self.bitmask)
        data_heightmap: bytes = self.buff.pack_nbt(self.heightmap)  # added in 1.14
        data_biomes: bytes = self.biomes if self.full else b''  # changed in 1.15
        data_sections: bytes = b''.join([i for i in self.sections if i])
        data_section_length: bytes = self.buff.pack_varint(len(data_sections))
        data_block_entity_num: bytes = self.buff.pack_varint(len(self.block_entities))
        data_block_entities: bytes = b''.join(self.buff.pack_nbt(entity) for entity in self.block_entities)

        packet_data = data1 + data_bitmask + data_heightmap + data_biomes + data_section_length \
                            + data_sections + data_block_entity_num + data_block_entities

        return packet_data
