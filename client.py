import struct
import zstd

from utils.network import proxy
from utils.protocol import auto_process_protocol, local, get_session_info
from utils.types import PacketChunkData
from utils.buffers import VarIntBuffer, CustomCompressBuffer17
from utils.packet_ids import *
from utils.config_manager import load_config, config
from utils.role_manager import set_role

set_role(1)


@auto_process_protocol
def s2c_process(packet_id: int, packet_data: bytes) -> bytes:
    if packet_id == CHUNK_DATA:
        packet_data = handle_chunk_data(packet_data)

    return packet_data


# actually processing protocol state
@auto_process_protocol
def c2s_process(packet_id: int, packet_data: bytes) -> bytes:
    return packet_data


def handle_chunk_data(data: bytes) -> bytes:
    packet_chunk_data = PacketChunkData(data)
    packet_chunk_data.unpack_custom_packet_data()
    cached_ys = []
    for y, section in enumerate(packet_chunk_data.sections):
        # if section exists, put the data into database
        if section:
            coords = get_chunk_section_coords(packet_chunk_data, y)
            get_session_info('chunk_section_db').put(coords, zstd.compress(section))
            cached_ys.append(y)

    # iter cached section mask
    for y in range(16):
        if packet_chunk_data.cached_section_mask.get(y):
            coords = get_chunk_section_coords(packet_chunk_data, y)
            packet_chunk_data.sections[y] = zstd.decompress(get_session_info('chunk_section_db').get(coords))

    # send ack packet
    if cached_ys:
        coords = VarIntBuffer.pack_varint(packet_chunk_data.x) + VarIntBuffer.pack_varint(packet_chunk_data.z)
        for y in cached_ys:
            coords += struct.pack('B', y)
        try:
            local.source.sendall(
                CustomCompressBuffer17.pack_packet_custom(VarIntBuffer.pack_varint(CHUNK_DATA_ACK) + coords,
                                                          config['compression_threshold'],
                                                          config['compression_method'])
            )
        except OSError:
            pass

    return packet_chunk_data.pack_vanilla_packet_data()


def get_chunk_section_coords(chunk: PacketChunkData, y: int) -> bytes:
    return VarIntBuffer.pack_varint(chunk.x) + VarIntBuffer.pack_varint(chunk.z) + struct.pack('B', y)


def main():
    load_config()
    proxy(config['listen_ip'], config['listen_port'],
          config['server_ip'], config['server_port'], s2c_process, c2s_process)


if __name__ == '__main__':
    main()
