from typing import *

from quarry.types.nbt import TagRoot

from utils.buffers import CustomVanillaBuffer114


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
    # vanilla protocol
    x: int
    z: int
    full: bool
    bitmask: Bits
    heightmap: TagRoot
    biomes: bytes
    section_length: int
    sections: List[bytes]
    block_entities: List[TagRoot]

    # custom protocol

    # if 0, this is not a full chunk. the biomes data will be empty and ignored.
    # if 1, this is a full chunk and as well as a new chunk
    # the biomes data should be 4096 bytes long, and client should force save the data
    # if 2, the biomes data will be empty, but client should find them in the cache.
    # Unsigned Byte
    biomes_mode: int

    # with bits set to 1 for every chunk that exist in the original packet
    # and the client should find those chunks in their cache
    # VarInt
    cached_section_mask: int

    def __init__(self, data: bytes):
        self.buff = CustomVanillaBuffer114(data)

    def unpack_custom_packet_data(self):
        pass

    def pack_custom_packet_data(self):
        pass

    def unpack_vanilla_packet_data(self):
        """
        origin:
        https://github.com/barneygale/quarry/blob/master/docs/data_types/chunks.rst
        """
        self.x, self.z, self.full = self.buff.unpack('ii?')
        self.bitmask = Bits(self.buff.unpack_varint())
        self.heightmap = self.buff.unpack_nbt()
        if self.full:
            self.biomes = self.buff.read(4*1024)  # biomes
        self.section_length = self.buff.unpack_varint()  # section_length
        self.sections = self.buff.unpack_chunk(self.bitmask.value)
        self.block_entities = [self.buff.unpack_nbt() for _ in range(self.buff.unpack_varint())]

    def pack_vanilla_packet_data(self):
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
