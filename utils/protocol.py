import socket
import threading

from quarry.types.buffer import BufferUnderrun

from utils.buffers import BasicPacketBuffer, CustomCompressBuffer17
from utils.types import *
from utils.packet_ids import *
from utils.state_constants import *
from utils.database import Database
from utils.config_manager import config
from utils.role_manager import get_role

# {0: {state: int, compression_threshold: int, chunk_section_db: Database, chunk_section_hash: dict, ...}, 1: {...}}
sessions = {}
local = threading.local()


def auto_process_protocol(process):
    def wrapper(packet_bytes: bytes) -> bytes:
        packet_buff = CustomCompressBuffer17(packet_bytes)

        mc_compression_threshold = get_session_info('compression_threshold')

        # basically an xor
        # if data from proxy
        if get_role() == local.direction:
            packet = packet_buff.unpack_packet_custom(config['compression_threshold'],
                                                      config['compression_method'])
        else:
            packet = packet_buff.unpack_packet_custom(mc_compression_threshold,
                                                      'zlib')

        packet_id = packet.unpack_varint()
        packet_data = packet.buff[packet.pos:]

        # if packet from client to server
        if local.direction == 0:
            # if handshaking
            if get_session_info('state') == HANDSHAKING:
                if packet_id == HANDSHAKE:
                    packet_handshake = PacketHandshake(packet_data)
                    set_session_info('state', packet_handshake.next_state)

        # if packet from server to client
        elif local.direction == 1:
            if get_session_info('state') == LOGIN:
                if packet_id == SET_COMPRESSION:
                    packet_compression_threshold = PacketSetCompression(packet_data)
                    set_session_info('compression_threshold', packet_compression_threshold.threshold)

                elif packet_id == LOGIN_SUCCESS:
                    packet_login_success = PacketLoginSuccess(packet_data)
                    set_session_info('state', PLAY)
                    set_session_info('username', packet_login_success.username)

            if get_session_info('state') == PLAY:
                if packet_id == JOIN_GAME:
                    packet_join_game = PacketJoinGame(packet_data)
                    reset_dimension(packet_join_game.dimension)

                elif packet_id == RESPAWN:
                    packet_respawn = PacketRespawn(packet_data)
                    reset_dimension(packet_respawn.dimension)

        handled_packet_data = process(packet_id, packet_data)

        # if process function decides to drop the packet
        if handled_packet_data is None:
            return b''

        packet_data = packet_buff.pack_varint(packet_id) + handled_packet_data

        # if data to minecraft
        if get_role() == local.direction:
            return packet_buff.pack_packet_custom(packet_data, mc_compression_threshold, 'zlib')
        else:
            return packet_buff.pack_packet_custom(packet_data, config['compression_threshold'],
                                                  config['compression_method'])

    return wrapper


def reset_dimension(dimension: int):
    set_session_info('dimension', dimension)

    # start init database and hash table
    db_path = f'data/{"client" if get_role() else "server"}' \
              f'/{get_session_info("username")}/{dimension}/chunk_sections'
    set_session_info('chunk_section_db', Database(db_path))
    # if server
    if get_role() == 0:
        set_session_info('chunk_section_hash', dict())


def get_session_info(key: str):
    return sessions[local.session_id][key]


def set_session_info(key: str, value):
    sessions[local.session_id][key] = value


def iter_packets_from_socket(source: socket.socket) -> Iterator[bytes]:
    """
    return: Buffer1_7 (without the first 'length' varint)
    separate packets from data received
    """
    recv_buff = BasicPacketBuffer()
    while True:
        # handling network outside of network.py, but can not figure out a better way of doing this
        try:
            data = source.recv(1024)
        except ConnectionResetError:
            data = None
        except ConnectionAbortedError:
            data = None
        except OSError:
            data = None
        if not data:
            break

        # reference: quarry.net.protocol
        recv_buff.add(data)
        while True:
            recv_buff.save()
            try:
                yield recv_buff.recv_packet()
            except BufferUnderrun:
                recv_buff.restore()
                break
