import socket

from quarry.types.buffer.v1_7 import Buffer1_7

from utils.network import proxy
from utils.protocol import PacketChunkData

listen_ip = '127.0.0.1'
listen_port = 2000
dst_ip = '127.0.0.1'
dst_port = 25565


def tweak(buff_bytes: bytes) -> bytes:
    buff = Buffer1_7(buff_bytes)
    packet_id: int = buff.unpack_varint()
    if packet_id == 0x22:
        packet_chunk_data = PacketChunkData(buff.buff[buff.pos:])
        return Buffer1_7.pack_packet(buff.pack_varint(packet_id) + packet_chunk_data.pack_packet_data())

    return Buffer1_7.pack_packet(buff.buff)


if __name__ == '__main__':
    proxy(listen_ip, listen_port, dst_ip, dst_port, tweak)
