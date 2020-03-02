import socket
from typing import *
from functools import partial

from quarry.types.buffer import BufferUnderrun

from utils.buffers import BasicPacketBuffer, CustomCompressBuffer17


def auto_unpack_pack(func, recv_compress=-1, send_compress=-1):
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

        packet_data = func(packet)

        return packet_buff.pack_packet(packet_data, send_compress)
    return wrapper


compress_auto_unpack_pack = partial(auto_unpack_pack, send_compress=256)
decompress_auto_unpack_pack = partial(auto_unpack_pack, recv_compress=256)
nocompress_auto_unpack_pack = auto_unpack_pack


def no_process(buff: bytes) -> bytes:
    return buff


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
