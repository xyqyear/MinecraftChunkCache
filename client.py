from quarry.types.buffer.v1_7 import Buffer1_7

from utils.network import proxy
from utils.protocol import client_auto_unpack_pack
from utils.types import PacketChunkData

listen_ip = '127.0.0.1'
listen_port = 1000
dst_ip = '127.0.0.1'
dst_port = 2000


@client_auto_unpack_pack
def tweak(buff: Buffer1_7) -> bytes:
    packet_id = buff.unpack_varint()
    if packet_id == 0x22 and False:
        packet_chunk_data = PacketChunkData(buff.buff[buff.pos:])
        print(f'{len(buff.buff)}, {len(b"".join(i for i in packet_chunk_data.sections if i))},'
              f' {len(packet_chunk_data.biomes) if packet_chunk_data.full else 0}\n')
        return buff.pack_varint(packet_id) + packet_chunk_data.pack_packet_data()

    return buff.buff


if __name__ == '__main__':
    proxy(listen_ip, listen_port, dst_ip, dst_port, tweak)
