import socket
import threading
from typing import *

from utils.protocol import iter_packets_from_socket, sessions, local


def forward(source: socket.socket, destination: socket.socket,
            process: Callable[[bytes], bytes], session_id: int, direction: int):
    """
    direction: 0:c2s, 1:s2c

    receive packets from source, process them using process function and send them to destination

    note: process function should receive a FULL network packet and return a FULL network packet.
          there is a auto_unpack_pack function you can use to simplify this process
    """
    local.session_id = session_id
    local.direction = direction
    local.source = source
    local.destination = destination

    if local.session_id not in sessions:
        sessions[local.session_id] = {'state': 0, 'compression_threshold': -1}
    for packet in iter_packets_from_socket(local.source):
        try:
            packet = process(packet)
        except KeyError as e:
            print(e)
            continue

        # if discard, like chunk data ack packet. we dont want mc server to receive this kind of packet
        if not packet:
            continue
        try:
            local.destination.sendall(packet)
        except OSError:
            break
        except ConnectionAbortedError:
            break

    local.source.close()
    local.destination.close()
    if local.session_id in sessions:
        del sessions[local.session_id]


def proxy(listen_ip: str, listen_port: int, dst_ip: str, dst_port: int,
          s2c_process: Callable[[bytes], bytes], c2s_process: Callable[[bytes], bytes]):
    """
    a proxy that forwards data
    """
    session_id = 0
    while True:
        try:
            proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            proxy_socket.bind((listen_ip, listen_port))
            proxy_socket.listen(5)
            while True:
                client_socket = proxy_socket.accept()[0]
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.connect((dst_ip, dst_port))
                threading.Thread(target=forward, args=(client_socket, server_socket, c2s_process, session_id, 0)).start()
                threading.Thread(target=forward, args=(server_socket, client_socket, s2c_process, session_id, 1)).start()

                session_id += 1
        finally:
            pass
