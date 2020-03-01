from typing import *

from quarry.types.nbt import TagRoot

from utils.buffers import CustomOriginalBuffer114


class Bits:
    def __init__(self, value):
        self.value = value

    def get(self, index: int) -> bool:
        if self.value & (1 << index):
            return True
        else:
            return False

    def put(self, index: int, flag: bool):
        if flag:
            self.value |= 1 << index
        else:
            self.value &= ~(1 << index)


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
        self.bitmask = Bits(self.buff.unpack_varint())
        self.heightmap: TagRoot = self.buff.unpack_nbt()
        if self.full:
            self.biomes: bytes = self.buff.read(4*1024)  # biomes
        self.section_length: int = self.buff.unpack_varint()  # section_length
        self.sections: List[bytes] = self.buff.unpack_chunk(self.bitmask.value)
        self.block_entities = [self.buff.unpack_nbt() for _ in range(self.buff.unpack_varint())]

    def pack_packet_data(self):
        data1: bytes = self.buff.pack('ii?', self.x, self.z, self.full)
        data_bitmask: bytes = self.buff.pack_varint(self.bitmask.value)
        data_heightmap: bytes = self.buff.pack_nbt(self.heightmap)
        data_biomes: bytes = self.biomes if self.full else b''
        data_sections: bytes = b''.join([i for i in self.sections if i])
        data_section_length: bytes = self.buff.pack_varint(len(data_sections))
        data_block_entity_num: bytes = self.buff.pack_varint(len(self.block_entities))
        data_block_entities: bytes = b''.join(self.buff.pack_nbt(entity) for entity in self.block_entities)

        packet_data = data1 + data_bitmask + data_heightmap + data_biomes + data_section_length \
                            + data_sections + data_block_entity_num + data_block_entities

        return packet_data
