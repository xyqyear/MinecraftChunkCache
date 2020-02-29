import socket
import struct

# 1.7 buffer is good enough to recognize packet
from quarry.types.buffer.v1_7 import Buffer1_7
from quarry.types.buffer.v1_14 import Buffer1_14
from quarry.types.buffer import BufferUnderrun

from typing import *


def no_process(buff: Buffer1_7) -> bytes:
    return Buffer1_7.pack_packet(buff.buff)


def iter_packets_from_socket(source: socket.socket) -> Iterator[Buffer1_7]:
    """
    return: Buffer1_7 (without the first 'length' varint)
    separate packets from data received
    """
    recv_buff = Buffer1_7()
    while True:
        # handling network outside of network.py, but can not figure out a better way of doing this
        data = source.recv(1024)
        if not data:
            break

        # reference: quarry.net.protocol
        recv_buff.add(data)
        while True:
            recv_buff.save()
            try:
                packet_buff: Buffer1_7 = recv_buff.unpack_packet(Buffer1_7)
                yield packet_buff
            except BufferUnderrun:
                recv_buff.restore()
                break
