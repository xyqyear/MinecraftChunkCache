import socket
import threading
from typing import *
from functools import partial

from quarry.types.buffer import BufferUnderrun

from utils.buffers import BasicPacketBuffer, CustomCompressBuffer17
from utils.types import PacketHandshake, PacketLoginSuccess
from utils.packet_ids import *
from utils.state_constants import *
from utils.database import Database

"""
clients = {0: {state: int, chunk_section_db: Database, chunk_section_hash: dict, ...}, 1: {...}}
"""
sessions = {}
local = threading.local()
# 0: proxy server, 1: proxy client
role = 0


def auto_unpack_pack(process, recv_compress=-1, send_compress=-1):
    """
    this decorator can help you
    retract data from full network packet
    (trim packet length, return a Buffer)
    and wrap the data you returned into a full network packet
    (re-calculate packet length and return a full network packet)
    """
    def wrapper(packet_bytes: bytes) -> bytes:
        packet_buff = CustomCompressBuffer17(packet_bytes)
        packet = packet_buff.unpack_packet(CustomCompressBuffer17, recv_compress)
        packet_id = packet.unpack_varint()
        packet_data = packet.buff[packet.pos:]

        # state switching
        # if packet from client to server
        if local.direction == 0:
            # if handshaking
            if get_client_info('state') == HANDSHAKING:
                if packet_id == HANDSHAKE:
                    packet_handshake = PacketHandshake(packet_data)
                    set_client_info('state', packet_handshake.next_state)

        # if packet from server to client
        elif local.direction == 1:
            if get_client_info('state') == LOGIN:
                if packet_id == LOGIN_SUCCESS:
                    packet_login_success = PacketLoginSuccess(packet_data)
                    sessions[local.session_id]['state'] = PLAY

                    # start init database and hash table
                    db_path = f'data/{"client" if get_role() else "server"}' \
                              f'/{packet_login_success.username}/chunk_sections'
                    set_client_info('chunk_section_db', Database(db_path))
                    # if server
                    if get_role() == 0:
                        set_client_info('chunk_section_hash', dict())

        handled_packet_data = process(packet_id, packet_data)

        # if process function decides to drop the packet
        if handled_packet_data is None:
            return b''

        packet_data = packet_buff.pack_varint(packet_id) + handled_packet_data
        return packet_buff.pack_packet(packet_data, send_compress)

    return wrapper


compress_auto_unpack_pack = partial(auto_unpack_pack, send_compress=256)
decompress_auto_unpack_pack = partial(auto_unpack_pack, recv_compress=256)
nocompress_auto_unpack_pack = auto_unpack_pack


def no_process(buff: bytes) -> bytes:
    return buff


def set_role(r: int):
    global role
    role = r


def get_role() -> int:
    global role
    return role


def get_client_info(key: str):
    return sessions[local.session_id][key]


def set_client_info(key: str, value):
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
