import socket
# 1.7 buffer is good enough to recognize packet
from quarry.types.buffer.v1_7 import Buffer1_7
from quarry.types.buffer import BufferUnderrun


def no_process(data: bytes) -> bytes:
    return data


def iter_packets_from_socket(source: socket.socket):
    recv_buff = Buffer1_7()
    while True:
        data = source.recv(1024)
        if not data:
            return

        # reference: quarry.net.protocol
        recv_buff.add(data)
        while True:
            recv_buff.save()
            try:
                packet_buff: Buffer1_7 = recv_buff.unpack_packet(Buffer1_7)
                yield Buffer1_7.pack_packet(packet_buff.buff)
            except BufferUnderrun:
                recv_buff.restore()
                break

