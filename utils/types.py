from typing import *

from quarry.types.nbt import TagRoot
from quarry.types.buffer.v1_7 import Buffer1_7

from utils.buffers import CustomVanillaBuffer114, VarIntBuffer, BaseBuffer


class Bits:
    def __init__(self, value=0):
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

    @staticmethod
    def from_list(_list: list):
        bitmask = 0
        for i, section in enumerate(_list):
            if section:
                bitmask |= 1 << i

        return bitmask


class PacketChunkData:
    # vanilla protocol
    x: int
    z: int
    full: bool
    heightmap: TagRoot
    biomes: bytes
    section_length: int
    sections: list
    block_entities: List[TagRoot]

    # custom protocol

    # if 0, this is not a full chunk. the biomes data will be empty and ignored.
    # if 1, this is a full chunk and as well as a new chunk
    # the biomes data should be 4096 bytes long, and client should force save the data
    # if 2, the biomes data will be empty, but client should find them in the cache.
    # signed Byte
    # in the same position as full presented in the vanilla protocol
    full: int

    # with bits set to 1 for every chunk that exist in the original packet
    # and the client should find those chunks in their cache
    # VarInt
    # in the end of the packet
    cached_section_mask: Bits

    def __init__(self, data: bytes):
        self.buff = CustomVanillaBuffer114(data)
        self.cached_section_mask = Bits()

    def pack_custom_packet_data(self):
        data_x_z = self.pack_x_z()
        data_full = self.pack_custom_full()
        data_bitmask2block_entities = self.pack_bitmask2block_entities()
        data_cached_section_mask = self.pack_cached_section_mask()

        return data_x_z + data_full + data_bitmask2block_entities + data_cached_section_mask

    def unpack_custom_packet_data(self):
        self.unpack_x_z()
        self.unpack_custom_full()
        self.unpack_bitmask2block_entities()
        self.unpack_cached_section_mask()

    def pack_vanilla_packet_data(self):
        data_x_z = self.pack_x_z()
        data_full = self.pack_vanilla_full()
        data_bitmask2block_entities = self.pack_bitmask2block_entities()

        return data_x_z + data_full + data_bitmask2block_entities

    def unpack_vanilla_packet_data(self):
        self.unpack_x_z()
        self.unpack_vanilla_full()
        self.unpack_bitmask2block_entities()

    def pack_x_z(self):
        return self.buff.pack('ii', self.x, self.z)

    def unpack_x_z(self):
        self.x, self.z = self.buff.unpack('ii')

    def pack_vanilla_full(self):
        return self.buff.pack('?', self.full)

    def unpack_vanilla_full(self):
        self.full = self.buff.unpack('?')

    def pack_custom_full(self):
        return self.buff.pack('B', self.full)

    def unpack_custom_full(self):
        self.full = self.buff.unpack('B')

    def pack_bitmask2block_entities(self):
        data_bitmask = self.buff.pack_varint(Bits.from_list(self.sections))
        data_heightmap = self.buff.pack_nbt(self.heightmap)
        data_biomes = self.biomes if self.full else b''
        data_sections = b''.join(i for i in self.sections if i)
        data_section_length = self.buff.pack_varint(len(data_sections))
        data_block_entity_num = self.buff.pack_varint(len(self.block_entities))
        data_block_entities = b''.join(self.buff.pack_nbt(entity) for entity in self.block_entities)

        return data_bitmask + data_heightmap + data_biomes + data_section_length \
                            + data_sections + data_block_entity_num + data_block_entities

    def unpack_bitmask2block_entities(self):
        bitmask = self.buff.unpack_varint()
        self.heightmap = self.buff.unpack_nbt()
        if self.full:
            self.biomes = self.buff.read(4*1024)  # biomes
        self.section_length = self.buff.unpack_varint()  # section_length
        self.sections = self.buff.unpack_chunk(bitmask)
        self.block_entities = [self.buff.unpack_nbt() for _ in range(self.buff.unpack_varint())]

    def pack_cached_section_mask(self):
        return self.buff.pack_varint(self.cached_section_mask.value)

    def unpack_cached_section_mask(self):
        self.cached_section_mask = Bits(self.buff.unpack_varint())

    def get_coords_bytes(self, y):
        return self.buff.pack_varint(self.x) + self.buff.pack_varint(self.z) + self.buff.pack('B', y)


# --- vanilla packets ---
class PacketHandshake:
    protocol_version: int
    server_address: str
    server_port: int
    next_state: int

    def __init__(self, data: bytes):
        buff = Buffer1_7(data)
        self.protocol_version = buff.unpack_varint()
        self.server_address = buff.unpack_string()
        self.server_port = buff.unpack('H')  # unsigned short
        self.next_state = buff.unpack_varint()


class PacketLoginSuccess:
    uuid: str
    username: str

    def __init__(self, data: bytes):
        buff = Buffer1_7(data)
        self.uuid = buff.unpack_string()
        self.username = buff.unpack_string()


class PacketSetCompression:
    threshold: int

    def __init__(self, data: bytes):
        buff = VarIntBuffer(data)
        self.threshold = buff.unpack_varint()


class PacketJoinGame:
    entity_id: int
    gamemode: int
    dimension: int

    def __init__(self, data):
        buff = VarIntBuffer(data)
        self.entity_id = buff.unpack('i')
        self.gamemode = buff.unpack('B')
        self.dimension = buff.unpack('i')


class PacketRespawn:
    dimension: int

    def __init__(self, data):
        buff = BaseBuffer(data)
        self.dimension = buff.unpack('i')


# --- custom packets ---
class PacketChunkDataAck:
    dimension: int
    chunk_x: int
    chunk_z: int
    section_ys: List[int]

    def __init__(self):
        self.section_ys = []

    def pack_packet(self):
        buff = VarIntBuffer()
        data_dimension = buff.pack('i', self.dimension)
        data_chunk_x = buff.pack_varint(self.chunk_x)
        data_chunk_z = buff.pack_varint(self.chunk_z)
        data_section_y = b''.join(buff.pack('B', i) for i in self.section_ys)
        return data_dimension + data_chunk_x + data_chunk_z + data_section_y

    def unpack_packet(self, data):
        buff = VarIntBuffer(data)
        self.dimension = buff.unpack('i')
        self.chunk_x = buff.unpack_varint()
        self.chunk_z = buff.unpack_varint()
        while len(buff):
            self.section_ys.append(buff.unpack('B'))
