import zstd

from utils.network import proxy
from utils.protocol import auto_process_protocol, local, get_session_info
from utils.buffers import CustomCompressBuffer17, VarIntBuffer
from utils.types import PacketChunkData, PacketChunkDataAck
from utils.packet_ids import *
from utils.config_manager import load_config, config
from utils.role_manager import set_role

set_role(1)

varint_buffer = VarIntBuffer()
compress_buffer = CustomCompressBuffer17()


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
            coords = packet_chunk_data.get_coords_bytes(y)
            get_session_info('chunk_section_db').put(coords, zstd.compress(section))
            cached_ys.append(y)

    # iter cached section mask
    for y in range(16):
        if packet_chunk_data.cached_section_mask.get(y):
            coords = packet_chunk_data.get_coords_bytes(y)
            packet_chunk_data.sections[y] = zstd.decompress(get_session_info('chunk_section_db').get(coords))

    # send ack packet
    if cached_ys:
        packet_chunk_data_ack = PacketChunkDataAck()

        packet_chunk_data_ack.dimension = get_session_info('dimension')
        packet_chunk_data_ack.chunk_x = packet_chunk_data.x
        packet_chunk_data_ack.chunk_z = packet_chunk_data.z
        for y in cached_ys:
            packet_chunk_data_ack.section_ys.append(y)

        try:
            send_packet(CHUNK_DATA_ACK, packet_chunk_data_ack.pack_packet())
        except OSError:
            pass

    return packet_chunk_data.pack_vanilla_packet_data()


def send_packet(packet_id, data):
    local.source.sendall(compress_buffer.pack_packet_custom(varint_buffer.pack_varint(packet_id) + data,
                                                            config['compression_threshold'],
                                                            config['compression_method']))


def main():
    load_config()
    proxy(config['listen_ip'], config['listen_port'],
          config['server_ip'], config['server_port'], s2c_process, c2s_process)


if __name__ == '__main__':
    main()
