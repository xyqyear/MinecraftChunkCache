from utils.network import proxy
from utils.protocol import auto_process_protocol, get_session_info
from utils.types import PacketChunkData, PacketChunkDataAck
from utils.buffers import VarIntBuffer
from utils.hashes import hash32
from utils.packet_ids import *
from utils.state_constants import *
from utils.config_manager import load_config, config
from utils.role_manager import set_role

set_role(0)

varint_buffer = VarIntBuffer


@auto_process_protocol
def s2c_process(packet_id: int, packet_data: bytes):
    if get_session_info('state') == PLAY:
        if packet_id == CHUNK_DATA:
            packet_data = handle_chunk_data(packet_data)

    return packet_data


@auto_process_protocol
def c2s_process(packet_id: int, packet_data: bytes):
    if get_session_info('state') == PLAY:
        if packet_id == CHUNK_DATA_ACK:
            handle_chunk_data_ack(packet_data)
            return None

    return packet_data


def handle_chunk_data(data: bytes) -> bytes:
    packet_chunk_data = PacketChunkData(data)
    packet_chunk_data.unpack_vanilla_packet_data()

    for y, section in enumerate(packet_chunk_data.sections):
        if section:
            # if hash exists
            coords = packet_chunk_data.get_coords_bytes(y)
            saved_hash = get_session_info('chunk_section_db').get(coords)
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
                get_session_info('chunk_section_hash')[coords] = current_hash

    return packet_chunk_data.pack_custom_packet_data()


def handle_chunk_data_ack(data: bytes):
    packet_chunk_data_ack = PacketChunkDataAck()
    packet_chunk_data_ack.unpack_packet(data)

    if packet_chunk_data_ack.dimension != get_session_info('dimension'):
        return

    x = packet_chunk_data_ack.chunk_x
    z = packet_chunk_data_ack.chunk_z
    x_z_bytes = varint_buffer.pack_varint(x) + varint_buffer.pack_varint(z)

    for y in packet_chunk_data_ack.section_ys:
        coords = x_z_bytes + varint_buffer.pack('B', y)
        # del hash in dict before it goes into database to prevent sudden crash or forced close
        hash_dict = get_session_info('chunk_section_hash')
        if coords in hash_dict:
            section = hash_dict[coords]
            del hash_dict[coords]
            get_session_info('chunk_section_db').put(coords, section)


def main():
    load_config()
    proxy(config['listen_ip'], config['listen_port'],
          config['server_ip'], config['server_port'], s2c_process, c2s_process)


if __name__ == '__main__':
    main()
