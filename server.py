import struct

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

db = Database('data/test/chunk_sections_hash')


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

    for i, section in enumerate(packet_chunk_data.sections):
        if section:
            # if hash exists
            coords = get_chunk_section_coords(packet_chunk_data, i)
            saved_hash = db.get(coords)
            current_hash = hash32(section)
            update_flag = False
            # if section unchanged, then delete section, otherwise, update hash in the database
            if saved_hash:
                if current_hash == saved_hash:
                    packet_chunk_data.cached_section_mask.put(i, True)
                    packet_chunk_data.sections[i] = None
                else:
                    update_flag = True
            else:
                update_flag = True

            if update_flag:
                db.put(coords, current_hash)

    return packet_chunk_data.pack_custom_packet_data()


def get_chunk_section_coords(chunk: PacketChunkData, y: int) -> bytes:
    return VarIntBuffer.pack_varint(chunk.x) + VarIntBuffer.pack_varint(chunk.z) + struct.pack('B', y)


if __name__ == '__main__':
    proxy(listen_ip, listen_port, dst_ip, dst_port, tweak)
