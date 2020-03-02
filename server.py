import struct
import os

from typing import *

from quarry.types.buffer.v1_7 import Buffer1_7

from utils.network import proxy
from utils.protocol import server_auto_unpack_pack
from utils.types import PacketChunkData
from utils.buffers import VarIntBuffer
from utils.database import Database
from utils.hashes import hash32


listen_ip = '127.0.0.1'
listen_port = 2000
dst_ip = '127.0.0.1'
dst_port = 25565

if not os.path.exists('data/test/chunk_sections'):
    os.makedirs('data/test/chunk_sections')
db = Database('data/test/chunk_sections')


@server_auto_unpack_pack
def tweak(buff: Buffer1_7) -> bytes:
    packet_id = buff.unpack_varint()
    packet_data = buff.buff[buff.pos:]
    if packet_id == 0x22:
        packet_data = handle_chunk_data(packet_data)

    return buff.pack_varint(packet_id) + packet_data


def handle_chunk_data(data: bytes) -> bytes:
    packet_chunk_data = PacketChunkData(data)
    packet_chunk_data.unpack_vanilla_packet_data()

    section_dict = get_chunk_section_keys_values(packet_chunk_data)
    for key, value in section_dict.items():
        db.put(key, value)

    return packet_chunk_data.pack_vanilla_packet_data()


def get_chunk_section_keys_values(chunk: PacketChunkData) -> Dict[bytes, bytes]:
    """
    returns a dict the key in which is coordinate in bytes form and the value in which is section bytes
    """
    coordinate_prefix = VarIntBuffer.pack_varint(chunk.x) + VarIntBuffer.pack_varint(chunk.z)
    return {coordinate_prefix+struct.pack('b', i): chunk.sections[i] for i in range(16) if chunk.sections[i]}


if __name__ == '__main__':
    proxy(listen_ip, listen_port, dst_ip, dst_port, tweak)
