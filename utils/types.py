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


# --- vanilla packets ---
# some of them are not fully unpacked, because no need for the rest of the data
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


class PacketLoginStart:
    username: str

    def __init__(self, data: bytes):
        buff = Buffer1_7(data)
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


# --- semi-vanilla packets ---
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
    # with bits set to 1 for every chunk that exist in the original packet
    # and the client should find those chunks in their cache
    # VarInt
    # in the end of the packet
    cached_section_mask: Bits

    def __init__(self, data: bytes):
        self.buff = CustomVanillaBuffer114(data)
        self.cached_section_mask = Bits()

    def pack_vanilla_packet_data(self):
        data_x_z_full = self.buff.pack('ii?', self.x, self.z, self.full)
        data_bitmask = self.buff.pack_varint(Bits.from_list(self.sections))
        data_heightmap = self.buff.pack_nbt(self.heightmap)
        data_biomes = self.biomes if self.full else b''
        data_sections = b''.join(i for i in self.sections if i)
        data_section_length = self.buff.pack_varint(len(data_sections))
        data_block_entity_num = self.buff.pack_varint(len(self.block_entities))
        data_block_entities = b''.join(self.buff.pack_nbt(entity) for entity in self.block_entities)

        return data_x_z_full + data_bitmask + data_heightmap + data_biomes + data_section_length + \
               data_sections + data_block_entity_num + data_block_entities

    def unpack_vanilla_packet_data(self):
        self.x, self.z, self.full = self.buff.unpack('ii?')
        bitmask = self.buff.unpack_varint()
        self.heightmap = self.buff.unpack_nbt()
        if self.full:
            self.biomes = self.buff.read(4 * 1024)  # biomes
        self.section_length = self.buff.unpack_varint()  # section_length
        self.sections = self.buff.unpack_chunk(bitmask)
        self.block_entities = [self.buff.unpack_nbt() for _ in range(self.buff.unpack_varint())]

    def pack_custom_packet_data(self):
        vanilla_data = self.pack_vanilla_packet_data()
        data_cached_section_mask = self.buff.pack_varint(self.cached_section_mask.value)
        return vanilla_data + data_cached_section_mask

    def unpack_custom_packet_data(self):
        self.unpack_vanilla_packet_data()
        self.cached_section_mask = Bits(self.buff.unpack_varint())

    def get_coords_bytes(self, y):
        return self.buff.pack_varint(self.x) + self.buff.pack_varint(self.z) + self.buff.pack('B', y)


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
