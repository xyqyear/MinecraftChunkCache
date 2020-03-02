import struct

from quarry.types.buffer.v1_7 import Buffer1_7

from utils.network import proxy
from utils.protocol import compress_auto_unpack_pack, nocompress_auto_unpack_pack
from utils.types import PacketChunkData
from utils.buffers import VarIntBuffer
from utils.database import Database
from utils.hashes import hash32
from utils.packet_ids import CHUNK_DATA, CHUNK_DATA_ACK

listen_ip = '127.0.0.1'
listen_port = 2000
dst_ip = '127.0.0.1'
dst_port = 25565

chunk_section_db = Database('data/test/chunk_sections_hash')
chunk_section_hash = dict()


@compress_auto_unpack_pack
def s2c_process(buff: Buffer1_7) -> bytes:
    packet_id = buff.unpack_varint()
    packet_data = buff.buff[buff.pos:]

    if packet_id == CHUNK_DATA:
        packet_data = handle_chunk_data(packet_data)

    return buff.pack_varint(packet_id) + packet_data


@nocompress_auto_unpack_pack
def c2s_process(buff: Buffer1_7) -> bytes:
    packet_id = buff.unpack_varint()
    packet_data = buff.buff[buff.pos:]

    if packet_id == CHUNK_DATA_ACK:
        handle_chunk_data_ack(packet_data)
        return b''

    return buff.pack_varint(packet_id) + packet_data


def handle_chunk_data(data: bytes) -> bytes:
    packet_chunk_data = PacketChunkData(data)
    packet_chunk_data.unpack_vanilla_packet_data()

    for y, section in enumerate(packet_chunk_data.sections):
        if section:
            # if hash exists
            coords = get_chunk_section_coords(packet_chunk_data, y)
            saved_hash = chunk_section_db.get(coords)
            current_hash = hash32(section)
            update_flag = False
            # if section unchanged, then delete section, otherwise, update hash in the database
            if saved_hash:
                if current_hash == saved_hash:
                    packet_chunk_data.cached_section_mask.put(y, True)
                    packet_chunk_data.sections[y] = None
                else:
                    update_flag = True
            else:
                update_flag = True

            if update_flag:
                chunk_section_hash[coords] = current_hash

    return packet_chunk_data.pack_custom_packet_data()


def handle_chunk_data_ack(data: bytes):
    buff = VarIntBuffer(data)
    x = buff.unpack_varint()
    z = buff.unpack_varint()
    buff.save()
    x_z_bytes = buff.pack_varint(x) + buff.pack_varint(z)

    # y is int for some reason
    for y in buff.buff:
        coords = x_z_bytes + struct.pack('B', y)
        # del hash in dict before it goes into database to prevent sudden crash or forced close
        section = chunk_section_hash[coords]
        del chunk_section_hash[coords]
        chunk_section_db.put(coords, section)


def get_chunk_section_coords(chunk: PacketChunkData, y: int) -> bytes:
    return VarIntBuffer.pack_varint(chunk.x) + VarIntBuffer.pack_varint(chunk.z) + struct.pack('B', y)


if __name__ == '__main__':
    proxy(listen_ip, listen_port, dst_ip, dst_port, s2c_process, c2s_process)
