import socket
import threading
from typing import *

from utils.protocol import iter_packets_from_socket, no_process


def forward(source: socket.socket, destination: socket.socket, process: Callable[[bytes], bytes]) -> None:
    """
    receive packets from source, process them using process function and send them to destination

    note: process function should receive a FULL network packet and return a FULL network packet.
          there is a auto_unpack_pack function you can use to simplify this process
    """
    for packet in iter_packets_from_socket(source):
        packet = process(packet)
        destination.sendall(packet)
    source.close()
    destination.close()


def proxy(listen_ip: str, listen_port: int, dst_ip: str, dst_port: int,
          s2c_process: Callable[[bytes], bytes], c2s_process: Callable[[bytes], bytes] = no_process) -> None:
    """
    a proxy that forwards data
    """
    while True:
        try:
            proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxy_socket.bind((listen_ip, listen_port))
            proxy_socket.listen(5)
            while True:
                client_socket = proxy_socket.accept()[0]
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.connect((dst_ip, dst_port))
                threading.Thread(target=forward, args=(client_socket, server_socket, c2s_process)).start()
                threading.Thread(target=forward, args=(server_socket, client_socket, s2c_process)).start()
        finally:
            pass
