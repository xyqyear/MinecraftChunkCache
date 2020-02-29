import socket

from quarry.types.buffer.v1_7 import Buffer1_7

from utils.network import proxy
from utils.protocol import unpack_original_chunk_data_1_15

listen_ip = '127.0.0.1'
listen_port = 2000
dst_ip = '127.0.0.1'
dst_port = 25565


def tweak(buff: Buffer1_7) -> bytes:
    # do nothing for now
    packet_id = buff.unpack_varint()
    if packet_id == 0x22:
        x, y, sections = unpack_original_chunk_data_1_15(buff.buff[buff.pos:])
    return Buffer1_7.pack_packet(buff.buff)


if __name__ == '__main__':
    proxy(listen_ip, listen_port, dst_ip, dst_port, tweak)
