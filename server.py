import socket

from utils.network import proxy

listen_ip = '127.0.0.1'
listen_port = 2000
dst_ip = '127.0.0.1'
dst_port = 25565


def tweak(data: bytes) -> bytes:
    return data


if __name__ == '__main__':
    proxy(listen_ip, listen_port, dst_ip, dst_port, tweak)
