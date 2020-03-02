import struct

from quarry.types.buffer.v1_7 import Buffer1_7

from utils.network import proxy
from utils.protocol import client_auto_unpack_pack
from utils.types import PacketChunkData
from utils.buffers import VarIntBuffer
from utils.database import Database

listen_ip = '127.0.0.1'
listen_port = 1000
dst_ip = '127.0.0.1'
dst_port = 2000

db = Database('data/test/chunk_sections')


@client_auto_unpack_pack
def tweak(buff: Buffer1_7) -> bytes:
    packet_id = buff.unpack_varint()
    packet_data = buff.buff[buff.pos:]
    if packet_id == 0x22:
        packet_data = handle_chunk_data(packet_data)

    return buff.pack_varint(packet_id) + packet_data


def handle_chunk_data(data: bytes) -> bytes:
    packet_chunk_data = PacketChunkData(data)
    packet_chunk_data.unpack_custom_packet_data()

    for i, section in enumerate(packet_chunk_data.sections):
        # if section exists, put the data into database
        if section:
            coords = get_chunk_section_coords(packet_chunk_data, i)
            db.put(coords, section)
            print(packet_chunk_data.x, packet_chunk_data.z, i, "caching...")

    # iter cached section mask
    for i in range(16):
        if packet_chunk_data.cached_section_mask.get(i):
            coords = get_chunk_section_coords(packet_chunk_data, i)
            packet_chunk_data.sections[i] = db.get(coords)
            print(packet_chunk_data.x, packet_chunk_data.z, i, "loaded from database")

    for i in range(16):
        print(packet_chunk_data.x, packet_chunk_data.z, packet_chunk_data.cached_section_mask.get(i), end='')
    print()

    return packet_chunk_data.pack_vanilla_packet_data()


def get_chunk_section_coords(chunk: PacketChunkData, y: int) -> bytes:
    return VarIntBuffer.pack_varint(chunk.x) + VarIntBuffer.pack_varint(chunk.z) + struct.pack('B', y)


if __name__ == '__main__':
    proxy(listen_ip, listen_port, dst_ip, dst_port, tweak)
