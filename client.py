import struct
import zstd

from quarry.types.buffer.v1_7 import Buffer1_7

from utils.network import proxy, local
from utils.protocol import decompress_auto_unpack_pack
from utils.types import PacketChunkData
from utils.buffers import VarIntBuffer, CustomCompressBuffer17
from utils.database import Database
from utils.packet_ids import CHUNK_DATA, CHUNK_DATA_ACK

listen_ip = '127.0.0.1'
listen_port = 1000
dst_ip = '127.0.0.1'
dst_port = 2000

chunk_section_db = Database('data/test/chunk_sections')


@decompress_auto_unpack_pack
def s2c_process(buff: Buffer1_7) -> bytes:
    packet_id = buff.unpack_varint()
    packet_data = buff.buff[buff.pos:]

    if packet_id == CHUNK_DATA:
        packet_data = handle_chunk_data(packet_data)

    return buff.pack_varint(packet_id) + packet_data


def handle_chunk_data(data: bytes) -> bytes:
    packet_chunk_data = PacketChunkData(data)
    packet_chunk_data.unpack_custom_packet_data()
    cached_ys = []
    for y, section in enumerate(packet_chunk_data.sections):
        # if section exists, put the data into database
        if section:
            coords = get_chunk_section_coords(packet_chunk_data, y)
            chunk_section_db.put(coords, zstd.compress(section))
            cached_ys.append(y)

    # iter cached section mask
    for y in range(16):
        if packet_chunk_data.cached_section_mask.get(y):
            coords = get_chunk_section_coords(packet_chunk_data, y)
            packet_chunk_data.sections[y] = zstd.decompress(chunk_section_db.get(coords))

    # send ack packet
    if cached_ys:
        coords = VarIntBuffer.pack_varint(packet_chunk_data.x) + VarIntBuffer.pack_varint(packet_chunk_data.z)
        for y in cached_ys:
            coords += struct.pack('B', y)
        local.source.sendall(CustomCompressBuffer17.pack_packet(VarIntBuffer.pack_varint(CHUNK_DATA_ACK) + coords))

    return packet_chunk_data.pack_vanilla_packet_data()


def get_chunk_section_coords(chunk: PacketChunkData, y: int) -> bytes:
    return VarIntBuffer.pack_varint(chunk.x) + VarIntBuffer.pack_varint(chunk.z) + struct.pack('B', y)


if __name__ == '__main__':
    proxy(listen_ip, listen_port, dst_ip, dst_port, s2c_process)
