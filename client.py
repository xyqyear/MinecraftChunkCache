from utils.network import proxy

listen_ip = '127.0.0.1'
listen_port = 1000
dst_ip = '127.0.0.1'
dst_port = 2000


def tweak(buff_bytes: bytes) -> bytes:
    return buff_bytes


if __name__ == '__main__':
    proxy(listen_ip, listen_port, dst_ip, dst_port, tweak)
